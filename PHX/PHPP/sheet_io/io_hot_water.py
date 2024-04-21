# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "DHW+Distribution" worksheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import hot_water_piping, hot_water_tank
from PHX.xl import xl_app


class RecircPiping:
    """The Recirculation Piping Section Group"""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self._header_row: Optional[int] = None

    @property
    def header_row(self) -> int:
        if not self._header_row:
            self._header_row = self.find_header_row()
        return self._header_row

    def find_header_row(self, _row_start: int = 100, _rows: int = 100) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.recirc_piping.locator_col_entry,
            _row_start=_row_start,
            _row_end=_row_start + _rows,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.recirc_piping.locator_string_entry == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.recirc_piping.locator_string_entry}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.recirc_piping.locator_string_entry}?"
        )


class BranchPiping:
    """The Branch Piping Section Group"""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self._header_row: Optional[int] = None

    @property
    def header_row(self) -> int:
        if not self._header_row:
            self._header_row = self.find_header_row()
        return self._header_row

    def find_header_row(self, _row_start: int = 100, _rows: int = 100) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.branch_piping.locator_col_entry,
            _row_start=_row_start,
            _row_end=_row_start + _rows,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.branch_piping.locator_string_entry == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.branch_piping.locator_string_entry}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.branch_piping.locator_string_entry}?"
        )


class DHWPiping:
    """The DHW Piping Section Group"""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self._header_row: Optional[int] = None
        self.recirc_piping = RecircPiping(self.xl, self.shape)
        self.branch_piping = BranchPiping(self.xl, self.shape)

    def find_header_row(self, _row_start: int = 100, _row_end: int = 200) -> int:
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.branch_piping.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.branch_piping.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.branch_piping.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.branch_piping.locator_string_header}?"
        )

    @property
    def header_row(self) -> int:
        if not self._header_row:
            self._header_row = self.find_header_row()
        return self._header_row

    def find_recirc_piping_start_row(self) -> int:
        return self.recirc_piping.header_row

    def find_branch_piping_start_row(self) -> int:
        return self.branch_piping.header_row


@dataclass
class TankData:
    """Convenience Wrapper for Tank Data read in from the PHPP."""

    type: str = ""
    heat_loss_rate: Unit = field(default_factory=Unit)
    volume: Unit = field(default_factory=Unit)

    @classmethod
    def from_phpp_data(cls, _d: Dict[str, Any]) -> "TankData":
        return cls(
            type=_d["type"],
            heat_loss_rate=Unit(_d["heat_loss_rate"], _d["heat_loss_rate_unit"]),
            volume=Unit(_d["volume"], _d["volume_unit"]),
        )


class Tank:
    """An individual tank entry item."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self._entry_row_start: Optional[int] = None

    @property
    def entry_row_start(self) -> int:
        """The row where the tank entry starts."""
        if not self._entry_row_start:
            self._entry_row_start = self.find_entry_row_start()
        return self._entry_row_start

    def find_entry_row_start(self) -> int:
        """Find the row where the tank entry starts."""
        return self.shape.tanks.entry_row_start

    def get_phpp_data(self, _tank_num: int) -> TankData:
        """Get the PHPP data for the specified tank number."""
        shape = self.shape.tanks
        rows = shape.input_rows
        col = getattr(shape.input_columns, f"tank_{_tank_num}")

        phpp_data = {
            "type": self.xl.get_data(
                self.shape.name,
                f"{col}{self.entry_row_start + rows.tank_type.row}",
            ),
            "heat_loss_rate": self.xl.get_data(
                self.shape.name,
                f"{col}{self.entry_row_start + rows.standby_losses.row}",
            ),
            "heat_loss_rate_unit": rows.standby_losses.unit,
            "volume": self.xl.get_data(
                self.shape.name,
                f"{col}{self.entry_row_start + rows.storage_capacity.row}",
            ),
            "volume_unit": rows.storage_capacity.unit,
        }

        return TankData.from_phpp_data(phpp_data)


class Tanks:
    """The Tanks (Storage Heat Loss) Section Group"""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw) -> None:
        self.xl = _xl
        self.shape = _shape
        self._header_row: Optional[int] = None

        self.tank_1 = Tank(self.xl, self.shape)
        self.tank_2 = Tank(self.xl, self.shape)

    @property
    def header_row(self) -> int:
        """The row where the tank header starts."""
        if not self._header_row:
            self._header_row = self.find_header_row()
        return self._header_row

    def find_header_row(self, _row_start: int = 150, _row_end: int = 200) -> int:
        """Find the row where the tank header starts."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=self.shape.tanks.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.shape.tanks.locator_string_header == val:
                return i

        raise Exception(
            f"Error: Cannot find the '{self.shape.tanks.locator_string_header}' "
            f"header on the '{self.shape.name}' sheet, column {self.shape.tanks.locator_string_header}?"
        )

    def get_all_tank_device_data(self) -> List[TankData]:
        """Get all the tank data from the spreadsheet."""
        return [
            self.tank_1.get_phpp_data(1),
            self.tank_2.get_phpp_data(2),
        ]


class HotWater:
    """IO Controller for the PHPP 'DHW+Distribution' PHPP worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Dhw):
        self.xl = _xl
        self.shape = _shape
        self.tanks = Tanks(self.xl, self.shape)
        self.dhw_piping = DHWPiping(self.xl, self.shape)

    def write_tanks(self, _phpp_hw_tanks: List[hot_water_tank.TankInput]) -> None:
        """Write the tank data to the spreadsheet."""
        for phpp_Tank_input in _phpp_hw_tanks:
            for item in phpp_Tank_input.create_xl_items(self.shape.name, self.tanks.tank_1.entry_row_start):
                self.xl.write_xl_item(item)

    def write_branch_piping(self, _phpp_branch_piping: List[hot_water_piping.BranchPipingInput]) -> None:
        """Write the branch piping data to the spreadsheet."""
        for pipe_inputs in _phpp_branch_piping:
            for item in pipe_inputs.create_xl_items(self.shape.name, self.dhw_piping.branch_piping.header_row):
                self.xl.write_xl_item(item)

    def write_recirc_piping(self, _phpp_recirc_piping: List[hot_water_piping.BranchPipingInput]) -> None:
        """Write the recirc piping data to the spreadsheet."""
        for pipe_inputs in _phpp_recirc_piping:
            for item in pipe_inputs.create_xl_items(self.shape.name, self.dhw_piping.recirc_piping.header_row):
                self.xl.write_xl_item(item)

    def get_all_tank_device_data(self) -> List[TankData]:
        """Get all the tank data from the PHPP worksheet."""
        return self.tanks.get_all_tank_device_data()
