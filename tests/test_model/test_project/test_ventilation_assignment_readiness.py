import pytest

from PHX.model.building import PhxZone
from PHX.model.hvac import PhxDeviceVentilator
from PHX.model.hvac.collection import PhxMechanicalSystemCollection
from PHX.model.hvac.ducting import PhxDuctElement
from PHX.model.project import PhxVariant, VentilationAssignmentError
from PHX.model.spaces import PhxSpace


def _variant_with_space(space):
    variant = PhxVariant(name="Primary")
    variant.building.zones.append(PhxZone(display_name="Zone A", spaces=[space]))
    return variant


def test_default_space_has_no_ventilation_assignment():
    assert PhxSpace().vent_unit_id_num is None


def test_readiness_accepts_unassigned_space_and_resolved_references(reset_class_counters):
    space = PhxSpace(display_name="Office")
    variant = _variant_with_space(space)
    ventilator = PhxDeviceVentilator()
    variant.default_mech_collection.add_new_mech_device("vent", ventilator)
    space.vent_unit_id_num = ventilator.id_num
    variant.default_mech_collection.add_vent_ducting(PhxDuctElement("supply", "Supply", ventilator.id_num))

    assert variant.ventilation_assignment_issues() == []
    variant.assert_ventilation_assignments_ready()


def test_readiness_rejects_unassigned_mechanical_airflow_when_a_device_is_modeled(reset_class_counters):
    space = PhxSpace(display_name="Office")
    space.ventilation.load.flow_supply = 25.0
    variant = _variant_with_space(space)
    variant.default_mech_collection.add_new_mech_device("vent", PhxDeviceVentilator())

    issues = variant.ventilation_assignment_issues()

    assert len(issues) == 1
    assert "mechanical airflow" in issues[0]
    assert "no ventilation-device assignment" in issues[0]


def test_readiness_accepts_unassigned_airflow_when_no_device_is_modeled():
    space = PhxSpace(display_name="Window ventilated")
    space.ventilation.load.flow_supply = 25.0
    variant = _variant_with_space(space)

    assert variant.ventilation_assignment_issues() == []


def test_readiness_aggregates_unresolved_space_and_duct_references(reset_class_counters):
    space = PhxSpace(display_name="Office", vent_unit_id_num=91)
    variant = _variant_with_space(space)
    variant.default_mech_collection.add_vent_ducting(PhxDuctElement("supply", "Supply", 92))

    issues = variant.ventilation_assignment_issues()

    assert len(issues) == 2
    assert "Space 'Office'" in issues[0]
    assert "91" in issues[0]
    assert "duct 'Supply'" in issues[1]
    assert "92" in issues[1]
    with pytest.raises(VentilationAssignmentError) as exc:
        variant.assert_ventilation_assignments_ready()
    assert "2 issue(s)" in str(exc.value)
    assert "Office" in str(exc.value)
    assert "Supply" in str(exc.value)


def test_readiness_rejects_ambiguous_ventilation_device_id(reset_class_counters):
    space = PhxSpace(display_name="Office")
    variant = _variant_with_space(space)
    first = PhxDeviceVentilator()
    second = PhxDeviceVentilator()
    second.id_num = first.id_num
    variant.default_mech_collection.add_new_mech_device("first", first)
    variant.default_mech_collection.add_new_mech_device("second", second)
    space.vent_unit_id_num = first.id_num

    issues = variant.ventilation_assignment_issues()

    assert len(issues) == 1
    assert "matches 2 ventilation devices" in issues[0]


def test_duct_references_are_scoped_to_their_mechanical_collection(reset_class_counters):
    variant = PhxVariant()
    second_collection = PhxMechanicalSystemCollection()
    variant.add_mechanical_collection(second_collection)
    first = PhxDeviceVentilator()
    second = PhxDeviceVentilator()
    second.id_num = first.id_num
    variant.default_mech_collection.add_new_mech_device("first", first)
    second_collection.add_new_mech_device("second", second)
    variant.default_mech_collection.add_vent_ducting(PhxDuctElement("first-duct", "First duct", first.id_num))
    second_collection.add_vent_ducting(PhxDuctElement("second-duct", "Second duct", second.id_num))

    assert variant.ventilation_assignment_issues() == []


def test_variant_ventilation_lookup_searches_later_collections(reset_class_counters):
    variant = PhxVariant()
    second_collection = PhxMechanicalSystemCollection()
    variant.add_mechanical_collection(second_collection)
    ventilator = PhxDeviceVentilator()
    second_collection.add_new_mech_device("vent", ventilator)

    assert variant.get_ventilation_device_by_id(ventilator.id_num) is ventilator
