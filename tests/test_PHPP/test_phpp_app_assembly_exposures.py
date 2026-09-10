# -*- Python Version: 3.10 -*-

"""Tests for PHPPConnection._rank_assembly_exposures()

PHPP allows one surface-resistance selector pair per assembly block, so an Assembly
used at more than one exposure has to be resolved down to a single pair before it can
be written.

See: https://github.com/PH-Tools/PHX/issues/118
"""

from PHX.model import components, geometry, project
from PHX.model.constructions import PhxConstructionOpaque
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_app import PHPPConnection

WALL_EXTERIOR = (ComponentFaceType.WALL, ComponentExposureExterior.EXTERIOR)
ROOF_EXTERIOR = (ComponentFaceType.ROOF_CEILING, ComponentExposureExterior.EXTERIOR)


def _make_polygon(_area: float) -> geometry.PhxPolygon:
    return geometry.PhxPolygon(
        "test_polygon",
        _area,
        geometry.PhxVertix(0, 0, 0),
        geometry.PhxVector(0, 0, 1),
        geometry.PhxPlane(
            geometry.PhxVector(0, 0, 1),
            geometry.PhxVertix(0, 0, 0),
            geometry.PhxVector(1, 0, 0),
            geometry.PhxVector(0, 1, 0),
        ),
    )


def _make_project(
    _assembly: PhxConstructionOpaque,
    *_uses: tuple[ComponentFaceType, ComponentExposureExterior, float],
) -> project.PhxProject:
    """Return a PhxProject with one variant holding one Component per (face-type, exposure, area)."""
    phx_project = project.PhxProject()
    phx_project.add_assembly_type(_assembly)

    phx_variant = project.PhxVariant()
    for i, (face_type, exposure, area) in enumerate(_uses):
        component = components.PhxComponentOpaque()
        component.display_name = f"component_{i}"
        component.face_type = face_type
        component.exposure_exterior = exposure
        component.add_polygons(_make_polygon(area))
        component.set_assembly_type(_assembly)
        phx_variant.building.add_components(component)
    phx_project.add_new_variant(phx_variant)

    return phx_project


def test_an_assembly_used_at_one_exposure_resolves_to_that_exposure() -> None:
    assembly = PhxConstructionOpaque()
    phx_project = _make_project(assembly, (*ROOF_EXTERIOR, 50.0))

    assert PHPPConnection._rank_assembly_exposures(phx_project) == {assembly.id_num: [ROOF_EXTERIOR]}


def test_an_assembly_used_at_two_exposures_ranks_the_larger_area_first() -> None:
    assembly = PhxConstructionOpaque()
    phx_project = _make_project(assembly, (*WALL_EXTERIOR, 10.0), (*ROOF_EXTERIOR, 90.0))

    assert PHPPConnection._rank_assembly_exposures(phx_project) == {assembly.id_num: [ROOF_EXTERIOR, WALL_EXTERIOR]}


def test_areas_accumulate_across_components_sharing_an_exposure() -> None:
    assembly = PhxConstructionOpaque()
    phx_project = _make_project(assembly, (*WALL_EXTERIOR, 60.0), (*ROOF_EXTERIOR, 90.0), (*WALL_EXTERIOR, 60.0))

    assert PHPPConnection._rank_assembly_exposures(phx_project) == {assembly.id_num: [WALL_EXTERIOR, ROOF_EXTERIOR]}


def test_an_assembly_no_component_references_is_absent_from_the_ranking() -> None:
    assembly = PhxConstructionOpaque()
    phx_project = _make_project(assembly)

    assert PHPPConnection._rank_assembly_exposures(phx_project) == {}
