# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Model class for a PHPP Electricity / Equipment row input."""

from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Tuple

from PHX.model import elec_equip
from PHX.model.enums.elec_equip import ElectricEquipmentType
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data

# -----------------------------------------------------------------------------
# -- Worksheet Writer


@dataclass
class ElectricityItemXLWriter:
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
        cols = _shape.input_columns
        rows = _shape.input_rows
        address_used = f"{cols.used}{rows.dishwasher.data}"
        address_inside = f"{cols.in_conditioned_space}{rows.dishwasher.data}"
        address_demand = f"{cols.energy_demand_per_use}{rows.dishwasher.data}"
        address_selection = f"{cols.selection}{rows.dishwasher.selection}"

        items: List[Tuple[str, xl_data.xl_writable]] = [
            (address_used, 1),
            (address_inside, str(int(equip.in_conditioned_space or 1))),
            (address_demand, equip.energy_demand_per_use),
            (
                address_selection,
                rows.dishwasher.selection_options[str(equip.water_connection)],
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _clothes_washer(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceClothesWasher = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.clothes_washing.data}", 1),
            (
                f"{_shape.input_columns.in_conditioned_space}{_shape.input_rows.clothes_washing.data}",
                str(int(equip.in_conditioned_space or 1)),
            ),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.clothes_washing.data}",
                equip.energy_demand_per_use,
            ),
            (
                f"{_shape.input_columns.selection}{_shape.input_rows.clothes_washing.selection}",
                _shape.input_rows.clothes_washing.selection_options[str(equip.water_connection)],
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _clothes_dryer(self, _shape: shape_model.Electricity) -> List[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceClothesDryer = self.phx_equipment
        items: List[Tuple[str, xl_data.xl_writable]] = [
            (
                f"{_shape.input_columns.in_conditioned_space}{_shape.input_rows.clothes_drying.data}",
                str(int(equip.in_conditioned_space or 1)),
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
                str(int(equip.in_conditioned_space or 1)),
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


# -----------------------------------------------------------------------------
# -- Worksheet Reader


class PHPPReadAddress(NamedTuple):
    """Attribute Name / PHPP Address pair."""

    attr_name: str
    phpp_address: str


class ReaderDataItem(NamedTuple):
    """Electric-Equipment data for a single PHPP item."""

    type: ElectricEquipmentType
    data: List[PHPPReadAddress]


class ReaderAddressesGroup(NamedTuple):
    """Electric-Equipment data for a single PHPP item."""

    used: str
    inside: str
    demand: str
    selection: str


@dataclass
class ElectricityItemXLReader:
    """Model class for defining read-locations for Electric-Equipment data in the PHPP."""

    __slots__ = ("shape", "cols", "rows")
    shape: shape_model.Electricity

    def __post_init__(self) -> None:
        """Aliases, just for convenience."""
        self.cols = self.shape.input_columns
        self.rows = self.shape.input_rows

    def _get_addresses(self, _rows: shape_model.ElectricityInputRow) -> ReaderAddressesGroup:
        """Return a group of addresses for a single PHPP Device."""
        return ReaderAddressesGroup(
            f"{self.cols.used}{_rows.data}",
            f"{self.cols.in_conditioned_space}{_rows.data}",
            f"{self.cols.annual_energy_demand}{_rows.data}",
            f"{self.cols.selection}{_rows.selection}",
        )

    @property
    def _dishwasher(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.dishwasher)
        return ReaderDataItem(
            ElectricEquipmentType.DISHWASHER,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
                PHPPReadAddress("water_connection", address.selection),
            ],
        )

    @property
    def _clothes_washer(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.clothes_washing)
        return ReaderDataItem(
            ElectricEquipmentType.CLOTHES_WASHER,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
                PHPPReadAddress("water_connection", address.selection),
            ],
        )

    @property
    def _clothes_dryer(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.clothes_drying)
        return ReaderDataItem(
            ElectricEquipmentType.CLOTHES_DRYER,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
                PHPPReadAddress("dryer_type", address.selection),
            ],
        )

    @property
    def _refrigerator(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.refrigerator)
        return ReaderDataItem(
            ElectricEquipmentType.REFRIGERATOR,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )

    @property
    def _fridge_freezer(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.fridge_freezer)
        return ReaderDataItem(
            ElectricEquipmentType.FRIDGE_FREEZER,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )

    @property
    def _freezer(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.freezer)
        return ReaderDataItem(
            ElectricEquipmentType.FREEZER,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )

    @property
    def _cooktop(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.cooking)
        return ReaderDataItem(
            ElectricEquipmentType.COOKING,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )

    @property
    def _mel(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.small_appliances)
        return ReaderDataItem(
            ElectricEquipmentType.MEL,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )

    @property
    def _lighting_interior(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.lighting_interior)
        return ReaderDataItem(
            ElectricEquipmentType.LIGHTING_INTERIOR,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )

    @property
    def _lighting_exterior(self) -> ReaderDataItem:
        address = self._get_addresses(self.rows.lighting_exterior)
        return ReaderDataItem(
            ElectricEquipmentType.LIGHTING_EXTERIOR,
            [
                PHPPReadAddress("quantity", address.used),
                PHPPReadAddress("in_conditioned_space", address.inside),
                PHPPReadAddress("energy_demand", address.demand),
            ],
        )
