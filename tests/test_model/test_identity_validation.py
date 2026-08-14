import pytest

from PHX.hbjson_to_phpp import write_phx_project_to_phpp
from PHX.model.building import PhxZone
from PHX.model.components import PhxComponentOpaque
from PHX.model.constructions import PhxConstructionOpaque
from PHX.model.geometry import PhxPlane, PhxPolygon, PhxVector, PhxVertix
from PHX.model.hvac import PhxDeviceVentilator
from PHX.model.hvac.ducting import PhxDuctElement
from PHX.model.hvac.piping import PhxPipeTrunk
from PHX.model.identity import IdentityNamespaces
from PHX.model.identity_validation import (
    IdentityValidationError,
    IdentityValidationTarget,
    validate_project_identities,
)
from PHX.model.project import PhxProject, PhxVariant
from PHX.model.spaces import PhxSpace
from PHX.to_METr_JSON.metr_builder import generate_metr_json_dict
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def _invalid_project() -> PhxProject:
    project = PhxProject()
    first_assembly = PhxConstructionOpaque()
    first_assembly.identifier = "first"
    second_assembly = PhxConstructionOpaque()
    second_assembly.identifier = "second"
    second_assembly.id_num = first_assembly.id_num
    project.assembly_types = {"first": first_assembly, "second": second_assembly}

    variant = PhxVariant()
    first_component = PhxComponentOpaque()
    second_component = PhxComponentOpaque()
    second_component._id_num = first_component.id_num
    first_component.assembly_type_id_num = 999
    variant.building.add_components((first_component, second_component))
    project.add_new_variant(variant)
    return project


def test_validator_aggregates_sorted_duplicate_and_dangling_issues():
    project = _invalid_project()
    assembly_id = next(iter(project.assembly_types.values())).id_num
    component_id = project.variants[0].building.all_components[0].id_num
    with pytest.raises(IdentityValidationError) as exc_info:
        validate_project_identities(project, IdentityValidationTarget.WUFI)

    issues = exc_info.value.issues
    assert tuple(sorted(issues, key=lambda issue: issue.sort_key)) == issues
    assert {(issue.namespace, issue.value, issue.kind) for issue in issues} >= {
        (IdentityNamespaces.ASSEMBLIES, assembly_id, "duplicate"),
        (("variants[0]", IdentityNamespaces.COMPONENTS), component_id, "duplicate"),
        (IdentityNamespaces.ASSEMBLIES, 999, "dangling-reference"),
    }
    assert all(issue.path for issue in issues)


def test_same_number_in_independent_namespaces_is_legal():
    project = PhxProject()
    assembly = PhxConstructionOpaque()
    assembly.identifier = "assembly"
    component = PhxComponentOpaque()
    component._id_num = assembly.id_num
    component.set_assembly_type(assembly)
    variant = PhxVariant()
    variant.building.add_component(component)
    project.assembly_types[assembly.identifier] = assembly
    project.add_new_variant(variant)

    validate_project_identities(project, IdentityValidationTarget.WUFI)


def test_variant_hvac_and_distribution_duplicates_are_aggregated():
    project = PhxProject()
    variant = PhxVariant()
    first_zone = PhxZone()
    second_zone = PhxZone()
    second_zone.id_num = first_zone.id_num
    variant.building.add_zones((first_zone, second_zone))

    collection = variant.default_mech_collection
    first_ventilator = PhxDeviceVentilator()
    second_ventilator = PhxDeviceVentilator()
    second_ventilator.id_num = first_ventilator.id_num
    collection.add_new_mech_device("first", first_ventilator)
    collection.add_new_mech_device("second", second_ventilator)
    first_duct = PhxDuctElement("first", "first", first_ventilator.id_num)
    second_duct = PhxDuctElement("second", "second", first_ventilator.id_num)
    second_duct.id_num = first_duct.id_num
    collection.add_vent_ducting(first_duct)
    collection.add_vent_ducting(second_duct)
    first_trunk = PhxPipeTrunk(identifier="first")
    second_trunk = PhxPipeTrunk(identifier="second")
    second_trunk.id_num = first_trunk.id_num
    second_trunk.pipe_element.id_num = first_trunk.pipe_element.id_num
    collection.add_distribution_piping(first_trunk)
    collection.add_distribution_piping(second_trunk)
    project.add_new_variant(variant)

    with pytest.raises(IdentityValidationError) as exc_info:
        validate_project_identities(project, IdentityValidationTarget.WUFI)

    duplicate_namespaces = {issue.namespace for issue in exc_info.value.issues if issue.kind == "duplicate"}
    assert duplicate_namespaces >= {
        ("variants[0]", IdentityNamespaces.ZONES),
        ("variants[0]", IdentityNamespaces.mechanical_devices(PhxDeviceVentilator)),
        ("variants[0]", IdentityNamespaces.DUCTS),
        ("variants[0]", IdentityNamespaces.PIPE_TRUNKS),
        ("variants[0]", IdentityNamespaces.PIPE_ELEMENTS),
    }


def test_geometry_and_schedule_references_report_the_consumed_namespace():
    project = PhxProject()
    variant = PhxVariant()
    component = PhxComponentOpaque()
    polygon = PhxPolygon(
        "polygon",
        1.0,
        PhxVertix(),
        PhxVector(0, 0, 1),
        PhxPlane(PhxVector(0, 0, 1), PhxVertix(), PhxVector(1, 0, 0), PhxVector(0, 1, 0)),
    )
    polygon.child_polygon_ids.append(999)
    component.add_polygons(polygon)
    variant.building.add_component(component)
    zone = PhxZone()
    space = PhxSpace()
    space.ventilation.load.flow_supply = 1.0
    zone.spaces.append(space)
    variant.building.add_zone(zone)
    project.add_new_variant(variant)

    with pytest.raises(IdentityValidationError) as exc_info:
        validate_project_identities(project, IdentityValidationTarget.WUFI)

    dangling_namespaces = {issue.namespace for issue in exc_info.value.issues if issue.kind == "dangling-reference"}
    assert dangling_namespaces >= {
        ("variants[0]", IdentityNamespaces.POLYGONS),
        IdentityNamespaces.VENTILATION_PATTERNS,
        IdentityNamespaces.OCCUPANCY_PATTERNS,
    }


@pytest.mark.parametrize("exporter", [generate_WUFI_XML_from_object, generate_metr_json_dict])
def test_serializing_exporters_validate_before_conversion(exporter):
    with pytest.raises(IdentityValidationError):
        exporter(_invalid_project())


def test_phpp_validates_before_first_excel_write():
    with pytest.raises(IdentityValidationError):
        write_phx_project_to_phpp(object(), _invalid_project())
