from functools import reduce
import operator
from PHX.model.components import PhxComponentThermalBridge
from PHX.model.enums.building import ThermalBridgeType


def test_PhxComponentThermalBridge_are_equal() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    assert thermal_bridge_a is not thermal_bridge_b
    assert thermal_bridge_a == thermal_bridge_b
    assert thermal_bridge_a.unique_key == thermal_bridge_b.unique_key


def test_PhxComponentThermalBridge_not_equal_different_length() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_b.length = 1

    assert thermal_bridge_a is not thermal_bridge_b
    assert thermal_bridge_a != thermal_bridge_b
    assert thermal_bridge_a.unique_key == thermal_bridge_b.unique_key


def test_PhxComponentThermalBridge_not_equal_different_type() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.group_type = ThermalBridgeType.PERIMETER
    thermal_bridge_b.group_type = ThermalBridgeType.AMBIENT

    assert thermal_bridge_a is not thermal_bridge_b
    assert thermal_bridge_a != thermal_bridge_b
    assert thermal_bridge_a.unique_key != thermal_bridge_b.unique_key


def test_PhxComponentThermalBridge_not_equal_different_psi_value() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.psi_value = 0.01
    thermal_bridge_b.psi_value = 0.02

    assert thermal_bridge_a is not thermal_bridge_b
    assert thermal_bridge_a != thermal_bridge_b
    assert thermal_bridge_a.unique_key != thermal_bridge_b.unique_key


def test_PhxComponentThermalBridge_not_equal_different_f_rsi() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.fRsi_value = 0.01
    thermal_bridge_b.fRsi_value = 0.02

    assert thermal_bridge_a is not thermal_bridge_b
    assert thermal_bridge_a != thermal_bridge_b
    assert thermal_bridge_a.unique_key == thermal_bridge_b.unique_key


def test_add_two_PhxComponentThermalBridge() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.quantity = 1
    thermal_bridge_a.psi_value = 0.01
    thermal_bridge_a.length = 1

    thermal_bridge_b.quantity = 1
    thermal_bridge_b.psi_value = 0.02
    thermal_bridge_b.length = 1

    thermal_bridge_c = thermal_bridge_a + thermal_bridge_b

    assert thermal_bridge_c.psi_value == 0.015


def test_add_two_PhxComponentThermalBridge_different_psi_values() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.quantity = 1
    thermal_bridge_a.psi_value = 0.01
    thermal_bridge_a.length = 2

    thermal_bridge_b.quantity = 1
    thermal_bridge_b.psi_value = 0.02
    thermal_bridge_b.length = 2

    thermal_bridge_c = thermal_bridge_a + thermal_bridge_b

    assert thermal_bridge_c.psi_value == 0.015


def test_add_two_PhxComponentThermalBridge_different_lengths() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.quantity = 1
    thermal_bridge_a.psi_value = 0.01
    thermal_bridge_a.length = 2

    thermal_bridge_b.quantity = 1
    thermal_bridge_b.psi_value = 0.01
    thermal_bridge_b.length = 4

    thermal_bridge_c = thermal_bridge_a + thermal_bridge_b

    assert thermal_bridge_c.psi_value == 0.01


def test_add_two_PhxComponentThermalBridge_different_quantities() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()

    thermal_bridge_a.quantity = 2
    thermal_bridge_a.psi_value = 0.01
    thermal_bridge_a.length = 2

    thermal_bridge_b.quantity = 1
    thermal_bridge_b.psi_value = 0.01
    thermal_bridge_b.length = 2

    thermal_bridge_c = thermal_bridge_a + thermal_bridge_b

    assert thermal_bridge_c.psi_value == 0.01


def test_merge_multiple_thermal_bridges() -> None:
    thermal_bridge_a = PhxComponentThermalBridge()
    thermal_bridge_b = PhxComponentThermalBridge()
    thermal_bridge_c = PhxComponentThermalBridge()

    thermal_bridge_a.quantity = 2
    thermal_bridge_a.psi_value = 0.01
    thermal_bridge_a.length = 2

    thermal_bridge_b.quantity = 1
    thermal_bridge_b.psi_value = 0.01
    thermal_bridge_b.length = 2

    thermal_bridge_c.quantity = 1
    thermal_bridge_c.psi_value = 0.01
    thermal_bridge_c.length = 2

    thermal_bridge_d: PhxComponentThermalBridge = reduce(
        operator.add, [thermal_bridge_a, thermal_bridge_b, thermal_bridge_c]
    )

    assert thermal_bridge_d.psi_value == 0.01
