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
