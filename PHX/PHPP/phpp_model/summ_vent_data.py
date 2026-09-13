# -*- Python Version: 3.10 -*-

"""Model class for the PHPP 'SummVent' summer heat-recovery mode."""

from __future__ import annotations

from dataclasses import dataclass

from PHX.model.enums.hvac import PhxSummerBypassMode
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model.xl_checkbox_group import checkbox_group_items
from PHX.xl import xl_data


class SummVentExportError(ValueError):
    """Raised when a summer heat-recovery mode cannot be mapped to PHPP."""


@dataclass
class SummerHrvMode:
    """A PHX summer heat-recovery mode mapped to the PHPP 'SummVent' checkbox group.

    Attributes:
        shape (shape_model.SummVent): The localized PHPP 'SummVent' worksheet shape.
        mode (PhxSummerBypassMode): The summer heat-recovery mode to select.
    """

    shape: shape_model.SummVent
    mode: PhxSummerBypassMode

    def create_xl_items(self, _sheet_name: str, _header_row: int) -> list[xl_data.XlItem]:
        """Return the four checkbox XlItems located relative to the section header row."""
        if not (input_shape := self.shape.columns.hrv_summer_mode):
            raise SummVentExportError(f"The '{self.shape.name}' worksheet layout is not mapped for this PHPP.")

        try:
            selected_index = input_shape.options[str(self.mode.value)]
        except (AttributeError, KeyError) as exc:
            raise SummVentExportError(
                f"The summer heat-recovery mode '{self.mode}' is not mapped for the '{self.shape.name}' worksheet."
            ) from exc

        addresses = [
            f"{input_shape.input_column}{_header_row + row_offset}" for row_offset in input_shape.option_row_offsets
        ]
        return checkbox_group_items(_sheet_name, addresses, selected_index)
