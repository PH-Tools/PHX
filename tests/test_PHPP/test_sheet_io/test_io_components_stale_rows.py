# -*- Python Version: 3.10 -*-

"""Tests for stale trailing rows in PHPP Components-section writes."""

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from PHX.model import constructions, hvac
from PHX.PHPP.phpp_model.component_frame import FrameRow
from PHX.PHPP.phpp_model.component_glazing import GlazingRow
from PHX.PHPP.phpp_model.component_vent import VentilatorRow
from PHX.PHPP.phpp_localization.shape_model import Components as ComponentsShape
from PHX.PHPP.sheet_io.io_components import Components
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

FIRST_ENTRY_ROW = 13
LAST_ENTRY_ROW = 18


@dataclass(frozen=True)
class SectionCase:
    section_name: str
    write_one_row: Callable[[Components], None]
    write_one_row_clear: Callable[[Components], None]
    stale_seed: dict[str, object]
    clean_seed: dict[str, object]
    expected_clear_ranges: tuple[str, ...]
    untouched_cells: tuple[str, ...]


def _components_shape() -> ComponentsShape:
    return load_shape("EN_10_6.json").COMPONENTS


def _window_type(_name: str) -> constructions.PhxConstructionWindow:
    window_type = constructions.PhxConstructionWindow.from_total_u_value(1.2, _g_value=0.52, _display_name=_name)
    window_type.frame_left.width = 0.08
    window_type.frame_right.width = 0.08
    window_type.frame_bottom.width = 0.1
    window_type.frame_top.width = 0.1
    return window_type


def _ventilator(_name: str) -> hvac.PhxDeviceVentilator:
    ventilator = hvac.PhxDeviceVentilator()
    ventilator.display_name = _name
    ventilator.params.sensible_heat_recovery = 0.75
    ventilator.params.latent_heat_recovery = 0.4
    ventilator.params.electric_efficiency = 0.45
    ventilator.params.frost_protection_reqd = True
    return ventilator


def _base_seed() -> dict[str, object]:
    seed: dict[str, object] = {
        "IO8": "Window and door frames",
        "LQ8": "Ventilation units",
    }
    seed.update(
        {f"IH{row}": f"{row - FIRST_ENTRY_ROW + 1:02d}ud" for row in range(FIRST_ENTRY_ROW, LAST_ENTRY_ROW + 1)}
    )
    seed.update(
        {f"IO{row}": f"{row - FIRST_ENTRY_ROW + 1:02d}ud" for row in range(FIRST_ENTRY_ROW, LAST_ENTRY_ROW + 1)}
    )
    seed.update(
        {f"LQ{row}": f"{row - FIRST_ENTRY_ROW + 1:02d}ud" for row in range(FIRST_ENTRY_ROW, LAST_ENTRY_ROW + 1)}
    )
    return seed


def _connect(
    _seed: dict[str, object],
) -> tuple[FakeXLFramework, XLConnection, Components, list[str]]:
    output: list[str] = []
    fake_xl = FakeXLFramework(sheet_names=["Components"], seed={"Components": _seed})
    connection = XLConnection(xl_framework=fake_xl, output=output.append)
    return fake_xl, connection, Components(connection, _components_shape()), output


