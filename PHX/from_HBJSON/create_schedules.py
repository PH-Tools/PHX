# -*- Python Version: 3.10 -*-

"""Functions used to create Project elements from the Honeybee-Model"""


from honeybee import model, room
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier
from honeybee_energy.schedule import ruleset as hbe_ruleset
from honeybee_energy_ph.properties import ruleset as phx_ruleset
from honeybee_ph_utils.schedules import calc_four_part_vent_sched_values_from_hb_room

from PHX.from_HBJSON._type_utils import (
    MissingEnergyPropertiesError,
    get_lighting_schedule,
    get_people_schedule,
    get_room_energy_properties,
    get_ventilation_schedule,
)
from PHX.model import project
from PHX.model.schedules import lighting, occupancy, ventilation


def _room_has_ph_style_ventilation(_hb_room: room.Room) -> bool:
    """Returns True if the HB Room has detailed PH-Style ventilation schedule
        information, False if not.

    Arguments:
    ----------
        * _hb_room (room.Room): The Honeybee Room to look at.

    Returns:
    --------
        * (bool):
    """

    # -------------------------------------------------------------------------
    # -- Honeybee-Energy data might not be there...
    try:
        hbe_vent_sched = get_ventilation_schedule(_hb_room)
    except MissingEnergyPropertiesError:
        # No Honeybee-Energy Room Properties or Ventilation Schedule
        return False

    # -------------------------------------------------------------------------
    # -- Check Honeybee-Energy-PH detailed data
    hbe_vent_sched_prop = hbe_vent_sched.properties
    hbph_sched_prop: phx_ruleset.ScheduleRulesetPhProperties = hbe_vent_sched_prop.ph  # type: ignore
    # No Honeybee-Energy-PH Schedule detailed Operating Periods - return whether they exist
    return bool(hbph_sched_prop.daily_operating_periods)


def _create_vent_schedule_from_hb_style(
    _hb_room: room.Room,
) -> ventilation.PhxScheduleVentilation:
    """Returns a new PHX Ventilation Schedule based on the HB-Room's E+
    HB-Style info found on the energy.ventilation

    This is used when no detailed PH-Style info is set by the user and you want to
    convert over an existing E+/HB style ventilation object to PH-Style.

    Arguments:
    ----------
        * _hb_room (room.Room): The Honeybee Room to build the new PHX UtilizationPatternVent from.

    Returns:
    --------
        * (ventilation.PhxScheduleVentilation): A new PHX Ventilation Schedule.
    """

    # -- Type Aliases
    hbe_vent_sched = get_ventilation_schedule(_hb_room)

    new_phx_vent_schedule = ventilation.PhxScheduleVentilation()

    wufi_sched = calc_four_part_vent_sched_values_from_hb_room(_hb_room)
    op_periods = new_phx_vent_schedule.operating_periods
    op_periods.high.period_operating_hours = wufi_sched.high.period_operating_hours
    op_periods.high.period_operation_speed = wufi_sched.high.period_speed
    op_periods.standard.period_operating_hours = wufi_sched.standard.period_operating_hours
    op_periods.standard.period_operation_speed = wufi_sched.standard.period_speed
    op_periods.basic.period_operating_hours = wufi_sched.basic.period_operating_hours
    op_periods.basic.period_operation_speed = wufi_sched.basic.period_speed
    op_periods.minimum.period_operating_hours = wufi_sched.minimum.period_operating_hours
    op_periods.minimum.period_operation_speed = wufi_sched.minimum.period_speed

    # -- Keep all the IDs in alignment....
    new_phx_vent_schedule.identifier = hbe_vent_sched.identifier
    new_phx_vent_schedule.id_num = new_phx_vent_schedule._count
    ph_sched_props: phx_ruleset.ScheduleRulesetPhProperties = hbe_vent_sched.properties.ph  # type: ignore
    ph_sched_props.id_num = new_phx_vent_schedule.id_num  # <--- Important!
    new_phx_vent_schedule.name = hbe_vent_sched.display_name

    return new_phx_vent_schedule


