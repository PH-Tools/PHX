# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "Cooling Units" worksheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ph_units.unit_type import Unit

from PHX.model.enums.hvac import CoolingType
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


@dataclass
class CoolingUnitData:
    """Convenience class for organizing and cleaning the data."""

    used: bool = False
    SEER: Unit = field(default_factory=Unit)
    num_units: int = 1
    _device_type_name: Optional[str] = None
    device_type: CoolingType = field(default=CoolingType.NONE)

    @property
    def device_type_name(self) -> Optional[str]:
        return self._device_type_name

    @device_type_name.setter
    def device_type_name(self, _value: Optional[str]) -> None:
        if _value is None:
            self._device_type_name = None
            return
        self._device_type_name = str(_value).split("-", 1)[-1].strip()

    @classmethod
    def from_PHPP_data(cls, _data: Dict[str, Any], _seer_unit: str) -> CoolingUnitData:
        """Clean up the data coming in from PHPP"""
        obj = cls()

        if _data.get("used", None) in ["X", "x"]:
            obj.used = True
        else:
            return obj

        obj.SEER = Unit(_data.get("SEER", 0.0), _seer_unit)
        obj.num_units = int(float(_data.get("num_units", 1.0)))
        # -- Since using named ranges, brings in a list of the merged columns...
        # -- Only want the first one.
        obj.device_type_name = str(_data.get("device_type_name", [None])[0])
        obj.device_type = _data["device_type"]

        return obj


class SupplyAir:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.CoolingUnits) -> None:
        self.xl = _xl
        self.shape = _shape

    def get_phpp_data(self) -> CoolingUnitData:
        shape = self.shape.supply_air
        data = {
            "used": self.xl.get_data(self.shape.name, shape.used),
            "SEER": self.xl.get_data(self.shape.name, shape.SEER),
            "num_units": self.xl.get_data(self.shape.name, shape.num_units),
            "device_type_name": self.xl.get_data(self.shape.name, shape.device_type_name),
            "device_type": CoolingType.VENTILATION,
        }
        return CoolingUnitData.from_PHPP_data(data, self.shape.SEER_unit)


class RecirculationAir:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.CoolingUnits) -> None:
        self.xl = _xl
        self.shape = _shape

    def get_phpp_data(self) -> CoolingUnitData:
        shape = self.shape.recirculation_air
        data = {
            "used": self.xl.get_data(self.shape.name, shape.used),
            "SEER": self.xl.get_data(self.shape.name, shape.SEER),
            "num_units": self.xl.get_data(self.shape.name, shape.num_units),
            "device_type_name": self.xl.get_data(self.shape.name, shape.device_type_name),
            "device_type": CoolingType.RECIRCULATION,
        }
        return CoolingUnitData.from_PHPP_data(data, self.shape.SEER_unit)


class Dehumidification:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.CoolingUnits) -> None:
        self.xl = _xl
        self.shape = _shape

    def get_phpp_data(self) -> CoolingUnitData:
        shape = self.shape.dehumidification
        data = {
            "used": self.xl.get_data(self.shape.name, shape.used),
            "SEER": self.xl.get_data(self.shape.name, shape.SEER),
            "device_type": CoolingType.DEHUMIDIFICATION,
        }
        return CoolingUnitData.from_PHPP_data(data, self.shape.SEER_unit)


class Panel:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.CoolingUnits) -> None:
        self.xl = _xl
        self.shape = _shape

    def get_phpp_data(self) -> CoolingUnitData:
        shape = self.shape.panel
        data = {
            "used": self.xl.get_data(self.shape.name, shape.used),
            "SEER": self.xl.get_data(self.shape.name, shape.SEER),
            "device_type_name": self.xl.get_data(self.shape.name, shape.device_type_name),
            "device_type": CoolingType.PANEL,
        }
        return CoolingUnitData.from_PHPP_data(data, self.shape.SEER_unit)


class CoolingUnits:
    """IO Controller for the PHPP Cooling Units worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.CoolingUnits) -> None:
        self.xl = _xl
        self.shape = _shape
        self.supply_air = SupplyAir(self.xl, self.shape)
        self.recirculation_air = RecirculationAir(self.xl, self.shape)
        self.dehumidification = Dehumidification(self.xl, self.shape)
        self.panel = Panel(self.xl, self.shape)

    def get_cooling_system_data(self) -> Tuple[CoolingUnitData, ...]:
        return (
            self.supply_air.get_phpp_data(),
            self.recirculation_air.get_phpp_data(),
            self.dehumidification.get_phpp_data(),
            self.panel.get_phpp_data(),
        )
