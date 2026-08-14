from unittest.mock import Mock

import pytest

from PHX.PHPP import phpp_app
from PHX.hbjson_to_phpp import write_phx_project_to_phpp
from PHX.model.building import PhxZone
from PHX.model.project import PhxProject, PhxVariant, VentilationAssignmentError
from PHX.model.spaces import PhxSpace
from PHX.to_METr_JSON import metr_builder, metr_schemas
from PHX.to_PPP import ppp_builder
from PHX.to_WUFI_XML import xml_builder, xml_schemas


def _invalid_project():
    project = PhxProject()
    variant = PhxVariant()
    variant.building.zones.append(
        PhxZone(display_name="Zone A", spaces=[PhxSpace(display_name="Office", vent_unit_id_num=99)])
    )
    project.add_new_variant(variant)
    return project


def test_scalar_writers_map_explicit_absence_to_legacy_zero():
    space = PhxSpace()

    xml_nodes = xml_schemas._PhxSpace(space)
    xml_assignment = next(node for node in xml_nodes if node.node_name == "IdentNrVentilationUnit")

    assert xml_assignment.node_value == 0
    assert metr_schemas._PhxSpace(space)["idVUnit"] == 0


def test_wufi_and_metr_project_exports_reject_before_schema_conversion(monkeypatch):
    project = _invalid_project()
    xml_schema = Mock(side_effect=AssertionError("XML schema conversion started"))
    metr_schema = Mock(side_effect=AssertionError("METr schema conversion started"))
    monkeypatch.setattr(xml_builder.xml_converter, "convert_HB_object_to_xml_writables_list", xml_schema)
    monkeypatch.setattr(metr_builder.metr_converter, "get_schema_function", Mock(return_value=metr_schema))

    with pytest.raises(VentilationAssignmentError, match="Office"):
        xml_builder.generate_WUFI_XML_from_object(project)
    with pytest.raises(VentilationAssignmentError, match="Office"):
        metr_builder.generate_metr_json_dict(project)

    xml_schema.assert_not_called()
    metr_schema.assert_not_called()


def test_phpp_project_export_rejects_before_first_write():
    project = _invalid_project()
    connection = Mock(spec=phpp_app.PHPPConnection)

    with pytest.raises(VentilationAssignmentError, match="Office"):
        write_phx_project_to_phpp(connection, project)

    connection.write_certification_config.assert_not_called()


def test_ppp_project_export_rejects_before_section_building(monkeypatch):
    project = _invalid_project()
    section_builder = Mock(side_effect=AssertionError("PPP section building started"))
    monkeypatch.setattr(ppp_builder, "meta_sections", section_builder)

    with pytest.raises(VentilationAssignmentError, match="Office"):
        ppp_builder.build_ppp_file(project)

    section_builder.assert_not_called()
