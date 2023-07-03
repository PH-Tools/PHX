# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Pydantic Model for WUFI-XML file format."""

from __future__ import annotations
from typing import Dict, Union, Any, Optional
from ph_units.converter import convert


# ------------------------------------------------------------------------------
# -- Unit Types


class _Int(int):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return int(v)
        if not v["value"]:
            return None
        return int(v["value"])


class _Float(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)
        if not v["value"]:
            return None
        return float(v["value"])


class Percentage(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            if not v["value"]:
                return None
            return float(v["value"])
        else:
            return float(v)


# ------------------------------------------------------------------------------
# -- Power


class Watts(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "W")
        if result is None:
            raise Exception(f"Could not convert: {v['value']} from {v['unit_type']} to W")
        return float(result)


class Watts_per_M2K(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float:
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "W/M2K")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to W/M2K"
            )
        return float(result)


class Watts_per_MK(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "W/MK")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to W/MK"
            )
        return float(result)


class Watts_per_M2(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> Optional[float]:
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "W/M2")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to W/M2"
            )
        return float(result)


class Watts_per_DegreeK(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> Optional[float]:
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "W/K")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to W/K"
            )
        return float(result)


# ------------------------------------------------------------------------------
# -- Energy


class kWh(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "KWH")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to KWH"
            )
        return float(result)


class kWh_per_M2(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "KWH/M2")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to KWH/M2"
            )
        return float(result)


class kWh_per_kWh(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        return float(v["value"])


class Wh_per_M3(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "WH/M3")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to WH/M3"
            )
        return float(result)


class Wh_per_M2K(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float:
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "WH/M2K")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to WH/M2K"
            )
        return float(result)


# ------------------------------------------------------------------------------
# -- Size


class M(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to Meters"
            )
        return float(result)


class M3(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float:
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M3")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to M3"
            )
        return float(result)


class M2(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float:
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M2")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to M2"
            )
        return float(result)


class Liter(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> Optional[float]:
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "L")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to Liter"
            )
        return float(result)


# ------------------------------------------------------------------------------
# -- Temperature


class DegreeC(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        if not v["value"]:
            return None

        result = convert(v["value"], v["unit_type"], "C")
        if result is None:
            raise Exception(f"Could not convert: {v['value']} from {v['unit_type']} to C")
        return float(result)


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


class M_per_Second(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M/S")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to M/S"
            )
        return float(result)


class M_per_Day(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M/DAY")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to M/DAY"
            )
        return float(result)


# ------------------------------------------------------------------------------
# -- Density


class KG_per_M3(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "KG/M3")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to KG/M3"
            )
        return float(result)


class MG_per_M3(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "MG/M3")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to MG/M3"
            )
        return float(result)


class Joule_per_KGK(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "J/KGK")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to J/KGK"
            )
        return float(result)


class PartsPerMillionByVolume(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return float(v["value"])
        else:
            return float(v)


# ------------------------------------------------------------------------------
# -- Time


class Hour(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return float(v["value"])
        else:
            return float(v)


class Days_per_Year(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return float(v["value"])
        else:
            return float(v)


class Hours_per_Year(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return float(v["value"])
        else:
            return float(v)


# ------------------------------------------------------------------------------
# -- Lighting


class Lux(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float:
        if isinstance(v, dict):
            return float(v["value"])
        else:
            return float(v)


# ------------------------------------------------------------------------------
# -- Airflow


class M3_per_Hour(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float:
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M3/HR")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to M3/HR"
            )
        return float(result)


class M3_per_Hour_per_M2(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]):
        if not isinstance(v, dict):
            return float(v)

        result = convert(v["value"], v["unit_type"], "M3/HRM2")
        if result is None:
            raise Exception(
                f"Could not convert: {v['value']} from {v['unit_type']} to M3/HRM2"
            )
        return float(result)


class ACH(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float | None:
        if isinstance(v, dict):
            return float(v["value"])
        if not v:
            return None
        return float(v)


# ------------------------------------------------------------------------------
# -- Geometry


class AngleDegree(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Dict[str, Any]]) -> float | None:
        if isinstance(v, dict):
            return float(v["value"])
        if not v:
            return None
        return float(v)


class CardinalDegrees(float):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return float(v["value"])
        else:
            return float(v)