def _create_vent_schedule_from_ph_style(
    _hb_room: room.Room,
) -> ventilation.PhxScheduleVentilation:
    """Returns a new PHX Utilization Pattern (Vent) based on the HB-Room's detailed
    PH-Style info found on the energy.ventilation.schedule.properties.ph

    Arguments:
    ----------
        * _hb_room (room.Room): The Honeybee Room to build the new PHX UtilizationPatternVent from.

    Returns:
    --------
        * (ventilation.PhxScheduleVentilation): A new PHX Ventilation Schedule
    """

    # -- Type Aliases
    hbe_vent_sched = get_ventilation_schedule(_hb_room)
    hbe_vent_sched_prop = hbe_vent_sched.properties
    hbe_vent_sched_prop_ph: phx_ruleset.ScheduleRulesetPhProperties = hbe_vent_sched_prop.ph  # type: ignore

    # -- Create the new Schedule object
    new_phx_vent_schedule = ventilation.PhxScheduleVentilation()
    new_phx_vent_schedule.name = hbe_vent_sched.display_name

    # -- Set all the ventilation schedule data from the room's properties
    new_phx_vent_schedule.operating_hours = 24.0
    new_phx_vent_schedule.operating_days = hbe_vent_sched_prop_ph.operating_days_wk
    new_phx_vent_schedule.operating_weeks = hbe_vent_sched_prop_ph.operating_weeks_year

    for op_period in hbe_vent_sched_prop_ph.daily_operating_periods:
        phx_vent_util_period = getattr(new_phx_vent_schedule.operating_periods, op_period.name)
        phx_vent_util_period.period_operating_hours = op_period.operation_hours
        phx_vent_util_period.period_operation_speed = op_period.operation_fraction
        setattr(new_phx_vent_schedule.operating_periods, op_period.name, phx_vent_util_period)

    # -- Keep all the IDs in alignment....
    new_phx_vent_schedule.identifier = hbe_vent_sched.identifier
    new_phx_vent_schedule.id_num = new_phx_vent_schedule._count
    hbe_vent_sched_prop_ph.id_num = new_phx_vent_schedule.id_num  # Important!

    return new_phx_vent_schedule


def build_ventilation_schedule_from_hb_room(
    _hb_room: room.Room,
) -> ventilation.PhxScheduleVentilation | None:
    """Build a new Ventilation Schedule based on a Honeybee-Room's energy.ventilation values.

    Arguments:
    ----------
        *_hb_room (room.Room): The Honeybee-Room to get the ventilation pattern data from.

    Returns:
    --------
        * (Optional[ventilation.PhxScheduleVentilation]): The new Ventilation Schedule or None
            if no energy.ventilation or energy.ventilation.schedule is found on the room.
    """

    # -- Make sure that the room has vent schedule
    try:
        get_ventilation_schedule(_hb_room)
    except MissingEnergyPropertiesError:
        # No ventilation or ventilation.schedule found
        return None

    if _room_has_ph_style_ventilation(_hb_room):
        # -- The room's ventilation DOES have detailed user-inputs for operation
        # -- periods, so just use those. This is the case when a Honeybee-PH
        # -- component is used to build the PH_ScheduleRuleset
        new_vent_schedule = _create_vent_schedule_from_ph_style(_hb_room)
    else:
        # -- There IS a ventilation.schedule, BUT there are no detailed
        # -- Passive House style user-input operation periods set on it. This
        # -- is the case when a normal HB-Ventilation ScheduleRuleset is
        # -- converted over to a PH_ScheduleRuleset
        new_vent_schedule = _create_vent_schedule_from_hb_style(_hb_room)

    # -- Ensure that the operating hours add up to exactly 24
    new_vent_schedule.force_max_utilization_hours()

    return new_vent_schedule


