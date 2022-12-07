# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions to build PHX-Variant from Honeybee Rooms"""

from typing import Dict, Set

from honeybee import room

from honeybee_ph import site, phi, phius
from honeybee_energy_ph.properties.load import equipment
from honeybee_energy_ph.hvac.ventilation import PhVentilationSystem
from honeybee_energy_ph.hvac.heating import PhHeatingSystem
from honeybee_energy_ph.hvac.cooling import PhCoolingSystem

from PHX.model import phx_site, project, ground, constructions, certification
from PHX.model.enums import (
    phi_certification_phpp_9,
    phi_certification_phpp_10,
    phius_certification,
)
from PHX.from_HBJSON import create_building, create_hvac, create_shw, create_elec_equip


def add_building_from_hb_room(
    _variant: project.PhxVariant,
    _hb_room: room.Room,
    _assembly_dict: Dict[str, constructions.PhxConstructionOpaque],
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    group_components: bool = False,
) -> None:
    """Create the  PHX-Building with all Components and Zones based on a Honeybee-Room.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the building to.
        * _hb_room (room.Room): The honeybee-Room to use as the source.
        * _assembly_dict (Dict[str, constructions.PhxConstructionOpaque]): The Assembly Type dict.
        * _window_type_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.
        * group_components (bool): default=False. Set to true to have the converter
            group the components by assembly-type.

    Returns:
    --------
        * None
    """
    _variant.building.add_components(
        create_building.create_components_from_hb_room(
            _hb_room, _assembly_dict, _window_type_dict
        )
    )
    _variant.building.add_zones(create_building.create_zones_from_hb_room(_hb_room))
    _variant.building.add_thermal_bridges(
        create_building.create_thermal_bridges_from_hb_room(_hb_room)
    )

    if group_components:
        _variant.building.merge_opaque_components_by_assembly()
        _variant.building.merge_aperture_components_by_assembly()


