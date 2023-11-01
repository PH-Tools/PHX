from PHX.model.enums import hvac
from PHX.model.hvac import heating


def test_PhxHeatingDevice(reset_class_counters):
    d1 = heating.PhxHeatingDevice()
    d2 = heating.PhxHeatingDevice()

    assert d1.id_num == 1
    assert d2.id_num == 2


# -----------------------------------------------------------------------------
# Electric


def test_default_PhxHeaterElectric(reset_class_counters):
    d1 = heating.PhxHeaterElectric()
    d2 = heating.PhxHeaterElectric()

    assert d1.id_num == 1
    assert d2.id_num == 2


# -----------------------------------------------------------------------------
# Boilers


def test_default_PhxHeaterBoilerFossil(reset_class_counters):
    d1 = heating.PhxHeaterBoilerFossil()
    d2 = heating.PhxHeaterBoilerFossil()

    assert d1.id_num == 1
    assert d2.id_num == 2


def test_PhxHeaterBoilerFossil_set_fuel(reset_class_counters):
    d1 = heating.PhxHeaterBoilerFossil()
    d1.params.fuel = 1
    d2 = heating.PhxHeaterBoilerFossil()
    d2.params.fuel = 2

    assert d1.params.fuel == hvac.PhxFuelType.NATURAL_GAS
    assert d2.params.fuel == hvac.PhxFuelType.OIL


def test_default_PhxHeaterBoilerWood(reset_class_counters):
    d1 = heating.PhxHeaterBoilerWood()
    d2 = heating.PhxHeaterBoilerWood()

    assert d1.id_num == 1
    assert d2.id_num == 2


def test_PhxHeaterBoilerWood_set_fuel(reset_class_counters):
    d1 = heating.PhxHeaterBoilerWood()
    d1.params.fuel = 3
    d2 = heating.PhxHeaterBoilerWood()
    d2.params.fuel = 4

    assert d1.params.fuel == hvac.PhxFuelType.WOOD_LOG
    assert d2.params.fuel == hvac.PhxFuelType.WOOD_PELLET


# -----------------------------------------------------------------------------
# District Heat


def test_default_PhxHeaterDistrictHeat(reset_class_counters):
    d1 = heating.PhxHeaterDistrictHeat()
    d2 = heating.PhxHeaterDistrictHeat()

    assert d1.id_num == 1
    assert d2.id_num == 2
