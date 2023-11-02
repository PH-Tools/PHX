from typing import ValuesView
from PHX.model.project import PhxProject
from PHX.model.schedules.occupancy import PhxScheduleOccupancy


def _find_matching_pattern(
    _util_pattern: PhxScheduleOccupancy,
    _util_patterns: ValuesView[PhxScheduleOccupancy],
) -> PhxScheduleOccupancy:
    """Helper Function: Find the matching pattern in the XML set"""
    
    for pat in _util_patterns:
        if _util_pattern.display_name == pat.display_name:
            return pat
    raise Exception(
        f"Utilization Pattern {_util_pattern.display_name} not found in XML set?"
    )


def test_vent_patterns_match(
    create_phx_project_from_hbjson: PhxProject,
    create_phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Occupancy Patterns
    utilization_patterns_from_hbjson = (
        create_phx_project_from_hbjson.utilization_patterns_occupancy.patterns
    )
    utilization_patterns_from_xml = (
        create_phx_project_from_wufi_xml.utilization_patterns_occupancy.patterns
    )

    assert len(utilization_patterns_from_hbjson) == len(utilization_patterns_from_xml)

    for pattern_from_hbjson in utilization_patterns_from_hbjson.values():
        pattern_from_xml = _find_matching_pattern(pattern_from_hbjson, 
                                                  utilization_patterns_from_xml.values())

        assert pattern_from_xml == pattern_from_hbjson
