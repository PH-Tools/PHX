from copy import deepcopy
from pathlib import Path

import pytest
from lxml import etree

from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


@pytest.mark.parametrize(
    ("fixture_name", "expected_space_loads", "expected_zone_loads"),
    (("_ridgeway.xml", 206, 1), ("_la_mora.xml", 4, 6)),
)
def test_wufi_occupancy_fields_round_trip(
    reset_class_counters,
    fixture_name: str,
    expected_space_loads: int,
    expected_zone_loads: int,
) -> None:
    source = Path("tests", "reference_files", "from_WUFI", "wufi_xml", fixture_name)
    source_root = etree.parse(source).getroot()

    wufi_data = get_WUFI_XML_file_as_dict(source)
    wufi_model = WUFIplusProject.model_validate(wufi_data)
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_model)
    output_root = etree.fromstring(generate_WUFI_XML_from_object(phx_project).encode())

    expected_counts = {
        "NumberOccupants": expected_space_loads,
        "FloorAreaUtilizationZone": expected_space_loads,
        "OccupantQuantityUserDef": expected_zone_loads,
        "NumberBedrooms": expected_zone_loads,
    }
    for tag, expected_count in expected_counts.items():
        source_values = [float(node.text) for node in source_root.xpath(f".//{tag}")]
        output_values = [float(node.text) for node in output_root.xpath(f".//{tag}")]
        assert len(source_values) == expected_count
        assert output_values == source_values


def test_duplicate_named_ventilation_rooms_are_preserved(reset_class_counters, tmp_path: Path) -> None:
    source = Path(
        "tests",
        "reference_files",
        "from_grasshopper_tests",
        "wufi_xml",
        "Multi_Room_Complete.xml",
    )
    source_root = etree.parse(source).getroot()
    rooms = source_root.xpath(".//RoomsVentilation")[0]
    duplicated_room = deepcopy(rooms[0])
    duplicate_name = duplicated_room.findtext("Name")
    rooms.append(duplicated_room)
    rooms.set("count", str(len(rooms)))

    modified_source = tmp_path / source.name
    etree.ElementTree(source_root).write(modified_source, encoding="utf-8", xml_declaration=True)
    wufi_data = get_WUFI_XML_file_as_dict(modified_source)
    wufi_model = WUFIplusProject.model_validate(wufi_data)
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_model)

    spaces = phx_project.variants[0].building.zones[0].spaces
    assert [space.display_name for space in spaces].count(duplicate_name) == 2
