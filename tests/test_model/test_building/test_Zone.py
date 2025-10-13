from PHX.model import building
from PHX.model.enums.building import SpecificHeatCapacityType
from PHX.model.hvac import ventilation


def test_default_zone(reset_class_counters):
    z1 = building.PhxZone()
    z2 = building.PhxZone()

    assert z1.id_num == 1
    assert z2.id_num == 2
    assert z1 != z2

    assert not z1.spaces
    assert not z2.spaces
    assert not z1.elec_equipment_collection
    assert not z2.elec_equipment_collection
    assert not z1.exhaust_ventilator_collection
    assert not z2.exhaust_ventilator_collection


def test_add_exhaust_device(reset_class_counters):
    z1 = building.PhxZone()
    d1 = ventilation.PhxExhaustVentilatorDryer()

    z1.exhaust_ventilator_collection.add_new_ventilator(d1.identifier, d1)
    assert z1.exhaust_ventilator_collection.device_in_collection(d1.identifier)
    assert len(z1.exhaust_ventilator_collection) == 1


def test_zone_specific_heat_capacity_defaults(reset_class_counters):
    """Test that PhxZone has correct defaults for specific heat capacity."""
    zone = building.PhxZone()

    # Test default specific heat capacity type
    assert zone.specific_heat_capacity == SpecificHeatCapacityType.LIGHTWEIGHT

    # Test default specific heat capacity value in Wh/m²K
    assert zone.specific_heat_capacity_wh_m2k == 60


def test_zone_specific_heat_capacity_custom_values(reset_class_counters):
    """Test that PhxZone can be created with custom specific heat capacity values."""
    # Test MIXED type
    zone_mixed = building.PhxZone(
        specific_heat_capacity=SpecificHeatCapacityType.MIXED, specific_heat_capacity_wh_m2k=132
    )
    assert zone_mixed.specific_heat_capacity == SpecificHeatCapacityType.MIXED
    assert zone_mixed.specific_heat_capacity_wh_m2k == 132

    # Test MASSIVE type
    zone_massive = building.PhxZone(
        specific_heat_capacity=SpecificHeatCapacityType.MASSIVE, specific_heat_capacity_wh_m2k=204
    )
    assert zone_massive.specific_heat_capacity == SpecificHeatCapacityType.MASSIVE
    assert zone_massive.specific_heat_capacity_wh_m2k == 204

    # Test USER_DEFINED type with custom value
    zone_custom = building.PhxZone(
        specific_heat_capacity=SpecificHeatCapacityType.USER_DEFINED, specific_heat_capacity_wh_m2k=150
    )
    assert zone_custom.specific_heat_capacity == SpecificHeatCapacityType.USER_DEFINED
    assert zone_custom.specific_heat_capacity_wh_m2k == 150


def test_zone_specific_heat_capacity_modification(reset_class_counters):
    """Test that PhxZone specific heat capacity attributes can be modified after creation."""
    zone = building.PhxZone()

    # Verify defaults
    assert zone.specific_heat_capacity == SpecificHeatCapacityType.LIGHTWEIGHT
    assert zone.specific_heat_capacity_wh_m2k == 60

    # Modify the values
    zone.specific_heat_capacity = SpecificHeatCapacityType.MASSIVE
    zone.specific_heat_capacity_wh_m2k = 204

    # Verify changes
    assert zone.specific_heat_capacity == SpecificHeatCapacityType.MASSIVE
    assert zone.specific_heat_capacity_wh_m2k == 204
