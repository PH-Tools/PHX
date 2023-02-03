# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a single PHPP Addition Vent / Space(room)-Entry row."""

from dataclasses import dataclass
from typing import List, Tuple
from functools import partial

from PHX.model.spaces import PhxSpace
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.xl import xl_data
from PHX.xl.xl_data import xl_writable
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class VentSpaceRow:
    """Model class for a single Ventilation Space/Room entry row."""

    __slots__ = ("shape", "phx_room_vent", "phpp_row_ventilator", "phx_vent_pattern")
    shape: shape_model.AddnlVent
    phx_room_vent: PhxSpace
    phpp_row_ventilator: xl_writable
    phx_vent_pattern: PhxScheduleVentilation

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.rooms.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.rooms.inputs, _field_name).unit

    def _get_time_periods(self) -> Tuple[float, float, float]:
        """Return a tuple of the high, standard and min operating periods as % values."""
        periods = self.phx_vent_pattern.operating_periods
        time_high = periods.high.period_operating_hours / 24.0
        time_standard = periods.standard.period_operating_hours / 24.0

        # Ensure total always equals 100%
        time_minimum = 1.0 - (time_high + time_standard)

        return time_high, time_standard, time_minimum

    def _calc_minimum_speed(self) -> float:
        # Weighted average of Min and Basic since PHPP only has 3 values
        periods = self.phx_vent_pattern.operating_periods
        weighted_basic = (
            periods.basic.period_operation_speed * periods.basic.period_operating_hours
        )
        weighed_minimum = (
            periods.minimum.period_operation_speed
            * periods.minimum.period_operating_hours
        )
        total_hours = (
            periods.basic.period_operating_hours + periods.minimum.period_operating_hours
        )

        try:
            return (weighted_basic + weighed_minimum) / total_hours
        except ZeroDivisionError:
            return 0.0

    def _get_speeds(self) -> Tuple[float, float, float]:
        """Return a tuple of the high, standard and minimum speeds as % of max"""
        speed_high = self.phx_vent_pattern.operating_periods.high.period_operation_speed
        speed_standard = (
            self.phx_vent_pattern.operating_periods.standard.period_operation_speed
        )
        speed_minimum = self._calc_minimum_speed()

        return speed_high, speed_standard, speed_minimum

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> List[xl_data.XlItem]:
        """Returns a list of the XL Items to write for this Surface Entry

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to write to.
            * _row_num: (int) The row number to build the XlItems for
        Returns:
        --------
            * (List[XlItem]): The XlItems to write to the sheet.
        """
        # -- Handle the percentages so always adds up to 100% hours
        time_high, time_standard, time_minimum = self._get_time_periods()
        speed_high, speed_standard, speed_minimum = self._get_speeds()

        # --
        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemAddnlVent = partial(xl_data.XlItem, _sheet_name)
        items: List[xl_data.XlItem] = [
            XLItemAddnlVent(create_range("quantity"), self.phx_room_vent.quantity),
            XLItemAddnlVent(
                create_range("display_name"), self.phx_room_vent.display_name
            ),
            XLItemAddnlVent(create_range("vent_unit_assigned"), self.phpp_row_ventilator),
            XLItemAddnlVent(
                create_range("weighted_floor_area"),
                self.phx_room_vent.floor_area,
                "M2",
                self._get_target_unit("weighted_floor_area"),
            ),
            XLItemAddnlVent(
                create_range("clear_height"),
                self.phx_room_vent.clear_height,
                "M",
                self._get_target_unit("clear_height"),
            ),
            XLItemAddnlVent(
                create_range("V_sup"),
                self.phx_room_vent.ventilation.load.flow_supply,
                "M3/HR",
                self._get_target_unit("V_sup"),
            ),
            XLItemAddnlVent(
                create_range("V_eta"),
                self.phx_room_vent.ventilation.load.flow_extract,
                "M3/HR",
                self._get_target_unit("V_eta"),
            ),
            XLItemAddnlVent(
                create_range("V_trans"),
                self.phx_room_vent.ventilation.load.flow_transfer,
                "M3/HR",
                self._get_target_unit("V_trans"),
            ),
            # -- Operating Days / weeks
            XLItemAddnlVent(
                create_range("operating_hours"), self.phx_vent_pattern.operating_hours
            ),
            XLItemAddnlVent(
                create_range("operating_days"), self.phx_vent_pattern.operating_days
            ),
            XLItemAddnlVent(
                create_range("holiday_days"), self.phx_vent_pattern.holiday_days
            ),
            # -- Operating hours / speeds
            XLItemAddnlVent(create_range("period_high_speed"), speed_high),
            XLItemAddnlVent(create_range("period_high_time"), time_high),
            XLItemAddnlVent(create_range("period_standard_speed"), speed_standard),
            XLItemAddnlVent(create_range("period_standard_time"), time_standard),
            XLItemAddnlVent(create_range("period_minimum_speed"), speed_minimum),
            XLItemAddnlVent(create_range("period_minimum_time"), time_minimum),
        ]

        return items
