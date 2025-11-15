from PHX.model.project import PhxProject, PhxVariant


def _total_num_polygons(variant: PhxVariant) -> int:
    """Calculate the total number of Polygons in a variant."""
    return len([p for c in variant.building.all_components for p in c.polygons])


def test_building_has_same_number_of_polygons(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    for hbjson_variant, wufi_xml_variant in zip(
        phx_project_from_hbjson.variants,
        phx_project_from_wufi_xml.variants,
        strict=False,
    ):
        num_hbjson_polygons = _total_num_polygons(hbjson_variant)
        num_xml_polygons = _total_num_polygons(wufi_xml_variant)
        assert num_hbjson_polygons == num_xml_polygons
