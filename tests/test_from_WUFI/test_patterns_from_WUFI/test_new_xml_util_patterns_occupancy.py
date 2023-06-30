from typing import ValuesView
from PHX.model.project import PhxProject
from PHX.model.schedules.occupancy import PhxScheduleOccupancy


def _find_matching_pattern(
    _util_pattern: PhxScheduleOccupancy,
    _util_patterns: ValuesView[PhxScheduleOccupancy],
) -> PhxScheduleOccupancy:
    for pat in _util_patterns:
        if _util_pattern.display_name == pat.display_name:
            return pat
    raise Exception(
        f"Utilization Pattern {_util_pattern.display_name} not found in XML set?"
    )


def test_vent_patterns_match(
    project_from_hbjson: PhxProject,
    project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Occupancy Patterns
    util_pats_hbjson = project_from_hbjson.utilization_patterns_occupancy.patterns
    util_pats_xml = project_from_wufi_xml.utilization_patterns_occupancy.patterns

    assert len(util_pats_hbjson) == len(util_pats_xml)

    for pattern_hbjson in util_pats_hbjson.values():
        util_pat_xml = _find_matching_pattern(pattern_hbjson, util_pats_xml.values())

        assert util_pat_xml == pattern_hbjson
