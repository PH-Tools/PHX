from typing import List, ValuesView
from PHX.model.project import PhxProject
from PHX.model.constructions import PhxConstructionOpaque


def test_assembly_types_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Assemblies
    hbjson_assemblies = phx_project_from_hbjson.assembly_types
    xml_assemblies = phx_project_from_wufi_xml.assembly_types
    assert len(hbjson_assemblies) == len(xml_assemblies)

    # -- From WUFI uses id-num as the key. while HBJSON uses the display_name
    # -- Since WUFI doesn't enforce unique names, we can't use that as a key
    hbjson_assembly_names = sorted([a.display_name for a in hbjson_assemblies.values()])
    xml_assembly_names = sorted([a.display_name for a in xml_assemblies.values()])
    assert hbjson_assembly_names == xml_assembly_names


def _find_matching_assembly(
    hbjson_type: PhxConstructionOpaque, xml_types: ValuesView[PhxConstructionOpaque]
) -> PhxConstructionOpaque:
    for xml_type in xml_types:
        if hbjson_type.display_name == xml_type.display_name:
            return xml_type
    raise Exception(f"Assembly Type {hbjson_type.display_name} not found in XML set?")


def test_assembly_type_layers_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Assemblies
    hbjson_assemblies = phx_project_from_hbjson.assembly_types
    xml_assemblies = phx_project_from_wufi_xml.assembly_types

    for hbjson_type in hbjson_assemblies.values():
        xml_type = _find_matching_assembly(hbjson_type, xml_assemblies.values())
        assert hbjson_type.layers == xml_type.layers


def test_assembly_type_materials_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Assemblies
    hbjson_assemblies = phx_project_from_hbjson.assembly_types
    xml_assemblies = phx_project_from_wufi_xml.assembly_types

    for hbjson_type in hbjson_assemblies.values():
        xml_type = _find_matching_assembly(hbjson_type, xml_assemblies.values())
        for i, hbjson_layer in enumerate(hbjson_type.layers):
            assert hbjson_layer.material == xml_type.layers[i].material
