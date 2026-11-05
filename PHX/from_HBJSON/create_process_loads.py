# -*- Python Version: 3.10 -*-

"""Build PHX Process Loads from Honeybee-Energy ElectricEquipment and Process loads.

Phius non-residential models take their internal loads from the Honeybee-Energy program,
the same loads EnergyPlus simulates. Each source Room contributes one row for its
ElectricEquipment and one row per electric Process load, so special loads (a kiln, a
commercial fridge) stay visible as their own line item for review.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from honeybee import room
from honeybee_energy.load.process import Process
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.schedule.ruleset import ScheduleRuleset

from PHX.from_HBJSON._type_utils import MissingEnergyPropertiesError, get_room_energy_properties
from PHX.model.enums.phius_certification import PhiusCertificationBuildingCategoryType
from PHX.model.loads.process import PhxProcessLoad

logger = logging.getLogger()


def is_phius_non_residential(_hb_room: room.Room) -> bool:
    """Return True if the Room's building segment is a Phius non-residential building."""
    room_prop_ph = getattr(_hb_room.properties, "ph", None)
    if room_prop_ph is None:
        return False
    category = room_prop_ph.ph_bldg_segment.phius_certification.building_category_type
    return category.number == PhiusCertificationBuildingCategoryType.NONRESIDENTIAL_BUILDING.value


def annual_full_load_hours(_schedule: ScheduleRuleset | ScheduleFixedInterval) -> float:
    """Return a schedule's annual full-load hours: its mean fractional value x 8760 [h].

    Fixed-interval schedules are read at their own timestep (sub-hourly values are not
    sampled), and a leap-year schedule is scaled to a 8760-hour year like a ruleset's.
    """
    if isinstance(_schedule, ScheduleFixedInterval):
        values = _schedule.values_at_timestep(_schedule.timestep)
        return float(sum(values)) / len(values) * 8760
    return float(sum(_schedule.values()))


def _inside_envelope(_lost_fraction: float, _row_name: str) -> bool:
    """A row is an internal gain unless all of its heat is lost; flag partial losses."""
    if 0.0 < _lost_fraction < 1.0:
        logger.warning(
            f"Process load '{_row_name}' has lost_fraction={_lost_fraction:.2f}. WUFI and METr cannot split "
            "a row's heat, so all of it is counted as an internal gain."
        )
    return _lost_fraction < 1.0


def _electric_equipment_row(_hb_room: room.Room) -> PhxProcessLoad | None:
    """Return the Room's ElectricEquipment as one annual-energy row, or None if it has none."""
    equipment = get_room_energy_properties(_hb_room).electric_equipment
    if equipment is None or equipment.watts_per_area <= 0.0:
        return None

    hours = annual_full_load_hours(equipment.schedule)
    name = f"{_hb_room.display_name}: Electric Equipment"
    return PhxProcessLoad(
        display_name=name,
        annual_energy_kwh=equipment.watts_per_area * _hb_room.floor_area * hours / 1_000,
        inside_thermal_envelope=_inside_envelope(equipment.lost_fraction, name),
        comment=(
            f"Honeybee-Energy ElectricEquipment: {equipment.watts_per_area:.2f} W/m2 x "
            f"{_hb_room.floor_area:.1f} m2 x {hours:.0f} full-load h ('{equipment.schedule.identifier}')"
        ),
    )


def _process_row(_hb_room: room.Room, _process: Process) -> PhxProcessLoad | None:
    """Return one electric Process load as an annual-energy row, or None if it carries no energy."""
    name = f"{_hb_room.display_name}: {_process.display_name}"
    if _process.watts <= 0.0:
        return None
    if _process.fuel_type != "Electricity":
        logger.warning(f"Process load '{name}' uses fuel '{_process.fuel_type}'; only electric rows are exported.")
        return None

    hours = annual_full_load_hours(_process.schedule)
    return PhxProcessLoad(
        display_name=name,
        annual_energy_kwh=_process.watts * hours / 1_000,
        inside_thermal_envelope=_inside_envelope(_process.lost_fraction, name),
        comment=(
            f"Honeybee-Energy Process: {_process.watts:.1f} W x {hours:.0f} full-load h "
            f"('{_process.schedule.identifier}')"
        ),
    )


def build_process_loads_from_hb_rooms(_hb_rooms: Iterable[room.Room]) -> list[PhxProcessLoad]:
    """Return the process-load rows for a set of (pre-merge) Honeybee Rooms.

    Each Room contributes its ElectricEquipment row, then one row per electric Process load.
    Rows are computed per source Room because merging Rooms keeps only one Room's
    equipment schedule.
    """
    rows: list[PhxProcessLoad] = []
    for hb_room in _hb_rooms:
        try:
            energy_props = get_room_energy_properties(hb_room)
        except MissingEnergyPropertiesError:
            continue

        if (equipment_row := _electric_equipment_row(hb_room)) is not None:
            rows.append(equipment_row)
        for process in energy_props.process_loads:
            if (process_row := _process_row(hb_room, process)) is not None:
                rows.append(process_row)

        if energy_props.gas_equipment is not None and energy_props.gas_equipment.watts_per_area > 0.0:
            logger.warning(
                f"Room '{hb_room.display_name}' has Honeybee-Energy GasEquipment; only electric loads are exported."
            )

    return rows
