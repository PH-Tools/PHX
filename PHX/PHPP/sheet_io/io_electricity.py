# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP 'Electricity' worksheet."""

from __future__ import annotations

from PHX.model import elec_equip
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import electricity_item
from PHX.xl import xl_app, xl_data


class Electricity:
    """IO Controller for PHPP "Electricity" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Electricity) -> None:
        self.xl = _xl
        self.shape = shape
        self.device_map = elec_equip.get_device_type_map()

    def _write_annual_rows(self, _devices: list[elec_equip.PhxElectricalDevice]) -> None:
        """Write annual-energy devices onto the 'Other devices' annual rows, one row per category."""
        if not _devices:
            return

        other_devices = self.shape.other_devices
        if other_devices is None:
            self.xl.output(
                f"Warning: this PHPP version's '{self.shape.name}' shape has no annual 'Other devices' rows, "
                f"so {len(_devices)} lighting / MEL / custom device(s) were not written."
            )
            return

        annual_rows = other_devices.annual_rows.rows
        for offset, (category, device_types) in enumerate(electricity_item.ANNUAL_ROW_CATEGORIES):
            devices = [device for device in _devices if device.device_type in device_types]
            if not devices:
                continue
            writer = electricity_item.ElectricityAnnualRowXLWriter(category, devices)
            for item in writer.create_xl_items(self.shape, other_devices.description_column, annual_rows[offset]):
                self.xl.write_xl_item(item)

    def write_equipment(self, _equipment_inputs: list[electricity_item.ElectricityItemXLWriter]) -> None:
        """Write the model's devices; each category it authors replaces PHPP's template rows for that category."""
        annual_devices: list[elec_equip.PhxElectricalDevice] = []
        row_writers: list[electricity_item.ElectricityItemXLWriter] = []
        for equip_input in _equipment_inputs:
            if equip_input.phx_equipment.device_type in electricity_item.ANNUAL_ROW_TYPES:
                annual_devices.append(equip_input.phx_equipment)
            else:
                row_writers.append(equip_input)

        authored_types = {equip_input.phx_equipment.device_type for equip_input in _equipment_inputs}
        for row in electricity_item.replaced_template_rows(self.shape, authored_types):
            self.xl.write_xl_item(xl_data.XlItem(self.shape.name, f"{self.shape.input_columns.used}{row}", 0))

        for equip_input in row_writers:
            for item in equip_input.create_xl_items(self.shape):
                self.xl.write_xl_item(item)

        self._write_annual_rows(annual_devices)

    def build_phx_device_from_phpp(self, _reader: electricity_item.ReaderDataItem) -> elec_equip.PhxElectricalDevice:
        """Build a PHX Electrical Device object from the PHPP worksheet data."""

        # -- Get the right device class based on the device-type
        cls = self.device_map[_reader.type]
        phx_elec_device = cls()

        # -- Build the new Device using the input data from the PHPP Reader
        for phpp_read_address in _reader.data:
            phpp_data = self.xl.get_single_data_item(self.shape.name, phpp_read_address.phpp_address)
            setattr(phx_elec_device, phpp_read_address.attr_name, phpp_data)
        return phx_elec_device

    def get_phx_elec_devices(self) -> list[elec_equip.PhxElectricalDevice]:
        """Read the Device data from the PHPP worksheet and return a list of PhxElectricalDevice objects."""
        # -- Setup the reader class
        reader = electricity_item.ElectricityItemXLReader(self.shape)

        phx_elec_devices = [
            self.build_phx_device_from_phpp(reader._dishwasher),
            self.build_phx_device_from_phpp(reader._clothes_washer),
            self.build_phx_device_from_phpp(reader._clothes_dryer),
            self.build_phx_device_from_phpp(reader._refrigerator),
            self.build_phx_device_from_phpp(reader._fridge_freezer),
            self.build_phx_device_from_phpp(reader._freezer),
            self.build_phx_device_from_phpp(reader._cooktop),
            self.build_phx_device_from_phpp(reader._mel),
            self.build_phx_device_from_phpp(reader._lighting_interior),
            self.build_phx_device_from_phpp(reader._lighting_exterior),
        ]

        return phx_elec_devices
