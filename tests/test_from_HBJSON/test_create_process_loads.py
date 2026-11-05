"""Phius non-residential Process Loads built from the Honeybee-Energy equipment loads."""

import pytest
from honeybee.room import Room
from honeybee_energy.load.equipment import ElectricEquipment
from honeybee_energy.load.process import Process
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy_ph.load.ph_equipment import PhCustomAnnualMEL
from ladybug.dt import Date

from PHX.from_HBJSON import create_project
from PHX.from_HBJSON.create_process_loads import annual_full_load_hours, build_process_loads_from_hb_rooms
from tests.test_from_HBJSON.test_create_rooms._occupancy_fixtures import NON_RES_FIXTURE, load_hb_model


def _constant(_identifier: str, _value: float) -> ScheduleRuleset:
    return ScheduleRuleset.from_constant_value(_identifier, _value)


def _room_with_equipment(_watts_per_m2: float, _fraction: float) -> Room:
    hb_room = Room.from_box("Lab", width=5, depth=4, height=3)  # -- 20 m2 floor
    hb_room.properties.energy.electric_equipment = ElectricEquipment(
        "Lab_Equipment", _watts_per_m2, _constant("Lab_Equipment_Schedule", _fraction)
    )
    return hb_room


def test_electric_equipment_becomes_one_annual_energy_row():
    """W/m2 x floor area x the schedule's full-load hours becomes the row's annual kWh."""
    rows = build_process_loads_from_hb_rooms([_room_with_equipment(10.0, 0.5)])

    assert [row.display_name for row in rows] == ["Lab: Electric Equipment"]
    assert rows[0].annual_energy_kwh == pytest.approx(10.0 * 20.0 * 0.5 * 8760 / 1000)
    assert rows[0].inside_thermal_envelope


def test_each_electric_process_load_is_its_own_row():
    """A special load keeps its own line; gas and zero-watt Process loads are not exported."""
    hb_room = _room_with_equipment(0.0, 1.0)
    for process in (
        Process("Kiln", 500.0, _constant("Kiln_Schedule", 1.0), "Electricity"),
        Process("Gas_Range", 800.0, _constant("Gas_Schedule", 1.0), "NaturalGas"),
        Process("PH_Placeholder", 0.0, _constant("Zero_Watt_Schedule", 1.0), "Electricity"),
    ):
        process.display_name = process.identifier
        hb_room.properties.energy.add_process_load(process)

    rows = build_process_loads_from_hb_rooms([hb_room])

    assert [(row.display_name, row.annual_energy_kwh) for row in rows] == [("Lab: Kiln", pytest.approx(4380.0))]


def _converted_zones(_non_residential: bool):
    hb_model = load_hb_model(NON_RES_FIXTURE)
    for hb_room in hb_model.rooms:
        if _non_residential:
            hb_room.properties.ph.ph_bldg_segment.phius_certification.building_category_type = 2
        # -- A real-watt Process carrying PH Equipment, as the residential components build them.
        process = Process(f"{hb_room.identifier}_MEL", 100.0, _constant("MEL_Schedule", 1.0), "Electricity")
        process.display_name = "MEL"
        process.properties.ph.ph_equipment = PhCustomAnnualMEL()
        hb_room.properties.energy.add_process_load(process)
    project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=False)
    return [zone for variant in project.variants for zone in variant.building.zones]


def test_phius_non_residential_zone_takes_equipment_from_honeybee_loads():
    """Non-res: one ElectricEquipment row and one Process row per source Room; no PH appliance devices."""
    zones = _converted_zones(_non_residential=True)

    rows = [row for zone in zones for row in zone.process_loads]
    assert len(rows) == 8
    assert sum("Electric Equipment" in row.display_name for row in rows) == 4
    assert sum(row.display_name.endswith(": MEL") for row in rows) == 4
    assert all(len(zone.elec_equipment_collection.devices) == 0 for zone in zones)


def test_phius_residential_zone_has_no_process_loads():
    """Residential models keep PH appliance equipment and get no Honeybee-derived process loads."""
    zones = _converted_zones(_non_residential=False)

    assert all(zone.process_loads == [] for zone in zones)
    assert sum(len(zone.elec_equipment_collection.devices) for zone in zones) > 0


@pytest.mark.parametrize(
    "schedule, expected_hours",
    [
        (ScheduleFixedInterval("Quarter_Hourly", [0, 1, 1, 1] * 8760, timestep=4), 6570.0),
        (ScheduleFixedInterval("Leap_Year", [0.5] * 8784, start_date=Date(1, 1, leap_year=True)), 4380.0),
    ],
)
def test_fixed_interval_full_load_hours_use_every_timestep_on_a_8760_hour_year(schedule, expected_hours):
    """Sub-hourly values are all counted, and a leap-year schedule scales to 8760 h like a ruleset."""
    assert annual_full_load_hours(schedule) == pytest.approx(expected_hours)


def test_merged_rooms_keep_one_row_and_one_schedule_per_source_room():
    """Rooms merged into one zone each keep their own equipment schedule (the merge keeps only one)."""
    hb_model = load_hb_model(NON_RES_FIXTURE)
    segment = hb_model.rooms[0].properties.ph.ph_bldg_segment
    segment.phius_certification.building_category_type = 2
    for i, hb_room in enumerate(hb_model.rooms, start=1):
        hb_room.properties.ph.ph_bldg_segment = segment
        hb_room.properties.energy.electric_equipment = ElectricEquipment(
            f"Equipment_{i}", 10.0, _constant(f"Equipment_Schedule_{i}", i / 10)
        )
    project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=False)
    zones = [zone for variant in project.variants for zone in variant.building.zones]

    assert len(zones) == 1
    assert [(row.display_name, row.annual_energy_kwh) for row in zones[0].process_loads] == [
        (f"{hb_room.display_name}: Electric Equipment", pytest.approx(10.0 * hb_room.floor_area * i / 10 * 8.76))
        for i, hb_room in enumerate(hb_model.rooms, start=1)
    ]