def build_occupancy_schedule_from_hb_room(
    _hb_room: room.Room,
) -> occupancy.PhxScheduleOccupancy | None:
    """Build a new PHX Occupancy Schedule based on a Honeybee-Room's energy.people values.

    Arguments:
    ----------
        * _hb_room (room.Room): The Honeybee Room to build the schedules from.

    Returns:
    --------
        * (Optional[occupancy.PhxScheduleOccupancy]): The new PHX Occupancy Schedule or None.
    """

    # -- Make sure that the room has an occupancy schedule
    try:
        hbe_schedule = get_people_schedule(_hb_room)
    except MissingEnergyPropertiesError:
        # No people or occupancy_schedule found
        return None

    hbe_schedule_prop_ph: phx_ruleset.ScheduleRulesetPhProperties = hbe_schedule.properties.ph  # type: ignore
    daily_period = hbe_schedule_prop_ph.first_operating_period

    # -- Build the new Schedule
    new_phx_occ_schedule = occupancy.PhxScheduleOccupancy()
    new_phx_occ_schedule.identifier = hbe_schedule.identifier
    new_phx_occ_schedule.display_name = hbe_schedule.display_name
    new_phx_occ_schedule.annual_utilization_days = hbe_schedule_prop_ph.operating_days_year
    new_phx_occ_schedule.relative_utilization_factor = hbe_schedule_prop_ph.annual_average_operating_fraction

    if daily_period:
        new_phx_occ_schedule.start_hour = daily_period.start_hour
        new_phx_occ_schedule.end_hour = daily_period.end_hour
    else:
        new_phx_occ_schedule.start_hour = 0
        new_phx_occ_schedule.end_hour = 24

    return new_phx_occ_schedule


def build_lighting_schedule_from_hb_room(
    _hb_room: room.Room,
) -> lighting.PhxScheduleLighting | None:
    """Build a new PHX Lighting Schedule based on a Honeybee-Room's energy.lighting.schedule values.

    Arguments:
    ----------
        * _hb_room (room.Room): The Honeybee Room to build the schedules from.

    Returns:
    --------
        * (Optional[occupancy.PhxScheduleLighting]): The new PHX Lighting Schedule or None.
    """

    # -- Make sure that the room has an occupancy schedule
    try:
        hbe_schedule = get_lighting_schedule(_hb_room)
    except MissingEnergyPropertiesError:
        # No lighting or lighting.schedule found
        return None

    hbe_schedule_prop_ph: phx_ruleset.ScheduleRulesetPhProperties = hbe_schedule.properties.ph  # type: ignore
    daily_period = hbe_schedule_prop_ph.first_operating_period

    # -- Build the new Schedule
    new_phx_occ_schedule = lighting.PhxScheduleLighting()
    new_phx_occ_schedule.identifier = hbe_schedule.identifier
    new_phx_occ_schedule.display_name = hbe_schedule.display_name
    new_phx_occ_schedule.annual_utilization_days = hbe_schedule_prop_ph.operating_days_year
    new_phx_occ_schedule.relative_utilization_factor = hbe_schedule_prop_ph.annual_average_operating_fraction

    if daily_period:
        new_phx_occ_schedule.start_hour = daily_period.start_hour
        new_phx_occ_schedule.end_hour = daily_period.end_hour
    else:
        new_phx_occ_schedule.start_hour = 0
        new_phx_occ_schedule.end_hour = 24

    return new_phx_occ_schedule


def _add_default_vent_schedule_to_Rooms(_hb_model: model.Model) -> model.Model:
    """Add a default ventilation.schedule to the HB Model's Rooms if they have None.

    Some HB Programs do not have a ventilation.schedule. I *think* this means
    constant operation. So add the constant value (1) default ventilation schedule to the room.

    Arguments:
    ----------
        * _hb_model (model.Model): The Honeybee Model to add the new constant value
            ventilation schedules to.

    Returns:
    --------
        * (model.Model): The Honeybee Model with new ventilation schedules added to
            any Rooms which were missing them.
    """
    type_limit = schedule_type_limit_by_identifier("Fractional")
    default_ventilation_schedule = hbe_ruleset.ScheduleRuleset.from_constant_value("default_schedule", 1.0, type_limit)

    for hb_room in _hb_model.rooms:
        try:
            get_ventilation_schedule(hb_room)
        except MissingEnergyPropertiesError:
            # No ventilation schedule found - add default
            try:
                room_energy_props = get_room_energy_properties(hb_room)
                if room_energy_props.ventilation is not None:
                    room_energy_props.ventilation.unlock()  # type: ignore
                    room_energy_props.ventilation.schedule = default_ventilation_schedule
                    room_energy_props.ventilation.lock()  # type: ignore
            except MissingEnergyPropertiesError:
                # Room has no energy properties at all - skip it
                continue

    return _hb_model


