# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Pydantic Model Unit-Types for WUFI-XML file format."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ph_units.converter import convert

# ------------------------------------------------------------------------------
# -- Base Unit Type Converters


class BaseConverter:
    """Base Class for any types which return a value, converted to the right unit."""

    __unit_type__ = ""
    __value_type__ = int

    # TODO: replace __get_validators__ with __get_pydantic_core_schema__

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        """
        Since WUFI XMl files come in several shapes and the XML tag may, or
        may not, include a "unit=..." attribute, we don't know what sort of input
        we're getting. So: if it is a dict input, that means it should have a
        "unit" type. But it if it is a bare int or float, then we assume it is
        the correct unit already (SI) and just return it.

        _input: Dict[str, Any] | str
            * {value: 7.5, unit_type: "hr"}
            * '7.5'
        """

        # If _input is NOT a dictionary, just cast it to the correct type and return it
        if not isinstance(v, dict):
            return cls.__value_type__(v)

        # If _input IS a dictionary but does NOT contain a 'value', return None
        if not v.get("value", None):
            return None

        # -- Otherwise, pull the value out of the dict and convert the value to the right unit
        try:
            result = convert(v["value"].strip(), v["unit_type"], cls.__unit_type__)
        except Exception as e:
            msg = f"Error converting to '{cls.__name__}' using the input of: [ {v} ]\n{e}"
            raise Exception(msg)

        # -- If the conversion was unsuccessful, raise an exception
        if result is None:
            msg = f"Error, could not convert:\n" f"\t{v['value']} from {v['unit_type']} to {cls.__unit_type__}"
            raise Exception(msg)

        # -- If the conversion was successful, cast the result to the correct type and return it
        return cls.__value_type__(result)


class BaseCaster:
    """Base Class for any types which return a value, cast to the right type."""

    __unit_type__ = ""
    __value_type__ = int

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        # def validate(cls, v: Union[Dict[str, Union[float, int]], None, float]):
        """
        _input: Dict[str, Any] | None | float
            * {value: 7.5, unit_type: "hr"}
            * None
            * '7.5'
        """

        # If v is a dictionary, get the 'value' key.
        # If 'value' key is not present, default to None.
        # If v is not a dictionary, use it as is.
        value = v.get("value", None) if isinstance(v, dict) else v

        # If value is None or the string "NONE", return None.
        if value is None or str(value).upper() == "NONE":
            return None

        # Cast the value to the correct type and return it.
        return cls.__value_type__(value)


# ------------------------------------------------------------------------------
# -- Generics


class _Int(int, BaseCaster):
    __unit_type__ = ""
    __value_type__ = int


