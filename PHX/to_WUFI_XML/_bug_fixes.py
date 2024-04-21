# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Apply bug-fixes to the WUFI-XML."""

from PHX.model.hvac.collection import PhxMechanicalSystemCollection
from PHX.model.hvac.heat_pumps import PhxHeatPumpAnnual
from PHX.model.project import PhxProject


def split_cooling_into_multiple_systems(_phx_project: PhxProject):
    """Split the PhxProject's cooling capacity across multiple systems.

    WUFI-Passive v3.x has a bug where any single Ideal-Air-System's cooling capacity may not be > 200 KW.
    This function will split the cooling systems into multiple systems if the total
    cooling load is greater than 200 KW.
    """
    # -- Check is any cooling system capacity is greater than 200 KW

    for phx_variant in _phx_project.variants:
        # ---------------------------------------------------------------------
        # -- Log all the existing cooling systems and their capacities
        total_number_of_cooling_devices = 0
        variant_total_cooling_capacity = 0.0
        variant_total_airflow_rate = 0.0
        total_recirc_cop = 0.0
        total_dehumid_cop = 0.0
        for phx_mech_collection in phx_variant.mech_collections:
            for hp_device in phx_mech_collection.heat_pump_devices:
                # -- If the device doesn't have a cooling system, skip it
                if hp_device.usage_profile.cooling is False:
                    continue

                # -- If the device has a cooling system, add it to the totals
                total_number_of_cooling_devices += 1
                variant_total_cooling_capacity += hp_device.params_cooling.recirculation.capacity
                variant_total_airflow_rate += hp_device.params_cooling.recirculation.flow_rate_m3_hr
                total_recirc_cop += hp_device.params_cooling.recirculation.annual_COP
                total_dehumid_cop += hp_device.params_cooling.dehumidification.annual_COP

        # ---------------------------------------------------------------------
        # -- If the total cooling capacity is less than 200 KW, ignore this variant
        if variant_total_cooling_capacity < 200.0:
            continue

        # ---------------------------------------------------------------------
        # -- Figure out the number of cooling systems needed and the attributes
        print(
            f"Total cooling system capacity = {variant_total_cooling_capacity :.1f} KW. "
            "Splitting the cooling system into multiple systems."
        )

        number_of_new_cooling_systems = int(variant_total_cooling_capacity / 200.0)
        target_number_of_cooling_systems = number_of_new_cooling_systems + 1
        target_number_of_cooling_devices = total_number_of_cooling_devices + number_of_new_cooling_systems
        target_cooling_system_size = variant_total_cooling_capacity / target_number_of_cooling_systems
        target_cooling_system_airflow_rate = variant_total_airflow_rate / target_number_of_cooling_systems
        target_cooling_system_coverage_percentage = 1.0 / target_number_of_cooling_devices
        target_recirc_cop = total_recirc_cop / total_number_of_cooling_devices
        target_dehumid_cop = total_dehumid_cop / total_number_of_cooling_devices
        print(
            f"Splitting {variant_total_cooling_capacity :.1f} KW into "
            f" {target_number_of_cooling_systems} equal-size systems of {target_cooling_system_size} KW."
        )

        # ---------------------------------------------------------------------
        # -- Reset the existing cooling systems
        for phx_mech_collection in phx_variant.mech_collections:
            for hp_device in phx_mech_collection.heat_pump_devices:
                # -- If the device doesn't have a cooling system, skip it
                if hp_device.usage_profile.cooling is False:
                    continue

                # -- If the device has a cooling system, reset it
                hp_device.params_cooling.recirculation.capacity = target_cooling_system_size
                hp_device.params_cooling.recirculation.flow_rate_m3_hr = target_cooling_system_airflow_rate
                hp_device.usage_profile.cooling_percent = target_cooling_system_coverage_percentage
                hp_device.params_cooling.recirculation.annual_COP = target_recirc_cop
                hp_device.params_cooling.dehumidification.annual_COP = target_dehumid_cop

        # ---------------------------------------------------------------------
        # -- Add each of the new cooling systems needed
        for i in range(number_of_new_cooling_systems):
            new_collection = PhxMechanicalSystemCollection()

            new_collection.display_name = "Cooling System [{}]".format(i + 2)

            # -- Build the new Heat Pump for cooling only
            new_cooling_heat_pump = PhxHeatPumpAnnual()
            new_cooling_heat_pump.display_name = "Cooling System [{}]".format(i + 2)
            new_cooling_heat_pump.usage_profile.cooling = True
            new_cooling_heat_pump.params_cooling.recirculation.used = True
            new_cooling_heat_pump.params_cooling.dehumidification.used = True
            new_cooling_heat_pump.params_cooling.recirculation.capacity = target_cooling_system_size
            new_cooling_heat_pump.params_cooling.recirculation.flow_rate_m3_hr = target_cooling_system_airflow_rate
            new_cooling_heat_pump.params_cooling.recirculation.annual_COP = target_recirc_cop
            new_cooling_heat_pump.params_cooling.dehumidification.annual_COP = target_dehumid_cop
            new_cooling_heat_pump.usage_profile.cooling_percent = target_cooling_system_coverage_percentage

            # -- Add the new heat-pump to the mech-collection and to the variant
            new_collection.add_new_mech_device(new_cooling_heat_pump.identifier, new_cooling_heat_pump)
            phx_variant.add_mechanical_collection(new_collection)

    return _phx_project
