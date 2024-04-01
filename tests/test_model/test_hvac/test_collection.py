from copy import copy

import pytest

from PHX.model.enums.hvac import PhxSupportiveDeviceType
from PHX.model.hvac import collection, cooling_params, heating, supportive_devices, ventilation, water


def test_default_PhxMechanicalEquipmentCollection(reset_class_counters):
    c1 = collection.PhxMechanicalSystemCollection()
    c2 = collection.PhxMechanicalSystemCollection()

    assert c1.id_num == 1
    assert c2.id_num == 2

    assert not c1.devices
    assert not c2.devices


def test_get_mech_device_by_key(reset_class_counters):
    c1 = collection.PhxMechanicalSystemCollection()
    vent_device = ventilation.PhxDeviceVentilator()
    c1.add_new_mech_device(vent_device.identifier, vent_device)

    assert c1.device_in_collection(vent_device.identifier)
    d = c1.get_mech_device_by_key(vent_device.identifier)
    assert d == vent_device


def test_get_mech_device_by_NONE_key(reset_class_counters):
    c1 = collection.PhxMechanicalSystemCollection()
    sys = c1.get_mech_device_by_key("")
    assert sys is None


def test_get_mech_device_by_id(reset_class_counters):
    c1 = collection.PhxMechanicalSystemCollection()
    vent_device = ventilation.PhxDeviceVentilator()
    c1.add_new_mech_device(vent_device.identifier, vent_device)

    assert c1.device_in_collection(vent_device.identifier)
    d = c1.get_mech_device_by_id(vent_device.id_num)
    assert d == vent_device


def test_get_mech_device_by_NONE_id(reset_class_counters):
    c1 = collection.PhxMechanicalSystemCollection()
    with pytest.raises(collection.NoDeviceFoundError):
        c1.get_mech_device_by_id(999_999_999)


# -----------------------------------------------------------------------------
# -- Ventilators (ERV)


def test_add_ventilation_device(reset_class_counters):
    c1 = collection.PhxMechanicalSystemCollection()
    vent_device = ventilation.PhxDeviceVentilator()
    c1.add_new_mech_device(vent_device.identifier, vent_device)

    assert c1.device_in_collection(vent_device.identifier)
    assert not c1.device_in_collection("not_a_key")


def test_get_ventilation_device():
    c1 = collection.PhxMechanicalSystemCollection()
    vent_device = ventilation.PhxDeviceVentilator()
    c1.add_new_mech_device(vent_device.identifier, vent_device)

    assert vent_device in c1.ventilation_devices
    assert vent_device == c1.get_mech_device_by_key(vent_device.identifier)
    assert vent_device == c1.get_mech_device_by_id(vent_device.id_num)


# -----------------------------------------------------------------------------
# -- Exhaust Ventilation Devices


def test_add_exhaust_ventilation_device_collection(reset_class_counters):
    c1 = collection.PhxExhaustVentilatorCollection()
    vent_device = ventilation.PhxExhaustVentilatorRangeHood()
    c1.add_new_ventilator(vent_device.identifier, vent_device)

    assert c1.device_in_collection(vent_device.identifier)
    assert not c1.device_in_collection("not_a_key")


def test_get_exhaust_ventilation_device(reset_class_counters):
    c1 = collection.PhxExhaustVentilatorCollection()
    vent_device = ventilation.PhxExhaustVentilatorRangeHood()
    c1.add_new_ventilator(vent_device.identifier, vent_device)

    assert vent_device in c1.devices
    assert vent_device == c1.get_ventilator_by_key(vent_device.identifier)
    assert vent_device == c1.get_ventilator_by_id(vent_device.id_num)


def test_get_exhaust_ventilation_device_error(reset_class_counters):
    c1 = collection.PhxExhaustVentilatorCollection()
    vent_device1 = ventilation.PhxExhaustVentilatorRangeHood()

    vent_device2 = ventilation.PhxExhaustVentilatorRangeHood()
    c1.add_new_ventilator(vent_device1.identifier, vent_device1)

    assert c1.get_ventilator_by_key(vent_device2.identifier) == None

    with pytest.raises(collection.NoDeviceFoundError):
        c1.get_ventilator_by_id(vent_device2.id_num)


# -----------------------------------------------------------------------------
# -- Supportive Devices


