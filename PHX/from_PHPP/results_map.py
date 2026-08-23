# -*- Python Version: 3.10 -*-

"""Where the headline results live, per PHPP version — with the caption each value must sit beside.

Addresses come from the phi-rules cell maps ('phpp-10-r1/calculators/phpp-verification',
'phpp-per', 'phpp-cooling-load') verified against the 10.6 EN blank workbook. Every
spec pairs the value cell with a label cell and the text expected there, so the reader
asserts the surface (the caption) before it trusts the number: a moved or renamed row
surfaces as 'label_mismatch', not as a silently wrong value.

PHPP 10.x addresses are one thing across the maintenance releases (phi-rules,
'phpp-10-r1/manual/README.md'), but only 10.6 EN has been read here; the other
10.x EN keys are registered as *assumed* and the report says so.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ValueKind(enum.Enum):
    """How to interpret a result cell.

    Values:
        NUMBER: A numeric result; a '-' string means 'not applicable' in this workbook state.
        TEXT: A selector string (ie: '10-Passive House').
    """

    NUMBER = "number"
    TEXT = "text"


@dataclass(frozen=True)
class ResultCellSpec:
    """One results-set item: value cell + the caption that must sit beside it.

    Attributes:
        key (str): The results-set key (ie: 'heating_demand').
        sheet (str): Worksheet name.
        cell (str): Value cell address.
        label_cell (str): The caption cell checked before the value is trusted.
        label_expected (str): Substring the caption must contain (case-insensitive, whitespace-collapsed).
        unit (str | None): The unit as PHPP displays it (ie: 'kWh/(m²a)'); None for selectors.
        ph_units_name (str | None): The ph_units unit name where one exists (ie: 'KWH/M2').
        kind (ValueKind): NUMBER or TEXT.
        unit_cell (str | None): The cell PHPP prints the unit in, read back as a second check, if any.
        note (str): What the cell is, in one line.
    """

    key: str
    sheet: str
    cell: str
    label_cell: str
    label_expected: str
    unit: str | None
    ph_units_name: str | None
    kind: ValueKind
    unit_cell: str | None = None
    note: str = ""


_V = "Verification"
_P = "PER"
_CL = "Cooling load"

RESULTS_MAP_EN_10_6: tuple[ResultCellSpec, ...] = (
    # -- program / class selectors (inputs, drop-downs)
    ResultCellSpec(
        "building_type",
        _V,
        "T9",
        "T8",
        "New building / Retrofit",
        None,
        None,
        ValueKind.TEXT,
        note="1-New building / 2-Retrofit / 3-Staged retrofit",
    ),
    ResultCellSpec(
        "energy_standard",
        _V,
        "T11",
        "T10",
        "Planned energy standard",
        None,
        None,
        ValueKind.TEXT,
        note="10-Passive House / 21-EnerPHit (Component) / 22-EnerPHit (Energy demand) / 30-PHI Low Energy Building / 40-Other",
    ),
    ResultCellSpec(
        "class_pe_method",
        _V,
        "T14",
        "T13",
        "Class | Primary energy method",
        None,
        None,
        ValueKind.TEXT,
        note="10-Classic|PER / 11-Classic|PE / 20-Plus|PER / 30-Premium|PER",
    ),
    # -- Verification results block
    ResultCellSpec("tfa", _V, "I35", "G35", "Treated floor area", "m²", "M2", ValueKind.NUMBER, "H35", "Areas!L8"),
    ResultCellSpec(
        "heating_demand",
        _V,
        "I36",
        "G36",
        "Heating demand",
        "kWh/(m²a)",
        "KWH/M2",
        ValueKind.NUMBER,
        "H36",
        "Heating!Q78",
    ),
    ResultCellSpec(
        "heating_load", _V, "I37", "G37", "Heating load", "W/m²", "W/M2", ValueKind.NUMBER, "H37", "'Heating load'!Q91"
    ),
    ResultCellSpec(
        "cooling_demand",
        _V,
        "I39",
        "G39",
        "Cooling & dehum. demand",
        "kWh/(m²a)",
        "KWH/M2",
        ValueKind.NUMBER,
        "H39",
        "Cooling!Q88+'Cooling units'!R82; '-' unless mechanical cooling (AB30)",
    ),
    ResultCellSpec(
        "overheating_frequency",
        _V,
        "I40",
        "G40",
        "Frequency of overheating",
        "%",
        None,
        ValueKind.NUMBER,
        "H40",
        "Summer!I62*100; blank when mechanical cooling",
    ),
    ResultCellSpec(
        "humidity_frequency",
        _V,
        "I41",
        "G41",
        "Frequency of excessively high humidity",
        "%",
        None,
        ValueKind.NUMBER,
        "H41",
        "SummVent!R66|L66*100",
    ),
    ResultCellSpec(
        "n50",
        _V,
        "I43",
        "G43",
        "Pressurisation test result n50",
        "1/h",
        None,
        ValueKind.NUMBER,
        "H43",
        "Ventilation!M23",
    ),
    ResultCellSpec(
        "pe_demand", _V, "I53", "G53", "PE demand", "kWh/(m²a)", "KWH/M2", ValueKind.NUMBER, "H53", "PER!X68"
    ),
    ResultCellSpec(
        "per_demand",
        _V,
        "I55",
        "G55",
        "PER demand",
        "kWh/(m²a)",
        "KWH/M2",
        ValueKind.NUMBER,
        "H55",
        "PER!V68 (total, incl. bioenergy budget)",
    ),
    ResultCellSpec(
        "renewable_generation",
        _V,
        "I56",
        "F56",
        "Renew. energy generation",
        "kWh/(m²a)",
        "KWH/M2",
        ValueKind.NUMBER,
        "H56",
        "PER!V77, per projected building footprint",
    ),
    # -- PER sheet
    ResultCellSpec(
        "per_demand_without_bioenergy",
        _P,
        "V65",
        "P65",
        "Total PER demand without bioenergy budget",
        "kWh/(m²a)",
        "KWH/M2",
        ValueKind.NUMBER,
        None,
        "PER!V65; V66 is the (negative) bioenergy utilisation",
    ),
    ResultCellSpec(
        "site_energy_demand",
        _P,
        "T114",
        "P114",
        "Demand",
        "MWh/a",
        None,
        ValueKind.NUMBER,
        "T113",
        "Final energy, whole building, annual balance",
    ),
    ResultCellSpec(
        "site_energy_generation",
        _P,
        "T115",
        "P115",
        "Generation",
        "MWh/a",
        None,
        ValueKind.NUMBER,
        "T113",
        "Final energy generation, whole building",
    ),
    # -- Cooling load sheet (not on Verification)
    ResultCellSpec(
        "cooling_load",
        _CL,
        "Q67",
        "N67",
        "Area specific cooling load",
        "W/m²",
        "W/M2",
        ValueKind.NUMBER,
        None,
        "'Cooling load'!Q66/D7",
    ),
)

# -- Keys verified by reading a workbook of that version; keys assumed from phi-rules' 10.x stability claim.
VERIFIED_VERSION_KEYS: dict[str, tuple[ResultCellSpec, ...]] = {"EN_10_6": RESULTS_MAP_EN_10_6}
ASSUMED_VERSION_KEYS: dict[str, tuple[ResultCellSpec, ...]] = {
    "EN_10_3": RESULTS_MAP_EN_10_6,
    "EN_10_4A": RESULTS_MAP_EN_10_6,
    "EN_10_4": RESULTS_MAP_EN_10_6,
    "EN_10_5": RESULTS_MAP_EN_10_6,
    "EN_10_7": RESULTS_MAP_EN_10_6,
}


@dataclass(frozen=True)
class ResolvedMap:
    """A results map picked for a version, with its provenance.

    Attributes:
        version_key (str): The key it was picked for (ie: 'EN_10_6').
        specs (tuple[ResultCellSpec, ...]): The cell specs.
        verified (bool): True if a workbook of this exact version was read when the map was built.
    """

    version_key: str
    specs: tuple[ResultCellSpec, ...]
    verified: bool


def resolve_map(version_key: str) -> ResolvedMap | None:
    """Return the results map for a PHX version key, or None if unsupported.

    Arguments:
    ----------
        * version_key: (str) ie: 'EN_10_6', 'EN_10_4A', 'EN_9_7IP'.

    Returns:
    --------
        * (ResolvedMap | None): None means 'refuse by name' (no map for this version/language).
    """
    if version_key in VERIFIED_VERSION_KEYS:
        return ResolvedMap(version_key, VERIFIED_VERSION_KEYS[version_key], verified=True)
    if version_key in ASSUMED_VERSION_KEYS:
        return ResolvedMap(version_key, ASSUMED_VERSION_KEYS[version_key], verified=False)
    return None