def _section_cases() -> tuple[SectionCase, ...]:
    return (
        SectionCase(
            section_name="glazings",
            write_one_row=lambda components: components.write_glazings(
                [GlazingRow(_components_shape(), _window_type("NEW-GLAZING"))]
            ),
            write_one_row_clear=lambda components: components.write_glazings(
                [GlazingRow(_components_shape(), _window_type("NEW-GLAZING"))],
                clear_stale=True,
            ),
            stale_seed={"II14": "OLD-GLAZING-A", "II15": "OLD-GLAZING-B", "IH16": "DO-NOT-CLEAR"},
            clean_seed={},
            expected_clear_ranges=("II14:IK15",),
            untouched_cells=("IH14", "IH15", "IH16"),
        ),
        SectionCase(
            section_name="frames",
            write_one_row=lambda components: components.write_frames(
                [FrameRow(_components_shape(), _window_type("NEW-FRAME"))]
            ),
            write_one_row_clear=lambda components: components.write_frames(
                [FrameRow(_components_shape(), _window_type("NEW-FRAME"))],
                clear_stale=True,
            ),
            stale_seed={
                "IP14": "OLD-FRAME-A",
                "IP15": "OLD-FRAME-B",
                "IQ14": "FORMULA",
                "IS14": "FORMULA",
                "JB14": "FORMULA",
            },
            clean_seed={"IQ14": "FORMULA", "IS14": "FORMULA", "JB14": "FORMULA"},
            expected_clear_ranges=("IP14:IP15", "IR14:IR15", "IT14:JA15", "JZ14:KB15"),
            untouched_cells=("IO14", "IQ14", "IS14", "JB14"),
        ),
        SectionCase(
            section_name="ventilators",
            write_one_row=lambda components: components.write_ventilators(
                [VentilatorRow(_components_shape(), _ventilator("NEW-VENTILATOR"))]
            ),
            write_one_row_clear=lambda components: components.write_ventilators(
                [VentilatorRow(_components_shape(), _ventilator("NEW-VENTILATOR"))],
                clear_stale=True,
            ),
            stale_seed={
                "LR14": "OLD-VENT-A",
                "LR15": "OLD-VENT-B",
                "LU14": "FORMULA",
                "LV14": "FORMULA",
                "LX14": "FORMULA",
            },
            clean_seed={"LU14": "FORMULA", "LV14": "FORMULA", "LX14": "FORMULA"},
            expected_clear_ranges=("LR14:LT15", "LW14:LW15", "MB14:MB15"),
            untouched_cells=("LQ14", "LU14", "LV14", "LX14"),
        ),
    )


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_components_write_warns_on_stale_trailing_rows_by_default(
    reset_class_counters,
    section_case: SectionCase,
) -> None:
    seed = {**_base_seed(), **section_case.stale_seed}
    _, connection, components, output = _connect(seed)
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_one_row(components)

    warnings = [message for message in output if "leftover entries from a previous export" in message]
    assert len(warnings) == 1
    assert "'Components' worksheet" in warnings[0]
    assert section_case.section_name in warnings[0]
    assert "rows 14, 15" in warnings[0]
    assert "should be cleared or verified" in warnings[0]
    connection.clear_range_data.assert_not_called()


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_components_write_can_clear_stale_rows_with_opt_in_flag(
    reset_class_counters,
    section_case: SectionCase,
) -> None:
    seed = {**_base_seed(), **section_case.stale_seed}
    fake_xl, connection, components, _ = _connect(seed)
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_one_row_clear(components)

    assert [call.args for call in connection.clear_range_data.call_args_list] == [
        ("Components", expected_range) for expected_range in section_case.expected_clear_ranges
    ]
    components_sheet = fake_xl._book.sheets["Components"]
    for address in section_case.untouched_cells:
        assert components_sheet.range(address).value is not None


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_components_write_on_clean_sheet_does_not_warn_or_clear(
    reset_class_counters,
    section_case: SectionCase,
) -> None:
    seed = {**_base_seed(), **section_case.clean_seed}
    _, connection, components, output = _connect(seed)
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_one_row_clear(components)

    warnings = [message for message in output if "leftover entries from a previous export" in message]
    assert warnings == []
    connection.clear_range_data.assert_not_called()


def test_components_write_empty_input_detects_stale_rows_from_section_start(reset_class_counters) -> None:
    seed = {**_base_seed(), "II13": "OLD-GLAZING"}
    _, connection, components, output = _connect(seed)
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    components.write_glazings([], clear_stale=True)

    warnings = [message for message in output if "leftover entries from a previous export" in message]
    assert len(warnings) == 1
    assert "row 13" in warnings[0]
    assert [call.args for call in connection.clear_range_data.call_args_list] == [("Components", "II13:IK13")]
