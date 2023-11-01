import importlib
from pathlib import Path
import pytest

from PHX.model import (
    building,
    project,
    geometry,
    schedules,
    certification,
    constructions,
    elec_equip,
    components,
    spaces,
    shades,
)
from PHX.model.hvac import (
    _base,
    collection,
    renewable_devices,
    water,
    ventilation,
    heating,
    ducting,
    piping,
    heat_pumps,
)
from PHX.model.schedules import ventilation as sched_ventilation
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.model.schedules import occupancy as sched_occupancy


@pytest.fixture
def polygon_1x1x0() -> geometry.PhxPolygon:
    p1 = geometry.PhxPolygon(
        "no_name",
        100.0,
        geometry.PhxVertix(1.0, 1.0, 0.0),
        geometry.PhxVector(0.0, 0.0, 1.0),
        geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(1, 1, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )
    p1.add_vertix(geometry.PhxVertix(0, 0, 0))
    p1.add_vertix(geometry.PhxVertix(0, 1, 0))
    p1.add_vertix(geometry.PhxVertix(1, 1, 0))
    p1.add_vertix(geometry.PhxVertix(1, 0, 0))
    return p1


@pytest.fixture
def polygon_2x2x0() -> geometry.PhxPolygon:
    p1 = geometry.PhxPolygon(
        "no_name",
        100.0,
        geometry.PhxVertix(1.0, 1.0, 0.0),
        geometry.PhxVector(0.0, 0.0, 1.0),
        geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(1, 1, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )
    p1.add_vertix(geometry.PhxVertix(0, 0, 0))
    p1.add_vertix(geometry.PhxVertix(0, 2, 0))
    p1.add_vertix(geometry.PhxVertix(2, 2, 0))
    p1.add_vertix(geometry.PhxVertix(2, 0, 0))
    return p1


def _reset_phx_class_counters():
    project.PhxVariant._count = 0
    geometry.PhxPolygon._count = 0
    geometry.PhxVertix._count = 0
    constructions.PhxConstructionOpaque._count = 0
    constructions.PhxConstructionWindow._count = 0
    building.PhxZone._count = 0
    certification.PhxPhBuildingData._count = 0

    components.PhxComponentBase._count = 0
    elec_equip.PhxElectricalDevice._count = 0
    elec_equip.PhxDeviceDishwasher._count = 0
    elec_equip.PhxDeviceClothesWasher._count = 0
    elec_equip.PhxDeviceClothesDryer._count = 0
    elec_equip.PhxDeviceRefrigerator._count = 0
    elec_equip.PhxDeviceFreezer._count = 0
    elec_equip.PhxDeviceFridgeFreezer._count = 0
    elec_equip.PhxDeviceCooktop._count = 0
    elec_equip.PhxDeviceMEL._count = 0
    elec_equip.PhxDeviceLightingInterior._count = 0
    elec_equip.PhxDeviceLightingExterior._count = 0
    elec_equip.PhxDeviceLightingGarage._count = 0
    elec_equip.PhxDeviceCustomElec._count = 0
    elec_equip.PhxDeviceCustomLighting._count = 0
    elec_equip.PhxDeviceCustomMEL._count = 0

    _base.PhxMechanicalDevice._count = 0
    collection.PhxMechanicalSystemCollection._count = 0

    spaces.PhxSpace._count = 0
    ventilation.PhxDeviceVentilation._count = 0
    ventilation.PhxDeviceVentilator._count = 0

    heating.PhxHeatingDevice._count = 0
    heating.PhxHeaterElectric._count = 0
    heating.PhxHeaterBoilerFossil._count = 0
    heating.PhxHeaterBoilerWood._count = 0
    heating.PhxHeaterDistrictHeat._count = 0
    
    heat_pumps.PhxHeatPumpAnnual._count = 0
    heat_pumps.PhxHeatPumpMonthly._count = 0
    heat_pumps.PhxHeatPumpHotWater._count = 0
    heat_pumps.PhxHeatPumpCombined._count = 0

    water.PhxHotWaterDevice._count = 0
    water.PhxHotWaterTank._count = 0

    piping.PhxPipeBranch._count = 0
    piping.PhxPipeTrunk._count = 0

    ventilation.PhxDeviceVentilation._count = 0
    ventilation.PhxDeviceVentilator._count = 0
    ventilation.PhxExhaustVentilatorBase._count = 0

    ducting.PhxDuctElement._count = 0

    shades.PhxWindowShade._count = 0

    renewable_devices.PhxDevicePhotovoltaic._count = 0

    sched_ventilation.PhxScheduleVentilation._count = 0
    PhxScheduleVentilation._count = 0
    PhxScheduleVentilation.id_num = 0
    sched_occupancy.PhxScheduleOccupancy._count = 0


def _reload_phx_classes():
    """reload all of the PHX model classes. This is similar to the 'reset_class_counters
    except that it will reset all of the PHX modules back to starting position. This is
    used for running the xml-reference-case testers, since otherwise the id-number
    counters will not line up correctly.
    """
    importlib.reload(building)
    importlib.reload(certification)
    importlib.reload(components)
    importlib.reload(constructions)
    importlib.reload(elec_equip)
    importlib.reload(geometry)
    importlib.reload(project)
    importlib.reload(geometry)
    importlib.reload(schedules)
    importlib.reload(spaces)
    importlib.reload(shades)
    importlib.reload(sched_ventilation)
    importlib.reload(sched_occupancy)
    importlib.reload(piping)
    importlib.reload(heat_pumps)


@pytest.fixture
def reset_class_counters():
    """Re-set class's _count variable in order to test id-num incrementing properly"""
    _reset_phx_class_counters()
    try:
        yield
    finally:
        _reset_phx_class_counters()


@pytest.fixture(
    params=[
        (
            Path("tests", "_source_hbjson", "Default_Model_Single_Zone.hbjson"),
            Path("tests", "_reference_xml", "Default_Model_Single_Zone.xml"),
        ),
        (
            Path("tests", "_source_hbjson", "Multi_Room_Complete.hbjson"),
            Path("tests", "_reference_xml", "Multi_Room_Complete.xml"),
        ),
    ]
)
def to_xml_reference_cases(request):
    """Yields file-paths to reference test-cases"""
    _reload_phx_classes()
    _reset_phx_class_counters()
    try:
        yield request.param
    finally:
        _reload_phx_classes()
        _reset_phx_class_counters()
