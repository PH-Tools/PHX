import pytest
from honeybee.model import Model
from honeybee.room import Room
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass

from PHX.from_HBJSON.create_assemblies import (
    _collapse_declared_u_sandwich,
    build_layer_from_hb_material,
    build_opaque_assemblies_from_HB_model,
)
from PHX.model.project import PhxProject

DECLARED_U = 0.150
R_SI = 0.13
R_SE = 0.04
R_NO_MASS = 1 / DECLARED_U - R_SI - R_SE
DECLARED_THICKNESS_MM = 305.0


def _shell(_identifier: str = "phn_declared_shell") -> EnergyMaterial:
    """A Declared-U sandwich shell: 10mm of a 100 W/mK material."""
    return EnergyMaterial(_identifier, 0.01, 100.0, 2500.0, 460.0, "Rough", 0.9, 0.7, 0.7)


def _declared_no_mass(_marker=DECLARED_THICKNESS_MM) -> EnergyMaterialNoMass:
    """The no-mass core of a Declared-U sandwich, marked with the declared thickness."""
    material = EnergyMaterialNoMass("phn_A1_declared", R_NO_MASS, "Rough", 0.9, 0.7, 0.7)
    if _marker is not None:
        material.properties.ph.user_data["phn_declared_u"] = {
            "u_w_m2k": DECLARED_U,
            "thickness_mm": _marker,
            "r_in": R_SI,
            "r_out": R_SE,
            "r_no_mass": R_NO_MASS,
        }
    return material


def test_marked_no_mass_material_uses_the_declared_thickness():
    layer = build_layer_from_hb_material(_declared_no_mass())

    assert layer.thickness_m == pytest.approx(0.305)
    # -- The R-Value comes from the material, not the marker, so it survives the new thickness
    assert layer.layer_resistance == pytest.approx(R_NO_MASS)


def test_unmarked_no_mass_material_keeps_the_default_thickness():
    layer = build_layer_from_hb_material(EnergyMaterialNoMass("Air Gap", R_NO_MASS, "Rough", 0.9, 0.7, 0.7))

    assert layer.thickness_m == pytest.approx(0.1)
    assert layer.layer_resistance == pytest.approx(R_NO_MASS)


@pytest.mark.parametrize("thickness_mm", [None, 0, -5, "not-a-number"])
def test_unusable_declared_thickness_falls_back_to_the_default(thickness_mm):
    layer = build_layer_from_hb_material(_declared_no_mass(thickness_mm))

    assert layer.thickness_m == pytest.approx(0.1)
    assert layer.layer_resistance == pytest.approx(R_NO_MASS)


def test_declared_thickness_accepts_a_numeric_string():
    layer = build_layer_from_hb_material(_declared_no_mass("305"))

    assert layer.thickness_m == pytest.approx(0.305)


def test_a_non_dict_marker_falls_back_to_the_default():
    material = EnergyMaterialNoMass("phn_A1_declared", R_NO_MASS, "Rough", 0.9, 0.7, 0.7)
    material.properties.ph.user_data["phn_declared_u"] = "not-a-dict"

    assert build_layer_from_hb_material(material).thickness_m == pytest.approx(0.1)


def test_a_marked_sandwich_collapses_to_its_no_mass_material():
    core = _declared_no_mass()

    collapsed = _collapse_declared_u_sandwich([_shell(), core, _shell()])

    assert collapsed == [core]


def test_collapsing_preserves_the_declared_u_value():
    sandwich = [_shell(), _declared_no_mass(), _shell()]

    uncollapsed_r = sum(build_layer_from_hb_material(m).layer_resistance for m in sandwich)
    collapsed_r = sum(build_layer_from_hb_material(m).layer_resistance for m in _collapse_declared_u_sandwich(sandwich))

    # -- The two shells are all that is dropped: 2 * 0.01m / 100 W/mK
    assert uncollapsed_r - collapsed_r == pytest.approx(0.0002)
    # -- Re-applying the films the upstream stripped returns the declared U-Value
    assert 1 / (collapsed_r + R_SI + R_SE) == pytest.approx(DECLARED_U)


def test_an_unmarked_mass_sandwich_is_not_collapsed():
    """The Grasshopper 'Create SD Constructions' shape has no marker, so it stays as-is."""
    sandwich = [
        _shell("MAT_Mass"),
        EnergyMaterialNoMass("MAT_SD", R_NO_MASS, "Rough", 0.9, 0.7, 0.7),
        _shell("MAT_Mass"),
    ]

    assert _collapse_declared_u_sandwich(sandwich) == sandwich


@pytest.mark.parametrize(
    "materials",
    [
        pytest.param([_shell(), _declared_no_mass()], id="only_one_shell"),
        pytest.param([_shell(), _declared_no_mass(), _shell(), _shell()], id="too_many_layers"),
        pytest.param(
            [_shell(), _declared_no_mass(), EnergyMaterial("Gypsum", 0.0127, 0.16, 640.0, 1150.0)],
            id="inner_is_not_a_shell",
        ),
        pytest.param([_shell(), _declared_no_mass(), _shell("other_shell")], id="shells_disagree"),
    ],
)
def test_a_shape_that_is_not_an_exact_sandwich_is_not_collapsed(materials):
    assert _collapse_declared_u_sandwich(materials) == materials


def _build_assembly(_construction: OpaqueConstruction):
    """Convert a one-room model whose every face carries the Construction, and return the PHX-Assembly."""
    room = Room.from_box("test_room", 5, 5, 3)
    for face in room.faces:
        face.properties.energy.construction = _construction

    phx_project = PhxProject()
    build_opaque_assemblies_from_HB_model(phx_project, Model("test_model", [room]))

    return phx_project.assembly_types[_construction.identifier]


def test_a_declared_u_assembly_converts_to_one_phx_layer(reset_class_counters):
    construction = OpaqueConstruction("phn_A1", [_shell(), _declared_no_mass(), _shell()])
    construction.display_name = "Declared-U Wall"

    phx_assembly = _build_assembly(construction)

    assert len(phx_assembly.layers) == 1
    assert phx_assembly.layers[0].thickness_m == pytest.approx(0.305)
    assert 1 / (phx_assembly.r_value + R_SI + R_SE) == pytest.approx(DECLARED_U)


def test_radiation_properties_come_from_the_no_mass_material_after_collapse(reset_class_counters):
    core = _declared_no_mass()
    core.unlock()
    core.solar_absorptance = 0.35
    core.thermal_absorptance = 0.82

    phx_assembly = _build_assembly(OpaqueConstruction("phn_A2", [_shell(), core, _shell()]))

    assert phx_assembly.exterior_solar_absorptance == pytest.approx(0.35)
    assert phx_assembly.exterior_thermal_emissivity == pytest.approx(0.82)
