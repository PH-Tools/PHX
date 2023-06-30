from PHX.model.project import PhxProject


def test_project_variants(
    project_from_hbjson: PhxProject,
    project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Project Data
    variants_hbjson = project_from_hbjson.variants
    variants_xml = project_from_wufi_xml.variants

    assert len(variants_hbjson) == len(variants_xml)

    for var_hbjson, var_xml in zip(variants_hbjson, variants_xml):
        assert var_hbjson.name == var_xml.name
        assert var_hbjson.remarks == var_xml.remarks
        assert var_hbjson.plugin == var_xml.plugin
        assert var_hbjson.phius_cert == var_xml.phius_cert
        assert var_hbjson.site == var_xml.site
        # assert var_hbjson.building == var_xml.building
        # assert var_hbjson.mech_systems == var_xml.mech_systems
