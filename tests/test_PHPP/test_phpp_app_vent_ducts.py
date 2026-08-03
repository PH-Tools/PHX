# -*- Python Version: 3.10 -*-

"""Tests for PHPPConnection ventilation-duct row construction."""

from types import SimpleNamespace
from unittest.mock import Mock

from PHX.model.hvac.ducting import PhxDuctElement
from PHX.PHPP.phpp_app import PHPPConnection


def _project(*collections):
    return SimpleNamespace(variants=[SimpleNamespace(mech_collections=list(collections))])


def _collection(ventilator_ids=(), ducts=()):
    return SimpleNamespace(
        ventilation_devices=[SimpleNamespace(id_num=id_num) for id_num in ventilator_ids],
        vent_ducting=list(ducts),
    )


def _duct(identifier: str, vent_unit_id: int) -> PhxDuctElement:
    return PhxDuctElement(identifier, identifier, vent_unit_id)


def _connection(first_entry_row=95, last_entry_row=109):
    connection = object.__new__(PHPPConnection)
    connection.easyPh = False
    connection.shape = SimpleNamespace(ADDNL_VENT=object())
    connection.xl = SimpleNamespace(output=Mock())
    connection.addnl_vent = SimpleNamespace(
        write_vent_ducts=Mock(),
        vent_ducts=SimpleNamespace(
            section_first_entry_row=first_entry_row,
            section_last_entry_row=last_entry_row,
            find_section_first_entry_row=Mock(return_value=first_entry_row),
            find_section_last_entry_row=Mock(return_value=last_entry_row),
        ),
    )
    return connection


def test_duct_assignments_follow_ventilator_write_order(reset_class_counters):
    connection = _connection()
    project = SimpleNamespace(
        variants=[
            SimpleNamespace(mech_collections=[_collection((11, 12), (_duct("d12", 12), _duct("d11", 11)))]),
            SimpleNamespace(mech_collections=[_collection((21,), (_duct("d21", 21),))]),
        ]
    )

    connection.write_project_vent_ducting(project)

    rows = connection.addnl_vent.write_vent_ducts.call_args.args[0]
    assert [row.phx_duct.vent_unit_id for row in rows] == [12, 11, 21]
    assert [row.phpp_vent_unit_number for row in rows] == [2, 1, 3]


def test_unknown_and_eleventh_ventilator_assignments_warn_and_skip(reset_class_counters):
    connection = _connection(first_entry_row=None, last_entry_row=None)
    project = _project(_collection(range(1, 12), (_duct("unknown", 99), _duct("eleventh", 11))))

    connection.write_project_vent_ducting(project)

    connection.addnl_vent.write_vent_ducts.assert_not_called()
    connection.addnl_vent.vent_ducts.find_section_first_entry_row.assert_not_called()
    connection.addnl_vent.vent_ducts.find_section_last_entry_row.assert_not_called()
    messages = [call.args[0] for call in connection.xl.output.call_args_list]
    assert any("unknown ventilator ID 99" in message for message in messages)
    assert any("beyond the 10-unit duct limit" in message for message in messages)


def test_duplicate_ventilator_ids_in_separate_collections_keep_distinct_ordinals(reset_class_counters):
    connection = _connection()
    first = _collection((7,), (_duct("first", 7),))
    second = _collection((7,), (_duct("second", 7),))

    connection.write_project_vent_ducting(_project(first, second))

    rows = connection.addnl_vent.write_vent_ducts.call_args.args[0]
    assert [row.phx_duct.identifier for row in rows] == ["first", "second"]
    assert [row.phpp_vent_unit_number for row in rows] == [1, 2]


def test_duplicate_ventilator_ids_in_one_collection_warn_and_skip(reset_class_counters):
    connection = _connection(first_entry_row=None, last_entry_row=None)
    collection = _collection((7, 7), (_duct("ambiguous", 7),))

    connection.write_project_vent_ducting(_project(collection))

    connection.addnl_vent.write_vent_ducts.assert_not_called()
    assert "occurs more than once" in connection.xl.output.call_args.args[0]


def test_duct_free_project_has_zero_sheet_interaction():
    connection = _connection(first_entry_row=None, last_entry_row=None)

    connection.write_project_vent_ducting(_project(_collection((1,), ())))

    connection.addnl_vent.write_vent_ducts.assert_not_called()
    connection.addnl_vent.vent_ducts.find_section_first_entry_row.assert_not_called()
    connection.addnl_vent.vent_ducts.find_section_last_entry_row.assert_not_called()


def test_rows_are_truncated_to_duct_section_capacity(reset_class_counters):
    connection = _connection(first_entry_row=95, last_entry_row=96)
    ducts = (_duct("one", 1), _duct("two", 1), _duct("three", 1))

    connection.write_project_vent_ducting(_project(_collection((1,), ducts)))

    rows = connection.addnl_vent.write_vent_ducts.call_args.args[0]
    assert [row.phx_duct.identifier for row in rows] == ["one", "two"]
    assert "3 ducts exceed the 2-row" in connection.xl.output.call_args.args[0]


def test_easyph_skips_ducts_before_project_access():
    connection = _connection(first_entry_row=None, last_entry_row=None)
    connection.easyPh = True

    connection.write_project_vent_ducting(object())

    connection.addnl_vent.write_vent_ducts.assert_not_called()
