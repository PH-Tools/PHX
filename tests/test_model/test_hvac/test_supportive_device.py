import pytest

from PHX.model.hvac.supportive_devices import PhxSupportiveDevice, PhxSupportiveDeviceParams


def test_add_PhxSupportiveDeviceParams(reset_class_counters):
    p1 = PhxSupportiveDeviceParams(
        in_conditioned_space=True,
        norm_energy_demand_W=100,
        annual_period_operation_khrs=100,
    )
    p2 = PhxSupportiveDeviceParams(
        in_conditioned_space=True,
        norm_energy_demand_W=100,
        annual_period_operation_khrs=100,
    )

    p3 = p1 + p2

    assert p3.norm_energy_demand_W == 100
    assert p3.annual_period_operation_khrs == 200
    assert p3.in_conditioned_space


def test_add_default_PhxSupportiveDevice(reset_class_counters):
    p1 = PhxSupportiveDevice()
    p2 = PhxSupportiveDevice()

    p3 = p1 + p2

    assert p3.quantity == 2
    assert p3.params.norm_energy_demand_W == 1.0
    assert p3.params.annual_period_operation_khrs == 17.52
    assert p3.params.in_conditioned_space


# ---------------------------------------------------------------------------
# --- IHG Utilization Factor
# ---------------------------------------------------------------------------


class TestPhxSupportiveDeviceParamsIHGFactor:
    def test_default_ihg_utilization_factor(self, reset_class_counters):
        params = PhxSupportiveDeviceParams()
        assert params.ihg_utilization_factor == 1.0

    def test_set_ihg_utilization_factor(self, reset_class_counters):
        params = PhxSupportiveDeviceParams(ihg_utilization_factor=0.0)
        assert params.ihg_utilization_factor == 0.0

        params2 = PhxSupportiveDeviceParams(ihg_utilization_factor=0.5)
        assert params2.ihg_utilization_factor == 0.5

    def test_add_params_ihg_factor_energy_weighted_average(self, reset_class_counters):
        """Merging two params produces an energy-weighted average ihg_utilization_factor."""
        p1 = PhxSupportiveDeviceParams(
            norm_energy_demand_W=100,
            annual_period_operation_khrs=8.76,
            ihg_utilization_factor=1.0,
        )
        p2 = PhxSupportiveDeviceParams(
            norm_energy_demand_W=50,
            annual_period_operation_khrs=8.76,
            ihg_utilization_factor=0.0,
        )
        merged = p1 + p2
        # energy1 = 100 * 8.76 = 876, energy2 = 50 * 8.76 = 438
        # weighted = (876 * 1.0 + 438 * 0.0) / (876 + 438) = 876 / 1314 ≈ 0.6667
        assert merged.ihg_utilization_factor == pytest.approx(876 / 1314, abs=1e-4)

    def test_add_params_ihg_factor_same_values(self, reset_class_counters):
        """Merging two params with the same factor keeps that factor."""
        p1 = PhxSupportiveDeviceParams(
            norm_energy_demand_W=100,
            annual_period_operation_khrs=8.76,
            ihg_utilization_factor=0.0,
        )
        p2 = PhxSupportiveDeviceParams(
            norm_energy_demand_W=200,
            annual_period_operation_khrs=4.38,
            ihg_utilization_factor=0.0,
        )
        merged = p1 + p2
        assert merged.ihg_utilization_factor == 0.0

    def test_add_params_ihg_factor_zero_watt_demand(self, reset_class_counters):
        """When both devices have zero watt demand, fall back to simple average."""
        p1 = PhxSupportiveDeviceParams(
            norm_energy_demand_W=0.0,
            annual_period_operation_khrs=8.76,
            ihg_utilization_factor=1.0,
        )
        p2 = PhxSupportiveDeviceParams(
            norm_energy_demand_W=0.0,
            annual_period_operation_khrs=8.76,
            ihg_utilization_factor=0.0,
        )
        merged = p1 + p2
        # energy = 0*8.76 + 0*8.76 = 0 => fallback: (1.0 + 0.0) / 2 = 0.5
        assert merged.ihg_utilization_factor == pytest.approx(0.5)


class TestPhxSupportiveDeviceIHGFactor:
    def test_device_default_ihg_utilization_factor(self, reset_class_counters):
        device = PhxSupportiveDevice()
        assert device.params.ihg_utilization_factor == 1.0

    def test_add_devices_preserves_ihg_factor(self, reset_class_counters):
        d1 = PhxSupportiveDevice()
        d1.params.ihg_utilization_factor = 0.0
        d1.params.norm_energy_demand_W = 50
        d1.params.annual_period_operation_khrs = 8.76

        d2 = PhxSupportiveDevice()
        d2.params.ihg_utilization_factor = 1.0
        d2.params.norm_energy_demand_W = 100
        d2.params.annual_period_operation_khrs = 8.76

        merged = d1 + d2
        # energy1=438 @ 0.0, energy2=876 @ 1.0 => 876/1314 ≈ 0.6667
        assert merged.params.ihg_utilization_factor == pytest.approx(876 / 1314, abs=1e-4)
