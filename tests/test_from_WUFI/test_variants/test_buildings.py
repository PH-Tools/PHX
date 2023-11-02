from PHX.model.project import PhxProject


def test_variant_buildings(
    create_phx_project_from_hbjson: PhxProject,
    create_phx_project_from_wufi_xml: PhxProject,
) -> None:
    TOLERANCE = 0.01

    # -- Pull out the Project Data
    variants_hbjson = create_phx_project_from_hbjson.variants
    variants_xml = create_phx_project_from_wufi_xml.variants

    assert len(variants_hbjson) == len(variants_xml)

    for var_hbjson, var_xml in zip(variants_hbjson, variants_xml):
        b1 = var_hbjson.building
        b2 = var_xml.building

        assert abs(b1.weighted_net_floor_area - b2.weighted_net_floor_area) < TOLERANCE
        assert abs(b1.net_volume - b2.net_volume) < TOLERANCE

        assert len(b1.all_components) == len(b2.all_components)
        assert len(b1.aperture_components) == len(b2.aperture_components)
        assert len(b1.opaque_components) == len(b2.opaque_components)
        assert len(b1.shading_components) == len(b2.shading_components)
        assert len(b1.polygon_ids) == len(b2.polygon_ids)
        assert len(b1.polygons) == len(b2.polygons)
        assert len(b1.zones) == len(b2.zones)
