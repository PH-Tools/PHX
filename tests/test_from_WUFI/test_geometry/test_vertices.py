from PHX.model.project import PhxProject, PhxVariant


def _total_num_vertices(variant: PhxVariant) -> int:
    """Calculate the total number of vertices in a variant."""
    return len(
        [
            v for c in variant.building.all_components 
            for p in c.polygons 
            for v in p.vertices
        ]
    )

def test_building_has_same_number_of_vertices(
    create_phx_project_from_hbjson: PhxProject,
    create_phx_project_from_wufi_xml: PhxProject,
) -> None:
    for hbjson_variant, wufi_xml_variant in zip(
        create_phx_project_from_hbjson.variants,
        create_phx_project_from_wufi_xml.variants,
    ):
        num_hbjson_vertices = _total_num_vertices(hbjson_variant)
        num_xml_vertices = _total_num_vertices(wufi_xml_variant)
        assert num_hbjson_vertices == num_xml_vertices
