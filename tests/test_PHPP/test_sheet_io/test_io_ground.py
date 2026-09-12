# -*- Python Version: 3.10 -*-

"""Tests for the PHPP 'Ground' worksheet controller and 'PHPPConnection.write_project_ground'.

See: https://github.com/PH-Tools/PHX/issues/120
"""

from types import SimpleNamespace

import pytest

from PHX.model import ground
from PHX.model.phx_site import PhxSite
from PHX.PHPP.phpp_app import PHPPConnection
from PHX.PHPP.phpp_model.ground_data import GroundExportError, GroundFoundationBlock
from PHX.PHPP.sheet_io.io_exceptions import FindSectionMarkerException
from PHX.PHPP.sheet_io.io_ground import Ground
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import SHAPE_FILENAMES, load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

MAPPED_SHAPES = ("EN_10_3.json", "EN_10_4A.json", "EN_10_6.json")


def _connect(_shape_filename: str = "EN_10_6.json", _header_cell: str | None = "C22"):
    shape = load_shape(_shape_filename)
    seed = {_header_cell: shape.GROUND.input_block.locator_string_header} if _header_cell else {}
    fake_xl = FakeXLFramework(sheet_names=[shape.GROUND.name], seed={shape.GROUND.name: seed})
    outputs: list[str] = []
    connection = XLConnection(xl_framework=fake_xl, output=outputs.append)
    return fake_xl, connection, shape, outputs


def _slab() -> ground.PhxSlabOnGrade:
    slab = ground.PhxSlabOnGrade()
    slab.floor_slab_exposed_perimeter_m = 18.0
    return slab


def _written(_fake_xl: FakeXLFramework) -> dict:
    return _fake_xl.written_state().get("Ground", {})


@pytest.mark.parametrize("filename", SHAPE_FILENAMES)
def test_ground_layout_is_mapped_for_the_10x_si_shapes_only(filename):
    assert (load_shape(filename).GROUND.input_block is not None) == (filename in MAPPED_SHAPES)


def test_writes_are_located_from_the_header_row():
    # -- Header two rows lower than in the blank 10.6: every input moves with it.
    fake_xl, connection, shape, _ = _connect(_header_cell="C24")

    Ground(connection, shape.GROUND).write_foundation(GroundFoundationBlock(shape.GROUND, PhxSite().ground, _slab()))

    written = _written(fake_xl)
    assert written["C26"] == "x"
    assert written["H21"] == 18.0


def test_missing_header_raises():
    _, connection, shape, _ = _connect(_header_cell=None)
    block = GroundFoundationBlock(shape.GROUND, PhxSite().ground, _slab())

    with pytest.raises(FindSectionMarkerException):
        Ground(connection, shape.GROUND).write_foundation(block)


# -----------------------------------------------------------------------------
# -- PHPPConnection.write_project_ground


def _phpp_connection(_shape_filename: str = "EN_10_6.json"):
    fake_xl, connection, shape, outputs = _connect(_shape_filename, _header_cell="C22")
    phpp_conn = object.__new__(PHPPConnection)
    phpp_conn.easyPh = False
    phpp_conn.xl = connection
    phpp_conn.shape = shape
    phpp_conn.version = SimpleNamespace(number_major="10", number_minor="6", language="EN")
    phpp_conn.ground = Ground(connection, shape.GROUND)
    return fake_xl, phpp_conn, outputs


def _project(*_foundations: ground.PhxFoundation):
    building_data = SimpleNamespace(foundations=list(_foundations))
    variant = SimpleNamespace(
        name="Variant", site=PhxSite(), phius_cert=SimpleNamespace(ph_building_data=building_data)
    )
    return SimpleNamespace(variants=[variant])


def test_the_single_foundation_is_written_without_touching_the_areas_links():
    fake_xl, phpp_conn, _ = _phpp_connection()

    phpp_conn.write_project_ground(_project(_slab()))

    written = _written(fake_xl)
    assert (written["C24"], written["C30"], written["C33"], written["C40"]) == ("x", None, None, None)
    assert "H18" not in written and "P18" not in written


def test_no_foundation_writes_nothing():
    fake_xl, phpp_conn, _ = _phpp_connection()

    phpp_conn.write_project_ground(_project())

    assert _written(fake_xl) == {}


def test_more_than_one_foundation_is_refused():
    _, phpp_conn, _ = _phpp_connection()

    with pytest.raises(GroundExportError, match="one foundation per variant"):
        phpp_conn.write_project_ground(_project(_slab(), ground.PhxHeatedBasement()))


def test_unmapped_layout_warns_and_writes_nothing():
    fake_xl, phpp_conn, outputs = _phpp_connection("EN_10_6.json")
    phpp_conn.shape = load_shape("EN_9_6A.json")

    phpp_conn.write_project_ground(_project(_slab()))

    assert _written(fake_xl) == {}
    assert any("not mapped" in _ for _ in outputs)
