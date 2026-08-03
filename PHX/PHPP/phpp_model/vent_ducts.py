# -*- Python Version: 3.10 -*-

"""Model class for a single PHPP Additional Ventilation duct row."""

from dataclasses import dataclass
from functools import partial

from PHX.model import hvac
from PHX.model.enums.hvac import PhxVentDuctType
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass(slots=True)
class VentDuctRow:
    """A single duct entry in the PHPP Additional Ventilation worksheet.

    Attributes:
        shape (shape_model.AddnlVent): PHPP localization contract for the worksheet.
        phx_duct (hvac.PhxDuctElement): PHX duct run to export.
        phpp_vent_unit_number (int): One-based PHPP ventilator assignment number (1-10).
    """

    shape: shape_model.AddnlVent
    phx_duct: hvac.PhxDuctElement
    phpp_vent_unit_number: int

    def __post_init__(self) -> None:
        if not 1 <= self.phpp_vent_unit_number <= 10:
            raise ValueError("phpp_vent_unit_number must be between 1 and 10")

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the Excel range for a duct field at the specified row."""
        column = getattr(self.shape.ducts.inputs, _field_name).column
        return f"{column}{_row_num}"

    def _get_target_unit(self, _field_name: str) -> str | None:
        """Return the localized PHPP unit for a duct field."""
        return getattr(self.shape.ducts.inputs, _field_name).unit

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> list[xl_data.XlItem]:
        """Build the Excel items for one PHPP duct entry row.

        Arguments:
        ----------
            * _sheet_name (str): Worksheet name to write.
            * _row_num (int): Worksheet row number for the duct entry.

        Returns:
        --------
            * list[xl_data.XlItem]: Cell values and unit conversions for the row.
        """
        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemVentDuct = partial(xl_data.XlItem, _sheet_name)
        items = [
            XLItemVentDuct(create_range("quantity"), self.phx_duct.quantity),
            XLItemVentDuct(
                create_range("insul_thickness"),
                self.phx_duct.insulation_thickness_mm,
                "MM",
                self._get_target_unit("insul_thickness"),
            ),
            XLItemVentDuct(
                create_range("insul_conductivity"),
                self.phx_duct.insulation_conductivity_wmk,
                "W/MK",
                self._get_target_unit("insul_conductivity"),
            ),
            XLItemVentDuct(
                create_range("duct_length"),
                self.phx_duct.length_m,
                "M",
                self._get_target_unit("duct_length"),
            ),
            XLItemVentDuct(create_range(f"duct_assign_{self.phpp_vent_unit_number}"), 1),
        ]

        height_mm = self.phx_duct.height_mm
        width_mm = self.phx_duct.width_mm if height_mm else 0.0
        if not height_mm or not width_mm:
            items.append(
                XLItemVentDuct(
                    create_range("diameter"),
                    self.phx_duct.diameter_mm,
                    "MM",
                    self._get_target_unit("diameter"),
                )
            )
        else:
            items.extend(
                [
                    XLItemVentDuct(
                        create_range("width"),
                        width_mm,
                        "MM",
                        self._get_target_unit("width"),
                    ),
                    XLItemVentDuct(
                        create_range("height"),
                        height_mm,
                        "MM",
                        self._get_target_unit("height"),
                    ),
                ]
            )

        if self.phx_duct.is_reflective:
            items.append(XLItemVentDuct(create_range("insul_reflective"), "x"))

        duct_type_field = {
            PhxVentDuctType.SUPPLY: "is_supply_flag",
            PhxVentDuctType.EXHAUST: "is_exhaust_flag",
        }[self.phx_duct.duct_type]
        items.append(XLItemVentDuct(create_range(duct_type_field), 1))

        return items
