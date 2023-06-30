from PHX.model.project import PhxProject


def test_building_all_components_are_equal(
    project_from_hbjson: PhxProject,
    project_from_wufi_xml: PhxProject,
) -> None:
    TOLERANCE = 0.01

    # -- Pull out the Variants
    variants_hbjson = project_from_hbjson.variants
    variants_xml = project_from_wufi_xml.variants

    assert len(variants_hbjson) == len(variants_xml)

    for var_hbjson, var_xml in zip(variants_hbjson, variants_xml):
        b1_all_compos = var_hbjson.building.opaque_components
        b2_all_compos = var_xml.building.opaque_components

        # -- Ensure each starting component is in the new list
        for compo in b1_all_compos:
            # -- This checks, the component, the assembly, and the geometry
            assert any((c == compo for c in b2_all_compos))
