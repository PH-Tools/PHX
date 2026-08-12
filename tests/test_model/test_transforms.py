# -*- Python Version: 3.10 -*-

"""Tests for PHX.model.transforms.synthesize_window_type_psi_variants."""

import pytest

from PHX.model import components, constructions, project
from PHX.model.transforms import synthesize_window_type_psi_variants


def _build_project_with_apertures(psi_tuples: list[tuple[float, float, float, float] | None]):
    """Build a PhxProject with one window type and one aperture per input psi tuple.

    A tuple of (top, right, bottom, left) sets that aperture element's resolved psi;
    None leaves the element inheriting the window-type's values (0.04 all around).
    """
    phx_project = project.PhxProject()

    window_type = constructions.PhxConstructionWindow()
    window_type.display_name = "Type-A1"
    window_type.identifier = "Type-A1"
    window_type.set_all_frames_psi_install(0.04)
    window_type.u_value_window = 1.0
    phx_project.add_new_window_type(window_type)

    phx_variant = project.PhxVariant()
    phx_project.add_new_variant(phx_variant)

    host_component = components.PhxComponentOpaque()
    phx_variant.building.add_components(host_component)

    apertures = []
    for psi_tuple in psi_tuples:
        aperture = components.PhxComponentAperture(_host=host_component)
        aperture.window_type = window_type
        element = components.PhxApertureElement(_host=aperture)
        if psi_tuple is not None:
            element.install_psi = components.PhxApertureElementPsiInstall(*psi_tuple)
        aperture.add_element(element)
        host_component.add_aperture(aperture)
        apertures.append(aperture)

    return phx_project, window_type, apertures


def test_no_overrides_is_a_no_op(reset_class_counters) -> None:
    phx_project, window_type, apertures = _build_project_with_apertures([None, None])

    synthesize_window_type_psi_variants(phx_project)

    assert len(phx_project.window_types) == 1
    assert all(ap.window_type is window_type for ap in apertures)


def test_explicit_values_equal_to_type_is_a_no_op(reset_class_counters) -> None:
    phx_project, window_type, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.04)])

    synthesize_window_type_psi_variants(phx_project)

    assert len(phx_project.window_types) == 1
    assert apertures[0].window_type is window_type


def test_override_creates_one_content_keyed_variant(reset_class_counters) -> None:
    phx_project, window_type, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])

    synthesize_window_type_psi_variants(phx_project)

    assert len(phx_project.window_types) == 2
    variant_type = apertures[0].window_type
    assert variant_type is not window_type
    assert variant_type.identifier.startswith("Type-A1__psi-")
    assert variant_type.frame_left.psi_install == 0.0
    assert variant_type.frame_top.psi_install == 0.04
    assert "Psi-i" in variant_type.display_name
    # -- the base type is never mutated
    assert window_type.frame_left.psi_install == 0.04
    # -- distinct id_num, resolvable through the project dict
    assert variant_type.id_num != window_type.id_num
    assert phx_project.window_types[variant_type.identifier] is variant_type


def test_count_invariant_m_plus_k(reset_class_counters) -> None:
    """M base types + K distinct non-default tuples -> exactly M + K window types."""
    phx_project, _, apertures = _build_project_with_apertures(
        [
            None,  # default
            (0.04, 0.04, 0.04, 0.0),  # tuple X
            (0.04, 0.04, 0.04, 0.0),  # tuple X again (same variant!)
            (0.10, 0.10, 0.10, 0.10),  # tuple Y
        ]
    )

    synthesize_window_type_psi_variants(phx_project)

    # -- 1 base + 2 distinct tuples = 3 types
    assert len(phx_project.window_types) == 3
    # -- apertures sharing a tuple share one variant object
    assert apertures[1].window_type is apertures[2].window_type
    assert apertures[1].window_type is not apertures[3].window_type


def test_determinism_across_runs(reset_class_counters) -> None:
    def _run() -> list[str]:
        components.PhxComponentBase._count = 0
        constructions.PhxConstructionWindow._count = 0
        phx_project, _, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0), (0.10, 0.10, 0.10, 0.10)])
        synthesize_window_type_psi_variants(phx_project)
        return sorted(phx_project.window_types.keys()) + [str(ap.window_type.id_num) for ap in apertures]

    assert _run() == _run()


def test_idempotent(reset_class_counters) -> None:
    phx_project, _, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])

    synthesize_window_type_psi_variants(phx_project)
    types_after_first = dict(phx_project.window_types)
    variant_after_first = apertures[0].window_type

    synthesize_window_type_psi_variants(phx_project)
    assert phx_project.window_types == types_after_first
    assert apertures[0].window_type is variant_after_first


def test_variant_u_value_window_is_adjusted_by_psi_delta(reset_class_counters) -> None:
    """u_value_window shifts by sum(delta_psi * std-window edge length) / std-window area."""
    phx_project, window_type, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])

    synthesize_window_type_psi_variants(phx_project)

    variant_type = apertures[0].window_type
    # -- left edge: delta = (0.0 - 0.04), edge length = 1.48m, area = 1.23 * 1.48
    expected = 1.0 + (0.0 - 0.04) * 1.48 / (1.23 * 1.48)
    assert variant_type.u_value_window == pytest.approx(expected)
    assert window_type.u_value_window == pytest.approx(1.0)


def test_heterogeneous_elements_raise(reset_class_counters) -> None:
    phx_project, _, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])
    extra_element = components.PhxApertureElement(_host=apertures[0])
    extra_element.install_psi = components.PhxApertureElementPsiInstall(0.1, 0.1, 0.1, 0.1)
    apertures[0].add_element(extra_element)

    with pytest.raises(ValueError):
        synthesize_window_type_psi_variants(phx_project)


def test_wufi_xml_builder_runs_the_transform(reset_class_counters) -> None:
    """generate_WUFI_XML_from_object on a PhxProject synthesizes variants automatically."""
    from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object

    phx_project, _, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])
    xml_text = generate_WUFI_XML_from_object(phx_project)

    assert len(phx_project.window_types) == 2
    variant_type = apertures[0].window_type
    assert f"<IdentNrWindowType>{variant_type.id_num}</IdentNrWindowType>" in xml_text
    assert '<WindowTypes count="2">' in xml_text


def test_transform_marks_the_project(reset_class_counters) -> None:
    """A project with synthesized variants is marked; no-op projects are not."""
    phx_project_noop, _, _ = _build_project_with_apertures([None])
    synthesize_window_type_psi_variants(phx_project_noop)
    assert not getattr(phx_project_noop, "_window_type_psi_variants_synthesized", False)

    phx_project, _, _ = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])
    synthesize_window_type_psi_variants(phx_project)
    assert phx_project._window_type_psi_variants_synthesized is True


def test_metr_builder_runs_the_transform(reset_class_counters) -> None:
    """generate_metr_json_dict on a PhxProject synthesizes variants automatically."""
    from PHX.to_METr_JSON.metr_builder import generate_metr_json_dict

    phx_project, _, apertures = _build_project_with_apertures([(0.04, 0.04, 0.04, 0.0)])
    generate_metr_json_dict(phx_project)

    assert len(phx_project.window_types) == 2
