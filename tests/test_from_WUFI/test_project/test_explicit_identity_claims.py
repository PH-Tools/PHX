from copy import deepcopy
from pathlib import Path

import pytest

from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.model.building import PhxZone
from PHX.model.identity import DuplicateIdentityError

REFERENCE_DIR = Path("tests", "reference_files", "from_grasshopper_tests", "wufi_xml")


def _wufi_model(filename: str) -> WUFIplusProject:
    return WUFIplusProject.model_validate(get_WUFI_XML_file_as_dict(REFERENCE_DIR / filename))


def test_sparse_zone_identity_is_preserved_and_reserved(reset_class_counters):
    source = _wufi_model("Multi_Room_Complete.xml")
    source.Variants[0].Building.Zones[0].IdentNr = 5

    phx_project = convert_WUFI_XML_to_PHX_project(source)
    variant = phx_project.variants[0]
    assert variant.zones[0].id_num == 5

    with phx_project.identity_scope(owner=variant.id_num):
        new_ids = [PhxZone().id_num for _ in range(4)]

    assert new_ids == [2, 3, 4, 6]


def test_duplicate_window_identity_reports_namespace_value_and_sources(reset_class_counters):
    source = _wufi_model("_la_mora.xml")
    duplicate = deepcopy(source.WindowTypes[0])
    duplicate.Name = "Conflicting window"
    source.WindowTypes.append(duplicate)

    with pytest.raises(DuplicateIdentityError) as exc_info:
        convert_WUFI_XML_to_PHX_project(source)

    message = str(exc_info.value)
    assert "project.windows" in message
    assert str(duplicate.IdentNr) in message
    assert source.WindowTypes[0].Name in message
    assert duplicate.Name in message


def test_same_number_is_legal_for_window_and_variant_namespaces(reset_class_counters):
    source = _wufi_model("_la_mora.xml")
    phx_project = convert_WUFI_XML_to_PHX_project(source)

    window_ids = {window.id_num for window in phx_project.window_types.values()}
    variant_ids = {variant.id_num for variant in phx_project.variants}
    assert window_ids & variant_ids
