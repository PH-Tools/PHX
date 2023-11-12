from PHX.model.project import PhxProject


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
        for hbjson_compo in hbjson_all_compos:
            # -- This checks: the component, the assembly, and the geometry
            assert any((xml_c == hbjson_compo for xml_c in xml_all_compos))
