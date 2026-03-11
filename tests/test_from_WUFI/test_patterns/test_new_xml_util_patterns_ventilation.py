from PHX.model.project import PhxProject


def test_vent_patterns_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Ventilation Patterns
    util_pats_hbjson = phx_project_from_hbjson.utilization_patterns_ventilation.patterns
    util_pats_xml = phx_project_from_wufi_xml.utilization_patterns_ventilation.patterns

    assert len(util_pats_hbjson) == len(util_pats_xml)

    # -- Match patterns by position since names may differ between
    # -- HBJSON and XML sources depending on the honeybee library version.
    for pattern_hbjson, util_pat_xml in zip(util_pats_hbjson.values(), util_pats_xml.values()):
        assert util_pat_xml.operating_hours == pattern_hbjson.operating_hours
        assert util_pat_xml.operating_days == pattern_hbjson.operating_days
        assert util_pat_xml.operating_weeks == pattern_hbjson.operating_weeks
        assert util_pat_xml.holiday_days == pattern_hbjson.holiday_days
        assert util_pat_xml.operating_periods == pattern_hbjson.operating_periods
