# -*- Python Version: 3.10 -*-

"""Tests for PHPP 'SummVent' summer heat-recovery mode writes."""

from types import SimpleNamespace

import pytest

from PHX.model import project
from PHX.model.enums.hvac import PhxSummerBypassMode
from PHX.PHPP.phpp_app import PHPPConnection
from PHX.PHPP.phpp_model.summ_vent_data import SummerHrvMode, SummVentExportError
from PHX.PHPP.sheet_io.io_exceptions import FindSectionMarkerException
from PHX.PHPP.sheet_io.io_summ_vent import SummVent
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

HEADER = "HRV/ERV in summer (check only one field)"


def _connect(_shape_filename: str, _header_cell: str | None):
    shape = load_shape(_shape_filename)
    seed = {_header_cell: HEADER} if _header_cell else {}
    fake_xl = FakeXLFramework(sheet_names=[shape.SUMM_VENT.name], seed={shape.SUMM_VENT.name: seed})
    outputs: list[str] = []
    connection = XLConnection(xl_framework=fake_xl, output=outputs.append)
    return fake_xl, connection, shape, outputs


@pytest.mark.parametrize(
    ("shape_filename", "header_cell", "option_cells"),
    (
        ("EN_10_6.json", "Q14", ("R15", "R16", "R17", "R18")),
        ("EN_9_6A.json", "Q20", ("R21", "R22", "R23", "R24")),
    ),
)
@pytest.mark.parametrize("mode", tuple(PhxSummerBypassMode))
def test_each_mode_writes_one_x_and_clears_its_siblings(
    shape_filename: str,
    header_cell: str,
    option_cells: tuple[str, str, str, str],
    mode: PhxSummerBypassMode,
):
    fake_xl, connection, shape, _ = _connect(shape_filename, header_cell)
    model = SummerHrvMode(shape.SUMM_VENT, mode)

    emitted = model.create_xl_items(shape.SUMM_VENT.name, int(header_cell[1:]))
    assert {item.xl_range: item.write_value for item in emitted} == {
        cell: "x" if index == mode.value - 1 else "" for index, cell in enumerate(option_cells)
    }

    SummVent(connection, shape.SUMM_VENT).write_summer_hrv_mode(model)

    assert fake_xl.written_state()[shape.SUMM_VENT.name] == {
        cell: "x" if index == mode.value - 1 else None for index, cell in enumerate(option_cells)
    }


def test_missing_header_raises():
    _, connection, shape, _ = _connect("EN_10_6.json", None)

    with pytest.raises(FindSectionMarkerException, match="HRV/ERV in summer"):
        SummVent(connection, shape.SUMM_VENT).write_summer_hrv_mode(
            SummerHrvMode(shape.SUMM_VENT, PhxSummerBypassMode.ALWAYS)
        )


def test_unmapped_mode_raises():
    shape = load_shape("EN_10_6.json")

    with pytest.raises(SummVentExportError, match="not mapped"):
        SummerHrvMode(shape.SUMM_VENT, SimpleNamespace(value=5)).create_xl_items("SummVent", 14)


def _phpp_connection(_easy_ph: bool = False):
    fake_xl, connection, shape, outputs = _connect("EN_10_6.json", "Q14")
    phpp = object.__new__(PHPPConnection)
    phpp.easyPh = _easy_ph
    phpp.xl = connection
    phpp.shape = shape
    phpp.version = SimpleNamespace(number_major="10", number_minor="6", language="EN")
    phpp.summ_vent = SummVent(connection, shape.SUMM_VENT)
    return fake_xl, phpp, outputs


def test_write_project_summer_ventilation_writes_the_last_variants_mode_group():
    fake_xl, phpp, _ = _phpp_connection()
    phx_project = project.PhxProject(variants=[project.PhxVariant(), project.PhxVariant()])
    phx_project.variants[0].phius_cert.ph_building_data.summer_ventilation.summer_bypass_mode = PhxSummerBypassMode.NONE
    phx_project.variants[1].phius_cert.ph_building_data.summer_ventilation.summer_bypass_mode = (
        PhxSummerBypassMode.ENTHALPY_CONTROLLED
    )

    phpp.write_project_summer_ventilation(phx_project)

    assert fake_xl.written_state()[phpp.shape.SUMM_VENT.name] == {
        "R15": None,
        "R16": None,
        "R17": "x",
        "R18": None,
    }


def test_write_project_summer_ventilation_skips_easyph():
    fake_xl, phpp, _ = _phpp_connection(_easy_ph=True)

    phpp.write_project_summer_ventilation(project.PhxProject(variants=[project.PhxVariant()]))

    assert fake_xl.written_state() == {}
