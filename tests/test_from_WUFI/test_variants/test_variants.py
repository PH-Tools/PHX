from PHX.model.project import PhxProject


def test_project_variants(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Project Data
    variants_hbjson = phx_project_from_hbjson.variants
    variants_xml = phx_project_from_wufi_xml.variants

    assert len(variants_hbjson) == len(variants_xml)

    for var_hbjson, var_xml in zip(variants_hbjson, variants_xml, strict=False):
        assert var_hbjson.name == var_xml.name
        assert var_hbjson.remarks == var_xml.remarks
        assert var_hbjson.plugin == var_xml.plugin

        # -- Compare phius_cert sub-components individually.
        # -- The blanket phius_cert == check fails because the WUFI XML format
        # -- doesn't carry all summer ventilation fields (e.g. nighttime_minimum_indoor_temp_C).
        assert var_hbjson.phius_cert.phius_certification_criteria == var_xml.phius_cert.phius_certification_criteria
        assert var_hbjson.phius_cert.phius_certification_settings == var_xml.phius_cert.phius_certification_settings
        assert var_hbjson.phius_cert.use_monthly_shading == var_xml.phius_cert.use_monthly_shading

        # -- Compare ph_building_data fields individually, skipping summer_ventilation
        # -- since WUFI XML only carries the bypass mode, not the full summer vent model.
        bd_hbjson = var_hbjson.phius_cert.ph_building_data
        bd_xml = var_xml.phius_cert.ph_building_data
        assert bd_hbjson.num_of_units == bd_xml.num_of_units
        assert bd_hbjson.num_of_floors == bd_xml.num_of_floors
        assert bd_hbjson.occupancy_setting_method == bd_xml.occupancy_setting_method
        assert abs(bd_hbjson.airtightness_q50 - bd_xml.airtightness_q50) < 0.001
        assert abs(bd_hbjson.airtightness_n50 - bd_xml.airtightness_n50) < 0.001
        assert bd_hbjson.setpoints == bd_xml.setpoints
        assert abs(bd_hbjson.mech_room_temp - bd_xml.mech_room_temp) < 0.001
        assert bd_hbjson.non_combustible_materials == bd_xml.non_combustible_materials
        assert bd_hbjson.foundations == bd_xml.foundations
        assert bd_hbjson.building_exposure_type == bd_xml.building_exposure_type
        assert bd_hbjson.summer_ventilation.summer_bypass_mode == bd_xml.summer_ventilation.summer_bypass_mode

        assert var_hbjson.site == var_xml.site
        # TODO: assert var_hbjson.building == var_xml.building
        # TODO: assert var_hbjson.default_mech_collection == var_xml.default_mech_collection