def add_all_HB_Model_ventilation_schedules_to_PHX_Project(_project: project.PhxProject, _hb_model: model.Model) -> None:
    """Add all the Room's Ventilation Schedules to the project's Collection.

    Arguments:
    ----------
        * _project (project.Project): The PHX-Project to add the new
            Ventilation Schedules to.
        * _hb_model (model.Model): Then Honeybee Model to build up the
            new Ventilation Schedules from.

    Returns:
    --------
        * None
    """

    # -- FIRST: Have to clean up the HB-ventilation schedules where they are missing.
    _hb_model = _add_default_vent_schedule_to_Rooms(_hb_model)

    # -- NEXT: Build up the new Ventilation Schedules from the Room's data
    for hb_room in _hb_model.rooms:
        try:
            vent_schedule = get_ventilation_schedule(hb_room)
            vent_schedule_id = vent_schedule.identifier
        except MissingEnergyPropertiesError:
            # No ventilation schedule found, skip this room
            continue

        if _project.vent_sched_in_project_collection(vent_schedule_id):
            # -- This is just to help speed things up.
            # -- Don't re-make the util-pattern if it is already in collection.
            continue

        new_phx_vent_schedule = build_ventilation_schedule_from_hb_room(hb_room)
        if new_phx_vent_schedule:
            _project.add_vent_sched_to_collection(new_phx_vent_schedule)


def add_all_HB_Model_occupancy_schedules_to_PHX_Project(_project: project.PhxProject, _hb_model: model.Model) -> None:
    """Add all the Room's Occupancy Schedules to the project's Collection.

    Arguments:
    ----------
        * _project (project.Project): The PHX-Project to add the new
            Occupancy Schedules to.
        * _hb_model (model.Model): Then Honeybee Model to build up the
            new Occupancy Schedules from.

    Returns:
    --------
        * None
    """
    for hb_room in _hb_model.rooms:
        try:
            occ_schedule = get_people_schedule(hb_room)
            occ_schedule_id = occ_schedule.identifier
        except MissingEnergyPropertiesError:
            # No people or occupancy schedule found, skip this room
            continue

        if _project.occupancy_sched_in_project_collection(occ_schedule_id):
            # -- This is just to help speed things up.
            # -- Don't re-make the util-pattern if it is already in collection.
            continue

        new_phx_occ_schedule = build_occupancy_schedule_from_hb_room(hb_room)
        _project.add_occupancy_sched_to_collection(new_phx_occ_schedule)


def add_all_HB_Model_lighting_schedules_to_PHX_Project(_project: project.PhxProject, _hb_model: model.Model) -> None:
    for hb_room in _hb_model.rooms:
        try:
            lighting_schedule = get_lighting_schedule(hb_room)
            lighting_schedule_id = lighting_schedule.identifier
        except MissingEnergyPropertiesError:
            # No lighting or lighting.schedule found, skip this room
            continue

        if _project.lighting_sched_in_project_collection(lighting_schedule_id):
            # -- This is just to help speed things up.
            # -- Don't re-make the util-pattern if it is already in collection.
            continue

        new_phx_lighting_schedule = build_lighting_schedule_from_hb_room(hb_room)
        _project.add_lighting_sched_to_collection(new_phx_lighting_schedule)


def add_all_HB_schedules_to_PHX_Project(_project: project.PhxProject, _hb_model: model.Model) -> None:
    """Add all the schedules (Ventilation, Occupancy, Lighting) to the PHX Project's Collections.

    Arguments:
    ----------
        * _project (project.Project): The PHX-Project to add the new
            Schedules to.
        * _hb_model (model.Model): Then Honeybee Model to build up the
            new Schedules from.

    Returns:
    --------
        * (None)
    """
    add_all_HB_Model_ventilation_schedules_to_PHX_Project(_project, _hb_model)
    add_all_HB_Model_occupancy_schedules_to_PHX_Project(_project, _hb_model)
    add_all_HB_Model_lighting_schedules_to_PHX_Project(_project, _hb_model)
