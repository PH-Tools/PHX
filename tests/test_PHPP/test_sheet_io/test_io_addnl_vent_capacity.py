# -*- Python Version: 3.10 -*-

"""Capacity tests for PHPP Additional Ventilation list sections."""

from dataclasses import dataclass
from unittest.mock import Mock

from PHX.PHPP.sheet_io.io_addnl_vent import AddnlVent, Spaces
from PHX.xl.xl_app import XLConnection
from PHX.xl.xl_data import XlItem
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework, parse_cell


@dataclass
class SyntheticRow:
    value: int

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> list[XlItem]:
        return [XlItem(_sheet_name, f"D{_row_num}", self.value)]


def _connect(_seed: dict[str, object]) -> tuple[FakeXLFramework, AddnlVent, list[str]]:
    shape = load_shape().ADDNL_VENT
    fake_xl = FakeXLFramework(sheet_names=[shape.name], seed={shape.name: _seed})
    outputs: list[str] = []
    connection = XLConnection(xl_framework=fake_xl, output=outputs.append)
    return fake_xl, AddnlVent(connection, shape), outputs


def _numbered_rows(_start: int, _count: int) -> dict[str, int]:
    return {f"C{row}": row - _start + 1 for row in range(_start, _start + _count)}


def _synthetic_rows(_count: int) -> list[SyntheticRow]:
    return [SyntheticRow(i) for i in range(1, _count + 1)]


def _written_rows(_fake_xl: FakeXLFramework) -> list[int]:
    written = _fake_xl.written_state().get("Addl vent", {})
    return sorted({parse_cell(address)[1] for address in written})


def _capacity_warnings(_outputs: list[str]) -> list[str]:
    return [message for message in _outputs if "PHPPAddlVentCapacityWarning" in message]


def test_spaces_over_capacity_warns_and_stops_at_last_entry_row():
    seed = {"C28": "Room", **_numbered_rows(31, 30)}
    fake_xl, addnl_vent, outputs = _connect(seed)

    addnl_vent.write_spaces(_synthetic_rows(31))  # type: ignore[arg-type]

    assert _written_rows(fake_xl) == list(range(31, 61))
    warning = _capacity_warnings(outputs)
    assert len(warning) == 1
    assert "worksheet 'Addl vent' section 'Rooms'" in warning[0]
    assert "31 entries but capacity is 30" in warning[0]
    assert "PHPP's Tools workbook" in warning[0]


def test_user_extended_spaces_block_writes_all_rows_without_warning():
    seed = {"C28": "Room", **_numbered_rows(31, 40)}
    fake_xl, addnl_vent, outputs = _connect(seed)
    addnl_vent.spaces.section_header_row = 10
    addnl_vent.spaces.section_first_entry_row = 13
    addnl_vent.spaces.section_last_entry_row = 42

    addnl_vent.write_spaces(_synthetic_rows(35))  # type: ignore[arg-type]

    assert _written_rows(fake_xl) == list(range(31, 66))
    assert _capacity_warnings(outputs) == []
    assert addnl_vent.spaces.section_header_row == 28
    assert addnl_vent.spaces.section_last_entry_row == 70


def test_ventilation_units_over_capacity_warns_and_truncates():
    seed = {"C64": "Venti-", **_numbered_rows(70, 10)}
    fake_xl, addnl_vent, outputs = _connect(seed)

    addnl_vent.write_vent_units(_synthetic_rows(11))  # type: ignore[arg-type]

    assert _written_rows(fake_xl) == list(range(70, 80))
    warning = _capacity_warnings(outputs)
    assert len(warning) == 1
    assert "section 'Ventilation units'" in warning[0]
    assert "11 entries but capacity is 10" in warning[0]


def test_ventilation_ducts_use_shared_capacity_guard():
    seed = {"E86": "Round duct diameter", "D115": "Additional lines"}
    fake_xl, addnl_vent, outputs = _connect(seed)

    addnl_vent.write_vent_ducts(_synthetic_rows(21))  # type: ignore[arg-type]

    assert _written_rows(fake_xl) == list(range(95, 115))
    warning = _capacity_warnings(outputs)
    assert len(warning) == 1
    assert "section 'Ducts'" in warning[0]
    assert "21 entries but capacity is 20" in warning[0]


def test_read_space_data_stops_at_last_entry_row():
    seed = {"C28": "Room", **_numbered_rows(31, 30)}
    _, addnl_vent, _ = _connect(seed)
    addnl_vent.xl.get_data_by_columns = Mock(return_value=[])

    assert addnl_vent.read_space_data() == []
    addnl_vent.xl.get_data_by_columns.assert_called_once_with(
        _sheet_name="Addl vent",
        _range_address="C28:Z60",
    )


def test_spaces_locator_class_returns_last_entry_row_directly():
    shape = load_shape().ADDNL_VENT
    seed = {"C28": "Room", **_numbered_rows(31, 30)}
    fake_xl = FakeXLFramework(sheet_names=[shape.name], seed={shape.name: seed})
    connection = XLConnection(xl_framework=fake_xl)

    assert Spaces(connection, shape).find_section_last_entry_row() == 60