class _Float(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


class _Percentage(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Power


class Watts(float, BaseConverter):
    __unit_type__ = "W"
    __value_type__ = float


class Watts_per_M2K(float, BaseConverter):
    __unit_type__ = "W/M2K"
    __value_type__ = float


class Watts_per_MK(float, BaseConverter):
    __unit_type__ = "W/MK"
    __value_type__ = float


class Watts_per_M2(float, BaseConverter):
    __unit_type__ = "W/M2"
    __value_type__ = float


class Watts_per_DegreeK(float, BaseConverter):
    __unit_type__ = "W/K"
    __value_type__ = float


class KiloWatt(float, BaseConverter):
    __unit_type__ = "KW"
    __value_type__ = float


class Watt_per_Watt(float, BaseConverter):
    __unit_type__ = "W/W"
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Energy


class kWh(float, BaseConverter):
    __unit_type__ = "KWH"
    __value_type__ = float


class kWh_per_M2(float, BaseConverter):
    __unit_type__ = "KWH/M2"
    __value_type__ = float


class kWh_per_kWh(float):
    __unit_type__ = "WUFI_MEW"
    __value_type__ = float

    # TODO: replace __get_validators__ with __get_pydantic_core_schema__

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> Optional[float]:
        # If v is not a dictionary, cast it to the correct type and return it
        if not isinstance(v, dict):
            return cls.__value_type__(v)

        # Extract value and unit_type from the dictionary
        value = v.get("value", None)
        unit_type = v.get("unit_type", None)

        # If value is not present or unit_type is "-", cast value to the correct type and return it
        if not value or (unit_type == "-"):
            return cls.__value_type__(value)

        # Try to convert the value
        result = convert(value, unit_type, cls.__unit_type__)

        # If the conversion was unsuccessful, raise an exception
        if result is None:
            raise Exception(f"Could not convert: {v['value']} from {v['unit_type']} to {cls.__unit_type__}")

        # If the conversion was successful, cast the result to the correct type and return it
        return cls.__value_type__(result)


class Wh_per_M3(float, BaseConverter):
    __unit_type__ = "WH/M3"
    __value_type__ = float


class Wh_per_M2K(float, BaseConverter):
    __unit_type__ = "WH/M2K"
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Size


class M(float, BaseConverter):
    __unit_type__ = "M"
    __value_type__ = float


class MM(float, BaseConverter):
    __unit_type__ = "MM"
    __value_type__ = float


class M3(float, BaseConverter):
    __unit_type__ = "M3"
    __value_type__ = float


class M2(float, BaseConverter):
    __unit_type__ = "M2"
    __value_type__ = float


class Liter(float):
    __unit_type__ = "L"
    __value_type__ = float

    # TODO: replace __get_validators__ with __get_pydantic_core_schema__

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> Optional[float]:
        if not isinstance(v, dict):
            return cls.__value_type__(v)

        if not v["value"]:
            return None

        if v["unit_type"] == "-":
            return cls.__value_type__(v["value"])

        result = convert(v["value"], v["unit_type"], cls.__unit_type__)
        if result is None:
            raise Exception(f"Could not convert: {v['value']} from {v['unit_type']} to {cls.__unit_type__}")
        return cls.__value_type__(result)


# ------------------------------------------------------------------------------
# -- Temperature


class DegreeC(float, BaseConverter):
    __unit_type__ = "C"
    __value_type__ = float


class DegreeDeltaK(float):
    # TODO: replace __get_validators__ with __get_pydantic_core_schema__

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        type = v["unit_type"]
        if type == "K":
            type = "DELTA-K"
        elif type == "C":
            type = "DELTA-C"
        elif type == "°F":
            type = "DELTA-F"

        result = convert(v["value"], type, "DELTA-C")
        if result is None:
            raise Exception(f"Could not convert: {v['value']} from {v['unit_type']} to C")
        return float(result)


# ------------------------------------------------------------------------------
# -- Speed


class M_per_Second(float, BaseConverter):
    __unit_type__ = "M/S"
    __value_type__ = float


class M_per_Day(float, BaseConverter):
    __unit_type__ = "M/DAY"
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Density


class KG_per_M3(float, BaseConverter):
    __unit_type__ = "KG/M3"
    __value_type__ = float


class MG_per_M3(float, BaseConverter):
    __unit_type__ = "MG/M3"
    __value_type__ = float


class Joule_per_KGK(float, BaseConverter):
    __unit_type__ = "J/KGK"
    __value_type__ = float


class PartsPerMillionByVolume(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Time


class Hour(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


class Days_per_Year(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


class Hours_per_Year(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


class KiloHours_per_Year(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Lighting


class Lux(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Airflow


class M3_per_Hour(float, BaseConverter):
    __unit_type__ = "M3/HR"
    __value_type__ = float


class M3_per_Hour_per_M2(float, BaseConverter):
    __unit_type__ = "M3/HRM2"
    __value_type__ = float


class ACH(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Geometry


class AngleDegree(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


class CardinalDegrees(float, BaseCaster):
    __unit_type__ = ""
    __value_type__ = float


# ------------------------------------------------------------------------------
# -- Moisture Resistance


class WUFI_Vapor_Resistance_Factor(float):
    __unit_type__ = "WUFI_MEW"
    __value_type__ = float

    # TODO: replace __get_validators__ with __get_pydantic_core_schema__

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> Optional[float]:
        if not isinstance(v, dict):
            return cls.__value_type__(v)

        if not v["value"]:
            return None

        if v["unit_type"] == "-":
            return cls.__value_type__(v["value"])

        result = convert(v["value"], v["unit_type"], cls.__unit_type__)
        if result is None:
            raise Exception(f"Could not convert: {v['value']} from {v['unit_type']} to {cls.__unit_type__}")
        return cls.__value_type__(result)
