# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP 'Electricity' worksheet."""

from __future__ import annotations

from typing import List, Type

from PHX.model import elec_equip
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import electricity_item
from PHX.PHPP.phpp_model.electricity_item import PHPPReadAddress
from PHX.xl import xl_app, xl_data


class Electricity:
    """IO Controller for PHPP "Electricity" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, shape: shape_model.Electricity) -> None:
        self.xl = _xl
        self.shape = shape
        self.device_map = elec_equip.get_device_type_map()

    def _turn_off_all_equipment(self) -> None:
        """Sets all the 'used' values to 0 to reset the sheet before writing new equipment."""
        for item in self.shape.input_rows:
            # Some items cannot be turned off....
            excluded = [
                "clothes_drying",
                "cooking",
                "consumer_elec",
                "lighting",
                "small_appliances",
            ]
            if item[0] in excluded:
                continue

            self.xl.write_xl_item(xl_data.XlItem(self.shape.name, f"{self.shape.input_columns.used}{item[1].data}", 0))

    def write_equipment(self, _equipment_inputs: List[electricity_item.ElectricityItemXLWriter]) -> None:
        """Write a list of equipment-input objects to the Worksheet."""
        self._turn_off_all_equipment()

        for equip_input in _equipment_inputs:
            for item in equip_input.create_xl_items(self.shape):
                self.xl.write_xl_item(item)

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

    def get_phx_elec_devices(self) -> List[elec_equip.PhxElectricalDevice]:
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
