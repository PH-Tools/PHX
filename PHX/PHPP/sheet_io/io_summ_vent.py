# -*- Python Version: 3.10 -*-

"""Controller class for the PHPP 'SummVent' worksheet."""

from __future__ import annotations

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import summ_vent_data
from PHX.PHPP.sheet_io.io_exceptions import FindSectionMarkerException
from PHX.xl import xl_app


class SummVentInputLocation:
    """Location of the summer heat-recovery checkbox group in 'SummVent'."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.SummVent):
        self.xl = _xl
        self.shape = _shape

    def find_input_row(self, _row_start: int = 1, _row_end: int = 150) -> int:
        """Return the row of the summer heat-recovery header in column Q."""
        if not (input_shape := self.shape.columns.hrv_summer_mode):
            raise summ_vent_data.SummVentExportError(
                f"The '{self.shape.name}' worksheet layout is not mapped for this PHPP."
            )

        row = self.xl.get_row_num_of_value_in_column(
            self.shape.name,
            _row_start,
            _row_end,
            input_shape.locator_col,
            input_shape.locator_string,
        )
        if row is not None:
            return row

        raise FindSectionMarkerException(input_shape.locator_string, self.shape.name, input_shape.locator_col)


class SummVent:
    """IO controller for the PHPP 'SummVent' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.SummVent):
        self.xl = _xl
        self.shape = _shape
        self.io_hrv_summer_mode = SummVentInputLocation(_xl, _shape)

    def write_summer_hrv_mode(self, _phpp_model_obj: summ_vent_data.SummerHrvMode) -> None:
        """Write one selected summer heat-recovery mode and clear its three siblings."""
        header_row = self.io_hrv_summer_mode.find_input_row()
        for xl_item in _phpp_model_obj.create_xl_items(self.shape.name, header_row):
            self.xl.write_xl_item(xl_item)
