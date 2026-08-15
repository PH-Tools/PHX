# -*- Python Version: 3.10 -*-

"""One invariant, across every IO class that locates a section by its header.

'find_section_header_row' reads a block of a column starting at '_row_start'
and returns the row carrying the section's marker string. The value is a
WORKSHEET ROW NUMBER, never an index into the block that was read - which
means the scan must enumerate from '_row_start', not from 0 and not from a
hard-coded 1.

Row positions are not fixed across PHPP files: an entry block sits lower in a
populated project file than in an empty one, so these locators are the only
thing standing between the write path and the wrong row.

Regression cover for the three classes that enumerated 0-based
(Components.Ventilators, Components.Frames, AddnlVent.Spaces) and the two that
hard-coded 'start=1' (Areas.Surfaces, ElecNonRes.Lighting).
"""

from unittest.mock import Mock

import pytest

from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.sheet_io.io_addnl_vent import Spaces, VentUnits
from PHX.PHPP.sheet_io.io_areas import Surfaces
from PHX.PHPP.sheet_io.io_components import Frames, Ventilators
from PHX.PHPP.sheet_io.io_elec_non_res import Lighting
from tests.test_PHPP.test_sheet_io.conftest import SHAPE_FILENAMES, load_shape


def _ventilators(shape: PhppShape):
    return Ventilators(Mock(), shape.COMPONENTS), shape.COMPONENTS.ventilators.locator_string_header


def _frames(shape: PhppShape):
    return Frames(Mock(), shape.COMPONENTS), shape.COMPONENTS.frames.locator_string_header


def _spaces(shape: PhppShape):
    return Spaces(Mock(), shape.ADDNL_VENT), shape.ADDNL_VENT.rooms.locator_string_header


def _vent_units(shape: PhppShape):
    return VentUnits(Mock(), shape.ADDNL_VENT), shape.ADDNL_VENT.units.locator_string_header


def _surfaces(shape: PhppShape):
    return Surfaces(Mock(), shape.AREAS, {}), shape.AREAS.surface_rows.locator_string_header


def _lighting(shape: PhppShape):
    return Lighting(Mock(), shape.ELEC_NON_RES), shape.ELEC_NON_RES.lighting_rows.locator_string_header


# -- (builder, default '_row_start' of that class's find_section_header_row)
SECTION_LOCATORS = (
    pytest.param(_ventilators, 1, id="Components.Ventilators"),
    pytest.param(_frames, 1, id="Components.Frames"),
    pytest.param(_spaces, 1, id="AddnlVent.Spaces"),
    pytest.param(_vent_units, 50, id="AddnlVent.VentUnits"),
    pytest.param(_surfaces, 1, id="Areas.Surfaces"),
    pytest.param(_lighting, 1, id="ElecNonRes.Lighting"),
)


@pytest.mark.parametrize("build_io, default_row_start", SECTION_LOCATORS)
def test_header_row_is_a_worksheet_row_number(build_io, default_row_start: int) -> None:
    """A marker 7 rows into the default read block reports as 'default + 7'."""
    io_class, marker = build_io(load_shape())
    io_class.xl.get_single_column_data.return_value = [None] * 7 + [marker]

    assert io_class.find_section_header_row() == default_row_start + 7


@pytest.mark.parametrize("build_io, default_row_start", SECTION_LOCATORS)
def test_header_row_honours_a_non_default_row_start(build_io, default_row_start: int) -> None:
    """A search told to begin at row 200 must report rows relative to row 200."""
    io_class, marker = build_io(load_shape())
    io_class.xl.get_single_column_data.return_value = [None, marker]

    assert io_class.find_section_header_row(_row_start=200) == 201


@pytest.mark.parametrize("shape_filename", SHAPE_FILENAMES)
def test_ventilator_header_row_is_a_row_number_in_every_localization(shape_filename: str) -> None:
    """The pristine PHPP ventilator header sits on row 8 in every shipped shape."""
    io_class, marker = _ventilators(load_shape(shape_filename))
    io_class.xl.get_single_column_data.return_value = [None] * 7 + [marker]

    assert io_class.find_section_header_row() == 8
