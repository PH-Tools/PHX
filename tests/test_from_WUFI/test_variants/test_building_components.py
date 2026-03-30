from PHX.model.components import PhxApertureElement, PhxComponentAperture, PhxComponentOpaque
from PHX.model.project import PhxProject

# Note: Can't check Shading Factors when reading in a WUFI-XML file.


def _label_component(_component: PhxComponentOpaque) -> str:
    return (
        f"name={_component.display_name!r}, face_type={_component.face_type!r}, "
        f"assembly_id={_component.assembly_type_id_num!r}, apertures={len(_component.apertures)}, "
        f"polygons={len(_component.polygons)}"
    )


def _label_aperture(_aperture: PhxComponentAperture) -> str:
    return (
        f"name={_aperture.display_name!r}, face_type={_aperture.face_type!r}, "
        f"window_type_id={_aperture.window_type_id_num!r}, elements={len(_aperture.elements)}, "
        f"polygons={len(_aperture.polygons)}"
    )


def _describe_polygon(_polygon: object) -> str:
    return repr(_polygon)


def _compare_scalar(_field_name: str, _xml_value: object, _hbjson_value: object) -> str | None:
    if _xml_value != _hbjson_value:
        return f"{_field_name} mismatch: xml={_xml_value!r}, hbjson={_hbjson_value!r}"
    return None


def _compare_float(_field_name: str, _xml_value: float, _hbjson_value: float, _tolerance: float = 0.001) -> str | None:
    if abs(_xml_value - _hbjson_value) >= _tolerance:
        return f"{_field_name} mismatch: xml={_xml_value!r}, hbjson={_hbjson_value!r}, tol={_tolerance}"
    return None


def _aperture_elements_diff(_xml_el: PhxApertureElement, _hbjson_el: PhxApertureElement) -> str | None:
    """Don't check the Shading Factors when reading from WUFI XML."""

    if _xml_el.polygons_are_equivalent(_hbjson_el):
        return None

    return f"aperture element polygons differ: xml={_xml_el!r}, hbjson={_hbjson_el!r}"


def _aperture_elements_are_equal(_xml_el: PhxApertureElement, _hbjson_el: PhxApertureElement) -> bool:
    """Don't check the Shading Factors when reading from WUFI XML."""

    return _aperture_elements_diff(_xml_el, _hbjson_el) is None


def _apertures_diff(_xml_ap: PhxComponentAperture, _hbjson_ap: PhxComponentAperture) -> str | None:
    """Custom Aperture Equality Checker. Can't check shading factors when reading from WUFI XML."""

    try:
        for field_name, xml_value, hbjson_value in (
            ("display_name", _xml_ap.display_name, _hbjson_ap.display_name),
            ("face_type", _xml_ap.face_type, _hbjson_ap.face_type),
            ("face_opacity", _xml_ap.face_opacity, _hbjson_ap.face_opacity),
            ("color_interior", _xml_ap.color_interior, _hbjson_ap.color_interior),
            ("color_exterior", _xml_ap.color_exterior, _hbjson_ap.color_exterior),
            ("exposure_exterior", _xml_ap.exposure_exterior, _hbjson_ap.exposure_exterior),
            ("exposure_interior", _xml_ap.exposure_interior, _hbjson_ap.exposure_interior),
            ("interior_attachment_id", _xml_ap.interior_attachment_id, _hbjson_ap.interior_attachment_id),
            ("window_type_id_num", _xml_ap.window_type_id_num, _hbjson_ap.window_type_id_num),
            ("variant_type_name", _xml_ap.variant_type_name, _hbjson_ap.variant_type_name),
        ):
            mismatch = _compare_scalar(field_name, xml_value, hbjson_value)
            if mismatch:
                return mismatch

        for field_name, xml_value, hbjson_value in (
            ("install_depth", _xml_ap.install_depth, _hbjson_ap.install_depth),
            (
                "default_monthly_shading_correction_factor",
                _xml_ap.default_monthly_shading_correction_factor,
                _hbjson_ap.default_monthly_shading_correction_factor,
            ),
        ):
            mismatch = _compare_float(field_name, xml_value, hbjson_value)
            if mismatch:
                return mismatch

        if len(_xml_ap.elements) != len(_hbjson_ap.elements):
            return (
                "elements length mismatch: "
                f"xml={len(_xml_ap.elements)}, hbjson={len(_hbjson_ap.elements)}"
            )
        for xml_ap_element in _xml_ap.elements:
            element_diffs = [
                _aperture_elements_diff(xml_ap_element, hbjson_ap_element) for hbjson_ap_element in _hbjson_ap.elements
            ]
            if all(element_diff is not None for element_diff in element_diffs):
                return (
                    "no matching aperture element found for "
                    f"xml element {xml_ap_element!r}; candidate diffs={element_diffs}"
                )

        if len(_xml_ap.polygons) != len(_hbjson_ap.polygons):
            return (
                "polygon length mismatch: "
                f"xml={len(_xml_ap.polygons)}, hbjson={len(_hbjson_ap.polygons)}"
            )
        for this_poly in _xml_ap.polygons:
            if not any(this_poly == other_poly for other_poly in _hbjson_ap.polygons):
                return (
                    "unmatched aperture polygon: "
                    f"xml={_describe_polygon(this_poly)}, "
                    f"hbjson_candidates={[ _describe_polygon(other_poly) for other_poly in _hbjson_ap.polygons ]}"
                )

        return None
    except Exception as exc:
        return f"unexpected exception: {type(exc).__name__}: {exc}"


