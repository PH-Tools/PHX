"""Tests for the ihg_utilization_factor attribute on all PhxElectricalDevice subclasses."""

import pytest

from PHX.model import elec_equip


class TestIhgUtilizationFactorDefaults:
    """Verify that each device class has the correct default ihg_utilization_factor."""

    def test_base_device_default(self, reset_class_counters):
        device = elec_equip.PhxElectricalDevice()
        assert device.ihg_utilization_factor == 1.0

    def test_dishwasher_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceDishwasher()
        assert device.ihg_utilization_factor == 0.30

    def test_clothes_washer_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceClothesWasher()
        assert device.ihg_utilization_factor == 0.30

    def test_clothes_dryer_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceClothesDryer()
        assert device.ihg_utilization_factor == 0.70

    def test_refrigerator_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceRefrigerator()
        assert device.ihg_utilization_factor == 1.0

    def test_freezer_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceFreezer()
        assert device.ihg_utilization_factor == 1.0

    def test_fridge_freezer_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceFridgeFreezer()
        assert device.ihg_utilization_factor == 1.0

    def test_cooktop_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceCooktop()
        assert device.ihg_utilization_factor == 0.50

    def test_mel_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceMEL()
        assert device.ihg_utilization_factor == 1.0

    def test_lighting_interior_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceLightingInterior()
        assert device.ihg_utilization_factor == 1.0

    def test_lighting_exterior_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceLightingExterior()
        assert device.ihg_utilization_factor == 1.0

    def test_lighting_garage_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceLightingGarage()
        assert device.ihg_utilization_factor == 1.0

    def test_custom_elec_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceCustomElec()
        assert device.ihg_utilization_factor == 1.0

    def test_custom_lighting_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceCustomLighting()
        assert device.ihg_utilization_factor == 1.0

    def test_custom_mel_default(self, reset_class_counters):
        device = elec_equip.PhxDeviceCustomMEL()
        assert device.ihg_utilization_factor == 1.0

    def test_elevator_hydraulic_default(self, reset_class_counters):
        device = elec_equip.PhxElevatorHydraulic()
        assert device.ihg_utilization_factor == 1.0

    def test_elevator_geared_traction_default(self, reset_class_counters):
        device = elec_equip.PhxElevatorGearedTraction()
        assert device.ihg_utilization_factor == 1.0

    def test_elevator_gearless_traction_default(self, reset_class_counters):
        device = elec_equip.PhxElevatorGearlessTraction()
        assert device.ihg_utilization_factor == 1.0


class TestIhgUtilizationFactorSetable:
    """Verify that ihg_utilization_factor can be set to a custom value."""

    def test_base_device_set(self, reset_class_counters):
        device = elec_equip.PhxElectricalDevice()
        device.ihg_utilization_factor = 0.75
        assert device.ihg_utilization_factor == 0.75

    def test_dishwasher_override(self, reset_class_counters):
        device = elec_equip.PhxDeviceDishwasher()
        device.ihg_utilization_factor = 0.99
        assert device.ihg_utilization_factor == 0.99

    def test_cooktop_override(self, reset_class_counters):
        device = elec_equip.PhxDeviceCooktop()
        device.ihg_utilization_factor = 0.0
        assert device.ihg_utilization_factor == 0.0
