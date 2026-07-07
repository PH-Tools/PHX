from honeybee_phhvac.supportive_device import PhSupportiveDevice

from PHX.from_HBJSON.create_hvac import build_phx_supportive_device


class TestBuildPhxSupportiveDeviceIHGFactor:
    def test_maps_ihg_utilization_factor(self, reset_class_counters):
        hb_device = PhSupportiveDevice()
        hb_device.ihg_utilization_factor = 0.0

        phx_device = build_phx_supportive_device(hb_device)
        assert phx_device.params.ihg_utilization_factor == 0.0

    def test_maps_ihg_utilization_factor_custom_value(self, reset_class_counters):
        hb_device = PhSupportiveDevice()
        hb_device.ihg_utilization_factor = 0.75

        phx_device = build_phx_supportive_device(hb_device)
        assert phx_device.params.ihg_utilization_factor == 0.75

    def test_maps_ihg_utilization_factor_default(self, reset_class_counters):
        hb_device = PhSupportiveDevice()
        # default is 1.0 on both sides
        phx_device = build_phx_supportive_device(hb_device)
        assert phx_device.params.ihg_utilization_factor == 1.0


class TestBuildPhxSupportiveDeviceIHGUsageProfile:
    def test_maps_ihg_usage_profile_default(self, reset_class_counters):
        # -- default device_type (10-Other) seeds ihg_usage_profile = 1 (ALL_YEAR)
        hb_device = PhSupportiveDevice()
        phx_device = build_phx_supportive_device(hb_device)
        assert phx_device.params.ihg_usage_profile == 1

    def test_maps_ihg_usage_profile_explicit(self, reset_class_counters):
        # -- an explicit WINTER tag (2) must be set AFTER device_type (the setter re-seeds)
        hb_device = PhSupportiveDevice()
        hb_device.ihg_usage_profile = 2
        phx_device = build_phx_supportive_device(hb_device)
        assert phx_device.params.ihg_usage_profile == 2

    def test_maps_ihg_usage_profile_dhw_default(self, reset_class_counters):
        # -- a DHW circulation pump (type 6) re-seeds to 4 (NONE) via the property setter
        hb_device = PhSupportiveDevice()
        hb_device.device_type = 6
        phx_device = build_phx_supportive_device(hb_device)
        assert phx_device.params.ihg_usage_profile == 4
