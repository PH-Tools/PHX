from PHX.model.components import PhxApertureElement, PhxComponentAperture, PhxComponentOpaque
from PHX.model.project import PhxProject

# Note: Can't check Shading Factors when reading in a WUFI-XML file.


def _aperture_elements_are_equal(_xml_el: PhxApertureElement, _hbjson_el: PhxApertureElement) -> bool:
    """Don't check the Shading Factors when reading from WUFI XML."""

    if _xml_el.polygons_are_equivalent(_hbjson_el):
        return True
    else:
        return False


def _apertures_are_equal(_xml_ap: PhxComponentAperture, _hbjson_ap: PhxComponentAperture) -> bool:
    """Custom Aperture Equality Checker. Can't check shading factors when reading from WUFI XML."""

    if _xml_ap.display_name == _hbjson_ap.display_name:
        assert _xml_ap.face_type == _hbjson_ap.face_type
        assert _xml_ap.face_opacity == _hbjson_ap.face_opacity
        assert _xml_ap.color_interior == _hbjson_ap.color_interior
        assert _xml_ap.color_exterior == _hbjson_ap.color_exterior
        assert _xml_ap.exposure_exterior == _hbjson_ap.exposure_exterior
        assert _xml_ap.exposure_interior == _hbjson_ap.exposure_interior
        assert _xml_ap.interior_attachment_id == _hbjson_ap.interior_attachment_id
        assert _xml_ap.window_type_id_num == _hbjson_ap.window_type_id_num
        assert _xml_ap.variant_type_name == _hbjson_ap.variant_type_name
        assert abs(_xml_ap.install_depth - _hbjson_ap.install_depth) < 0.001
        assert (
            abs(
                _xml_ap.default_monthly_shading_correction_factor - _hbjson_ap.default_monthly_shading_correction_factor
            )
            < 0.001
        )

        # -- check the Aperture Elements
        assert len(_xml_ap.elements) == len(_hbjson_ap.elements)
        for xml_ap_element in _xml_ap.elements:
            assert any(
                (
                    _aperture_elements_are_equal(xml_ap_element, hbjson_ap_element)
                    for hbjson_ap_element in _hbjson_ap.elements
                )
            )

        # -- check the Aperture Polygons
        assert len(_xml_ap.polygons) == len(_hbjson_ap.polygons)
        for this_poly in _xml_ap.polygons:
            assert any((this_poly == other_poly for other_poly in _hbjson_ap.polygons))

        return True
    else:
        return False


def _components_are_equal(_xml_compo: PhxComponentOpaque, _hbjson_compo: PhxComponentOpaque) -> bool:
    """Custom Component Equality Checker. Can't check shading factors when reading from WUFI XML."""

    if _xml_compo.display_name == _hbjson_compo.display_name:
        assert _xml_compo.face_type == _hbjson_compo.face_type
        assert _xml_compo.face_opacity == _hbjson_compo.face_opacity
        assert _xml_compo.color_interior == _hbjson_compo.color_interior
        assert _xml_compo.color_exterior == _hbjson_compo.color_exterior
        assert _xml_compo.exposure_exterior == _hbjson_compo.exposure_exterior
        assert _xml_compo.exposure_interior == _hbjson_compo.exposure_interior
        assert _xml_compo.interior_attachment_id == _hbjson_compo.interior_attachment_id
        assert _xml_compo.assembly_type_id_num == _hbjson_compo.assembly_type_id_num

        # -- check the Component Apertures
        assert len(_xml_compo.apertures) == len(_hbjson_compo.apertures)
        for xml_ap in _xml_compo.apertures:
            assert any((_apertures_are_equal(xml_ap, hbjson_ap) for hbjson_ap in _hbjson_compo.apertures))

        # -- check the Component Polygons
        assert len(_xml_compo.polygons) == len(_hbjson_compo.polygons)
        for this_poly in _xml_compo.polygons:
            assert any((this_poly == other_poly for other_poly in _hbjson_compo.polygons))

        return True
    else:
        return False


def test_building_all_components_are_equal(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    TOLERANCE = 0.01

    # -- Pull out the Variants
    variants_hbjson = phx_project_from_hbjson.variants
    variants_xml = phx_project_from_wufi_xml.variants

    assert len(variants_hbjson) == len(variants_xml)

    for var_hbjson, var_xml in zip(variants_hbjson, variants_xml):
        hbjson_all_compos = var_hbjson.building.opaque_components
        xml_all_compos = var_xml.building.opaque_components

        # -- Ensure each starting component is in the new list
        for hbjson_component in hbjson_all_compos:
            # -- This checks: the component, the assembly, and the geometry
            # -- Note that when reading in from WUFI, aperture elements will NOT include any
            # -- shading factors, so we can't check those here. Use a custom equal checker instead
            assert any((_components_are_equal(xml_component, hbjson_component) for xml_component in xml_all_compos))
