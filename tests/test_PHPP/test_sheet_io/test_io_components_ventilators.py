# -*- Python Version: 3.10 -*-

"""Tests for the PHPP 'Components' ventilator section locators and ID lookup.

The ventilator block lives at 'Components!LQ:MF'. In a pristine PHPP 10.6 EN
workbook the section header ("Ventilation units") sits on row 8, the column
labels on row 11, the unit labels ("%", "%", "Wh/m3") on row 12, and the first
user-entry row ("01ud") on row 13.

Row positions are NOT fixed: an entry block sits lower in a populated project
file than in an empty one, which is why the IO classes locate the section by
searching for its header/entry marker strings rather than hard-coding rows.
The tests below therefore pin the *locator behaviour*, not the row numbers of
any one workbook.

PHPP's own performance lookups read 'Components!$LQ$13:$MF$914' - the entry
section only. Anything above the first entry row is unresolvable to PHPP, so
PHX must never build a component ID out of it.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from PHX.model import hvac, project
from PHX.PHPP import phpp_app
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.sheet_io.io_components import Frames, Ventilators
from PHX.PHPP.sheet_io.io_exceptions import ResolveComponentIDException
from PHX.xl.xl_app import XLConnection
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")
REPLAY_FIXTURE = Path("tests", "test_xl_replay", "fixtures", "single_zone_replay.json")

# -- The pristine 'Components' ventilator block, read from PHPP_EN_V10.6_Empty.xlsx.
PRISTINE_VENTILATOR_BLOCK: dict[str, object] = {
    "LQ6": "◄ Contents",
    "LR6": "Link to 'Addl vent' worksheet",
    "LQ8": "Ventilation units",
    "LQ9": "Typical for climate zone 'Cool-temperate': Frost protection: Yes, humidity recovery: No",
    "LS9": "75 %",
    "LW9": 0.45,
    "LS10": "Heating period",
    "LQ11": "ID",
    "LR11": "Description",
    "LS11": "Heat recovery efficiency",
    "LT11": "Humidity recovery efficiency hERV",
    "LW11": "Specific electric power",
    "MB11": "Frost protection necessary",
    "LS12": "%",
    "LT12": "%",
    "LW12": "Wh/m³",
    **{f"LQ{12 + i}": f"{i:02d}ud" for i in range(1, 31)},
}

# -- The pristine 'Addl vent' ventilation-unit block, from the same workbook.
PRISTINE_VENT_UNIT_BLOCK: dict[str, object] = {
    "C63": "Selection of the ventilation unit",
    "F64": "Go to list of ventilation units",
    "C65": "Venti-",
    "D65": "Quan-",
    "E65": "Description of",
    "F65": "Selection of",
    "C66": "lation",
    "D66": "tity",
    "E66": "ventilation units",
    "F66": "ventilation unit",
    "C67": "unit no.",
    "D68": "[-]",
    "F69": "Sorting options",
    **{f"C{69 + i}": i for i in range(1, 11)},
}

FIRST_ENTRY_ROW = 13
LAST_ENTRY_ROW = 42
UNIT_SELECTION_COL = "F"
FIRST_UNIT_ROW = 70


def load_shape(filename: str) -> PhppShape:
    return PhppShape.model_validate_json((SHAPE_DIR / filename).read_bytes())


def components_shape(filename: str = "EN_10_6.json"):
    return load_shape(filename).COMPONENTS


def connect(_extra_components: dict | None = None) -> tuple[FakeXLFramework, XLConnection, phpp_app.PHPPConnection]:
    """Return a PHPPConnection backed by a fake workbook holding a pristine ventilator block.

    The sheet list and base seed come from the replay fixture so that
    'PHPPConnection' can initialize (it reads the 'Data' and 'Areas' sheets).
    """
    import json

    fixture = json.loads(REPLAY_FIXTURE.read_text())
    seed = dict(fixture["seed"])
    seed["Components"] = {**PRISTINE_VENTILATOR_BLOCK, **(_extra_components or {})}
    seed["Addl vent"] = dict(PRISTINE_VENT_UNIT_BLOCK)

    fake_xl = FakeXLFramework(sheet_names=fixture["sheet_names"], seed=seed)
    connection = XLConnection(xl_framework=fake_xl)
    return fake_xl, connection, phpp_app.PHPPConnection(connection)


def build_ventilator(_name: str) -> hvac.PhxDeviceVentilator:
    vent = hvac.PhxDeviceVentilator()
    vent.display_name = _name
    vent.params.sensible_heat_recovery = 0.75
    vent.params.latent_heat_recovery = 0.6
    vent.params.electric_efficiency = 0.45
    vent.params.frost_protection_reqd = True
    return vent


def build_project(_ventilator_names_by_variant: list[list[str]]) -> project.PhxProject:
    """Return a PhxProject with one variant per inner list, carrying those ventilators."""
    phx_project = project.PhxProject()
    for variant_names in _ventilator_names_by_variant:
        variant = project.PhxVariant()
        phx_project.add_new_variant(variant)
        for i, name in enumerate(variant_names):
            vent = build_ventilator(name)
            variant.mech_collections[0].add_new_mech_device(f"{vent.identifier}_{i}", vent)
    return phx_project


def row_num(_address: str) -> int:
    return int("".join(c for c in _address if c.isdigit()))


# -----------------------------------------------------------------------------
# -- Entry-section location.
# --
# -- 'find_section_header_row' is covered in test_section_header_locators.py.
# -- The entry-row locators below are invariant under that fix: they read from
# -- 'section_header_row' and enumerate from the same value, so the old
# -- off-by-one cancelled. They must stay green before AND after it.


def test_first_entry_row_is_located_in_a_pristine_phpp(reset_class_counters) -> None:
    _, _, phpp = connect()
    assert phpp.components.ventilators.section_first_entry_row == FIRST_ENTRY_ROW


def test_last_entry_row_is_located_in_a_pristine_phpp(reset_class_counters) -> None:
    _, _, phpp = connect()
    assert phpp.components.ventilators.section_last_entry_row == LAST_ENTRY_ROW


def test_last_entry_row_is_correct_when_the_section_exceeds_one_read_block() -> None:
    """The 500-row recursion must report rows relative to the block it just read."""
    shape = components_shape()
    xl = Mock()
    xl.get_single_column_data.side_effect = (
        ["01ud"] * 501,  # -- rows 13..513, no gap: recurse
        ["01ud"] * 10 + [None] * 491,  # -- rows 513..1013, first gap on row 523
    )

    ventilators = Ventilators(xl, shape)
    ventilators._section_first_entry_row = FIRST_ENTRY_ROW

    assert ventilators.find_section_last_entry_row() == 522


def test_frame_last_entry_row_is_correct_when_the_section_exceeds_one_read_block() -> None:
    """Same recursion defect on the Frames section, which reaches it via find_first_empty_row()."""
    shape = components_shape()
    xl = Mock()
    xl.get_single_column_data.side_effect = (
        ["01ud"] * 501,
        ["01ud"] * 10 + [None] * 491,
    )

    frames = Frames(xl, shape)
    frames._section_first_entry_row = FIRST_ENTRY_ROW

    assert frames.find_section_last_entry_row() == 522


# -----------------------------------------------------------------------------
# -- Component-ID lookup: bounded to the entry section, and never silently 'None'


def test_ventilator_id_resolves_against_the_entry_row(reset_class_counters) -> None:
    _, _, phpp = connect({"LR13": "REF-HRV"})
    assert phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV") == "01ud-REF-HRV"


def test_ventilator_id_ignores_a_matching_name_in_the_label_row(reset_class_counters) -> None:
    """LR12 is the units label row - above the entry section, and unresolvable to PHPP.

    This is the reported defect: the unbounded scan matched row 12 first and
    read its empty ID cell, yielding "None-REF-HRV".
    """
    _, _, phpp = connect({"LR12": "REF-HRV", "LR13": "REF-HRV"})
    assert phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV") == "01ud-REF-HRV"


def test_ventilator_id_never_formats_none_into_the_string(reset_class_counters) -> None:
    _, _, phpp = connect({"LR12": "REF-HRV", "LR13": "REF-HRV"})
    assert "None-" not in phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV")


def test_ventilator_id_raises_when_the_id_cell_is_empty(reset_class_counters) -> None:
    """An explicit row-span may still reach a row with no ID; it must fail loudly."""
    _, _, phpp = connect({"LR12": "REF-HRV"})

    with pytest.raises(ResolveComponentIDException):
        # -- the pre-fix default span, kept available for callers
        phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV", _row_start=1, _row_end=500)


def test_ventilator_id_by_row_num_raises_when_the_id_cell_is_empty(reset_class_counters) -> None:
    _, _, phpp = connect({"LR12": "REF-HRV"})

    with pytest.raises(ResolveComponentIDException):
        phpp.components.ventilators.get_ventilator_phpp_id_by_row_num(12)


def test_ventilator_id_raises_when_the_name_is_absent(reset_class_counters) -> None:
    _, _, phpp = connect()

    with pytest.raises(Exception, match="NOT-A-VENTILATOR"):
        phpp.components.ventilators.get_ventilator_phpp_id_by_name("NOT-A-VENTILATOR")


def test_ventilator_id_honours_an_explicit_row_span(reset_class_counters) -> None:
    """Backwards compatibility: explicit bounds still override the section bounds."""
    _, _, phpp = connect({"LR13": "REF-HRV"})

    with pytest.raises(Exception, match="REF-HRV"):
        # -- a span that excludes row 13 must not find it
        phpp.components.ventilators.get_ventilator_phpp_id_by_name("REF-HRV", _row_start=20, _row_end=30)


# -----------------------------------------------------------------------------
# -- Write path: the ventilator must land in the entry section, and only there.


@pytest.mark.parametrize(
    "ventilator_names_by_variant, expected_rows",
    (
        pytest.param([["REF-HRV"]], {13}, id="one-variant-one-unit"),
        pytest.param([["REF-HRV-A"], ["REF-HRV-B"]], {13, 14}, id="two-variants-one-unit-each"),
        pytest.param([["REF-HRV", "REF-HRV"]], {13, 14}, id="one-variant-two-units"),
    ),
)
def test_ventilator_write_touches_only_entry_rows(
    reset_class_counters, ventilator_names_by_variant: list[list[str]], expected_rows: set[int]
) -> None:
    """Regression: nothing may be written into the label row (12) or any row above it."""
    fake_xl, connection, phpp = connect()

    with connection.in_silent_mode():
        phpp.write_project_ventilation_components(build_project(ventilator_names_by_variant))

    written = fake_xl.written_state()["Components"]
    assert {row_num(address) for address in written} == expected_rows


def test_ventilator_write_fills_every_mapped_input_column(reset_class_counters) -> None:
    fake_xl, connection, phpp = connect()

    with connection.in_silent_mode():
        phpp.write_project_ventilation_components(build_project([["REF-HRV"]]))

    written = fake_xl.written_state()["Components"]
    assert written == {
        "LR13": "REF-HRV",
        "LS13": 0.75,
        "LT13": 0.6,
        "LW13": 0.45,
        "MB13": "yes",
    }


def test_full_ventilator_round_trip_produces_a_resolvable_unit_selection(reset_class_counters) -> None:
    """The chain that produced the bad workbook: write Components, look the name back up, write 'Addl vent'.

    A PHPP-resolvable selection carries the entry-row ID prefix. "None-REF-HRV"
    is what the unbounded lookup used to write here, and PHPP silently zeroed
    the unit's heat recovery in response.
    """
    fake_xl, connection, phpp = connect()
    phx_project = build_project([["REF-HRV"]])

    with connection.in_silent_mode():
        phpp.write_project_ventilation_components(phx_project)
        phpp.write_project_ventilators(phx_project)

    selection = fake_xl.written_state()["Addl vent"][f"{UNIT_SELECTION_COL}{FIRST_UNIT_ROW}"]
    assert selection == "01ud-REF-HRV"


def test_full_ventilator_round_trip_numbers_multiple_units_in_project_order(reset_class_counters) -> None:
    fake_xl, connection, phpp = connect()
    phx_project = build_project([["REF-HRV-A"], ["REF-HRV-B"]])

    with connection.in_silent_mode():
        phpp.write_project_ventilation_components(phx_project)
        phpp.write_project_ventilators(phx_project)

    written = fake_xl.written_state()["Addl vent"]
    assert written[f"{UNIT_SELECTION_COL}{FIRST_UNIT_ROW}"] == "01ud-REF-HRV-A"
    assert written[f"{UNIT_SELECTION_COL}{FIRST_UNIT_ROW + 1}"] == "02ud-REF-HRV-B"


def test_full_ventilator_round_trip_survives_a_name_in_the_label_row(reset_class_counters) -> None:
    """The reported failure, end to end.

    With the ventilator's name also present in the units label row (12), the
    unbounded lookup matched that row, read its empty ID cell, and wrote
    "None-REF-HRV" into the 'Addl vent' unit selection. PHPP cannot resolve
    that, so 'Ventilation'!L32 (effective heat recovery) fell to 0 and the
    workbook modelled a balanced HRV with no heat recovery at all.
    """
    fake_xl, connection, phpp = connect({"LR12": "REF-HRV"})
    phx_project = build_project([["REF-HRV"]])

    with connection.in_silent_mode():
        phpp.write_project_ventilation_components(phx_project)
        phpp.write_project_ventilators(phx_project)

    assert fake_xl.written_state()["Addl vent"][f"{UNIT_SELECTION_COL}{FIRST_UNIT_ROW}"] == "01ud-REF-HRV"