def test_add_supportive_device_collection(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device = supportive_devices.PhxSupportiveDevice()
    c1.add_new_device(supp_device.identifier, supp_device)

    assert c1.device_in_collection(supp_device.identifier)
    assert not c1.device_in_collection("not_a_key")


def test_get_supportive_device(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device = supportive_devices.PhxSupportiveDevice()
    c1.add_new_device(supp_device.identifier, supp_device)

    assert supp_device in c1.devices
    assert supp_device == c1.get_device_by_key(supp_device.identifier)
    assert supp_device == c1.get_device_by_id(supp_device.id_num)


def test_get_supportive_device_error(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice()

    supp_device2 = supportive_devices.PhxSupportiveDevice()
    c1.add_new_device(supp_device1.identifier, supp_device1)

    assert c1.get_device_by_key(supp_device2.identifier) == None

    with pytest.raises(collection.NoSupportiveDeviceUnitFoundError):
        c1.get_device_by_id(supp_device2.id_num)


def test_group_homogenous_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice()
    supp_device2 = copy(supp_device1)
    supp_device3 = copy(supp_device1)

    gr = c1.group_devices_by_identifier([supp_device1, supp_device2, supp_device3])
    assert len(gr) == 1


def test_group_mixed_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice()
    supp_device2 = copy(supp_device1)
    supp_device3 = supportive_devices.PhxSupportiveDevice()

    gr = c1.group_devices_by_identifier([supp_device1, supp_device2, supp_device3])
    assert len(gr) == 2


def test_merge_homogeneous_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.OTHER)
    supp_device2 = copy(supp_device1)
    supp_device3 = copy(supp_device1)

    assert supp_device1.identifier == supp_device2.identifier
    assert supp_device1.identifier == supp_device3.identifier

    c1.add_new_device(supp_device1.identifier, supp_device1)
    c1.add_new_device(supp_device2.identifier, supp_device2)
    c1.add_new_device(supp_device3.identifier, supp_device3)

    c1.merge_all_devices()

    assert len(c1.devices) == 1
    assert len(c1) == 1
    assert c1.devices[0].identifier == supp_device1.identifier


def test_merge_mixed_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.OTHER)
    supp_device2 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.OTHER)
    supp_device3 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.OTHER)

    assert supp_device1.identifier != supp_device2.identifier
    assert supp_device1.identifier != supp_device3.identifier
    assert supp_device2.identifier != supp_device3.identifier

    c1.add_new_device(supp_device1.identifier, supp_device1)
    c1.add_new_device(supp_device2.identifier, supp_device2)
    c1.add_new_device(supp_device3.identifier, supp_device3)

    c1.merge_all_devices()  # -- nothing should happen

    assert len(c1.devices) == 3
    assert c1.devices[0].identifier == supp_device1.identifier
    assert c1.devices[1].identifier == supp_device2.identifier
    assert c1.devices[2].identifier == supp_device3.identifier


def test_merge_homogeneous_DHW_recirc_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.DHW_CIRCULATING_PUMP)
    supp_device2 = copy(supp_device1)
    supp_device3 = copy(supp_device1)

    assert supp_device1.identifier == supp_device2.identifier
    assert supp_device1.identifier == supp_device3.identifier

    c1.add_new_device(supp_device1.identifier, supp_device1)
    c1.add_new_device(supp_device2.identifier, supp_device2)
    c1.add_new_device(supp_device3.identifier, supp_device3)

    c1.merge_all_devices()

    assert len(c1.devices) == 1
    assert c1.devices[0].identifier == supp_device1.identifier


def test_merge_homogeneous_DHW_storage_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.DHW_STORAGE_LOAD_PUMP)
    supp_device2 = copy(supp_device1)
    supp_device3 = copy(supp_device1)

    assert supp_device1.identifier == supp_device2.identifier
    assert supp_device1.identifier == supp_device3.identifier

    c1.add_new_device(supp_device1.identifier, supp_device1)
    c1.add_new_device(supp_device2.identifier, supp_device2)
    c1.add_new_device(supp_device3.identifier, supp_device3)

    c1.merge_all_devices()

    assert len(c1.devices) == 1
    assert c1.devices[0].identifier == supp_device1.identifier


def test_merge_homogeneous_Heat_Recirc_supportive_devices(reset_class_counters):
    c1 = collection.PhxSupportiveDeviceCollection()
    supp_device1 = supportive_devices.PhxSupportiveDevice(device_type=PhxSupportiveDeviceType.HEAT_CIRCULATING_PUMP)
    supp_device2 = copy(supp_device1)
    supp_device3 = copy(supp_device1)

    assert supp_device1.identifier == supp_device2.identifier
    assert supp_device1.identifier == supp_device3.identifier

    c1.add_new_device(supp_device1.identifier, supp_device1)
    c1.add_new_device(supp_device2.identifier, supp_device2)
    c1.add_new_device(supp_device3.identifier, supp_device3)

    c1.merge_all_devices()

    assert len(c1.devices) == 1
    assert c1.devices[0].identifier == supp_device1.identifier


# TODO: Finish Mech Collection Tests
# -- Heating

# -- Cooling

# -- DHW

# -- DHW Recric Piping

# -- DHW Branch Piping
