# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "SolarDHW" worksheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any, Dict

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


@dataclass
class SolarDHWData:
    """Convenience class for organizing and cleaning the data."""

    footprint: Unit = field(default_factory=Unit)
    annual_dhw_energy: Unit = field(default_factory=Unit)
    annual_dhw_contribution: Unit = field(default_factory=Unit)
    annual_heating_energy: Unit = field(default_factory=Unit)
    annual_heating_contribution: Unit = field(default_factory=Unit)

    @classmethod
    def from_PHPP_data(cls, _data: Dict[str, Any]) -> SolarDHWData:
        """Clean up the data coming in from PHPP"""
        obj = cls()

        obj.footprint = Unit(_data["footprint"], _data["footprint_unit"])
        obj.annual_dhw_energy = Unit(_data["dhw_energy"], _data["energy_unit"])
        obj.annual_dhw_contribution = Unit(_data["dhw_contribution"], "-")
        obj.annual_heating_energy = Unit(_data["heating_energy"], _data["energy_unit"])
        obj.annual_heating_contribution = Unit(_data["heating_contribution"], "-")

        return obj


class SolarDHW:
    """IO Controller for the PHPP 'Solar DHW' worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.SolarDhw) -> None:
        self.xl = _xl
        self.shape = _shape

    def get_phpp_data(self) -> SolarDHWData:
        """Get the data from the PHPP worksheet."""
        get_ = partial(self.xl.get_single_data_item, self.shape.name)
        ranges = self.shape.ranges
        return SolarDHWData.from_PHPP_data(
            {
                "footprint_unit": self.shape.footprint_unit,
                "energy_unit": self.shape.energy_unit,
                "footprint": get_(ranges.footprint),
                "dhw_energy": get_(ranges.annual_dhw_energy),
                "dhw_contribution": get_(ranges.annual_dhw_contribution),
                "heating_energy": get_(ranges.annual_heating_energy),
                "heating_contribution": get_(ranges.annual_heating_contribution),
            }
        )
