"""A WUFI Zone carries three independent, name-keyed Space-shaped lists: the ventilation
rooms ('RoomsVentilation') and the person / lighting utilization zones ('LoadsPersonsPH',
'LoadsLightingsPH'). Neither WUFI nor METr carries a cross-list ID, so 'Name' is the only
join-key available and pairing them is best-effort. These tests pin the reconciliation
behavior against a WUFI-authored source whose lists do NOT line up.

'School.xml' is that source: 2 ventilation rooms ('a', 'b') and 2 utilization zones
('Office' = 2 occupants, 'Workshop' = 17) with nothing pairing. It also leaves every area
field blank, so each case below patches in real areas to keep the effects visible.
"""

import logging
import re
from pathlib import Path

import pytest

from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.model.project import PhxProject
from PHX.model.spaces import PhxSpace

SOURCE_XML_FILE = Path("tests", "reference_files", "from_grasshopper_tests", "wufi_xml", "School.xml")
SOURCE_TOTAL_OCCUPANTS = 19.0  # 'Office' (2) + 'Workshop' (17)


def _school_xml_variant(
    tmp_path: Path,
    *,
    room_names: tuple[str, str],
    room_area: str = '<AreaRoom unit="m²">30.0</AreaRoom>',
    zone_area: str = '<FloorAreaUtilizationZone unit="m²">50.0</FloorAreaUtilizationZone>',
) -> Path:
    """Write a copy of School.xml with the ventilation rooms re-named and areas filled in."""
    src = SOURCE_XML_FILE.read_text()
    src = src.replace('<FloorAreaUtilizationZone unit="m²" />', zone_area)
    src = src.replace('<AreaRoom unit="m²" />', room_area)

    rooms_block = re.search(r"<RoomsVentilation.*?</RoomsVentilation>", src, re.S)
    assert rooms_block is not None
    renamed = rooms_block.group(0)
    for old, new in zip(("a", "b"), room_names):
        renamed = renamed.replace(f"<Name>{old}</Name>", f"<Name>{new}</Name>")

    target = tmp_path / "school_variant.xml"
    target.write_text(src[: rooms_block.start()] + renamed + src[rooms_block.end() :])
    return target


def _convert(xml_file: Path) -> PhxProject:
    wufi_model = WUFIplusProject.model_validate(get_WUFI_XML_file_as_dict(xml_file))
    return convert_WUFI_XML_to_PHX_project(wufi_model)


def _spaces(phx_project: PhxProject) -> list[PhxSpace]:
    return [space for variant in phx_project.variants for zone in variant.zones for space in zone.spaces]


def test_duplicate_room_names_consume_each_person_load_only_once(reset_class_counters, tmp_path: Path) -> None:
    """Two rooms sharing one name must not both claim the same person-load record."""
    phx_project = _convert(_school_xml_variant(tmp_path, room_names=("Office", "Office")))

    spaces = _spaces(phx_project)
    assert len(spaces) == 3  # 'Office' + 'Office' + the un-paired 'Workshop' utilization zone
    assert sum(s.peak_occupancy for s in spaces) == pytest.approx(SOURCE_TOTAL_OCCUPANTS)


def test_join_key_ignores_surrounding_whitespace(reset_class_counters, tmp_path: Path) -> None:
    """Names are hand-typed free text in WUFI; one stray space must not split a Space."""
    phx_project = _convert(_school_xml_variant(tmp_path, room_names=("Office ", "Workshop")))

    spaces = _spaces(phx_project)
    assert len(spaces) == 2
    assert all(s.has_ventilation_airflow and s.peak_occupancy for s in spaces)
    assert sum(s.peak_occupancy for s in spaces) == pytest.approx(SOURCE_TOTAL_OCCUPANTS)


def test_blank_room_area_falls_back_to_the_utilization_zone_area(reset_class_counters, tmp_path: Path) -> None:
    """A blank 'AreaRoom' must not zero the occupancy, which is stored as a density."""
    xml_file = _school_xml_variant(tmp_path, room_names=("Office", "Workshop"), room_area='<AreaRoom unit="m²" />')
    phx_project = _convert(xml_file)

    spaces = _spaces(phx_project)
    assert len(spaces) == 2
    assert all(s.floor_area == pytest.approx(50.0) for s in spaces)
    assert sum(s.peak_occupancy for s in spaces) == pytest.approx(SOURCE_TOTAL_OCCUPANTS)


def test_matched_lists_do_not_warn(reset_class_counters, tmp_path: Path, caplog) -> None:
    """A file whose lists pair 1:1 (ie; one PHX wrote) reconciles silently."""
    xml_file = _school_xml_variant(tmp_path, room_names=("Office", "Workshop"))

    with caplog.at_level(logging.WARNING, logger="PHX.from_WUFI_XML.phx_schemas"):
        _convert(xml_file)

    assert not caplog.records


def test_unreconciled_lists_are_reported(reset_class_counters, caplog) -> None:
    """The un-patched source pairs nothing; the lossy import must not be silent."""
    with caplog.at_level(logging.WARNING, logger="PHX.from_WUFI_XML.phx_schemas"):
        phx_project = _convert(SOURCE_XML_FILE)

    assert len(_spaces(phx_project)) == 4  # the union: 2 ventilation rooms + 2 utilization zones
    assert len(caplog.records) == 1
    message = caplog.records[0].message
    assert "do not pair 1:1 by name" in message
    for unpaired_name in ("'a'", "'b'", "'Office'", "'Workshop'"):
        assert unpaired_name in message
