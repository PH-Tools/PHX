from typing import ValuesView

from pytest import approx

from PHX.model.project import PhxProject
from PHX.model.schedules.occupancy import PhxScheduleOccupancy


def _find_matching_pattern(
    _hbjson_util_pattern: PhxScheduleOccupancy,
    _xml_util_patterns: ValuesView[PhxScheduleOccupancy],
) -> PhxScheduleOccupancy:
    """Helper Function: Find the matching pattern in the XML set"""

    for xml_pat in _xml_util_patterns:
        if _hbjson_util_pattern.id_num == xml_pat.id_num:
            return xml_pat
    raise Exception(
        f"HBJSON Utilization Pattern '{_hbjson_util_pattern.display_name}' was not found in XML collection?"
        f"Valid Utilization Patterns include: {[p.display_name for p in _xml_util_patterns]}"
    )


def test_vent_patterns_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Occupancy Patterns
    utilization_patterns_from_hbjson = phx_project_from_hbjson.utilization_patterns_occupancy.patterns
    utilization_patterns_from_xml = phx_project_from_wufi_xml.utilization_patterns_occupancy.patterns

    for pattern_from_hbjson in utilization_patterns_from_hbjson.values():
        pattern_from_xml = _find_matching_pattern(pattern_from_hbjson, utilization_patterns_from_xml.values())

        assert pattern_from_xml.id_num == pattern_from_hbjson.id_num
        assert pattern_from_xml.display_name == approx(pattern_from_hbjson.display_name)
        assert pattern_from_xml.start_hour == approx(pattern_from_hbjson.start_hour)
        assert pattern_from_xml.end_hour == approx(pattern_from_hbjson.end_hour)
        assert pattern_from_xml.annual_utilization_days == approx(pattern_from_hbjson.annual_utilization_days)
        assert pattern_from_xml.relative_utilization_factor == approx(pattern_from_hbjson.relative_utilization_factor)
        assert pattern_from_xml.annual_operating_hours == approx(pattern_from_hbjson.annual_operating_hours)
        assert pattern_from_xml.annual_utilization_factor == approx(pattern_from_hbjson.annual_utilization_factor)
