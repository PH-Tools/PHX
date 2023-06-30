from typing import ValuesView
from PHX.model.project import PhxProject
from PHX.model.schedules.ventilation import PhxScheduleVentilation


def _find_matching_pattern(
    _util_pattern: PhxScheduleVentilation,
    _util_patterns: ValuesView[PhxScheduleVentilation],
) -> PhxScheduleVentilation:
    for pat in _util_patterns:
        if _util_pattern.name == pat.name:
            return pat
    raise Exception(f"Utilization Pattern {_util_pattern.name} not found in XML set?")


def test_vent_patterns_match(
    project_from_hbjson: PhxProject,
    project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Ventilation Patterns
    util_pats_hbjson = project_from_hbjson.utilization_patterns_ventilation.patterns
    util_pats_xml = project_from_wufi_xml.utilization_patterns_ventilation.patterns

    assert len(util_pats_hbjson) == len(util_pats_xml)

    for pattern_hbjson in util_pats_hbjson.values():
        util_pat_xml = _find_matching_pattern(pattern_hbjson, util_pats_xml.values())

        assert util_pat_xml.name == pattern_hbjson.name
        assert util_pat_xml.operating_hours == pattern_hbjson.operating_hours
        assert util_pat_xml.operating_days == pattern_hbjson.operating_days
        assert util_pat_xml.operating_weeks == pattern_hbjson.operating_weeks
        assert util_pat_xml.holiday_days == pattern_hbjson.holiday_days
        assert util_pat_xml.operating_periods == pattern_hbjson.operating_periods
