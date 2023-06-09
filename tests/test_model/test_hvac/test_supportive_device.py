from PHX.model.hvac.supportive_devices import (
    PhxSupportiveDevice,
    PhxSupportiveDeviceParams,
)


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
    assert p3.in_conditioned_space == True


def test_add_default_PhxSupportiveDevice(reset_class_counters):
    p1 = PhxSupportiveDevice()
    p2 = PhxSupportiveDevice()

    p3 = p1 + p2

    assert p3.quantity == 2
    assert p3.params.norm_energy_demand_W == 1.0
    assert p3.params.annual_period_operation_khrs == 17.52
    assert p3.params.in_conditioned_space == True