def add_phius_certification_from_hb_room(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Set all the PhxPhiusCertificationCriteria on a PhxVariant based on a Honeybee-Room's Building Segment.

    Arguments:
    ----------
        * _variant (project.Variant): The PhxVariant to set the PhxPhiusCertificationCriteria on.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    # alias cus' all this shit is deep in there...
    hbph_phius_cert: phius.PhiusCertification = _hb_room.properties.ph.ph_bldg_segment.phius_certification  # type: ignore # alias
    phx_phius_cert_criteria = (
        _variant.phius_certification.phius_certification_criteria
    )  # alias
    phx_phius_cert_settings = (
        _variant.phius_certification.phius_certification_settings
    )  # alias

    # some random bullshit
    phx_phius_cert_criteria.ph_certificate_criteria = (
        hbph_phius_cert.certification_criteria
    )
    phx_phius_cert_criteria.ph_selection_target_data = (
        hbph_phius_cert.localization_selection_type
    )

    # certification thresholds (for Phius, they change)
    phx_phius_cert_criteria.phius_annual_heating_demand = (
        hbph_phius_cert.PHIUS2021_heating_demand
    )
    phx_phius_cert_criteria.phius_annual_cooling_demand = (
        hbph_phius_cert.PHIUS2021_cooling_demand
    )
    phx_phius_cert_criteria.phius_peak_heating_load = (
        hbph_phius_cert.PHIUS2021_heating_load
    )
    phx_phius_cert_criteria.phius_peak_cooling_load = (
        hbph_phius_cert.PHIUS2021_cooling_load
    )

    # certification settings / types
    phx_phius_cert_settings.phius_building_category_type = (
        phius_certification.PhiusCertificationBuildingCategoryType(
            hbph_phius_cert.building_category_type.number
        )
    )
    phx_phius_cert_settings.phius_building_use_type = (
        phius_certification.PhiusCertificationBuildingUseType(
            hbph_phius_cert.building_use_type.number
        )
    )
    phx_phius_cert_settings.phius_building_status = (
        phius_certification.PhiusCertificationBuildingStatus(
            hbph_phius_cert.building_status.number
        )
    )
    phx_phius_cert_settings.phius_building_type = (
        phius_certification.PhiusCertificationBuildingType(
            hbph_phius_cert.building_type.number
        )
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
    _phx_settings.phi_building_category_type = (
        phi_certification_phpp_9.PhiCertBuildingCategoryType(
            _attributes.building_category_type.number
        )
    )
    _phx_settings.phi_building_use_type = phi_certification_phpp_9.PhiCertBuildingUseType(
        _attributes.building_use_type.number
    )
    _phx_settings.phi_building_ihg_type = phi_certification_phpp_9.PhiCertIHGType(
        _attributes.ihg_type.number
    )
    _phx_settings.phi_building_occupancy_type = (
        phi_certification_phpp_9.PhiCertOccupancyType(_attributes.occupancy_type.number)
    )

    _phx_settings.phi_certification_type = phi_certification_phpp_9.PhiCertType(
        _attributes.certification_type.number
    )
    _phx_settings.phi_certification_class = phi_certification_phpp_9.PhiCertClass(
        _attributes.certification_class.number
    )
    _phx_settings.phi_pe_type = phi_certification_phpp_9.PhiCertificationPEType(
        _attributes.primary_energy_type.number
    )
    _phx_settings.phi_enerphit_type = phi_certification_phpp_9.PhiCertEnerPHitType(
        _attributes.enerphit_type.number
    )
    _phx_settings.phi_retrofit_type = phi_certification_phpp_9.PhiCertRetrofitType(
        _attributes.retrofit_type.number
    )


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
    _phx_settings.phi_building_use_type = (
        phi_certification_phpp_10.PhiCertBuildingUseType(
            _attributes.building_use_type.number
        )
    )
    _phx_settings.phi_building_ihg_type = phi_certification_phpp_10.PhiCertIHGType(
        _attributes.ihg_type.number
    )

    _phx_settings.phi_certification_type = phi_certification_phpp_10.PhiCertType(
        _attributes.certification_type.number
    )
    _phx_settings.phi_certification_class = phi_certification_phpp_10.PhiCertClass(
        _attributes.certification_class.number
    )
    _phx_settings.phi_pe_type = phi_certification_phpp_10.PhiCertificationPEType(
        _attributes.primary_energy_type.number
    )
    _phx_settings.phi_retrofit_type = phi_certification_phpp_10.PhiCertRetrofitType(
        _attributes.retrofit_type.number
    )


def add_phi_certification_from_hb_room(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Set all the PhxPhiCertificationCriteria on a PhxVariant based on a Honeybee-Room's Building Segment.

    Arguments:
    ----------
        * _variant (project.Variant): The PhxVariant to set the PhxPhiCertificationCriteria to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """
    # alias cus' all this shit is deep in there...
    hbph_settings: phi.PhiCertification = _hb_room.properties.ph.ph_bldg_segment.phi_certification  # type: ignore
    phx_settings = _variant.phi_certification.phi_certification_settings  # type: ignore

    if hbph_settings.attributes.phpp_version == 10:
        set_phx_phpp10_settings(phx_settings, hbph_settings.attributes)
    elif hbph_settings.attributes.phpp_version == 9:
        set_phx_phpp9_settings(phx_settings, hbph_settings.attributes)
    else:
        msg = f"Error: Unknown PHPP Settings Version? Got: '{hbph_settings.attributes.phpp_version}'"
        raise Exception(msg)

    return None


def add_PhxPhBuildingData_from_hb_room(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Create and add a PhxPhBuildingData with data from a Honeybee-Room to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the PH-Building to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """
    ph_bldg = _variant.phius_certification.ph_building_data  # alias

    ph_bldg.num_of_units = _hb_room.properties.ph.ph_bldg_segment.num_dwelling_units  # type: ignore
    ph_bldg.num_of_floors = _hb_room.properties.ph.ph_bldg_segment.num_floor_levels  # type: ignore

    # TODO: Foundations. For now: set to None
    ph_bldg.add_foundation(ground.PhxFoundation())

    # Set the airtightness for Building
    ph_bldg.airtightness_q50 = _hb_room.properties.energy.infiltration.flow_per_exterior_area * 3600  # type: ignore

    # Air temp Setpoints
    ph_bldg.setpoints.winter = _hb_room.properties.ph.ph_bldg_segment.set_points.winter  # type: ignore
    ph_bldg.setpoints.summer = _hb_room.properties.ph.ph_bldg_segment.set_points.summer  # type: ignore

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

    ud_site: site.Site = _hb_room.properties.ph.ph_bldg_segment.site  # type: ignore

    # -- Location
    _variant.site.location.latitude = ud_site.location.latitude
    _variant.site.location.longitude = ud_site.location.longitude
    _variant.site.location.site_elevation = ud_site.location.site_elevation
    _variant.site.location.climate_zone = ud_site.location.climate_zone
    _variant.site.location.hours_from_UTC = ud_site.location.hours_from_UTC

    # -- Basics
    _variant.site.climate.daily_temp_swing = (
        ud_site.climate.summer_daily_temperature_swing
    )
    _variant.site.climate.avg_wind_speed = ud_site.climate.average_wind_speed

    # -- PHPP Stuff
    _variant.site.phpp_codes.country_code = ud_site.phpp_library_codes.country_code
    _variant.site.phpp_codes.region_code = ud_site.phpp_library_codes.region_code
    _variant.site.phpp_codes.dataset_name = ud_site.phpp_library_codes.dataset_name

    # -- Ground
    _variant.site.ground.ground_thermal_conductivity = (
        ud_site.climate.ground.ground_thermal_conductivity
    )
    _variant.site.ground.ground_heat_capacity = (
        ud_site.climate.ground.ground_heat_capacity
    )
    _variant.site.ground.ground_density = ud_site.climate.ground.ground_density
    _variant.site.ground.depth_groundwater = ud_site.climate.ground.depth_groundwater
    _variant.site.ground.flow_rate_groundwater = (
        ud_site.climate.ground.flow_rate_groundwater
    )

    # -- Monthly Values
    _variant.site.climate.temperature_air = ud_site.climate.monthly_temps.air_temps.values
    _variant.site.climate.temperature_dewpoint = (
        ud_site.climate.monthly_temps.dewpoints.values
    )
    _variant.site.climate.temperature_sky = ud_site.climate.monthly_temps.sky_temps.values

    _variant.site.climate.radiation_north = ud_site.climate.monthly_radiation.north.values
    _variant.site.climate.radiation_east = ud_site.climate.monthly_radiation.east.values
    _variant.site.climate.radiation_south = ud_site.climate.monthly_radiation.south.values
    _variant.site.climate.radiation_west = ud_site.climate.monthly_radiation.west.values
    _variant.site.climate.radiation_global = ud_site.climate.monthly_radiation.glob.values

    # -- Peak Load Values
    _variant.site.climate.peak_heating_1.temperature_air = (
        ud_site.climate.peak_loads.heat_load_1.temp
    )
    _variant.site.climate.peak_heating_1.radiation_north = (
        ud_site.climate.peak_loads.heat_load_1.rad_north
    )
    _variant.site.climate.peak_heating_1.radiation_east = (
        ud_site.climate.peak_loads.heat_load_1.rad_east
    )
    _variant.site.climate.peak_heating_1.radiation_south = (
        ud_site.climate.peak_loads.heat_load_1.rad_south
    )
    _variant.site.climate.peak_heating_1.radiation_west = (
        ud_site.climate.peak_loads.heat_load_1.rad_west
    )
    _variant.site.climate.peak_heating_1.radiation_global = (
        ud_site.climate.peak_loads.heat_load_1.rad_global
    )

    _variant.site.climate.peak_heating_2.temperature_air = (
        ud_site.climate.peak_loads.heat_load_2.temp
    )
    _variant.site.climate.peak_heating_2.radiation_north = (
        ud_site.climate.peak_loads.heat_load_2.rad_north
    )
    _variant.site.climate.peak_heating_2.radiation_east = (
        ud_site.climate.peak_loads.heat_load_2.rad_east
    )
    _variant.site.climate.peak_heating_2.radiation_south = (
        ud_site.climate.peak_loads.heat_load_2.rad_south
    )
    _variant.site.climate.peak_heating_2.radiation_west = (
        ud_site.climate.peak_loads.heat_load_2.rad_west
    )
    _variant.site.climate.peak_heating_2.radiation_global = (
        ud_site.climate.peak_loads.heat_load_2.rad_global
    )

    _variant.site.climate.peak_cooling_1.temperature_air = (
        ud_site.climate.peak_loads.cooling_load_1.temp
    )
    _variant.site.climate.peak_cooling_1.radiation_north = (
        ud_site.climate.peak_loads.cooling_load_1.rad_north
    )
    _variant.site.climate.peak_cooling_1.radiation_east = (
        ud_site.climate.peak_loads.cooling_load_1.rad_east
    )
    _variant.site.climate.peak_cooling_1.radiation_south = (
        ud_site.climate.peak_loads.cooling_load_1.rad_south
    )
    _variant.site.climate.peak_cooling_1.radiation_west = (
        ud_site.climate.peak_loads.cooling_load_1.rad_west
    )
    _variant.site.climate.peak_cooling_1.radiation_global = (
        ud_site.climate.peak_loads.cooling_load_1.rad_global
    )

    _variant.site.climate.peak_cooling_2.temperature_air = (
        ud_site.climate.peak_loads.cooling_load_2.temp
    )
    _variant.site.climate.peak_cooling_2.radiation_north = (
        ud_site.climate.peak_loads.cooling_load_2.rad_north
    )
    _variant.site.climate.peak_cooling_2.radiation_east = (
        ud_site.climate.peak_loads.cooling_load_2.rad_east
    )
    _variant.site.climate.peak_cooling_2.radiation_south = (
        ud_site.climate.peak_loads.cooling_load_2.rad_south
    )
    _variant.site.climate.peak_cooling_2.radiation_west = (
        ud_site.climate.peak_loads.cooling_load_2.rad_west
    )
    _variant.site.climate.peak_cooling_2.radiation_global = (
        ud_site.climate.peak_loads.cooling_load_2.rad_global
    )

    return None


def add_local_pe_conversion_factors(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Copy local Site->Source conversion factors from a Honeybee-Room over to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the factor data to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """
    for factor in _hb_room.properties.ph.ph_bldg_segment.source_energy_factors:  # type: ignore
        new_phx_factor = phx_site.PhxPEFactor()
        new_phx_factor.fuel_name = factor.fuel_name
        new_phx_factor.value = factor.value
        new_phx_factor.unit = factor.unit
        _variant.site.energy_factors.pe_factors[new_phx_factor.fuel_name] = new_phx_factor
    return


def add_local_co2_conversion_factors(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Copy local Site->CO2e conversion factors from a Honeybee-Room over to a PHX-Variant.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the factor data to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    for factor in _hb_room.properties.ph.ph_bldg_segment.co2e_factors:  # type: ignore
        new_phx_factor = phx_site.PhxCO2Factor()
        new_phx_factor.fuel_name = factor.fuel_name
        new_phx_factor.value = factor.value
        new_phx_factor.unit = factor.unit
        _variant.site.energy_factors.co2_factors[
            new_phx_factor.fuel_name
        ] = new_phx_factor
    return


def add_ventilation_systems_from_hb_rooms(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Add new HVAC (Ventilation, etc) Systems to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new hvac systems to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    for hbph_space in _hb_room.properties.ph.spaces:  # type: ignore
        # -- Get the Honeybee-PH Ventilation system from the space's host room
        # -- Note: in the case of a merged room, the space host may not be the same
        # -- as _hb_room, so always refer back to the space.host to be sure.
        hbph_vent_sys: PhVentilationSystem = (
            hbph_space.host.properties.energy.hvac.properties.ph.ventilation_system
        )

        if not hbph_vent_sys:
            continue

        # -- Get or Build the PHX Ventilation Device
        # -- If the ventilator already exists, just use that one.
        phx_ventilator = _variant.mech_systems.get_mech_device_by_key(hbph_vent_sys.key)
        if not phx_ventilator:
            # -- otherwise, build a new PH-Ventilator from the HB-hvac
            phx_ventilator = create_hvac.build_phx_ventilation_sys(hbph_vent_sys)
            _variant.mech_systems.add_new_mech_device(hbph_vent_sys.key, phx_ventilator)

        # -- Re-set the HBPH Ventilator and sys id_num to keep everything aligned
        hbph_vent_sys.id_num = phx_ventilator.id_num

        if hbph_vent_sys.ventilation_unit:
            hbph_vent_sys.ventilation_unit.id_num = phx_ventilator.id_num

    return None


def add_heating_systems_from_hb_rooms(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Add a new PHX-Heating SubSystem to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new hvac systems to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    for space in _hb_room.properties.ph.spaces:  # type: ignore
        # -- Get the Honeybee-PH Heating Systems from the space's host room
        # -- Note: in the case of a merged room, the space host may not be the same
        # -- as _hb_room, so always refer back to the space.host to be sure.
        heating_systems: Set[
            PhHeatingSystem
        ] = space.host.properties.energy.hvac.properties.ph.heating_systems

        # -- Get or Build the PHX Heating systems
        # -- If the system already exists, just use that one.
        for hbph_sys in heating_systems:
            phx_heating_device = _variant.mech_systems.get_mech_device_by_key(
                hbph_sys.key
            )
            if not phx_heating_device:
                # -- otherwise, build a new PHX-Heating-Sys from the HB-hvac
                phx_heating_device = create_hvac.build_phx_heating_sys(hbph_sys)
                _variant.mech_systems.add_new_mech_device(
                    hbph_sys.key, phx_heating_device
                )

            hbph_sys.id_num = phx_heating_device.id_num

    return None


def add_cooling_systems_from_hb_rooms(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Add new PHX-Cooling SubSystem to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX-Variant to add the new hvac systems to.
        * _hb_room (room.Room): The Honeybee-Room to use as the source.

    Returns:
    --------
        * None
    """

    for space in _hb_room.properties.ph.spaces:
        # -- Get the Honeybee-PH Cooling-Systems from the space's host room
        # -- Note: in the case of a merged room, the space host may not be the same
        # -- as _hb_room, so always refer back to the space.host to be sure.
        cooling_systems: Set[
            PhCoolingSystem
        ] = space.host.properties.energy.hvac.properties.ph.cooling_systems

        # -- Get or Build the PHX-Cooling systems
        # -- If the system already exists, just use that one.
        for hbph_sys in cooling_systems:
            phx_cooling_device = _variant.mech_systems.get_mech_device_by_key(
                hbph_sys.key
            )
            if not phx_cooling_device:
                # -- otherwise, build a new PHX-Cooling-Sys from the HB-hvac
                phx_cooling_device = create_hvac.build_phx_cooling_sys(hbph_sys)
                _variant.mech_systems.add_new_mech_device(
                    hbph_sys.key, phx_cooling_device
                )

            hbph_sys.id_num = phx_cooling_device.id_num

    return None


def add_dhw_storage_from_hb_rooms(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Add new Service Hot Water Equipment to the Variant based on the HB-Rooms.

    Arguments:
    ----------
        * _variant (project.Variant): The PHX Variant to add the PHX DHW System to.
        * _hb_room (room.Room): The Honeybee room to get the DHW System data from.

    Returns:
    --------
        * None
    """

    for space in _hb_room.properties.ph.spaces:  # type: ignore
        # -- Guard Clause
        if (
            not space.host.properties.energy.shw
            or not space.host.properties.energy.service_hot_water
        ):
            continue

        # -- Build the HW-Tank
        for hw_tank in space.host.properties.energy.shw.properties.ph.tanks:
            if not hw_tank:
                continue

            if _variant.mech_systems.device_in_collection(hw_tank.key):
                continue

            # -- Build a new PHS-HW-Tank from the HB-hvac
            phx_dhw_tank = create_shw.build_phx_hw_storage(hw_tank)
            _variant.mech_systems.add_new_mech_device(hw_tank.key, phx_dhw_tank)

    return None


def add_dhw_heaters_from_hb_rooms(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """

    Arguments:
    ----------
        *_variant (project.PhxVariant): The PHX Variant to add the PHX DHW Heaters to.
        _hb_room (room.Room): The Honeybee room to get the DHW Heater data from.

    Returns:
    --------
        * None
    """

    for space in _hb_room.properties.ph.spaces:  # type: ignore

        if not space.host.properties.energy.shw:
            continue

        for heater in space.host.properties.energy.shw.properties.ph.heaters:
            if _variant.mech_systems.device_in_collection(heater.identifier):
                continue

            # -- Build a new PHX-HW-Heater from the Honeybee-PH HW-Heater
            phx_hw_heater = create_shw.build_phx_hw_heater(heater)
            _variant.mech_systems.add_new_mech_device(heater.identifier, phx_hw_heater)


def add_dhw_piping_from_hb_rooms(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    for space in _hb_room.properties.ph.spaces:  # type: ignore

        if not space.host.properties.energy.shw:
            continue

        for (
            branch_piping_element
        ) in space.host.properties.energy.shw.properties.ph.branch_piping:
            _variant.mech_systems.add_branch_piping(
                create_shw.build_phx_piping(branch_piping_element)
            )

        _variant.mech_systems._distribution_num_hw_tap_points = (
            space.host.properties.energy.shw.properties.ph.number_tap_points
        )

        for (
            recirc_piping_element
        ) in space.host.properties.energy.shw.properties.ph.recirc_piping:
            _variant.mech_systems.add_recirc_piping(
                create_shw.build_phx_piping(recirc_piping_element)
            )

    return None


def add_elec_equip_from_hb_room(
    _variant: project.PhxVariant, _hb_room: room.Room
) -> None:
    """Creates new PHX-Elec-Equipment (Appliances) and adds them to each of the Variant.building.zones

    Arguments:
    ----------
        * _variant (project.Variant): The Variant to add the new elec-equipment to.
        # _hb_room (room.Room): The Honeybee Room to get the elec-equipment from.

    Returns:
    --------
        * None
    """

    ee_properties_ph: equipment.ElectricEquipmentPhProperties = _hb_room.properties.energy.electric_equipment.properties.ph  # type: ignore
    for equip_key, device in ee_properties_ph.equipment_collection.items():
        phx_elec_device = create_elec_equip.build_phx_elec_device(device)
        for zone in _variant.building.zones:
            zone.elec_equipment_collection.add_new_device(equip_key, phx_elec_device)

    return


def from_hb_room(
    _hb_room: room.Room,
    _assembly_dict: Dict[str, constructions.PhxConstructionOpaque],
    _window_type_dict: Dict[str, constructions.PhxConstructionWindow],
    group_components: bool = False,
) -> project.PhxVariant:
    """Create a new PHX-Variant based on a single PH/Honeybee Room.

    Arguments:
    ----------
        * _hb_room (honeybee.room.Room): The honeybee room to base the Variant on.
        * _assembly_dict (Dict[str, constructions.PhxConstructionOpaque]): The Assembly Type dict.
        * _window_type_dict (Dict[str, constructions.PhxConstructionWindow]): The Window Type dict.
        * group_components (bool): default=False. Set to true to have the converter
            group the components by assembly-type.

    Returns:
    --------
        * A new Variant object.
    """

    new_variant = project.PhxVariant()

    # -- Keep all the ID numbers aligned
    new_variant.id_num = project.PhxVariant._count
    _hb_room.properties.ph.id_num = new_variant.id_num  # type: ignore
    new_variant.name = _hb_room.display_name

    # -- Build the Variant Elements (Dev. note: order matters!)
    add_ventilation_systems_from_hb_rooms(new_variant, _hb_room)
    add_heating_systems_from_hb_rooms(new_variant, _hb_room)
    add_cooling_systems_from_hb_rooms(new_variant, _hb_room)
    add_dhw_heaters_from_hb_rooms(new_variant, _hb_room)
    add_dhw_piping_from_hb_rooms(new_variant, _hb_room)
    add_dhw_storage_from_hb_rooms(new_variant, _hb_room)
    add_building_from_hb_room(
        new_variant, _hb_room, _assembly_dict, _window_type_dict, group_components
    )
    add_phius_certification_from_hb_room(new_variant, _hb_room)
    add_phi_certification_from_hb_room(new_variant, _hb_room)
    add_PhxPhBuildingData_from_hb_room(new_variant, _hb_room)
    add_climate_from_hb_room(new_variant, _hb_room)
    add_local_pe_conversion_factors(new_variant, _hb_room)
    add_local_co2_conversion_factors(new_variant, _hb_room)
    add_elec_equip_from_hb_room(new_variant, _hb_room)

    return new_variant
