# -*- Python Version: 3.10 -*-

"""Tests for PHPPConnection.write_certification_config."""

from collections.abc import Iterable
from functools import lru_cache

import pytest

from PHX.model import project
from PHX.model.enums import phi_certification_phpp_9 as phi_v9
from PHX.model.enums import phi_certification_phpp_10 as phi_v10
from PHX.PHPP.phpp_app import PHPPConnection
from PHX.PHPP.phpp_localization.shape_model import Verification as VerificationShape
from PHX.PHPP.phpp_model import verification_data, version
from PHX.PHPP.sheet_io.io_verification import Verification
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import SHAPE_FILENAMES, load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

ENUM_INPUT_TYPES = (
    "phi_building_category_type",
    "phi_building_use_type",
    "phi_building_ihg_type",
    "phi_building_occupancy_type",
    "phi_certification_type",
    "phi_certification_class",
    "phi_pe_type",
    "phi_enerphit_type",
    "phi_retrofit_type",
)
ITEM_INPUT_TYPES = ("num_of_units", "setpoint_winter", "setpoint_summer", "mechanical_cooling")

ENUM_CLASSES_BY_MAJOR = {
    9: (
        ("phi_building_category_type", phi_v9.PhiCertBuildingCategoryType),
        ("phi_building_use_type", phi_v9.PhiCertBuildingUseType),
        ("phi_building_ihg_type", phi_v9.PhiCertIHGType),
        ("phi_building_occupancy_type", phi_v9.PhiCertOccupancyType),
        ("phi_certification_type", phi_v9.PhiCertType),
        ("phi_certification_class", phi_v9.PhiCertClass),
        ("phi_pe_type", phi_v9.PhiCertificationPEType),
        ("phi_enerphit_type", phi_v9.PhiCertEnerPHitType),
        ("phi_retrofit_type", phi_v9.PhiCertRetrofitType),
    ),
    10: (
        # -- These three deliberately remain v9 members in PHPP-10 settings.
        ("phi_building_category_type", phi_v9.PhiCertBuildingCategoryType),
        ("phi_building_use_type", phi_v10.PhiCertBuildingUseType),
        ("phi_building_ihg_type", phi_v10.PhiCertIHGType),
        ("phi_building_occupancy_type", phi_v9.PhiCertOccupancyType),
        ("phi_certification_type", phi_v10.PhiCertType),
        ("phi_certification_class", phi_v10.PhiCertClass),
        ("phi_pe_type", phi_v10.PhiCertificationPEType),
        ("phi_enerphit_type", phi_v9.PhiCertEnerPHitType),
        ("phi_retrofit_type", phi_v10.PhiCertRetrofitType),
    ),
}
SHAPES_BY_MAJOR = {
    major: tuple(filename for filename in SHAPE_FILENAMES if filename.startswith(f"EN_{major}_"))
    for major in ENUM_CLASSES_BY_MAJOR
}


def _enum_cases() -> Iterable[tuple[str, str, object]]:
    for major, shape_filenames in SHAPES_BY_MAJOR.items():
        for shape_filename in shape_filenames:
            for input_type, enum_class in ENUM_CLASSES_BY_MAJOR[major]:
                for enum_member in enum_class:
                    yield shape_filename, input_type, enum_member


@lru_cache
def _load_verification_shape(_shape_filename: str) -> VerificationShape:
    return load_shape(_shape_filename).VERIFICATION


