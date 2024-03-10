from PHX.model.project import PhxProject, PhxVariant
from PHX.model.building import PhxZone
from PHX.model.hvac.heat_pumps import PhxHeatPumpAnnual
from PHX.to_WUFI_XML._bug_fixes import split_cooling_into_multiple_systems

def test_cooling_capacity_fix_below_200KW() -> None:
    # -- Setup a dummy Project
    phx_project = PhxProject()
    phx_variant = PhxVariant()
    phx_variant.building.add_zone(PhxZone())
    phx_project.add_new_variant(phx_variant)


    # -- Add Mech System with cooling capacity < 200 KW
    new_heat_pump = PhxHeatPumpAnnual()
    new_heat_pump.params_cooling.recirculation.capacity = 100.0
    phx_variant.default_mech_collection.add_new_mech_device(new_heat_pump.identifier, new_heat_pump)

    phx_project = split_cooling_into_multiple_systems(phx_project)

    # -- Check if the cooling capacity is not split
    assert len(phx_project.variants[0].mech_collections[0].heat_pump_devices) == 1

def test_cooling_capacity_fix_300KW_makes_2_systems() -> None:
    # -- Setup a dummy Project
    phx_project = PhxProject()
    phx_variant = PhxVariant()
    phx_variant.building.add_zone(PhxZone())
    phx_project.add_new_variant(phx_variant)

    # -- Add Mech System with cooling capacity > 200 KW
    new_heat_pump = PhxHeatPumpAnnual()
    new_heat_pump.usage_profile.cooling = True
    new_heat_pump.params_cooling.recirculation.used = True
    new_heat_pump.params_cooling.recirculation.capacity = 300.0
    phx_variant.default_mech_collection.add_new_mech_device(new_heat_pump.identifier, new_heat_pump)

    phx_project = split_cooling_into_multiple_systems(phx_project)

    # -- Check if the cooling capacity is split
    assert len(phx_project.variants[0].mech_collections) == 2
    for collection in phx_project.variants[0].mech_collections:
        assert len(collection.heat_pump_devices) == 1
        assert collection.heat_pump_devices[0].params_cooling.recirculation.capacity == 150.0

def test_cooling_capacity_fix_540KW_makes_3_systems() -> None:
    # -- Setup a dummy Project
    phx_project = PhxProject()
    phx_variant = PhxVariant()
    phx_variant.building.add_zone(PhxZone())
    phx_project.add_new_variant(phx_variant)

    # -- Add Mech System with cooling capacity > 200 KW
    new_heat_pump = PhxHeatPumpAnnual()
    new_heat_pump.usage_profile.cooling = True
    new_heat_pump.params_cooling.recirculation.used = True
    new_heat_pump.params_cooling.recirculation.capacity = 540.0
    phx_variant.default_mech_collection.add_new_mech_device(new_heat_pump.identifier, new_heat_pump)

    phx_project = split_cooling_into_multiple_systems(phx_project)

    # -- Check if the cooling capacity is split
    assert len(phx_project.variants[0].mech_collections) == 3
    for collection in phx_project.variants[0].mech_collections:
        assert len(collection.heat_pump_devices) == 1
        assert collection.heat_pump_devices[0].params_cooling.recirculation.capacity == 180.0

def test_cooling_capacity_fix_300KW_with_2_mech_systems() -> None:
    # -- Setup a dummy Project
    phx_project = PhxProject()
    phx_variant = PhxVariant()
    phx_variant.building.add_zone(PhxZone())
    phx_project.add_new_variant(phx_variant)

    # -- Add Mech System with cooling capacity > 200 KW
    new_heat_pump = PhxHeatPumpAnnual()
    new_heat_pump.usage_profile.cooling = True
    new_heat_pump.params_cooling.recirculation.used = True
    new_heat_pump.params_cooling.recirculation.capacity = 150.0
    phx_variant.default_mech_collection.add_new_mech_device(new_heat_pump.identifier, new_heat_pump)

    # -- Add another Mech System with cooling capacity > 200 KW
    new_heat_pump = PhxHeatPumpAnnual()
    new_heat_pump.usage_profile.cooling = True
    new_heat_pump.params_cooling.recirculation.used = True
    new_heat_pump.params_cooling.recirculation.capacity = 150.0
    phx_variant.default_mech_collection.add_new_mech_device(new_heat_pump.identifier, new_heat_pump)

    phx_project = split_cooling_into_multiple_systems(phx_project)

    # -- Check if the cooling capacity is split
    assert len(phx_project.variants[0].mech_collections) == 2
    assert len(phx_project.variants[0].mech_collections[0].heat_pump_devices) == 2
    assert phx_project.variants[0].mech_collections[0].heat_pump_devices[0].params_cooling.recirculation.capacity == 150.0

    assert len(phx_project.variants[0].mech_collections[1].heat_pump_devices) == 1
    assert phx_project.variants[0].mech_collections[1].heat_pump_devices[0].params_cooling.recirculation.capacity == 150.0
