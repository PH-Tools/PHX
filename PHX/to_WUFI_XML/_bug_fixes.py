# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Apply bug-fixes to the WUFI-XML."""

from PHX.model.project import PhxProject


def split_cooling_into_multiple_systems(_phx_project: PhxProject):
    """Split the cooling system into multiple systems.

    WUFI-Passive v3 has a bug where any single cooling system may not be > 200 KW.
    This function will split the cooling system into multiple systems if the total
    cooling load is greater than 200 KW.
    """
    # -- Check is any cooling system capacity is greater than 200 KW

    for phx_variant in _phx_project.variants:
        variant_total_cooling_capacity = 0.0
        for phx_mech_collection in phx_variant.mech_collections:
            for hp_device in phx_mech_collection.heat_pump_devices:
                variant_total_cooling_capacity += hp_device.params_cooling.recirculation.capacity

        if variant_total_cooling_capacity > 200.0:
            print(
                f"Total cooling system capacity = {variant_total_cooling_capacity :.1f} KW. "
                "Splitting the cooling system into multiple systems."
            )

            new_cooling_systems_needed = int(variant_total_cooling_capacity / 200.0)
            target_number_of_cooling_systems = new_cooling_systems_needed + 1
            print(
                f"Splitting {variant_total_cooling_capacity :.1f} KW into {target_number_of_cooling_systems} equal-size systems."
            )

    return _phx_project
