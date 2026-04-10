# -*- Python Version: 3.10 -*-

"""Tests for PHX.PHPP.phpp_model.areas_surface.SurfaceRow.phpp_group_number

Verifies that the PHPP group number is assigned based on BOTH face_type AND
exposure_exterior — not face_type alone. Floors over open air or unconditioned
zones must NOT be lumped into group 11 (ground-contact).

See: PHX_BUG_REPORT_floor_group_type.md
"""

import pytest

from PHX.model import components, geometry
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_model import areas_surface, version

# ---------------------------------------------------------------------------
# Helpers — lightweight stubs so we can test phpp_group_number in isolation
# ---------------------------------------------------------------------------


def _make_polygon(name: str = "test_polygon") -> geometry.PhxPolygon:
    """Return a minimal PhxPolygon stub (only display_name matters for group tests)."""
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
    """Return a PhxComponentOpaque with the given face_type and exposure."""
    comp = components.PhxComponentOpaque()
    comp.face_type = face_type
    comp.exposure_exterior = exposure
    return comp


def _make_shape():
    """Load the real EN v10.6 shape so we get correct column/format data."""
    import json
    from pathlib import Path

    from PHX.PHPP.phpp_localization import shape_model

    json_path = Path(__file__).resolve().parents[3] / "PHX" / "PHPP" / "phpp_localization" / "EN_10_6.json"
    with open(json_path) as f:
        data = json.load(f)
    return shape_model.Areas(**data["AREAS"])


@pytest.fixture
def shape():
    return _make_shape()


@pytest.fixture
def phpp_v10() -> version.PHPPVersion:
    return version.PHPPVersion("10", "6", "EN")


@pytest.fixture
def phpp_v9() -> version.PHPPVersion:
    return version.PHPPVersion("9", "6", "EN")


def _surface_row(
    shape,
    phpp_version: version.PHPPVersion,
    face_type: ComponentFaceType,
    exposure: ComponentExposureExterior,
) -> areas_surface.SurfaceRow:
    """Build a SurfaceRow with controlled face_type and exposure."""
    return areas_surface.SurfaceRow(
        shape=shape,
        phx_polygon=_make_polygon(),
        phx_component=_make_component(face_type, exposure),
        phpp_assembly_id_name="01ud-TestAssembly",
        phpp_version=phpp_version,
    )


# ===========================================================================
# Group 1: Regression guards — existing behaviour MUST be preserved
# ===========================================================================


class TestRegressionExistingGroupNumbers:
    """These should pass both before AND after the fix."""

    def test_wall_exterior_returns_8(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.WALL, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number == "8-"

    def test_wall_ground_returns_9(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.WALL, ComponentExposureExterior.GROUND)
        assert row.phpp_group_number == "9-"

    def test_floor_ground_returns_11(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.GROUND)
        assert row.phpp_group_number == "11-"

    def test_roof_exterior_returns_10(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.ROOF_CEILING, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number == "10-"

    def test_adiabatic_returns_18(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.WALL, ComponentExposureExterior.SURFACE)
        assert row.phpp_group_number == "18-"


# ===========================================================================
# Group 2: Bug-fix cases — these FAIL on the current code, PASS after fix
# ===========================================================================


class TestBugFixNewGroupNumbers:
    """These test the corrected exposure-based branching."""

    def test_floor_exterior_returns_12(self, shape, phpp_v10):
        """Floor over open air / crawlspace should be custom group 12, not group 11 (ground)."""
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number == "12-"

    def test_floor_zone_n_returns_13(self, shape, phpp_v10):
        """Floor over unconditioned zone (e.g. garage) should be custom group 13."""
        zone_exposure = ComponentExposureExterior(1)  # ZONE_1 via _missing_
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, zone_exposure)
        assert row.phpp_group_number == "13-"

    def test_roof_ground_returns_14(self, shape, phpp_v10):
        """Buried roof (earth-sheltered) should be custom group 14, not group 10 (ambient)."""
        row = _surface_row(shape, phpp_v10, ComponentFaceType.ROOF_CEILING, ComponentExposureExterior.GROUND)
        assert row.phpp_group_number == "14-"

    def test_wall_zone_n_returns_12(self, shape, phpp_v10):
        """Wall adjacent to unconditioned zone should be custom group 12, not group 9 (ground)."""
        zone_exposure = ComponentExposureExterior(1)  # ZONE_1
        row = _surface_row(shape, phpp_v10, ComponentFaceType.WALL, zone_exposure)
        assert row.phpp_group_number == "12-"


# ===========================================================================
# Group 3: Edge cases
# ===========================================================================


class TestEdgeCases:
    def test_unknown_face_type_returns_12(self, shape, phpp_v10):
        """Fallback for unrecognized face types should be custom group 12."""
        row = _surface_row(shape, phpp_v10, ComponentFaceType.CUSTOM, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number == "12-"

    def test_floor_adiabatic_returns_18(self, shape, phpp_v10):
        """SURFACE exposure takes priority over face_type — always group 18."""
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.SURFACE)
        assert row.phpp_group_number == "18-"

    def test_roof_zone_n_returns_10(self, shape, phpp_v10):
        """Roof over unconditioned zone — treat as ambient (group 10) since roof ZONE_N is rare."""
        zone_exposure = ComponentExposureExterior(2)  # ZONE_2
        row = _surface_row(shape, phpp_v10, ComponentFaceType.ROOF_CEILING, zone_exposure)
        assert row.phpp_group_number == "10-"


# ===========================================================================
# Group 4: PHPP version formatting
# ===========================================================================


class TestGroupNumberInt:
    """Tests for the phpp_group_number_int property (raw integer, no formatting)."""

    def test_floor_ground_returns_11(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.GROUND)
        assert row.phpp_group_number_int == 11

    def test_floor_exterior_returns_12(self, shape, phpp_v10):
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number_int == 12

    def test_floor_zone_n_returns_13(self, shape, phpp_v10):
        zone_exposure = ComponentExposureExterior(1)
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, zone_exposure)
        assert row.phpp_group_number_int == 13

    def test_int_is_version_independent(self, shape, phpp_v9):
        """phpp_group_number_int should return the same int regardless of PHPP version."""
        row = _surface_row(shape, phpp_v9, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number_int == 12


# ===========================================================================
# Group 5: PHPP version formatting
# ===========================================================================


class TestVersionFormatting:
    def test_v9_format_no_dash(self, shape, phpp_v9):
        """PHPP v9 uses bare numbers: '11' not '11-'."""
        row = _surface_row(shape, phpp_v9, ComponentFaceType.FLOOR, ComponentExposureExterior.GROUND)
        assert row.phpp_group_number == "11"

    def test_v10_format_has_dash(self, shape, phpp_v10):
        """PHPP v10 appends a dash: '11-'."""
        row = _surface_row(shape, phpp_v10, ComponentFaceType.FLOOR, ComponentExposureExterior.GROUND)
        assert row.phpp_group_number == "11-"

    def test_v9_floor_exterior_no_dash(self, shape, phpp_v9):
        """v9 format for the new group 12 should also be bare: '12'."""
        row = _surface_row(shape, phpp_v9, ComponentFaceType.FLOOR, ComponentExposureExterior.EXTERIOR)
        assert row.phpp_group_number == "12"
