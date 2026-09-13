# -*- Python Version: 3.10 -*-

"""Tests for PHPP climate-block writing and active-data-set selection."""

from dataclasses import fields

import pytest

from PHX.model import phx_site, project
from PHX.PHPP.phpp_app import PHPPConnection
from PHX.PHPP.phpp_model import climate_entry
from PHX.PHPP.sheet_io.io_climate import Climate
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

SHAPE_CLIMATE_LAYOUTS = (
    ("EN_9_6A.json", 61, "L", "P", "Klimadaten_Muster", "ud-User Data", ("AE", 63, 162)),
    ("EN_9_7IP.json", 61, "L", "P", "IP_Klimadaten_Muster", "ud-User Data", ("AE", 63, 162)),
    ("EN_10_3.json", 67, "D", "E", "Klimadaten_Muster", "ud-User-defined data", ("AE", 69, 175)),
    ("EN_10_4A.json", 67, "D", "E", "Klimadaten_Muster", "ud-User-defined data", ("AE", 69, 175)),
    ("EN_10_4IP.json", 67, "D", "E", "IP_Klimadaten_Muster", "ud-User-defined data", ("AE", 69, 175)),
    ("EN_10_6.json", 67, "D", "E", "Klimadaten_Muster", "ud-User-defined data", ("AE", 69, 175)),
    ("EN_10_6IP.json", 67, "D", "E", "IP_Klimadaten_Muster", "ud-User-defined data", ("AE", 69, 175)),
)


def _named_ranges() -> dict[str, dict[str, str]]:
    return {
        "Climate": {
            "Klima_Region": "D9",
            "Klima_Region2": "D10",
            "Klima_Standort": "D12",
            "Klimadaten_Muster": "D67",
            "Klimadaten_Muster_Quelle": "E76",
        }
    }


def _site() -> phx_site.PhxSite:
    site = phx_site.PhxSite(display_name="Synthetic Climate", source="Synthetic source")
    site.location.latitude = 41.25
    site.location.longitude = -73.5
    site.climate.station_elevation = 125.0
    site.climate.daily_temp_swing = 9.5
    monthly_fields = (
        "temperature_air",
        "radiation_north",
        "radiation_east",
        "radiation_south",
        "radiation_west",
        "radiation_global",
        "temperature_dewpoint",
        "temperature_sky",
    )
    for field_index, field_name in enumerate(monthly_fields):
        setattr(site.climate, field_name, [float(field_index * 100 + month) for month in range(12)])
    return site


def _connection(
    _seed: dict[str, object] | None = None,
    _epoch_deltas: list[dict[str, dict[str, object]]] | None = None,
) -> tuple[FakeXLFramework, PHPPConnection]:
    shape = load_shape("EN_10_6.json")
    fake_xl = FakeXLFramework(
        sheet_names=[shape.CLIMATE.name],
        seed={shape.CLIMATE.name: _seed or {}},
        epoch_deltas=_epoch_deltas,
        named_ranges=_named_ranges(),
    )
    xl = XLConnection(xl_framework=fake_xl)
    phpp = object.__new__(PHPPConnection)
    phpp.easyPh = False
    phpp.xl = xl
    phpp.shape = shape
    phpp.climate = Climate(xl, shape.CLIMATE)
    return fake_xl, phpp


def _export(_epoch_deltas: list[dict[str, dict[str, object]]]) -> tuple[FakeXLFramework, dict[str, object]]:
    fake_xl, phpp = _connection(_epoch_deltas=_epoch_deltas)
    variant = project.PhxVariant(site=_site())
    phpp.write_climate_data(project.PhxProject(variants=[variant]))
    return fake_xl, fake_xl.written_state()["Climate"]


@pytest.mark.parametrize(
    "shape_filename,start_row,name_col,comment_col,name_range,country_literal,country_validation",
    SHAPE_CLIMATE_LAYOUTS,
)
def test_localized_climate_shape_carries_verified_block_and_gate_data(
    shape_filename: str,
    start_row: int,
    name_col: str,
    comment_col: str,
    name_range: str,
    country_literal: str,
    country_validation: tuple[str, int, int],
) -> None:
    climate = load_shape(shape_filename).CLIMATE

    assert climate.ud_block.start_row == start_row
    assert climate.ud_block.input_columns.name == name_col
    assert climate.ud_block.input_columns.comment == comment_col
    assert climate.named_ranges.ud_block_name == name_range
    assert climate.user_defined_selectors is not None
    assert climate.user_defined_selectors.country == country_literal
    assert climate.library_validation_ranges is not None
    country = climate.library_validation_ranges.country
    assert (country.column, country.start_row, country.end_row) == country_validation


def test_user_defined_block_writes_name_comment_and_existing_data_cells() -> None:
    fake_xl, phpp = _connection()
    phpp.climate.write_climate_block(climate_entry.ClimateDataBlock(phpp.shape.CLIMATE, _site()))

    written = fake_xl.written_state()["Climate"]
    assert written["D67"] == "Synthetic Climate"
    assert written["E76"] == "Synthetic source"
    assert "L67" not in written
    assert "P67" not in written
    assert written["F67"] == pytest.approx(41.25)
    assert written["H67"] == pytest.approx(-73.5)
    assert written["J67"] == pytest.approx(125.0)
    assert written["N67"] == pytest.approx(9.5)
    assert all(f"{column}{row}" in written for row in range(68, 76) for column in "EFGHIJKLMNOP")
    assert written["E68"] == pytest.approx(0.0)
    assert written["P75"] == pytest.approx(711.0)


def test_valid_library_triple_skips_user_defined_block() -> None:
    fake_xl, written = _export(
        [
            {"Climate": {"AE69": "US-United States of America"}},
            {"Climate": {"AJ69": "New York"}},
            {"Climate": {"AU69": "US0055b-New York"}},
        ]
    )

    assert written["D9"] == "US-United States of America"
    assert written["D10"] == "New York"
    assert written["D12"] == "US0055b-New York"
    assert "D67" not in written
    assert "E76" not in written
    assert fake_xl._epoch == 3


def test_invalid_data_set_falls_back_without_library_codes() -> None:
    fake_xl, written = _export(
        [
            {"Climate": {"AE69": "US-United States of America"}},
            {"Climate": {"AJ69": "New York"}},
            {"Climate": {"AU69": "A different data set"}},
        ]
    )

    assert written["D9"] == "ud-User-defined data"
    assert written["D10"] == "All"
    assert written["D12"] == "ud---00-Synthetic Climate"
    assert written["D67"] == "Synthetic Climate"
    assert written["E76"] == "Synthetic source"
    assert fake_xl._epoch == 3


def test_invalid_country_falls_back_cleanly() -> None:
    fake_xl, written = _export([{"Climate": {"AE69": "A different country"}}])

    assert written["D9"] == "ud-User-defined data"
    assert written["D10"] == "All"
    assert written["D12"] == "ud---00-Synthetic Climate"
    assert written["D67"] == "Synthetic Climate"
    assert fake_xl._epoch == 1


def test_phpp_dataset_name_is_a_dataclass_field() -> None:
    assert "dataset_name" in {field.name for field in fields(phx_site.PhxPHPPCodes)}
    assert phx_site.PhxPHPPCodes(dataset_name="Synthetic data").dataset_name == "Synthetic data"
