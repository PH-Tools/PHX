# -*- Python Version: 3.10 -*-

"""Tests for the PHPP 'U-values' surface-resistance selector writes.

'activate_variants' clears each constructor block before re-linking it to the
'Variants' worksheet, which wipes the two selector cells. PHPP leaves the block's
U-value blank when either one is empty, so they have to be restored.

See: https://github.com/PH-Tools/PHX/issues/118
"""

from PHX.model.constructions import PhxConstructionOpaque
from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.PHPP.phpp_localization.shape_model import UValues as UValuesShape
from PHX.PHPP.phpp_model.uvalues_constructor import ConstructorBlock
from PHX.PHPP.sheet_io.io_u_values import UValues
from PHX.PHPP.sheet_io.io_variants import VariantAssemblyLayerName
from PHX.xl.xl_app import XLConnection
from tests.test_PHPP.test_sheet_io.conftest import load_shape
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

ASSEMBLY_NAME = "Generic Ground Slab"
# -- 'get_start_rows' enumerates from row 1, so the header at L7 is block start-row 6.
START_ROW = 6
RSI_RANGE = "M10"
RSE_RANGE = "M11"


def _u_values_shape() -> UValuesShape:
    return load_shape("EN_10_6.json").UVALUES


def _connect() -> tuple[FakeXLFramework, UValues]:
    shape = _u_values_shape()
    seed = {
        "L7": shape.constructor.locator_string_header,
        "L8": ASSEMBLY_NAME,
    }
    fake_xl = FakeXLFramework(sheet_names=[shape.name], seed={shape.name: seed})
    connection = XLConnection(xl_framework=fake_xl, output=lambda _: None)
    return fake_xl, UValues(connection, shape)


def _ground_slab_block() -> ConstructorBlock:
    construction = PhxConstructionOpaque()
    construction.display_name = ASSEMBLY_NAME
    return ConstructorBlock(
        shape=_u_values_shape(),
        phx_construction=construction,
        face_type=ComponentFaceType.FLOOR,
        exposure_exterior=ComponentExposureExterior.GROUND,
    )


def test_writing_a_block_writes_both_selectors() -> None:
    fake_xl, u_values = _connect()

    u_values.write_constructor_blocks([_ground_slab_block()])

    written = fake_xl.written_state()[u_values.shape.name]
    assert written[RSI_RANGE] == "3-Floor"
    assert written[RSE_RANGE] == "2-Ground"


def test_activating_the_variants_restores_the_selectors() -> None:
    fake_xl, u_values = _connect()
    u_values.write_constructor_blocks([_ground_slab_block()])

    u_values.activate_variants([VariantAssemblyLayerName("01ud", ASSEMBLY_NAME)])

    written = fake_xl.written_state()[u_values.shape.name]
    assert written[RSI_RANGE] == "3-Floor"
    assert written[RSE_RANGE] == "2-Ground"


def test_an_assembly_this_connection_never_wrote_falls_back_to_the_phpp_defaults() -> None:
    fake_xl, u_values = _connect()

    u_values.write_surface_resistance_selectors(START_ROW, "Some Other Assembly")

    written = fake_xl.written_state()[u_values.shape.name]
    assert written[RSI_RANGE] == "2-Wall"
    assert written[RSE_RANGE] == "1-Outdoor air"
