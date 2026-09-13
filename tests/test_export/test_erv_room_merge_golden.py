# -*- Python Version: 3.10 -*-

"""Golden room rows for WUFI XML and METr JSON with the ERV Space merge on and off.

Captured on 'main' before the Ventilation Room projection (#127), so moving the merge out of the
two exporters can be checked for byte-identical room output. Only the sections the merge produces
are compared: the WUFI '<RoomsVentilation>' and '<UtilisationPatternsVentilation>' blocks and the
METr room lists. Whole documents are not yet stable between processes (heat pump ID Numbers and
supportive-device order vary, #133); the room sections are.

Regenerate only when the room output legitimately changes:

    python -m tests.test_export.test_erv_room_merge_golden
"""

import json
import re
from pathlib import Path

import pytest

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_METr_JSON import metr_builder
from PHX.to_WUFI_XML import xml_builder
from tests.conftest import _reset_phx_class_counters

HBJSON_DIR = Path("tests", "reference_files", "from_grasshopper_tests", "hbjson")
GOLDEN_DIR = Path("tests", "reference_files", "erv_room_merge")

# -- (HBJSON path under HBJSON_DIR, merge Spaces by ERV)
CASES = (
    ("Multi_Room_Complete", True),  # one Ventilator serving two Spaces
    ("Multi_Room_Complete", False),
    ("occupancy_scenarios/03_single_dwelling_set_occupancy", True),  # one Ventilator serving four Spaces
    ("occupancy_scenarios/03_single_dwelling_set_occupancy", False),
    ("Non_Residential_Office", True),  # ventilated Spaces with no Ventilation Assignment
)

_XML_SECTIONS = re.compile(
    r"<RoomsVentilation\b[^>]*/>|<RoomsVentilation\b[^>]*>.*?</RoomsVentilation>"
    r"|<UtilisationPatternsVentilation\b[^>]*/>|<UtilisationPatternsVentilation\b[^>]*>.*?</UtilisationPatternsVentilation>",
    re.S,
)


def _case_id(_model_name: str, _merge: bool) -> str:
    return f"{Path(_model_name).name}__merge_{'on' if _merge else 'off'}"


def _metr_room_lists(_metr_text: str) -> list[list[dict]]:
    """Return every METr room list (lists of dicts carrying 'dVFrSup'), in document order."""
    found: list[list[dict]] = []

    def walk(_obj) -> None:
        if isinstance(_obj, dict):
            for value in _obj.values():
                if isinstance(value, list) and value and isinstance(value[0], dict) and "dVFrSup" in value[0]:
                    found.append(value)
                walk(value)
        elif isinstance(_obj, list):
            for value in _obj:
                walk(value)

    walk(json.loads(_metr_text))
    return found


def render(_model_name: str, _merge: bool) -> tuple[str, str]:
    """Return the (WUFI room sections, METr room lists) text for one golden case."""
    _reset_phx_class_counters()
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(HBJSON_DIR / f"{_model_name}.hbjson")
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project = create_project.convert_hb_model_to_PhxProject(
        hb_model, _group_components=True, _merge_faces=True, _merge_spaces_by_erv=_merge
    )
    xml_sections = "\n".join(_XML_SECTIONS.findall(xml_builder.generate_WUFI_XML_from_object(phx_project))) + "\n"
    metr_rooms = json.dumps(_metr_room_lists(metr_builder.generate_metr_json_text(phx_project)), indent=2) + "\n"
    return xml_sections, metr_rooms


@pytest.mark.parametrize(("model_name", "merge"), CASES, ids=[_case_id(*c) for c in CASES])
def test_wufi_and_metr_room_output_match_golden(model_name: str, merge: bool) -> None:
    xml_sections, metr_rooms = render(model_name, merge)
    case_id = _case_id(model_name, merge)

    assert xml_sections == (GOLDEN_DIR / f"{case_id}.rooms.xml").read_text(encoding="utf-8")
    assert metr_rooms == (GOLDEN_DIR / f"{case_id}.rooms.json").read_text(encoding="utf-8")


if __name__ == "__main__":
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for model_name, merge in CASES:
        xml_sections, metr_rooms = render(model_name, merge)
        case_id = _case_id(model_name, merge)
        (GOLDEN_DIR / f"{case_id}.rooms.xml").write_text(xml_sections, encoding="utf-8")
        (GOLDEN_DIR / f"{case_id}.rooms.json").write_text(metr_rooms, encoding="utf-8")
        print(f"wrote {case_id}.rooms.xml / .rooms.json")
