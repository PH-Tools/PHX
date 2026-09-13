# -*- Python Version: 3.10 -*-

"""Tests for stale trailing rows in PHPP Additional Vent-section writes."""

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import Mock

import pytest

from PHX.PHPP.sheet_io.io_addnl_vent import AddnlVent
from PHX.xl.xl_app import XLConnection
from PHX.xl.xl_data import XlItem
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework


@dataclass
class SyntheticRow:
    value: int

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> list[XlItem]:
        return [XlItem(_sheet_name, f"D{_row_num}", self.value)]


@dataclass(frozen=True)
class SectionCase:
    section_name: str
    first_entry_row: int
    last_entry_row: int
    rows_written: int
    stale_rows: tuple[int, ...]
    write_rows: Callable[[AddnlVent, list[SyntheticRow], bool], None]
    expected_clear_ranges: tuple[str, ...]
    untouched_cells: tuple[str, ...]

    @property
    def capacity(self) -> int:
        return self.last_entry_row - self.first_entry_row + 1


def _numbered_rows(_start: int, _count: int) -> dict[str, int]:
    return {f"C{row}": row - _start + 1 for row in range(_start, _start + _count)}


def _base_seed() -> dict[str, object]:
    seed: dict[str, object] = {
        "C28": "Room",
        "C65": "Venti-",
        "E86": "Round duct diameter",
        "D115": "Additional rows can be added with PHPP's Tools workbook",
    }
    seed.update(_numbered_rows(31, 30))
    seed.update(_numbered_rows(70, 10))
    seed.update({f"Q{row}": 1 for row in range(31, 61)})
    seed.update({f"R{row}": 1 for row in range(31, 61)})
    seed.update({f"Z{row}": "2-Elec." for row in range(70, 80)})
    return seed


def _connect(_seed: dict[str, object]) -> tuple[FakeXLFramework, XLConnection, AddnlVent, list[str]]:
    shape = load_shape("EN_10_6.json").ADDNL_VENT
    output: list[str] = []
    fake_xl = FakeXLFramework(sheet_names=[shape.name], seed={shape.name: _seed})
    connection = XLConnection(xl_framework=fake_xl, output=output.append)
    return fake_xl, connection, AddnlVent(connection, shape), output


def _synthetic_rows(_count: int) -> list[SyntheticRow]:
    return [SyntheticRow(value) for value in range(1, _count + 1)]


def _section_cases() -> tuple[SectionCase, ...]:
    return (
        SectionCase(
            section_name="Rooms",
            first_entry_row=31,
            last_entry_row=60,
            rows_written=5,
            stale_rows=(36, 37, 38),
            write_rows=lambda addnl_vent, rows, clear: addnl_vent.write_spaces(  # type: ignore[arg-type]
                rows,
                clear_stale=clear,
            ),
            expected_clear_ranges=("D36:H38", "J36:L38", "N36:P38", "S36:V38"),
            untouched_cells=("C36", "C37", "C38", "Q36", "R36"),
        ),
        SectionCase(
            section_name="Ventilation units",
            first_entry_row=70,
            last_entry_row=79,
            rows_written=3,
            stale_rows=(73, 74, 75, 76, 77),
            write_rows=lambda addnl_vent, rows, clear: addnl_vent.write_vent_units(  # type: ignore[arg-type]
                rows,
                clear_stale=clear,
            ),
            expected_clear_ranges=("D73:F77", "K73:M77", "Q73:Q77", "X73:X77", "AA73:AA77"),
            untouched_cells=("C73", "C74", "C75", "C76", "C77", "Z73", "Z77"),
        ),
        SectionCase(
            section_name="Ducts",
            first_entry_row=95,
            last_entry_row=114,
            rows_written=4,
            stale_rows=(99, 100, 101, 102),
            write_rows=lambda addnl_vent, rows, clear: addnl_vent.write_vent_ducts(  # type: ignore[arg-type]
                rows,
                clear_stale=clear,
            ),
            expected_clear_ranges=("D99:J102", "L99:N102", "Q99:Z102"),
            untouched_cells=("K99", "O99", "P99"),
        ),
    )


def _stale_seed(_section_case: SectionCase) -> dict[str, object]:
    seed = _base_seed()
    seed.update({f"D{row}": f"OLD-{row}" for row in _section_case.stale_rows})
    if _section_case.section_name == "Ducts":
        seed.update({"K99": "FORMULA", "O99": "FORMULA", "P99": "FORMULA"})
    return seed


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_addnl_vent_write_warns_on_stale_trailing_rows_by_default(section_case: SectionCase) -> None:
    _, connection, addnl_vent, output = _connect(_stale_seed(section_case))
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_rows(addnl_vent, _synthetic_rows(section_case.rows_written), False)

    warnings = [message for message in output if "leftover entries from a previous export" in message]
    assert len(warnings) == 1
    assert "'Addl vent' worksheet" in warnings[0]
    assert section_case.section_name in warnings[0]
    assert f"rows {', '.join(str(row) for row in section_case.stale_rows)}" in warnings[0]
    assert "should be cleared or verified" in warnings[0]
    connection.clear_range_data.assert_not_called()


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_addnl_vent_write_can_clear_stale_rows_with_opt_in_flag(section_case: SectionCase) -> None:
    fake_xl, connection, addnl_vent, _ = _connect(_stale_seed(section_case))
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_rows(addnl_vent, _synthetic_rows(section_case.rows_written), True)

    assert [call.args for call in connection.clear_range_data.call_args_list] == [
        ("Addl vent", expected_range) for expected_range in section_case.expected_clear_ranges
    ]
    worksheet = fake_xl._book.sheets["Addl vent"]
    for address in section_case.untouched_cells:
        assert worksheet.range(address).value is not None


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_addnl_vent_write_on_clean_section_does_not_warn_or_clear(section_case: SectionCase) -> None:
    _, connection, addnl_vent, output = _connect(_base_seed())
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_rows(addnl_vent, _synthetic_rows(section_case.rows_written), True)

    warnings = [message for message in output if "leftover entries from a previous export" in message]
    assert warnings == []
    connection.clear_range_data.assert_not_called()


@pytest.mark.parametrize("section_case", _section_cases(), ids=lambda section_case: section_case.section_name)
def test_addnl_vent_over_capacity_write_does_not_report_stale_rows(section_case: SectionCase) -> None:
    _, connection, addnl_vent, output = _connect(_base_seed())
    connection.clear_range_data = Mock(wraps=connection.clear_range_data)  # type: ignore[method-assign]

    section_case.write_rows(addnl_vent, _synthetic_rows(section_case.capacity + 1), True)

    capacity_warnings = [message for message in output if "PHPPAddlVentCapacityWarning" in message]
    stale_warnings = [message for message in output if "leftover entries from a previous export" in message]
    assert len(capacity_warnings) == 1
    assert stale_warnings == []
    connection.clear_range_data.assert_not_called()
