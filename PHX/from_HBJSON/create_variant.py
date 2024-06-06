# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to build PHX-Variant from Honeybee Rooms"""

import logging
from typing import Dict, Set

logger = logging.getLogger()

from honeybee import room
from honeybee_energy.load.equipment import ElectricEquipment
from honeybee_energy.properties.room import RoomEnergyProperties
from honeybee_energy_ph.properties.load import equipment, people
from honeybee_ph import phi, phius, site
from honeybee_ph.bldg_segment import BldgSegment
from honeybee_ph.properties.room import RoomPhProperties, get_ph_prop_from_room
from honeybee_phhvac.properties.room import (
    get_exhaust_vent_devices_from_space,
    get_heat_pump_systems_from_space,
    get_heating_systems_from_space,
    get_ph_hvac_from_space,
    get_renewable_devices_from_space,
    get_supportive_devices_from_space,
    get_ventilation_system_from_space,
)

from PHX.from_HBJSON import create_building, create_elec_equip, create_foundations, create_hvac
from PHX.from_HBJSON.create_shw_devices import (
    build_phx_hw_heater,
    build_phx_hw_storage,
    build_phx_pipe_element,
    build_phx_trunk_pipe,
)
from PHX.model import certification, constructions, phx_site, project
from PHX.model.enums import hvac, phi_certification_phpp_9, phi_certification_phpp_10, phius_certification
from PHX.model.utilization_patterns import (
    UtilizationPatternCollection_Lighting,
    UtilizationPatternCollection_Occupancy,
    UtilizationPatternCollection_Ventilation,
)


def add_building_from_hb_room(
    _variant: project.PhxVariant,
    _hb_room: room.Room,
    _assembly_dict: Dict[str, constructions.PhxConstructionOpaque],
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    _vent_sched_collection: UtilizationPatternCollection_Ventilation,
    _occ_sched_collection: UtilizationPatternCollection_Occupancy,
    _lighting_sched_collection: UtilizationPatternCollection_Lighting,
    _group_components: bool = False,
    _merge_spaces_by_erv: bool = False,
    _tolerance: float = 0.001,
) -> None:
    """Create the  PHX-Building with all Components and Zones based on a Honeybee-Room.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the building to.
        * _hb_room (room.Room): The honeybee-Room to use as the source.
        * _assembly_dict (Dict[str, constructions.PhxConstructionOpaque]): The Assembly Type dict.
        * _window_type_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.
        * _vent_sched_collection (UtilizationPatternVentCollection): The PhxProject's
            UtilizationPatternVentCollection with the ventilation schedules.
        * _occ_sched_collection (UtilizationPatternOccCollection): The PhxProject's
            UtilizationPatternOccCollection with the occupancy schedules.
        * _lighting_sched_collection (UtilizationPatternLightingCollection): The PhxProject's
            UtilizationPatternLightingCollection with the lighting schedules.
        * group_components (bool): default=False. Set to true to have the converter
            group the components by assembly-type.

    Returns:
    --------
        * None
    """
    _variant.building.add_components(
        create_building.create_components_from_hb_room(_hb_room, _assembly_dict, _window_type_dict, _tolerance)
    )
    _variant.building.add_zones(
        create_building.create_zones_from_hb_room(
            _hb_room,
            _vent_sched_collection,
            _occ_sched_collection,
            _lighting_sched_collection,
            _merge_spaces_by_erv,
        )
    )

    if _group_components:
        _variant.building.merge_opaque_components_by_assembly()
        _variant.building.merge_aperture_components_by_assembly()
        _variant.building.merge_thermal_bridges()


