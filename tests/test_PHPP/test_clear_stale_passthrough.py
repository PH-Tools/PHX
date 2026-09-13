# -*- Python Version: 3.10 -*-

"""Tests for the opt-in stale-row clearing flag through the PHPP export stack."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from PHX import hbjson_to_phpp, run
from PHX.model import hvac, project
from PHX.model.hvac.ducting import PhxDuctElement
from PHX.PHPP import phpp_app


@pytest.mark.parametrize("clear_stale", (False, True))
def test_project_export_forwards_clear_stale_to_list_writers(monkeypatch, clear_stale: bool) -> None:
    monkeypatch.setattr(hbjson_to_phpp, "validate_project_export_readiness", Mock())
    connection = Mock(spec=phpp_app.PHPPConnection)
    phx_project = project.PhxProject()

    if clear_stale:
        hbjson_to_phpp.write_phx_project_to_phpp(connection, phx_project, clear_stale=True)
    else:
        hbjson_to_phpp.write_phx_project_to_phpp(connection, phx_project)

    connection.write_project_window_components.assert_called_once_with(phx_project, clear_stale=clear_stale)
    connection.write_project_ventilation_components.assert_called_once_with(phx_project, clear_stale=clear_stale)
    connection.write_project_ventilators.assert_called_once_with(phx_project, clear_stale=clear_stale)
    connection.write_project_vent_ducting.assert_called_once_with(phx_project, clear_stale=clear_stale)
    connection.write_project_spaces.assert_called_once_with(phx_project, clear_stale=clear_stale)


def _project_with_ventilator_and_duct() -> project.PhxProject:
    phx_project = project.PhxProject()
    variant = project.PhxVariant()
    phx_project.add_new_variant(variant)

    ventilator = hvac.PhxDeviceVentilator(display_name="Test Ventilator")
    collection = variant.mech_collections[0]
    collection.add_new_mech_device("test-ventilator", ventilator)
    collection.add_vent_ducting(PhxDuctElement("test-duct", "Test Duct", ventilator.id_num))
    return phx_project


def _phpp_connection() -> phpp_app.PHPPConnection:
    connection = phpp_app.PHPPConnection.__new__(phpp_app.PHPPConnection)
    connection.easyPh = False
    connection.shape = SimpleNamespace(COMPONENTS=object(), ADDNL_VENT=object())
    connection.xl = SimpleNamespace(output=Mock())
    connection.components = Mock()
    connection.addnl_vent = Mock()
    return connection


@pytest.mark.parametrize("clear_stale", (False, True))
def test_phpp_app_forwards_clear_stale_to_sheet_writers(reset_class_counters, clear_stale: bool) -> None:
    connection = _phpp_connection()
    phx_project = _project_with_ventilator_and_duct()

    kwargs = {"clear_stale": True} if clear_stale else {}
    connection.write_project_window_components(phx_project, **kwargs)
    connection.write_project_ventilation_components(phx_project, **kwargs)
    connection.write_project_ventilators(phx_project, **kwargs)
    connection.write_project_vent_ducting(phx_project, **kwargs)
    connection.write_project_spaces(phx_project, **kwargs)

    connection.components.write_glazings.assert_called_once_with([], clear_stale=clear_stale)
    connection.components.write_frames.assert_called_once_with([], clear_stale=clear_stale)
    assert connection.components.write_ventilators.call_args.kwargs == {"clear_stale": clear_stale}
    assert len(connection.components.write_ventilators.call_args.args[0]) == 1
    assert connection.addnl_vent.write_vent_units.call_args.kwargs == {"clear_stale": clear_stale}
    assert len(connection.addnl_vent.write_vent_units.call_args.args[0]) == 1
    assert connection.addnl_vent.write_vent_ducts.call_args.kwargs == {"clear_stale": clear_stale}
    assert len(connection.addnl_vent.write_vent_ducts.call_args.args[0]) == 1
    connection.addnl_vent.write_spaces.assert_called_once_with([], clear_stale=clear_stale)


@pytest.mark.parametrize(
    "argv, expected",
    (
        pytest.param([], (False, False), id="no-flags"),
        pytest.param(["--clear-stale"], (False, True), id="clear-only"),
        pytest.param(["True"], (True, False), id="variants-only"),
        pytest.param(["True", "--clear-stale"], (True, True), id="macos-layout"),
        pytest.param(["site-packages", " true ", "--clear-stale"], (True, True), id="windows-layout"),
    ),
)
def test_parse_cli_flags(argv: list[str], expected: tuple[bool, bool]) -> None:
    assert hbjson_to_phpp._parse_cli_flags(argv) == expected


@pytest.mark.parametrize(
    "os_name, clear_stale, runner_name, expected_last_arg",
    (
        pytest.param("nt", " true ", "_run_subprocess", "--clear-stale", id="windows-clear"),
        pytest.param("nt", "yes", "_run_subprocess", "False", id="windows-default"),
        pytest.param("posix", "TRUE", "_run_subprocess_from_shell", "--clear-stale", id="macos-clear"),
        pytest.param("posix", "False", "_run_subprocess_from_shell", "", id="macos-default"),
    ),
)
def test_run_phpp_command_clear_stale_token(
    monkeypatch, os_name: str, clear_stale: str, runner_name: str, expected_last_arg: str
) -> None:
    runner = Mock(return_value=(b"stdout", b"stderr"))
    fake_path = SimpleNamespace(join=run.os.path.join, isfile=lambda _: True, exists=lambda _: True)
    monkeypatch.setattr(run, "hb_folders", SimpleNamespace(python_package_path="/package", python_exe_path="python"))
    monkeypatch.setattr(run, "os", SimpleNamespace(name=os_name, path=fake_path))
    monkeypatch.setattr(run, runner_name, runner)

    run.write_hbjson_to_phpp("model.hbjson", "/site-packages", "False", clear_stale)

    commands = runner.call_args.args[0]
    assert commands[-1] == expected_last_arg
    assert ("--clear-stale" in commands) is (expected_last_arg == "--clear-stale")
