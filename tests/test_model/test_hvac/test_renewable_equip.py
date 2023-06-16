import pytest
from PHX.model.hvac import PhxDevicePhotovoltaic, PhxDevicePhotovoltaicParams
from PHX.model.enums.hvac import DeviceType, SystemType


def test_add_default_PhxDevicePhotovoltaicParams(reset_class_counters):
    p1 = PhxDevicePhotovoltaicParams()
    p1.photovoltaic_renewable_energy = 1_000
    p2 = PhxDevicePhotovoltaicParams()
    p2.photovoltaic_renewable_energy = 2_000

    p3 = p1 + p2
    assert p3.photovoltaic_renewable_energy == 3_000


def test_default_PhxDevicePhotovoltaic(reset_class_counters):
    d1 = PhxDevicePhotovoltaic()
    d2 = PhxDevicePhotovoltaic()

    assert d1.id_num == 1
    assert d2.id_num == 2
