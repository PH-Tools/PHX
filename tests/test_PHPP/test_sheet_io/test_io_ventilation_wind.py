# -*- Python Version: 3.10 -*-

"""Tests for PHPP ventilation wind-protection writes."""

import pytest

from PHX.model import building, project
from PHX.model.enums.building import WindExposureType
from PHX.PHPP.phpp_app import PHPPConnection
from PHX.PHPP.phpp_model import ventilation_data
from PHX.PHPP.sheet_io.io_ventilation import Ventilation
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework


def _phpp_connection(_shape_filename: str) -> tuple[FakeXLFramework, PHPPConnection, list[str]]:
    shape = load_shape(_shape_filename)
    ventilation_shape = shape.VENTILATION
    if ventilation_shape.wind_protection_class:
        seed = {
            "I12": ventilation_shape.vent_type.locator_string,
            "I15": ventilation_shape.multi_unit_on.locator_string,
            "I19": ventilation_shape.wind_protection_class.locator_string,
            "I22": ventilation_shape.airtightness_n50.locator_string,
            "I23": ventilation_shape.airtightness_Vn50.locator_string,
        }
    else:
        assert ventilation_shape.wind_coeff_e is not None
        assert ventilation_shape.wind_coeff_f is not None
        seed = {
            "I25": ventilation_shape.wind_coeff_e.locator_string,
            "I26": ventilation_shape.wind_coeff_f.locator_string,
            "I29": ventilation_shape.airtightness_n50.locator_string,
        }

    fake_xl = FakeXLFramework(sheet_names=[ventilation_shape.name], seed={ventilation_shape.name: seed})
    outputs: list[str] = []
    xl = XLConnection(xl_framework=fake_xl, output=outputs.append)
    phpp = object.__new__(PHPPConnection)
    phpp.easyPh = False
    phpp.xl = xl
    phpp.shape = shape
    phpp.ventilation = Ventilation(xl, ventilation_shape)
    return fake_xl, phpp, outputs


def _project(_exposure: WindExposureType, _wind_coefficient_f: float = 15) -> project.PhxProject:
    variant = project.PhxVariant()
    variant.phius_cert.ph_building_data.building_exposure_type = _exposure
    variant.phius_cert.ph_building_data.wind_coefficient_f = _wind_coefficient_f
    variant.phius_cert.ph_building_data.airtightness_n50 = 0.6
    variant.building.zones.append(building.PhxZone(volume_net=150))
    return project.PhxProject(variants=[variant])


@pytest.mark.parametrize(
    ("exposure", "expected"),
    (
        (WindExposureType.SEVERAL_SIDES_EXPOSED_NO_SCREENING, "1-No protection"),
        (WindExposureType.SEVERAL_SIDES_EXPOSED_MODERATE_SCREENING, "2-Moderate protection"),
        (WindExposureType.SEVERAL_SIDES_EXPOSED_HIGH_SCREENING, "3-High protection"),
    ),
)
def test_phpp_10_writes_the_wind_protection_class(exposure: WindExposureType, expected: str):
    fake_xl, phpp, _ = _phpp_connection("EN_10_6.json")

    phpp.write_project_airtightness(_project(exposure))

    assert fake_xl.written_state()["Ventilation"]["K19"] == expected


def test_unknown_wind_coefficient_raises_instead_of_falling_back():
    shape = load_shape("EN_10_6.json").VENTILATION

    with pytest.raises(KeyError):
        ventilation_data.VentilationInputItem.wind_protection_class(shape, 0.08)


@pytest.mark.parametrize(("wind_coefficient_f", "warning_expected"), ((20, True), (15, False)))
def test_phpp_10_does_not_write_coefficients_and_warns_for_nondefault_f(
    wind_coefficient_f: float, warning_expected: bool
):
    fake_xl, phpp, outputs = _phpp_connection("EN_10_6.json")

    phpp.write_project_airtightness(_project(WindExposureType.SEVERAL_SIDES_EXPOSED_NO_SCREENING, wind_coefficient_f))

    written = fake_xl.written_state()["Ventilation"]
    assert not {"J19", "J20", "M20"}.intersection(written)
    warnings = [message for message in outputs if "PHPPVentilationWarning" in message]
    assert bool(warnings) is warning_expected
    if warning_expected:
        assert len(warnings) == 1
        assert "fixes wind coefficient f at 15" in warnings[0]
        assert "model value 20" in warnings[0]


def test_phpp_9_writes_both_wind_coefficients_without_a_class_write():
    fake_xl, phpp, _ = _phpp_connection("EN_9_6A.json")

    phpp.write_project_airtightness(_project(WindExposureType.SEVERAL_SIDES_EXPOSED_HIGH_SCREENING, 20))

    written = fake_xl.written_state()["Ventilation"]
    assert written["N25"] == 0.04
    assert written["N26"] == 20.0
    assert "K25" not in written


def test_phpp_10_keeps_other_ventilation_writes_unchanged():
    fake_xl, phpp, _ = _phpp_connection("EN_10_6.json")
    phx_project = _project(WindExposureType.SEVERAL_SIDES_EXPOSED_NO_SCREENING)

    phpp.write_project_ventilation_type(phx_project)
    phpp.write_project_airtightness(phx_project)
    phpp.write_project_volume(phx_project)

    written = fake_xl.written_state()["Ventilation"]
    assert written["K12"] == "1-Balanced PH ventilation with HR"
    assert written["K15"] == "x"
    assert written["M22"] == 0.6
    assert written["M23"] == 150.0
