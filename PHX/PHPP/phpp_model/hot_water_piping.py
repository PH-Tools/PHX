# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Model class for a PHPP DHW Piping Elements."""

from dataclasses import dataclass
from functools import partial
from typing import List

from PHX.model.hvac import piping
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class RecircPipingInput:
    """Model class for a single DHW Recirculation Pipe Element."""

    __slots__ = ("shape", "phx_pipe", "pipe_group_num")
    shape: shape_model.Dhw
    phx_pipe: List[piping.PhxPipeSegment]
    pipe_group_num: int

    @property
    def input_column(self) -> str:
        """Return the right input column based on the pipe-group-number."""
        return xl_data.col_offset(self.shape.recirc_piping.input_col_start, self.pipe_group_num)

    def _create_range(
        self,
        _field_name: str,
        _row_num: int,
    ) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return f"{self.input_column}{_row_num + getattr(self.shape.recirc_piping.input_rows_offset, _field_name).row}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.recirc_piping.input_rows_offset, _field_name).unit

    def _bool_as_x(self, _value: bool):
        if _value == True:
            return "x"
        else:
            return ""

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> List[xl_data.XlItem]:
        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemDHW = partial(xl_data.XlItem, _sheet_name)
        total_length = sum(s.length_m for s in self.phx_pipe)

        return [
            XLItemDHW(
                create_range("total_length"),
                total_length,
                "M",
                self._get_target_unit("total_length"),
            ),
            XLItemDHW(
                create_range("diameter"),
                sum(s.diameter_m * s.length_m for s in self.phx_pipe) / total_length,
                "M",
                self._get_target_unit("diameter"),
            ),
            XLItemDHW(
                create_range("insul_thickness"),
                sum(s.insulation_thickness_m * s.length_m for s in self.phx_pipe) / total_length,
                "M",
                self._get_target_unit("insul_thickness"),
            ),
            XLItemDHW(
                create_range("insul_reflective"),
                self._bool_as_x(any([s.insulation_reflective for s in self.phx_pipe])),
            ),
            XLItemDHW(
                create_range("insul_conductivity"),
                sum(s.insulation_conductivity * s.length_m for s in self.phx_pipe) / total_length,
                "W/MK",
                self._get_target_unit("insul_conductivity"),
            ),
            XLItemDHW(
                create_range("daily_period"),
                sum(s.daily_period * s.length_m for s in self.phx_pipe) / total_length,
                "",
                self._get_target_unit("daily_period"),
            ),
            XLItemDHW(
                create_range("water_temp"),
                sum(s.water_temp_c * s.length_m for s in self.phx_pipe) / total_length,
                "C",
                self._get_target_unit("water_temp"),
            ),
        ]


@dataclass
class BranchPipingInput:
    """Model class for a single DHW Branch Pipe Element."""

    __slots__ = ("shape", "phx_pipe", "pipe_group_num", "num_tap_points")
    shape: shape_model.Dhw
    phx_pipe: List[piping.PhxPipeSegment]
    pipe_group_num: int
    num_tap_points: int

    @property
    def input_column(self) -> str:
        """Return the right input column based on the pipe-group-number."""
        return xl_data.col_offset(self.shape.branch_piping.input_col_start, self.pipe_group_num)

    def create_range(self, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        return f"{self.input_column}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.branch_piping.input_rows_offset, _field_name).unit

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> List[xl_data.XlItem]:
        """Returns a list of Branch Piping Xl-Write items."""

        XLItemDHW = partial(xl_data.XlItem, _sheet_name)
        total_length = sum(s.length_m for s in self.phx_pipe)
        if total_length == 0:
            return []
        return [
            # -- Branch Piping
            XLItemDHW(
                self.create_range(_row_num + self.shape.branch_piping.input_rows_offset.water_temp.row),  # type: ignore
                sum(s.water_temp_c * s.length_m for s in self.phx_pipe) / total_length,
                "C",
                self._get_target_unit("water_temp"),
            ),
            XLItemDHW(
                self.create_range(_row_num + self.shape.branch_piping.input_rows_offset.diameter.row),  # type: ignore
                sum(s.diameter_m * s.length_m for s in self.phx_pipe) / total_length,
                "M",
                self._get_target_unit("diameter"),
            ),
            XLItemDHW(
                self.create_range(_row_num + self.shape.branch_piping.input_rows_offset.total_length.row),  # type: ignore
                total_length,
                "M",
                self._get_target_unit("total_length"),
            ),
            # -- Add Tapping Points
            XLItemDHW(
                self.create_range(_row_num + self.shape.branch_piping.input_rows_offset.num_taps),
                self.num_tap_points,
            ),
        ]