def _phpp_connection() -> tuple[FakeXLFramework, PHPPConnection, list[str], list[str]]:
    shape = load_shape("EN_10_6.json")
    verification_shape = shape.VERIFICATION
    seed = {
        "R1": verification_shape.phi_building_category_type.locator_string,
        "R10": verification_shape.phi_building_occupancy_type.locator_string,
        "T20": verification_shape.phi_certification_type.locator_string,
        "T30": verification_shape.phi_certification_class.locator_string,
        "T40": verification_shape.phi_pe_type.locator_string,
        "T50": verification_shape.phi_enerphit_type.locator_string,
        "E29": verification_shape.num_of_units.locator_string,
        "J28": verification_shape.setpoint_winter.locator_string,
        "M28": verification_shape.setpoint_summer.locator_string,
        "M30": verification_shape.mechanical_cooling.locator_string,
    }
    fake_xl = FakeXLFramework(sheet_names=[verification_shape.name], seed={verification_shape.name: seed})
    outputs: list[str] = []
    xl = XLConnection(xl_framework=fake_xl, output=outputs.append)

    phpp = object.__new__(PHPPConnection)
    phpp.easyPh = False
    phpp.xl = xl
    phpp.shape = shape
    phpp.version = version.PHPPVersion("10", "6", "EN")
    phpp.verification = Verification(xl, verification_shape)

    written_input_types: list[str] = []
    write_item = phpp.verification.write_item

    def record_write(item: verification_data.VerificationInput) -> None:
        written_input_types.append(item.input_type)
        write_item(item)

    phpp.verification.write_item = record_write
    return fake_xl, phpp, outputs, written_input_types


def _variant(_phi_version: int) -> project.PhxVariant:
    variant = project.PhxVariant()
    variant.phi_cert.version = _phi_version
    variant.phius_cert.ph_building_data.num_of_units = 3
    variant.phius_cert.ph_building_data.setpoints.winter = 21.0
    variant.phius_cert.ph_building_data.setpoints.summer = 26.0
    variant.phius_cert.ph_building_data.setpoints.mechanical_cooling = True

    if _phi_version == 10:
        settings = variant.phi_cert.phi_certification_settings
        settings.phi_building_use_type = phi_v10.PhiCertBuildingUseType.DWELLING
        settings.phi_building_ihg_type = phi_v10.PhiCertIHGType.STANDARD
        settings.phi_certification_type = phi_v10.PhiCertType.PASSIVE_HOUSE
        settings.phi_certification_class = phi_v10.PhiCertClass.CLASSIC
        settings.phi_pe_type = phi_v10.PhiCertificationPEType.STANDARD
        settings.phi_retrofit_type = phi_v10.PhiCertRetrofitType.NEW_BUILDING

    return variant


def test_version_mismatch_skips_enums_but_writes_model_parameters():
    fake_xl, phpp, _, written_input_types = _phpp_connection()

    phpp.write_certification_config(project.PhxProject(variants=[_variant(9)]))

    assert written_input_types == list(ITEM_INPUT_TYPES)
    assert fake_xl.written_state()["Verification"] == {
        "F29": 3.0,
        "K28": 21.0,
        "N28": 26.0,
        "N30": "x",
    }


def test_matching_version_writes_enums_and_model_parameters():
    fake_xl, phpp, _, written_input_types = _phpp_connection()

    phpp.write_certification_config(project.PhxProject(variants=[_variant(10)]))

    assert written_input_types == [*ENUM_INPUT_TYPES, *ITEM_INPUT_TYPES]
    written = fake_xl.written_state()["Verification"]
    assert {"F29", "K28", "N28", "N30"}.issubset(written)


def test_version_mismatch_warns_once_for_two_variants():
    _, phpp, outputs, written_input_types = _phpp_connection()

    phpp.write_certification_config(project.PhxProject(variants=[_variant(9), _variant(9)]))

    warnings = [message for message in outputs if "PHPPVersionWarning" in message]
    assert len(warnings) == 1
    assert "V=9" in warnings[0]
    assert "V=10" in warnings[0]
    assert "certification selections" in warnings[0]
    assert "dwelling units, setpoints, and mechanical cooling" in warnings[0]
    assert written_input_types == [*ITEM_INPUT_TYPES, *ITEM_INPUT_TYPES]


@pytest.mark.parametrize(
    ("shape_filename", "input_type", "enum_member"),
    _enum_cases(),
    ids=lambda value: getattr(value, "name", str(value)),
)
def test_every_phi_certification_enum_member_resolves_for_matching_shape(
    shape_filename: str, input_type: str, enum_member: object
):
    shape = _load_verification_shape(shape_filename)

    item = verification_data.VerificationInput.enum(shape, input_type, enum_member)

    assert item.input_data == getattr(shape, input_type).options[str(enum_member.value)]
