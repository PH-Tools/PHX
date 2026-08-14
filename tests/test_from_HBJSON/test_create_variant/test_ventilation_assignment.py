from types import SimpleNamespace

import pytest
from honeybee_phhvac.ventilation import PhVentilationSystem, Ventilator

from PHX.from_HBJSON import create_variant
from PHX.model.hvac import PhxDeviceVentilator
from PHX.model.project import PhxVariant


def test_missing_source_ventilation_unit_rejects_before_variant_or_source_mutation(monkeypatch):
    variant = PhxVariant()
    system = PhVentilationSystem()
    original_id = system.id_num
    monkeypatch.setattr(
        create_variant,
        "get_ph_prop_from_room",
        lambda room: SimpleNamespace(spaces=[object()]),
    )
    monkeypatch.setattr(create_variant, "get_ventilation_system_from_space", lambda space: system)

    with pytest.raises(ValueError, match="ventilation_unit"):
        create_variant.add_ventilation_systems_from_hb_rooms(variant, object())

    assert variant.default_mech_collection.ventilation_devices == []
    assert system.id_num == original_id


def test_all_source_systems_are_validated_before_any_mutation(monkeypatch):
    variant = PhxVariant()
    valid = PhVentilationSystem()
    valid.ventilation_unit = Ventilator()
    invalid = PhVentilationSystem()
    original_valid_id = valid.id_num
    valid_space = object()
    invalid_space = object()
    systems = {valid_space: valid, invalid_space: invalid}
    monkeypatch.setattr(
        create_variant,
        "get_ph_prop_from_room",
        lambda room: SimpleNamespace(spaces=[valid_space, invalid_space]),
    )
    monkeypatch.setattr(create_variant, "get_ventilation_system_from_space", systems.__getitem__)

    with pytest.raises(ValueError, match="ventilation_unit"):
        create_variant.add_ventilation_systems_from_hb_rooms(variant, object())

    assert variant.default_mech_collection.ventilation_devices == []
    assert valid.id_num == original_valid_id


def test_existing_same_key_device_does_not_bypass_missing_source_unit_validation(monkeypatch):
    variant = PhxVariant()
    invalid = PhVentilationSystem()
    variant.default_mech_collection.add_new_mech_device(invalid.key, PhxDeviceVentilator())
    existing_devices = list(variant.default_mech_collection.ventilation_devices)
    monkeypatch.setattr(
        create_variant,
        "get_ph_prop_from_room",
        lambda room: SimpleNamespace(spaces=[object()]),
    )
    monkeypatch.setattr(create_variant, "get_ventilation_system_from_space", lambda space: invalid)

    with pytest.raises(ValueError, match="ventilation_unit"):
        create_variant.add_ventilation_systems_from_hb_rooms(variant, object())

    assert variant.default_mech_collection.ventilation_devices == existing_devices