def add_phius_certification_from_hb_room(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Set all the PhxPhiusCertificationCriteria on a PhxVariant based on a Honeybee-Room's Building Segment.

    Arguments:
    ----------
        * _variant (project.Variant): The PhxVariant to set the PhxPhiusCertificationCriteria on.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    # -- alias cus' all this shit is deep in there...
    room_ph_prop: RoomPhProperties = getattr(_hb_room.properties, "ph")
    hbph_phius_cert: phius.PhiusCertification = room_ph_prop.ph_bldg_segment.phius_certification
    phx_phius_cert_criteria = _variant.phius_cert.phius_certification_criteria
    phx_phius_cert_settings = _variant.phius_cert.phius_certification_settings

    # -- some random bullshit
    phx_phius_cert_criteria.ph_selection_target_data = hbph_phius_cert.localization_selection_type

    # -- certification thresholds (for Phius, they change with climate)
    phx_phius_cert_criteria.phius_annual_heating_demand = hbph_phius_cert.PHIUS2021_heating_demand
    phx_phius_cert_criteria.phius_annual_cooling_demand = hbph_phius_cert.PHIUS2021_cooling_demand
    phx_phius_cert_criteria.phius_peak_heating_load = hbph_phius_cert.PHIUS2021_heating_load
    phx_phius_cert_criteria.phius_peak_cooling_load = hbph_phius_cert.PHIUS2021_cooling_load

    # -- certification settings / types
    phx_phius_cert_settings.phius_building_certification_program = phius_certification.PhiusCertificationProgram(
        hbph_phius_cert.certification_program.number
    )
    phx_phius_cert_settings.phius_building_category_type = phius_certification.PhiusCertificationBuildingCategoryType(
        hbph_phius_cert.building_category_type.number
    )
    phx_phius_cert_settings.phius_building_use_type = phius_certification.PhiusCertificationBuildingUseType(
        hbph_phius_cert.building_use_type.number
    )
    phx_phius_cert_settings.phius_building_status = phius_certification.PhiusCertificationBuildingStatus(
        hbph_phius_cert.building_status.number
    )
    phx_phius_cert_settings.phius_building_type = phius_certification.PhiusCertificationBuildingType(
        hbph_phius_cert.building_type.number
    )

    return None


def set_phx_phpp9_settings(
    _phx_settings: certification.PhxPhiCertificationSettings,
    _attributes: phi.PHPPSettings9,
) -> None:
    """Set the values of the PHX-PHI Settings object for PHPP-v9 Settings.

    Arguments:
    ----------
        * _phx_settings: certification.PhxPhiCertificationSettings
        * _hbph_settings:phi.PhiCertification)

    Returns:
    --------
        * None
    """
    _phx_settings.phi_building_category_type = phi_certification_phpp_9.PhiCertBuildingCategoryType(
        _attributes.building_category_type.number
    )
    _phx_settings.phi_building_use_type = phi_certification_phpp_9.PhiCertBuildingUseType(
        _attributes.building_use_type.number
    )
    _phx_settings.phi_building_ihg_type = phi_certification_phpp_9.PhiCertIHGType(_attributes.ihg_type.number)
    _phx_settings.phi_building_occupancy_type = phi_certification_phpp_9.PhiCertOccupancyType(
        _attributes.occupancy_type.number
    )

    _phx_settings.phi_certification_type = phi_certification_phpp_9.PhiCertType(_attributes.certification_type.number)
    _phx_settings.phi_certification_class = phi_certification_phpp_9.PhiCertClass(
        _attributes.certification_class.number
    )
    _phx_settings.phi_pe_type = phi_certification_phpp_9.PhiCertificationPEType(_attributes.primary_energy_type.number)
    _phx_settings.phi_enerphit_type = phi_certification_phpp_9.PhiCertEnerPHitType(_attributes.enerphit_type.number)
    _phx_settings.phi_retrofit_type = phi_certification_phpp_9.PhiCertRetrofitType(_attributes.retrofit_type.number)


def set_phx_phpp10_settings(
    _phx_settings: certification.PhxPhiCertificationSettings,
    _attributes: phi.PHPPSettings10,
) -> None:
    """Set the values of the PHX-PHI Settings object for PHPP-v10 Settings.

    Arguments:
    ----------
        * _phx_settings: certification.PhxPhiCertificationSettings
        * _hbph_settings:phi.PhiCertification)

    Returns:
    --------
        * None
    """
    _phx_settings.phi_building_use_type = phi_certification_phpp_10.PhiCertBuildingUseType(
        _attributes.building_use_type.number
    )
    _phx_settings.phi_building_ihg_type = phi_certification_phpp_10.PhiCertIHGType(_attributes.ihg_type.number)

    _phx_settings.phi_certification_type = phi_certification_phpp_10.PhiCertType(_attributes.certification_type.number)
    _phx_settings.phi_certification_class = phi_certification_phpp_10.PhiCertClass(
        _attributes.certification_class.number
    )
    _phx_settings.phi_pe_type = phi_certification_phpp_10.PhiCertificationPEType(_attributes.primary_energy_type.number)
    _phx_settings.phi_retrofit_type = phi_certification_phpp_10.PhiCertRetrofitType(_attributes.retrofit_type.number)


def add_phi_certification_from_hb_room(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Set all the PhxPhiCertificationCriteria on a PhxVariant based on a Honeybee-Room's Building Segment.

    Arguments:
    ----------
        * _variant (project.Variant): The PhxVariant to set the PhxPhiCertificationCriteria to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """
    # alias
    room_ph_prop: RoomPhProperties = getattr(_hb_room.properties, "ph")
    hbph_settings: phi.PhiCertification = room_ph_prop.ph_bldg_segment.phi_certification
    phx_phi_cert = _variant.phi_cert
    phx_settings = _variant.phi_cert.phi_certification_settings

    if isinstance(hbph_settings.attributes, phi.PHPPSettings10):
        phx_phi_cert.version = 10
        set_phx_phpp10_settings(phx_settings, hbph_settings.attributes)
    elif isinstance(hbph_settings.attributes, phi.PHPPSettings9):
        phx_phi_cert.version = 9
        set_phx_phpp9_settings(phx_settings, hbph_settings.attributes)
    else:
        msg = (
            "Error: Unknown PHPP Settings Version? Expected 9 | 10, " f"Got: '{hbph_settings.attributes.phpp_version}'"
        )
        raise Exception(msg)

    return None


def add_PhxPhBuildingData_from_hb_room(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Create and add a PhxPhBuildingData with data from a Honeybee-Room to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the PH-Building to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    # -- Type Aliases
    ph_bldg = _variant.phius_cert.ph_building_data  # alias
    hb_prop_energy: RoomEnergyProperties = getattr(_hb_room.properties, "energy")
    hb_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    hbph_bldg_seg: BldgSegment = hb_prop_ph.ph_bldg_segment

    # -- Set the occupancy
    if hb_prop_energy.people:
        hb_ppl_prop_ph: people.PeoplePhProperties = getattr(hb_prop_energy.people.properties, "ph")
        ph_bldg.num_of_units = hb_ppl_prop_ph.number_dwelling_units
    ph_bldg.num_of_floors = hbph_bldg_seg.num_floor_levels

    # -- Add Foundations
    for hbph_foundation in hb_prop_ph.ph_foundations:
        phx_foundation = create_foundations.create_phx_foundation_from_hbph(hbph_foundation)
        ph_bldg.add_foundation(phx_foundation)

    # -- Set the airtightness for Building
    ph_bldg.airtightness_q50 = hb_prop_energy.infiltration.flow_per_exterior_area * 3600

    # -- Set the air temp setpoints
    ph_bldg.setpoints.winter = hbph_bldg_seg.set_points.winter
    ph_bldg.setpoints.summer = hbph_bldg_seg.set_points.summer
    ph_bldg.mech_room_temp = hbph_bldg_seg.mech_room_temp
    ph_bldg.non_combustible_materials = hbph_bldg_seg.non_combustible_materials

    # -- Summer HRV Bypass mode
    bm = hbph_bldg_seg.summer_hrv_bypass_mode.number
    ph_bldg.summer_hrv_bypass_mode = hvac.PhxSummerBypassMode(bm)

    # -- Wind Exposure
    wt = hbph_bldg_seg.wind_exposure_type.number
    ph_bldg.building_exposure_type = certification.WindExposureType(wt)

    return None


def add_climate_from_hb_room(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Copy PHX-Climate info from a Honeybee-Room over to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the climate data to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    # -- aliases
    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    ud_site: site.Site = room_prop_ph.ph_bldg_segment.site
    ud_ground = ud_site.climate.ground
    phx_climate = _variant.site.climate

    # -- Location
    _variant.site.location.latitude = ud_site.location.latitude
    _variant.site.location.longitude = ud_site.location.longitude
    _variant.site.location.site_elevation = ud_site.location.site_elevation
    _variant.site.location.climate_zone = ud_site.location.climate_zone
    _variant.site.location.hours_from_UTC = ud_site.location.hours_from_UTC

    # -- Basics
    phx_climate.station_elevation = ud_site.climate.station_elevation
    phx_climate.daily_temp_swing = ud_site.climate.summer_daily_temperature_swing
    phx_climate.avg_wind_speed = ud_site.climate.average_wind_speed

    # -- PHPP Stuff
    _variant.site.phpp_codes.country_code = ud_site.phpp_library_codes.country_code
    _variant.site.phpp_codes.region_code = ud_site.phpp_library_codes.region_code
    _variant.site.phpp_codes.dataset_name = ud_site.phpp_library_codes.dataset_name

    # -- Ground
    _variant.site.ground.ground_thermal_conductivity = ud_ground.ground_thermal_conductivity
    _variant.site.ground.ground_heat_capacity = ud_ground.ground_heat_capacity
    _variant.site.ground.ground_density = ud_ground.ground_density
    _variant.site.ground.depth_groundwater = ud_ground.depth_groundwater
    _variant.site.ground.flow_rate_groundwater = ud_ground.flow_rate_groundwater

    # -- Monthly Values
    phx_climate.temperature_air = ud_site.climate.monthly_temps.air_temps.values
    phx_climate.temperature_dewpoint = ud_site.climate.monthly_temps.dewpoints.values
    phx_climate.temperature_sky = ud_site.climate.monthly_temps.sky_temps.values

    phx_climate.radiation_north = ud_site.climate.monthly_radiation.north.values
    phx_climate.radiation_east = ud_site.climate.monthly_radiation.east.values
    phx_climate.radiation_south = ud_site.climate.monthly_radiation.south.values
    phx_climate.radiation_west = ud_site.climate.monthly_radiation.west.values
    phx_climate.radiation_global = ud_site.climate.monthly_radiation.glob.values

    # -- Peak Load Values
    phx_climate.peak_heating_1.temperature_air = ud_site.climate.peak_loads.heat_load_1.temp
    phx_climate.peak_heating_1.radiation_north = ud_site.climate.peak_loads.heat_load_1.rad_north
    phx_climate.peak_heating_1.radiation_east = ud_site.climate.peak_loads.heat_load_1.rad_east
    phx_climate.peak_heating_1.radiation_south = ud_site.climate.peak_loads.heat_load_1.rad_south
    phx_climate.peak_heating_1.radiation_west = ud_site.climate.peak_loads.heat_load_1.rad_west
    phx_climate.peak_heating_1.radiation_global = ud_site.climate.peak_loads.heat_load_1.rad_global

    phx_climate.peak_heating_2.temperature_air = ud_site.climate.peak_loads.heat_load_2.temp
    phx_climate.peak_heating_2.radiation_north = ud_site.climate.peak_loads.heat_load_2.rad_north
    phx_climate.peak_heating_2.radiation_east = ud_site.climate.peak_loads.heat_load_2.rad_east
    phx_climate.peak_heating_2.radiation_south = ud_site.climate.peak_loads.heat_load_2.rad_south
    phx_climate.peak_heating_2.radiation_west = ud_site.climate.peak_loads.heat_load_2.rad_west
    phx_climate.peak_heating_2.radiation_global = ud_site.climate.peak_loads.heat_load_2.rad_global

    phx_climate.peak_cooling_1.temperature_air = ud_site.climate.peak_loads.cooling_load_1.temp
    phx_climate.peak_cooling_1.radiation_north = ud_site.climate.peak_loads.cooling_load_1.rad_north
    phx_climate.peak_cooling_1.radiation_east = ud_site.climate.peak_loads.cooling_load_1.rad_east
    phx_climate.peak_cooling_1.radiation_south = ud_site.climate.peak_loads.cooling_load_1.rad_south
    phx_climate.peak_cooling_1.radiation_west = ud_site.climate.peak_loads.cooling_load_1.rad_west
    phx_climate.peak_cooling_1.radiation_global = ud_site.climate.peak_loads.cooling_load_1.rad_global

    phx_climate.peak_cooling_2.temperature_air = ud_site.climate.peak_loads.cooling_load_2.temp
    phx_climate.peak_cooling_2.radiation_north = ud_site.climate.peak_loads.cooling_load_2.rad_north
    phx_climate.peak_cooling_2.radiation_east = ud_site.climate.peak_loads.cooling_load_2.rad_east
    phx_climate.peak_cooling_2.radiation_south = ud_site.climate.peak_loads.cooling_load_2.rad_south
    phx_climate.peak_cooling_2.radiation_west = ud_site.climate.peak_loads.cooling_load_2.rad_west
    phx_climate.peak_cooling_2.radiation_global = ud_site.climate.peak_loads.cooling_load_2.rad_global

    return None


def add_local_pe_conversion_factors(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Copy local Site->Source conversion factors from a Honeybee-Room over to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the factor data to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for factor in room_prop_ph.ph_bldg_segment.source_energy_factors:
        new_phx_factor = phx_site.PhxPEFactor()
        new_phx_factor.fuel_name = factor.fuel_name
        new_phx_factor.value = factor.value
        new_phx_factor.unit = factor.unit
        _variant.site.energy_factors.pe_factors[new_phx_factor.fuel_name] = new_phx_factor
    return


def add_local_co2_conversion_factors(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Copy local Site->CO2e conversion factors from a Honeybee-Room over to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the factor data to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for factor in room_prop_ph.ph_bldg_segment.co2e_factors:
        new_phx_factor = phx_site.PhxCO2Factor()
        new_phx_factor.fuel_name = factor.fuel_name
        new_phx_factor.value = factor.value
        new_phx_factor.unit = factor.unit
        _variant.site.energy_factors.co2_factors[new_phx_factor.fuel_name] = new_phx_factor
    return


# -- HVAC Systems -------------------------------------------------------------


def add_ventilation_systems_from_hb_rooms(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Add new HVAC (Ventilation, etc) Systems to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new hvac systems to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    ph_prop = get_ph_prop_from_room(_hb_room)
    for hbph_space in ph_prop.spaces:
        # -- Note: in the case of a merged room, the space's host may NOT be the same
        # -- as '_hb_room', so always refer back to the space to get the mechanical devices
        hbph_vent_sys = get_ventilation_system_from_space(hbph_space)
        if not hbph_vent_sys:
            continue

        # ---------------------------------------------------------------------
        # -- Get or Build the PHX Ventilation Device
        # -- If the ventilator already exists, just use that one.
        mech_collection, phx_ventilator = _variant.get_mech_device_by_key(hbph_vent_sys.key)
        if not phx_ventilator or not mech_collection:
            # -- otherwise, build a new PH-Ventilator from the HB-hvac, add it to the
            # -- base mech-system
            mech_collection = _variant.mech_collections[0]
            phx_ventilator = create_hvac.build_phx_ventilator(hbph_vent_sys)
            mech_collection.add_new_mech_device(hbph_vent_sys.key, phx_ventilator)

        # ---------------------------------------------------------------------
        # -- Re-set the HBPH Ventilator and sys id_num to keep everything aligned
        hbph_vent_sys.id_num = phx_ventilator.id_num
        if hbph_vent_sys.ventilation_unit:
            hbph_vent_sys.ventilation_unit.id_num = phx_ventilator.id_num

        # ---------------------------------------------------------------------
        # -- Add PHX Distribution Ducting from the HBPH Ducts
        for hbph_supply_duct in hbph_vent_sys.supply_ducting:
            mech_collection.add_vent_ducting(create_hvac.build_phx_duct(hbph_supply_duct, phx_ventilator.id_num))
        for hbph_exhaust_duct in hbph_vent_sys.exhaust_ducting:
            mech_collection.add_vent_ducting(create_hvac.build_phx_duct(hbph_exhaust_duct, phx_ventilator.id_num))

    return None


def add_exhaust_vent_devices_from_hb_rooms(
    _variant: project.PhxVariant,
    _hb_room: room.Room,
    _merge_devices: bool = True,
) -> None:
    """Add all the Exhaust Ventilation Equipment from the HB Room onto the new Variant/Zone.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new exhaust equipment to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.
        * _merge_devices (bool): Default=True. Merge together the Exhaust Ventilation
            Devices into a single device (per type)?

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for hbph_space in room_prop_ph.spaces:
        # -- Note: in the case of a merged room, the space's host may NOT be the same
        # -- as '_hb_room', so always refer back to the space to get the mechanical devices
        for hbph_device in get_exhaust_vent_devices_from_space(hbph_space):
            key = hbph_device.key

            # -- Get or Build the PHX Exhaust Ventilation Device
            # -- If the Device already exists, just use that one.
            for zone in _variant.zones:
                # -- If the device is already in the Zone's collection, dont add another one.
                if zone.exhaust_ventilator_collection.device_in_collection(key):
                    continue

                # -- Otherwise, build a new PHX-Exhaust Ventilator from the HBPH-Object
                phx_device = create_hvac.build_phx_exhaust_vent_device(hbph_device)

                #  -- And add the new ventilator to the Zone's set
                zone.exhaust_ventilator_collection.add_new_ventilator(key, phx_device)

    # -- Once all the Exhaust Ventilators have been added to the Zones,
    # -- merge them together
    for zone in _variant.zones:
        if _merge_devices:
            zone.exhaust_ventilator_collection.merge_all_devices()

    return None


def add_heating_systems_from_hb_rooms(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Add a new PHX-Heating SubSystem to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new hvac systems to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for space in room_prop_ph.spaces:
        # -- Note: in the case of a merged room, the space's host may NOT be the same
        # -- as '_hb_room', so always refer back to the space to get the mechanical devices
        heating_systems = get_heating_systems_from_space(space)

        # -- Get or Build the PHX Heating systems
        for hbph_sys in heating_systems:
            # -- If the device already exists, just use that one.
            mech_collection, phx_heating_device = _variant.get_mech_device_by_key(hbph_sys.key)

            # -- otherwise, build a new PHX-Heating-Sys from the HB-hvac
            if not phx_heating_device or not mech_collection:
                phx_heating_device = create_hvac.build_phx_heating_sys(hbph_sys)
                _variant.default_mech_collection.add_new_mech_device(hbph_sys.key, phx_heating_device)

            # -- Keep the ID-Numbers aligned
            setattr(hbph_sys, "id_num", phx_heating_device.id_num)

    return None


def add_heat_pump_systems_from_hb_rooms(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Add new PHX-Heat-Pump SubSystem to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new hvac systems to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for space in room_prop_ph.spaces:
        # -- Note: in the case of a merged room, the space's host may NOT be the same
        # -- as '_hb_room', so always refer back to the space to get the mechanical devices
        heat_pump_systems = get_heat_pump_systems_from_space(space)

        # -- Get or Build the PHX-Cooling systems
        for hbph_sys in heat_pump_systems:
            # -- If the system already exists, just use that one.
            mech_collection, phx_heat_pump_device = _variant.get_mech_device_by_key(hbph_sys.key)

            # -- otherwise, build a new PHX-Heat-Pump-System from the HB-hvac
            if not phx_heat_pump_device or not mech_collection:
                phx_heat_pump_device = create_hvac.build_phx_heat_pump_sys(hbph_sys)
                _variant.default_mech_collection.add_new_mech_device(hbph_sys.key, phx_heat_pump_device)

            # -- Keep the ID-Numbers aligned
            setattr(hbph_sys, "id_num", phx_heat_pump_device.id_num)

    return None


# --- Hot Water ---------------------------------------------------------------


def add_shw_storage_from_hb_rooms(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Add new Service Hot Water Equipment to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX Variant to add the PHX DHW System to.
        * _hb_room (room.Room): The Honeybee room to get the DHW System data from.

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for space in room_prop_ph.spaces:
        if not space.host:
            continue

        host_room_prop_ph_hvac = get_ph_hvac_from_space(space)
        if not host_room_prop_ph_hvac or not host_room_prop_ph_hvac.hot_water_system:
            continue

        # -- Build the HW-Tank
        for ph_hvac_hw_tank in host_room_prop_ph_hvac.hot_water_system.tanks:
            if not ph_hvac_hw_tank:
                continue

            # -- If the tank already exists, move on
            if _variant.device_in_collections(ph_hvac_hw_tank.key):
                continue

            # -- Build a new PHX-HW-Tank from the PH-HVAC Tank
            phx_dhw_tank = build_phx_hw_storage(ph_hvac_hw_tank)
            _variant.default_mech_collection.add_new_mech_device(ph_hvac_hw_tank.key, phx_dhw_tank)

    return None


def add_shw_heaters_from_hb_rooms(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """

    Arguments:
    ----------
        *_variant (project.PhxVariant): The PHX Variant to add the PHX DHW Heaters to.
        _hb_room (room.Room): The Honeybee room to get the DHW Heater data from.

    Returns:
    --------
        * None
    """

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for space in room_prop_ph.spaces:
        if not space.host:
            continue

        host_room_prop_ph_hvac = get_ph_hvac_from_space(space)
        if not host_room_prop_ph_hvac or not host_room_prop_ph_hvac.hot_water_system:
            continue

        for heater in host_room_prop_ph_hvac.hot_water_system.heaters:
            # -- If the heater already exists, move on
            if _variant.device_in_collections(heater.identifier):
                continue

            # -- Build a new PHX-HW-Heater from the Honeybee-PH HW-Heater
            phx_hw_heater = build_phx_hw_heater(heater)
            _variant.default_mech_collection.add_new_mech_device(heater.identifier, phx_hw_heater)


def shw_recirc_temp(_recirc_temps: Set[float]):
    """Get the DHW recirculation temperature."""
    if len(_recirc_temps) == 0:
        return 60.0
    elif len(_recirc_temps) == 1:
        return _recirc_temps.pop()
    else:
        print(f"Warning: Multiple recirculation temperatures found. {_recirc_temps}")
        return 60.0


def shw_recirc_hours(_recirc_temps: Set[int]) -> int:
    """Get the number of hours that the DHW recirculation is active."""
    if len(_recirc_temps) == 0:
        return 24
    elif len(_recirc_temps) == 1:
        return _recirc_temps.pop()
    else:
        print(f"Warning: Multiple recirculation run-times found. {_recirc_temps}")
        return 24


def add_shw_piping_from_hb_rooms(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    phx_mech_sys = _variant.default_mech_collection
    phx_recirc_temps: Set[float] = set()
    phx_recirc_hours: Set[int] = set()

    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for hbph_space in room_prop_ph.spaces:
        if not hbph_space.host:
            continue

        host_room_prop_ph_hvac = get_ph_hvac_from_space(hbph_space)
        if not host_room_prop_ph_hvac or not host_room_prop_ph_hvac.hot_water_system:
            continue

        # -- Add the DHW Distribution Piping
        for distribution_piping_element in host_room_prop_ph_hvac.hot_water_system.distribution_piping:
            phx_mech_sys.add_distribution_piping(build_phx_trunk_pipe(distribution_piping_element))

        # -- Set the tap points
        phx_mech_sys._distribution_num_hw_tap_points = host_room_prop_ph_hvac.hot_water_system.number_tap_points

        # -- Add the DHW Recirculation Piping
        for recirc_piping_element in host_room_prop_ph_hvac.hot_water_system.recirc_piping:
            phx_mech_sys.add_recirc_piping(build_phx_pipe_element(recirc_piping_element))

        # -- Get the DHW recirculation parameters
        phx_recirc_temps.add(host_room_prop_ph_hvac.hot_water_system.recirc_temp)
        phx_recirc_hours.add(host_room_prop_ph_hvac.hot_water_system.recirc_hours)

    # -- Set the Recirc parameters
    phx_params = phx_mech_sys._distribution_hw_recirculation_params
    phx_params.water_temp = shw_recirc_temp(phx_recirc_temps)
    phx_params.daily_recirc_hours = shw_recirc_hours(phx_recirc_hours)

    return None


# --- Equipment ---------------------------------------------------------------


def add_elec_equip_from_hb_room(_variant: project.PhxVariant, _hb_room: room.Room) -> None:
    """Creates new PHX-Elec-Equipment (Appliances) and adds them to each of the Variant.building.zones

    Arguments:
    ----------
        * _variant (project.Variant): The Variant to add the new elec-equipment to.
        * _hb_room (room.Room): The Honeybee Room to get the elec-equipment from.

    Returns:
    --------
        * None
    """

    room_prop_hb_energy: RoomEnergyProperties = getattr(_hb_room.properties, "energy")
    room_hb_energy_elec_equip: ElectricEquipment = room_prop_hb_energy.electric_equipment
    if not room_hb_energy_elec_equip:
        return

    ee_properties_ph: equipment.ElectricEquipmentPhProperties = getattr(room_hb_energy_elec_equip.properties, "ph")
    for equip_key, device in ee_properties_ph.equipment_collection.items():
        phx_elec_device = create_elec_equip.build_phx_elec_device(device)
        for zone in _variant.building.zones:
            zone.elec_equipment_collection.add_new_device(equip_key, phx_elec_device)

    return


def add_supportive_devices_from_hb_room(
    _variant: project.PhxVariant,
    _hb_room: room.Room,
    _merge_devices: bool = True,
) -> None:
    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for hbph_space in room_prop_ph.spaces:
        # -- Note: in the case of a merged room, the space's host may NOT be the same
        # -- as '_hb_room', so always refer back to the space to get the mechanical devices.
        for hbph_device in get_supportive_devices_from_space(hbph_space):
            # -- Get or Build the PHX Supportive Device
            # -- If the Device already exists, just use that one.
            # -- If the device is already in one of the Mech System's collection, move on.
            if _variant.supportive_device_in_collections(hbph_device.key):
                continue

            # -- Otherwise, build a new PHX-Exhaust Ventilator from the HBPH-Object
            phx_device = create_hvac.build_phx_supportive_device(hbph_device)
            _variant.default_mech_collection.supportive_devices.add_new_device(hbph_device.key, phx_device)

    # -- Once all the Supportive Devices have been added to the Zones, merge them together
    if _merge_devices:
        _variant.default_mech_collection.supportive_devices.merge_all_devices()

    return None


def add_renewable_devices_from_hb_room(
    _variant: project.PhxVariant,
    _hb_room: room.Room,
    _merge_devices: bool = True,
) -> None:
    room_prop_ph: RoomPhProperties = getattr(_hb_room.properties, "ph")
    for hbph_space in room_prop_ph.spaces:
        # -- Note: in the case of a merged room, the space's host may NOT be the same
        # -- as '_hb_room', so always refer back to the space to get the mechanical devices
        for hbph_device in get_renewable_devices_from_space(hbph_space):
            # -- Get or Build the PHX Renewable Device
            # -- If the Device already exists, just use that one.
            # -- If the device is already in the Mech System's collection, move on.
            if _variant.renewable_device_in_collections(hbph_device.key):
                continue

            # -- Otherwise, build a new PHX-Renewable Device from the HBPH-Object
            phx_device = create_hvac.build_phx_renewable_device(hbph_device)
            _variant.default_mech_collection.renewable_devices.add_new_device(hbph_device.key, phx_device)

    # -- Once all the Renewable Devices have been added to the Zones, merge them together
    if _merge_devices:
        _variant.default_mech_collection.renewable_devices.merge_all_devices()

    return None


def from_hb_room(
    _hb_room: room.Room,
    _assembly_dict: Dict[str, constructions.PhxConstructionOpaque],
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    _vent_sched_collection: UtilizationPatternCollection_Ventilation,
    _occ_sched_collection: UtilizationPatternCollection_Occupancy,
    _lighting_sched_collection: UtilizationPatternCollection_Lighting,
    _group_components: bool = False,
    _merge_spaces_by_erv: bool = False,
    _tolerance: float = 0.001,
) -> project.PhxVariant:
    """Create a new PHX-Variant based on a single PH/Honeybee Room.

    Arguments:
    ----------
        * _hb_room (honeybee.room.Room): The honeybee room to base the Variant on.
        * _assembly_dict (Dict[str, constructions.PhxConstructionOpaque]): The Assembly Type dict.
        * _window_type_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.
        * _group_components (bool): default=False. Set to true to have the converter
            group the components by assembly-type.
        * _merge_spaces_by_erv (bool): default=False. Set to true to merge spaces that
            have the same ERV system.
        * _tolerance (float): The tolerance to use when merging spaces.

    Returns:
    --------
        * A new Variant object.
    """

    new_variant = project.PhxVariant()

    # -- Keep all the ID numbers aligned
    room_ph_prop: RoomPhProperties = getattr(_hb_room.properties, "ph")
    new_variant.id_num = project.PhxVariant._count
    room_ph_prop.id_num = new_variant.id_num
    new_variant.name = _hb_room.display_name

    # -- Build the Variant Elements (Dev. note: order matters!!)
    add_ventilation_systems_from_hb_rooms(new_variant, _hb_room)
    add_heating_systems_from_hb_rooms(new_variant, _hb_room)
    add_heat_pump_systems_from_hb_rooms(new_variant, _hb_room)
    add_shw_heaters_from_hb_rooms(new_variant, _hb_room)
    add_shw_piping_from_hb_rooms(new_variant, _hb_room)
    add_shw_storage_from_hb_rooms(new_variant, _hb_room)
    add_building_from_hb_room(
        _variant=new_variant,
        _hb_room=_hb_room,
        _assembly_dict=_assembly_dict,
        _window_type_dict=_window_type_dict,
        _vent_sched_collection=_vent_sched_collection,
        _occ_sched_collection=_occ_sched_collection,
        _lighting_sched_collection=_lighting_sched_collection,
        _group_components=_group_components,
        _merge_spaces_by_erv=_merge_spaces_by_erv,
        _tolerance=_tolerance,
    )
    # -- Ventilation-Exhaust Equip must come AFTER zones are instantiated, since these
    # -- devices are down at the zone level instead of up at the Variant level.
    add_exhaust_vent_devices_from_hb_rooms(new_variant, _hb_room)
    add_supportive_devices_from_hb_room(new_variant, _hb_room)
    add_renewable_devices_from_hb_room(new_variant, _hb_room)
    add_phius_certification_from_hb_room(new_variant, _hb_room)
    add_phi_certification_from_hb_room(new_variant, _hb_room)
    add_PhxPhBuildingData_from_hb_room(new_variant, _hb_room)
    add_climate_from_hb_room(new_variant, _hb_room)
    add_local_pe_conversion_factors(new_variant, _hb_room)
    add_local_co2_conversion_factors(new_variant, _hb_room)
    add_elec_equip_from_hb_room(new_variant, _hb_room)

    return new_variant
