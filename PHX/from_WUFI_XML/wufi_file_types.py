# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Pydantic Model for WUFI-XML file format."""

from __future__ import annotations
from typing import Dict, Union, Any, Optional
from ph_units.converter import convert


# ------------------------------------------------------------------------------
# -- Unit Types


class BaseConverter:
    """Base Class for any types which return a value, converted to the right unit."""

    __unit_type__ = ""
    __value_type__ = int

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        """
        Since WUFI XMl files come in several shapes and the XML tag may, or
        may not, include a "unit=__" attribute, we don't know what sort of input
        we're getting. So if it is a dict input, that means it should have a
        "unit" type. But it if it is a bare int or float, then we assume it is
        the correct unit already (SI) and just return it.
        """

        # -- If it is not a dict or None, just return the value
        if not isinstance(v, dict):
            return cls.__value_type__(v)

        # -- If its None, Return None
        if not v["value"]:
            return None

        # -- Otherwise, pull the value out of the dict and convert the value to the right unit
        try:
            result = convert(v["value"], v["unit_type"], cls.__unit_type__)
        except Exception:
            msg = f"Error converting input for '{cls.__name__}' using inputs: {v}"
            raise Exception(msg)
        if result is None:
            msg = (
                f"Error, could not convert:\n"
                f"\t{v['value']} from {v['unit_type']} to {cls.__unit_type__}"
            )
            raise Exception(msg)
        return cls.__value_type__(result)


class BaseCaster:
    """Base Class for any types which return a value, cast to the right type."""

    __unit_type__ = ""
    __value_type__ = int

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            if v["value"] is None:
                return None
            return cls.__value_type__(v["value"])
        elif v is None:
            return None
        else:
            return cls.__value_type__(v)


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
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to {cls.__unit_type__}"
            )
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


class M3(float, BaseConverter):
    __unit_type__ = "M3"
    __value_type__ = float


class M2(float, BaseConverter):
    __unit_type__ = "M2"
    __value_type__ = float


class Liter(float):
    __unit_type__ = "L"
    __value_type__ = float

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
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to {cls.__unit_type__}"
            )
        return cls.__value_type__(result)


# ------------------------------------------------------------------------------
# -- Temperature


class DegreeC(float, BaseConverter):
    __unit_type__ = "C"
    __value_type__ = float


class DegreeDeltaK(float):
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
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to {cls.__unit_type__}"
            )
        return cls.__value_type__(result)