def _apertures_are_equal(_xml_ap: PhxComponentAperture, _hbjson_ap: PhxComponentAperture) -> bool:
    """Custom Aperture Equality Checker. Can't check shading factors when reading from WUFI XML."""

    return _apertures_diff(_xml_ap, _hbjson_ap) is None


def _components_diff(_xml_compo: PhxComponentOpaque, _hbjson_compo: PhxComponentOpaque) -> str | None:
    """Custom Component Equality Checker. Can't check shading factors when reading from WUFI XML."""

    try:
        for field_name, xml_value, hbjson_value in (
            ("display_name", _xml_compo.display_name, _hbjson_compo.display_name),
            ("face_type", _xml_compo.face_type, _hbjson_compo.face_type),
            ("face_opacity", _xml_compo.face_opacity, _hbjson_compo.face_opacity),
            ("color_interior", _xml_compo.color_interior, _hbjson_compo.color_interior),
            ("color_exterior", _xml_compo.color_exterior, _hbjson_compo.color_exterior),
            ("exposure_exterior", _xml_compo.exposure_exterior, _hbjson_compo.exposure_exterior),
            ("exposure_interior", _xml_compo.exposure_interior, _hbjson_compo.exposure_interior),
            (
                "interior_attachment_id",
                _xml_compo.interior_attachment_id,
                _hbjson_compo.interior_attachment_id,
            ),
            ("assembly_type_id_num", _xml_compo.assembly_type_id_num, _hbjson_compo.assembly_type_id_num),
        ):
            mismatch = _compare_scalar(field_name, xml_value, hbjson_value)
            if mismatch:
                return mismatch

        if len(_xml_compo.apertures) != len(_hbjson_compo.apertures):
            return (
                "aperture length mismatch: "
                f"xml={len(_xml_compo.apertures)}, hbjson={len(_hbjson_compo.apertures)}"
            )
        for xml_ap in _xml_compo.apertures:
            aperture_diffs = [_apertures_diff(xml_ap, hbjson_ap) for hbjson_ap in _hbjson_compo.apertures]
            if all(aperture_diff is not None for aperture_diff in aperture_diffs):
                return (
                    f"no matching aperture found for xml aperture [{_label_aperture(xml_ap)}]; "
                    f"candidate diffs={aperture_diffs}"
                )

        if len(_xml_compo.polygons) != len(_hbjson_compo.polygons):
            return (
                "polygon length mismatch: "
                f"xml={len(_xml_compo.polygons)}, hbjson={len(_hbjson_compo.polygons)}"
            )
        for this_poly in _xml_compo.polygons:
            if not any(this_poly == other_poly for other_poly in _hbjson_compo.polygons):
                return (
                    "unmatched component polygon: "
                    f"xml={_describe_polygon(this_poly)}, "
                    f"hbjson_candidates={[ _describe_polygon(other_poly) for other_poly in _hbjson_compo.polygons ]}"
                )

        return None
    except Exception as exc:
        return f"unexpected exception: {type(exc).__name__}: {exc}"


def _components_are_equal(_xml_compo: PhxComponentOpaque, _hbjson_compo: PhxComponentOpaque) -> bool:
    """Custom Component Equality Checker. Can't check shading factors when reading from WUFI XML."""

    return _components_diff(_xml_compo, _hbjson_compo) is None


def test_building_all_components_are_equal(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:

    # -- Pull out the Variants
    variants_hbjson = phx_project_from_hbjson.variants
    variants_xml = phx_project_from_wufi_xml.variants

    assert len(variants_hbjson) == len(variants_xml)

    for var_hbjson, var_xml in zip(variants_hbjson, variants_xml, strict=False):
        hbjson_all_compos = var_hbjson.building.opaque_components
        xml_all_compos = var_xml.building.opaque_components

        # -- Ensure each starting component is in the new list
        for hbjson_component in hbjson_all_compos:
            component_diffs: list[str] = []

            # -- This checks: the component, the assembly, and the geometry
            # -- Note that when reading in from WUFI, aperture elements will NOT include any
            # -- shading factors, so we can't check those here. Use a custom equal checker instead
            for xml_component in xml_all_compos:
                component_diff = _components_diff(xml_component, hbjson_component)
                if component_diff is None:
                    break

                component_diffs.append(
                    f"candidate xml component [{_label_component(xml_component)}] -> {component_diff}"
                )
            else:
                print(f"FAILED HBJSON component: [{_label_component(hbjson_component)}]")
                for component_diff in component_diffs:
                    print(component_diff)

                raise AssertionError(
                    f"No XML component matched HBJSON component [{_label_component(hbjson_component)}]. "
                    f"Candidate mismatches: {component_diffs}"
                )
