# -*- Python Version: 3.10 -*-

"""Tests for PHPPConnection._collect_custom_groups()

Verifies that the helper correctly identifies which custom PHPP groups (12-14)
are in use from a list of SurfaceRow objects, and returns the right
(group_number, temp_zone_letter, description) tuples.

See: PHX_BUG_REPORT_floor_group_type.md
"""

import json
from pathlib import Path

import pytest

from PHX.model import components, geometry
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_app import PHPPConnection
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import areas_surface, version


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_polygon(name: str = "test") -> geometry.PhxPolygon:
    return geometry.PhxPolygon(
        name,
        100.0,
        geometry.PhxVertix(0, 0, 0),
        geometry.PhxVector(0, 0, 1),
        geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(0, 0, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )


def _make_component(
    face_type: ComponentFaceType,
    exposure: ComponentExposureExterior,
) -> components.PhxComponentOpaque:
    comp = components.PhxComponentOpaque()
    comp.face_type = face_type
    comp.exposure_exterior = exposure
    return comp


@pytest.fixture
def shape() -> shape_model.Areas:
    json_path = Path(__file__).resolve().parents[3] / "PHX" / "PHPP" / "phpp_localization" / "EN_10_6.json"
    with open(json_path) as f:
        data = json.load(f)
    return shape_model.Areas(**data["AREAS"])


@pytest.fixture
def phpp_v10() -> version.PHPPVersion:
    return version.PHPPVersion("10", "6", "EN")


def _surface_row(
    shape: shape_model.Areas,
    phpp_version: version.PHPPVersion,
    face_type: ComponentFaceType,
    exposure: ComponentExposureExterior,
) -> areas_surface.SurfaceRow:
    return areas_surface.SurfaceRow(
        shape=shape,
        phx_polygon=_make_polygon(),
        phx_component=_make_component(face_type, exposure),
        phpp_assembly_id_name="01ud-TestAssembly",
        phpp_version=phpp_version,
    )


# ===========================================================================
# Tests for _collect_custom_groups
# ===========================================================================


class TestCollectCustomGroups:
    def test_no_custom_groups_returns_empty(self, shape, phpp_v10):
        """All standard groups → empty set."""
        surfaces = [
            _surface_row(shape, phpp_v10, ComponentFaceType.WALL, ComponentExposureExterior.EXTERIOR),
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.GROUND),
            _surface_row(shape, phpp_v10, ComponentFaceType.ROOF_CEILING, ComponentExposureExterior.EXTERIOR),
        ]
        result = PHPPConnection._collect_custom_groups(surfaces)
        assert result == set()

    def test_floor_exterior_includes_group_12(self, shape, phpp_v10):
        """Floor over open air → group 12 with temp zone 'A'."""
        surfaces = [
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR),
        ]
        result = PHPPConnection._collect_custom_groups(surfaces)
        assert (12, "A", "Exposed / attached zone (ambient)") in result

    def test_floor_zone_n_includes_group_13(self, shape, phpp_v10):
        """Floor over unconditioned zone → group 13 with temp zone 'A'."""
        zone_exposure = ComponentExposureExterior(1)
        surfaces = [
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, zone_exposure),
        ]
        result = PHPPConnection._collect_custom_groups(surfaces)
        assert (13, "A", "Floor over uncond. zone") in result

    def test_roof_ground_includes_group_14(self, shape, phpp_v10):
        """Buried roof → group 14 with temp zone 'B'."""
        surfaces = [
            _surface_row(shape, phpp_v10, ComponentFaceType.ROOF_CEILING, ComponentExposureExterior.GROUND),
        ]
        result = PHPPConnection._collect_custom_groups(surfaces)
        assert (14, "B", "Underground roof / ceiling") in result

    def test_mixed_surfaces_deduplicates(self, shape, phpp_v10):
        """Multiple surfaces in the same custom group → single entry in the result set."""
        surfaces = [
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR),
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR),
            _surface_row(shape, phpp_v10, ComponentFaceType.WALL, ComponentExposureExterior.EXTERIOR),
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.GROUND),
        ]
        result = PHPPConnection._collect_custom_groups(surfaces)
        # Only one custom group (12) — the wall/EXTERIOR is group 8, floor/GROUND is group 11
        assert len(result) == 1
        assert (12, "A", "Exposed / attached zone (ambient)") in result

    def test_multiple_custom_groups(self, shape, phpp_v10):
        """Surfaces spanning multiple custom groups → all represented."""
        zone_exposure = ComponentExposureExterior(1)
        surfaces = [
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR),
            _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, zone_exposure),
            _surface_row(shape, phpp_v10, ComponentFaceType.ROOF_CEILING, ComponentExposureExterior.GROUND),
        ]
        result = PHPPConnection._collect_custom_groups(surfaces)
        assert len(result) == 3
        assert (12, "A", "Exposed / attached zone (ambient)") in result
        assert (13, "A", "Floor over uncond. zone") in result
        assert (14, "B", "Underground roof / ceiling") in result
