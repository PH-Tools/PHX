# -*- Python Version: 3.10 -*-

"""Model class for a PHPP Electricity / Equipment row input."""

from dataclasses import dataclass
from typing import Any, NamedTuple

from PHX.model import elec_equip
from PHX.model.enums.elec_equip import ElectricEquipmentType
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data

# -----------------------------------------------------------------------------
# -- Device categories
#
# A category the model authors replaces PHPP's template entries for that
# category; a category it does not author keeps PHPP's template default.

REFRIGERATION_TYPES = frozenset(
    {
        ElectricEquipmentType.REFRIGERATOR,
        ElectricEquipmentType.FREEZER,
        ElectricEquipmentType.FRIDGE_FREEZER,
    }
)
INTERIOR_LIGHTING_TYPES = frozenset({ElectricEquipmentType.LIGHTING_INTERIOR, ElectricEquipmentType.CUSTOM_LIGHTING})
LIGHTING_TYPES = INTERIOR_LIGHTING_TYPES | {
    ElectricEquipmentType.LIGHTING_EXTERIOR,
    ElectricEquipmentType.LIGHTING_GARAGE,
}
MEL_TYPES = frozenset({ElectricEquipmentType.MEL, ElectricEquipmentType.CUSTOM_MEL})
CUSTOM_TYPES = frozenset({ElectricEquipmentType.CUSTOM})

#: Devices the model carries as annual energy, written to PHPP's 'Other devices'
#: annual rows (``Y = E·N``, kWh/a in ``N``), one row per category in this order.
#: PHPP's residential lighting rows take no annual energy (row 38 is per occupant,
#: from a lamp efficacy), so annual lighting is filed here too.
ANNUAL_ROW_CATEGORIES: tuple[tuple[str, frozenset[ElectricEquipmentType]], ...] = (
    ("Lighting", LIGHTING_TYPES),
    ("Misc. electric loads", MEL_TYPES),
    ("User defined", CUSTOM_TYPES),
)
ANNUAL_ROW_TYPES = LIGHTING_TYPES | MEL_TYPES | CUSTOM_TYPES


def replaced_template_rows(_shape: shape_model.Electricity, _authored_types: set[ElectricEquipmentType]) -> list[int]:
    """Return the template rows whose quantity PHX writes 0 because the model authors their category.

    Cooking, dishwashing, washing and drying are one row each, which the device's
    own writer overwrites, so they never appear here. Annual devices replace a
    template only where the shape has annual rows to write them to; elsewhere
    the template stays. 'E39' (lighting outside the dwelling unit) is a formula
    over rows 40-42 and is never replaced.
    """
    rows = _shape.input_rows
    replaced: list[int] = []
    if _authored_types & REFRIGERATION_TYPES:
        replaced.extend([rows.refrigerator.data, rows.freezer.data, rows.fridge_freezer.data])
    if _shape.other_devices is None:
        return replaced
    if _authored_types & INTERIOR_LIGHTING_TYPES:
        replaced.append(rows.lighting_interior.data)
    if _authored_types & (MEL_TYPES | CUSTOM_TYPES):
        replaced.extend(_shape.other_devices.standard_rows.rows)
    return replaced


# -----------------------------------------------------------------------------
# -- Worksheet Writer


@dataclass
class ElectricityAnnualRowXLWriter:
    """One PHPP 'Other devices' annual row holding every device of one category."""

    __slots__ = ("category", "devices")
    category: str
    devices: list[elec_equip.PhxElectricalDevice]

    @staticmethod
    def _annual_kwh(_device: elec_equip.PhxElectricalDevice) -> float:
        return _device.get_energy_demand() * _device.get_quantity()

    @property
    def total_kwh(self) -> float:
        """The category's annual energy, kWh/a."""
        return sum(self._annual_kwh(device) for device in self.devices)

    def create_xl_items(
        self, _shape: shape_model.Electricity, _description_column: str, _row: int
    ) -> list[xl_data.XlItem]:
        """Return the description, quantity, IHG flag and annual energy for one annual row."""
        total_kwh = self.total_kwh
        inside_kwh = sum(self._annual_kwh(device) for device in self.devices if device.in_conditioned_space)
        names = ", ".join(device.display_name or "" for device in self.devices)
        cols = _shape.input_columns

        items: list[tuple[str, xl_data.xl_writable]] = [
            (f"{_description_column}{_row}", f"{self.category}: {names}"),
            (f"{cols.used}{_row}", 1),
            # -- The IHG flag is 1 inside the envelope, 0 outside. PHPP weights it by
            # -- energy ('Electricity!F68'), so a mixed category writes its inside share.
            (f"{cols.in_conditioned_space}{_row}", inside_kwh / total_kwh if total_kwh else 0),
            # -- On the annual rows column N is the energy per device, kWh/a.
            (f"{cols.energy_demand_per_use}{_row}", total_kwh),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]


