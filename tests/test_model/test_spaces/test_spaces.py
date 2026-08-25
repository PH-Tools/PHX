import pytest

from PHX.model import spaces


def test_default_room_ventilation(reset_class_counters):
    rm_vent_1 = spaces.PhxSpace()
    rm_vent_2 = spaces.PhxSpace()

    assert rm_vent_1 != rm_vent_2
    assert rm_vent_1.id_num == 1
    assert rm_vent_2.id_num == 2


def test_space_no_vent(reset_class_counters) -> None:
    rm_vent_1 = spaces.PhxSpace()
    rm_vent_1.ventilation.load.flow_extract = 0
    rm_vent_1.ventilation.load.flow_supply = 0
    rm_vent_1.ventilation.load.flow_transfer = 0
    assert not rm_vent_1.has_ventilation_airflow

    rm_vent_2 = spaces.PhxSpace()
    rm_vent_2.ventilation.load.flow_extract = 1
    rm_vent_2.ventilation.load.flow_supply = 1
    rm_vent_2.ventilation.load.flow_transfer = 1
    assert rm_vent_2.has_ventilation_airflow


def _space_with_flow(_flow: float, _vent_unit_id: int = 1) -> spaces.PhxSpace:
    space = spaces.PhxSpace()
    space.vent_unit_id_num = _vent_unit_id
    space.vent_unit_display_name = "ERV-1"
    space.floor_area = 10.0
    space.weighted_floor_area = 10.0
    space.net_volume = 27.5
    space.ventilation.load.flow_supply = _flow
    space.ventilation.load.flow_extract = _flow
    return space


def test_adding_spaces_sums_the_ventilation_load(reset_class_counters) -> None:
    space_a, space_b = _space_with_flow(53.24), _space_with_flow(53.24)

    merged = space_a + space_b

    assert merged.ventilation.load.flow_supply == pytest.approx(106.48)
    assert merged.ventilation.load.flow_extract == pytest.approx(106.48)


def test_adding_spaces_does_not_mutate_either_source(reset_class_counters) -> None:
    """'__add__' must not write the summed load back through a shared reference.

    The ERV merge runs while an exporter is serializing, so a source-mutating
    '__add__' means exporting one project twice compounds the flows.
    """
    space_a, space_b = _space_with_flow(53.24), _space_with_flow(53.24)

    space_a + space_b

    assert space_a.ventilation.load.flow_supply == pytest.approx(53.24)
    assert space_b.ventilation.load.flow_supply == pytest.approx(53.24)


def test_adding_spaces_is_repeatable(reset_class_counters) -> None:
    """Merging the same group twice must give the same answer both times."""
    space_a, space_b = _space_with_flow(53.24), _space_with_flow(53.24)

    # -- read the value out each time: while '__add__' aliases the source program,
    # -- holding the merged Spaces would have both names pointing at one object.
    first = (space_a + space_b).ventilation.load.flow_supply
    second = (space_a + space_b).ventilation.load.flow_supply

    assert first == pytest.approx(second)


def test_merged_space_does_not_share_its_ventilation_program(reset_class_counters) -> None:
    space_a, space_b = _space_with_flow(53.24), _space_with_flow(53.24)

    merged = space_a + space_b

    assert merged.ventilation is not space_a.ventilation
    assert merged.ventilation.load is not space_a.ventilation.load


def test_merged_space_keeps_the_registered_ventilation_schedule(reset_class_counters) -> None:
    """The schedule is a project-registered utilization pattern referenced by id_num.

    It must stay the *same object*, not a copy - a copied schedule is unregistered
    and the exporters would write a dangling 'IdentNrUtilizationPatternVent'.
    """
    space_a, space_b = _space_with_flow(53.24), _space_with_flow(53.24)

    merged = space_a + space_b

    assert merged.ventilation.schedule is space_a.ventilation.schedule
