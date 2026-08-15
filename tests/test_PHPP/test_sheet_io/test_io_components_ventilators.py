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
from PHX.PHPP.sheet_io.io_addnl_vent import Spaces
from PHX.PHPP.sheet_io.io_components import Frames, Ventilators
from PHX.PHPP.sheet_io.io_exceptions import ResolveComponentIDException
from PHX.xl.xl_app import XLConnection
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")
SHAPE_FILENAMES = (
    "EN_9_6A.json",
    "EN_9_7IP.json",
    "EN_10_3.json",
    "EN_10_4A.json",
    "EN_10_4IP.json",
    "EN_10_6.json",
    "EN_10_6IP.json",
)

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

HEADER_ROW = 8
FIRST_ENTRY_ROW = 13
LAST_ENTRY_ROW = 42


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
# -- Section-header location: the returned value must be a ROW NUMBER


@pytest.mark.parametrize("shape_filename", SHAPE_FILENAMES)
def test_ventilator_header_row_is_a_row_number_not_an_index(shape_filename: str) -> None:
    """The header on row 8 must report as 8, not as its 0-based index in the read block."""
    shape = components_shape(shape_filename)
    xl = Mock()
    xl.get_single_column_data.return_value = [None] * (HEADER_ROW - 1) + [shape.ventilators.locator_string_header]

    assert Ventilators(xl, shape).find_section_header_row() == HEADER_ROW


def test_ventilator_header_row_honours_a_non_default_row_start() -> None:
    """A search that begins at row 50 must report rows relative to row 50."""
    shape = components_shape()
    xl = Mock()
    xl.get_single_column_data.return_value = [shape.ventilators.locator_string_header]

    assert Ventilators(xl, shape).find_section_header_row(_row_start=50) == 50


def test_frame_header_row_is_a_row_number_not_an_index() -> None:
    shape = components_shape()
    xl = Mock()
    xl.get_single_column_data.return_value = [None] * 7 + [shape.frames.locator_string_header]

    assert Frames(xl, shape).find_section_header_row() == 8


def test_room_header_row_is_a_row_number_not_an_index() -> None:
    shape = load_shape("EN_10_6.json").ADDNL_VENT
    xl = Mock()
    xl.get_single_column_data.return_value = [None] * 7 + [shape.rooms.locator_string_header]

    assert Spaces(xl, shape).find_section_header_row() == 8


# -----------------------------------------------------------------------------
# -- Characterization: the entry-row locator is invariant under the fix above.
# -- It read from 'section_header_row' and enumerated from the same value, so
# -- the old off-by-one cancelled. These must stay green before AND after.


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