@dataclass
class ElectricityItemXLWriter:
    """Model class for a single Electric-Equipment item entry row."""

    __slots__ = "phx_equipment"
    phx_equipment: Any

    def create_xl_items(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        """Returns a list of xl_data.XlItem or raises and Error if equipment type is unrecognized.

        Annual-energy devices (``ANNUAL_ROW_TYPES``) have no row of their own; the
        worksheet controller groups them with ``ElectricityAnnualRowXLWriter``.
        """
        xl_item_functions = {
            ElectricEquipmentType.DISHWASHER: self._dishwasher,
            ElectricEquipmentType.CLOTHES_WASHER: self._clothes_washer,
            ElectricEquipmentType.CLOTHES_DRYER: self._clothes_dryer,
            ElectricEquipmentType.REFRIGERATOR: self._refrigerator,
            ElectricEquipmentType.FREEZER: self._freezer,
            ElectricEquipmentType.FRIDGE_FREEZER: self._fridge_freezer,
            ElectricEquipmentType.COOKING: self._cooktop,
        }
        try:
            return xl_item_functions[self.phx_equipment.device_type](_shape)
        except KeyError:
            raise NotImplementedError(
                f"No matching XL-write function found for equipment type: '{self.phx_equipment.device_type}'"
            )

    def _dishwasher(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceDishwasher = self.phx_equipment
        cols = _shape.input_columns
        rows = _shape.input_rows
        address_used = f"{cols.used}{rows.dishwasher.data}"
        address_inside = f"{cols.in_conditioned_space}{rows.dishwasher.data}"
        address_demand = f"{cols.energy_demand_per_use}{rows.dishwasher.data}"
        address_selection = f"{cols.selection}{rows.dishwasher.selection}"

        items: list[tuple[str, xl_data.xl_writable]] = [
            (address_used, 1),
            (address_inside, str(int(equip.in_conditioned_space or 1))),
            (address_demand, equip.energy_demand_per_use),
            (
                address_selection,
                rows.dishwasher.selection_options[str(equip.water_connection)],
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _clothes_washer(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceClothesWasher = self.phx_equipment
        items: list[tuple[str, xl_data.xl_writable]] = [
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

    def _clothes_dryer(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceClothesDryer = self.phx_equipment
        items: list[tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.clothes_drying.data}", 1),
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

    def _refrigerator(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceRefrigerator = self.phx_equipment
        items: list[tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.refrigerator.data}", 1),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.refrigerator.data}",
                equip.energy_demand_per_use,
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _fridge_freezer(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceFridgeFreezer = self.phx_equipment
        items: list[tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.fridge_freezer.data}", 1),
            (
                f"{_shape.input_columns.energy_demand_per_use}{_shape.input_rows.fridge_freezer.data}",
                equip.energy_demand_per_use,
            ),
        ]
        return [xl_data.XlItem(_shape.name, *item) for item in items]

    def _freezer(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceFreezer = self.phx_equipment
        items: list[tuple[str, xl_data.xl_writable]] = [
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

    def _cooktop(self, _shape: shape_model.Electricity) -> list[xl_data.XlItem]:
        equip: elec_equip.PhxDeviceCooktop = self.phx_equipment
        items: list[tuple[str, xl_data.xl_writable]] = [
            (f"{_shape.input_columns.used}{_shape.input_rows.cooking.data}", 1),
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


# -----------------------------------------------------------------------------
# -- Worksheet Reader


class PHPPReadAddress(NamedTuple):
    """Attribute Name / PHPP Address pair."""

    attr_name: str
    phpp_address: str


class ReaderDataItem(NamedTuple):
    """Electric-Equipment data for a single PHPP item."""

    type: ElectricEquipmentType
    data: list[PHPPReadAddress]


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
