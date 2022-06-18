# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Shading/Shading-Entry row"""

from dataclasses import dataclass
from typing import List, Tuple
from functools import partial
from PHX.model import components

from PHX.to_PHPP import xl_data
from PHX.to_PHPP.phpp_localization import shape_model


@dataclass
class ShadingRow:
    """Model class for a single Window's Shading entry row."""

    __slots__ = ('shape', 'shading_dims', 'winter_shading_factor', 'summer_shading_factor')
    shape: shape_model.Shading
    shading_dims: components.PhxApertureShadingDimensions
    winter_shading_factor: float
    summer_shading_factor: float

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.shading_rows.input_columns, _field_name)
        return f'{col}{_row_num}'

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
        create_range = partial(self._create_range, _row_num=_row_num)
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (create_range('h_hori'), self.shading_dims.h_hori),
            (create_range('d_hori'), self.shading_dims.d_hori),
            (create_range('o_reveal'), self.shading_dims.o_reveal),
            (create_range('d_reveal'), self.shading_dims.d_reveal),
            (create_range('o_over'), self.shading_dims.o_over),
            (create_range('d_over'), self.shading_dims.d_over),
            (create_range('r_other_winter'), self.winter_shading_factor),
            (create_range('r_other_summer'), self.summer_shading_factor),
        ]

        return [xl_data.XlItem(_sheet_name, *item) for item in items]
