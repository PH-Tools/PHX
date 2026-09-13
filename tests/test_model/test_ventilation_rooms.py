import operator
from dataclasses import fields
from functools import reduce

import pytest

from PHX.model.building import PhxZone
from PHX.model.spaces import PhxSpace
from PHX.model.ventilation_rooms import VentilationRoom, ventilation_rooms


def _space(
    _name: str,
    _ventilator_id: int | None,
    _ventilator_name: str,
    _floor_area: float,
    _weighted_floor_area: float,
    _clear_height: float,
    _flow_supply: float,
    _flow_extract: float,
    _wufi_type: int = 1,
) -> PhxSpace:
    space = PhxSpace(
        display_name=_name,
        vent_unit_id_num=_ventilator_id,
        vent_unit_display_name=_ventilator_name,
        floor_area=_floor_area,
        weighted_floor_area=_weighted_floor_area,
        clear_height=_clear_height,
        wufi_type=_wufi_type,
    )
    space.ventilation.load.flow_supply = _flow_supply
    space.ventilation.load.flow_extract = _flow_extract
    return space


def _expected_fields(_space: PhxSpace) -> dict:
    return {
        "display_name": _space.display_name,
        "wufi_type": _space.wufi_type,
        "quantity": _space.quantity,
        "weighted_floor_area": _space.weighted_floor_area,
        "clear_height": _space.clear_height,
        "flow_supply": _space.ventilation.load.flow_supply,
        "flow_extract": _space.ventilation.load.flow_extract,
        "ventilation_pattern_id_num": _space.ventilation.schedule.id_num,
        "ventilator_id_num": _space.vent_unit_id_num,
    }


def _record_fields(_room: VentilationRoom) -> dict:
    return {field.name: getattr(_room, field.name) for field in fields(_room)}


def test_merge_off_returns_each_ventilated_space_in_order(reset_class_counters) -> None:
    first = _space("Office", 2, "Ventilator B", 10.0, 8.0, 2.6, 30.0, 20.0)
    unventilated = _space("Storage", None, "", 4.0, 2.0, 2.4, 0.0, 0.0)
    second = _space("Kitchen", 1, "Ventilator A", 12.0, 10.0, 2.8, 15.0, 25.0, _wufi_type=2)
    zone = PhxZone(spaces=[first, unventilated, second])

    rooms = ventilation_rooms(zone)

    assert [_record_fields(room) for room in rooms] == [_expected_fields(first), _expected_fields(second)]


def test_merge_on_matches_phx_space_left_fold_for_groups_of_one_two_and_three(reset_class_counters) -> None:
    groups = [
        [_space("Ventilator A", 1, "Ventilator A", 7.0, 6.0, 2.4, 0.1, 0.2)],
        [
            _space("Ventilator B", 2, "Ventilator B", 11.0, 8.0, 2.3, 0.1, 0.2),
            _space("Ventilator B", 2, "Ventilator B", 13.0, 9.0, 2.9, 0.2, 0.4),
        ],
        [
            _space("Ventilator C", 3, "Ventilator C", 5.0, 4.0, 2.1, 0.1, 0.2),
            _space("Ventilator C", 3, "Ventilator C", 8.0, 7.0, 2.7, 0.2, 0.4),
            _space("Ventilator C", 3, "Ventilator C", 17.0, 15.0, 3.2, 0.3, 0.8),
        ],
    ]
    zone = PhxZone(spaces=[space for group in groups for space in group], merge_spaces_by_erv=True)

    expected = [reduce(operator.add, group) for group in groups]
    rooms = ventilation_rooms(zone)

    assert [_record_fields(room) for room in rooms] == [_expected_fields(space) for space in expected]


def test_merge_on_rejects_mixed_wufi_types_in_one_group(reset_class_counters) -> None:
    first = _space("Office", 1, "Ventilator A", 10.0, 8.0, 2.5, 20.0, 10.0, _wufi_type=1)
    second = _space("Kitchen", 1, "Ventilator A", 12.0, 9.0, 2.7, 15.0, 25.0, _wufi_type=2)
    zone = PhxZone(spaces=[first, second], merge_spaces_by_erv=True)

    with pytest.raises(ValueError, match="Space Office cannot be added to space Kitchen"):
        ventilation_rooms(zone)


def test_projection_is_repeatable_and_does_not_change_source_spaces(reset_class_counters) -> None:
    spaces = [
        _space("Office", 1, "Ventilator A", 10.0, 8.0, 2.5, 20.0, 10.0),
        _space("Kitchen", 1, "Ventilator A", 12.0, 9.0, 2.7, 15.0, 25.0),
    ]
    zone = PhxZone(spaces=spaces, merge_spaces_by_erv=True)
    before = [
        (space.display_name, space.ventilation.load.flow_supply, space.ventilation.load.flow_extract, space.id_num)
        for space in spaces
    ]

    first = ventilation_rooms(zone)
    second = ventilation_rooms(zone)

    after = [
        (space.display_name, space.ventilation.load.flow_supply, space.ventilation.load.flow_extract, space.id_num)
        for space in spaces
    ]
    assert first == second
    assert after == before


def test_projection_does_not_allocate_a_space_id_number(monkeypatch, reset_class_counters) -> None:
    spaces = [
        _space("Office", 1, "Ventilator A", 10.0, 8.0, 2.5, 20.0, 10.0),
        _space("Kitchen", 1, "Ventilator A", 12.0, 9.0, 2.7, 15.0, 25.0),
    ]
    zone = PhxZone(spaces=spaces, merge_spaces_by_erv=True)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Space ID Number allocated")

    monkeypatch.setattr("PHX.model.spaces.allocate_identity", fail_if_called)

    ventilation_rooms(zone)
