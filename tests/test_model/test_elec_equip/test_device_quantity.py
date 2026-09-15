# -*- Python Version: 3.10 -*-

"""One quantity rule for every electrical device: a stored 0 counts as one unit (PHX#153).

`energy_demand` is per unit; `quantity` is the number of units. The annual energy every
writer derives is `get_energy_demand() * get_quantity()`.
"""

import pytest

from PHX.model import elec_equip

ENERGY_DEMAND = 400.0  # kWh/a per unit


@pytest.mark.parametrize(
    "device_class",
    [
        elec_equip.PhxDeviceCustomElec,
        elec_equip.PhxDeviceCustomLighting,
        elec_equip.PhxDeviceCustomMEL,
        elec_equip.PhxElevatorHydraulic,
    ],
)
@pytest.mark.parametrize("quantity, expected_kwh", [(0, 400.0), (1, 400.0), (2, 800.0)])
def test_annual_energy_uses_the_resolved_quantity(reset_class_counters, device_class, quantity, expected_kwh):
    device = device_class()
    device.energy_demand = ENERGY_DEMAND
    device.quantity = quantity

    assert device.get_energy_demand() * device.get_quantity() == pytest.approx(expected_kwh)


@pytest.mark.parametrize(
    "device_class",
    [elec_equip.PhxDeviceCustomLighting, elec_equip.PhxDeviceCustomMEL, elec_equip.PhxElevatorHydraulic],
)
def test_totaled_devices_report_one_line_item(reset_class_counters, device_class):
    """WUFI and METr show these devices as one line item carrying the total demand."""
    device = device_class()
    device.energy_demand = ENERGY_DEMAND
    device.quantity = 2

    assert device.get_quantity() == 1
    assert device.get_energy_demand() == pytest.approx(800.0)
