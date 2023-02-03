from PHX.model import building
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
