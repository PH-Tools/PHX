# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Model class for a PHPP Electricity / Equipment row input."""

from dataclasses import dataclass
from typing import List, Tuple, Any

from PHX.model import elec_equip

from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class ElectricityItem:
    """Model class for a single Electric-Equipment item entry row."""

    __slots__ = "phx_equipment"
    phx_equipment: Any

    def create_xl_items(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        """Returns a list of xl_data.XlItem or raises and Error if equipment type is unrecognized."""
        xl_item_functions = {
            "PhxDeviceDishwasher": self._dishwasher,
            "PhxDeviceClothesWasher": self._clothes_washer,
            "PhxDeviceClothesDryer": self._clothes_dryer,
            "PhxDeviceRefrigerator": self._refrigerator,
            "PhxDeviceFreezer": self._freezer,
            "PhxDeviceFridgeFreezer": self._fridge_freezer,
            "PhxDeviceCooktop": self._cooktop,
            "PhxDeviceMEL": self._mel,
            "PhxDeviceLightingInterior": self._lighting_interior,
            "PhxDeviceLightingExterior": self._lighting_exterior,
            "PhxDeviceLightingGarage": self._lighting_garage,
            "PhxDeviceCustomElec": self._custom_elec,
            "PhxDeviceCustomLighting": self._custom_lighting,
            "PhxDeviceCustomMEL": self._custom_mel,
        }
        try:
            return xl_item_functions[self.phx_equipment.__class__.__name__](_shape)
        except KeyError:
            raise NotImplementedError(
                f"No matching XL-write function found for equipment type: '{self.phx_equipment.__class__.__name__}'"
            )

    def _dishwasher(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceDishwasher = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.dishwasher.data}", 1),
            (
                f"{_shape.input_columns.in_conditioned_space}{_shape.input_rows.dishwasher.data}",
                str(int(equip.in_conditioned_space)),
            ),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.dishwasher.data}",
                equip.energy_demand_per_use,
            ),
            (
                f"{_shape.input_columns.selection}{_shape.input_rows.dishwasher.selection}",
                _shape.input_rows.dishwasher.selection_options[
                    str(equip.water_connection)
                ],
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _clothes_washer(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceClothesWasher = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.clothes_washing.data}", 1),
            (
                f"{_shape.input_columns.in_conditioned_space}{_shape.input_rows.clothes_washing.data}",
                str(int(equip.in_conditioned_space)),
            ),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.clothes_washing.data}",
                equip.energy_demand_per_use,
            ),
            (
                f"{_shape.input_columns.selection}{_shape.input_rows.clothes_washing.selection}",
                _shape.input_rows.clothes_washing.selection_options[
                    str(equip.water_connection)
                ],
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _clothes_dryer(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceClothesDryer = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (
                f"{_shape.input_columns.in_conditioned_space}{_shape.input_rows.clothes_drying.data}",
                str(int(equip.in_conditioned_space)),
            ),
            (
                f"{_shape.input_columns.selection}{_shape.input_rows.clothes_drying.selection}",
                _shape.input_rows.clothes_drying.selection_options[str(equip.dryer_type)],
            ),
        ]

        # -- Add energy consumption, location depends on fuel type
        if equip.dryer_type == 6:
            # Gas dryer
            items.append(
                (
                    f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.clothes_drying.selection}",
                    equip.gas_consumption,
                )
            )
        else:
            # non-Gas dryer
            items.append(
                (
                    f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.clothes_drying.data}",
                    equip.energy_demand_per_use,
                ),
            )

        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _refrigerator(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceRefrigerator = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.refrigerator.data}", 1),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.refrigerator.data}",
                equip.energy_demand_per_use,
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _fridge_freezer(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceFridgeFreezer = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.fridge_freezer.data}", 1),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.fridge_freezer.data}",
                equip.energy_demand_per_use,
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _freezer(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceFreezer = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.freezer.data}", 1),
            (
                f"{_shape.input_columns.in_conditioned_space}{_shape.input_rows.freezer.data}",
                str(int(equip.in_conditioned_space)),
            ),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.freezer.data}",
                equip.energy_demand_per_use,
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _cooktop(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceCooktop = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.cooking.data}",
                equip.energy_demand_per_use,
            ),
            (
                f"{_shape.input_columns.selection}{_shape.input_rows.cooking.selection}",
                _shape.input_rows.cooking.selection_options[str(equip.cooktop_type)],
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _mel(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []

    def _lighting_interior(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []

    def _lighting_exterior(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []

    def _lighting_garage(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []

    def _custom_elec(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []

    def _custom_lighting(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []

    def _custom_mel(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        return []
