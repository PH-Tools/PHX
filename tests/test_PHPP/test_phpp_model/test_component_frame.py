# -*- Python Version: 3.10 -*-

"""Tests for PHX.PHPP.phpp_model.component_frame.FrameRow"""

import pytest

from PHX.model.constructions import PhxConstructionWindow, PhxWindowFrameElement
from PHX.PHPP.phpp_localization.shape_model import (
    ComponentsFrames,
    ComponentsFramesInputs,
    InputItem,
)
from PHX.PHPP.phpp_model.component_frame import FrameRow

# -- Helpers ------------------------------------------------------------------


def _make_frames_shape(psi_g_columns: dict[str, str], psi_i_columns: dict[str, str] | None = None) -> ComponentsFrames:
    """Build a minimal ComponentsFrames shape with specified psi_g column mappings."""
    psi_i = psi_i_columns or {"left": "IY", "right": "IZ", "bottom": "JA", "top": "JB"}
    return ComponentsFrames(
        locator_col_header="A",
        locator_string_header="x",
        locator_col_entry="A",
        locator_string_entry="x",
        inputs=ComponentsFramesInputs(
            id=InputItem(column="A"),
            description=InputItem(column="B"),
            u_value_left=InputItem(column="C", unit="W/M2K"),
            u_value_right=InputItem(column="D", unit="W/M2K"),
            u_value_bottom=InputItem(column="E", unit="W/M2K"),
            u_value_top=InputItem(column="F", unit="W/M2K"),
            width_left=InputItem(column="G", unit="M"),
            width_right=InputItem(column="H", unit="M"),
            width_bottom=InputItem(column="I", unit="M"),
            width_top=InputItem(column="J", unit="M"),
            psi_g_left=InputItem(column=psi_g_columns["left"], unit="W/MK"),
            psi_g_right=InputItem(column=psi_g_columns["right"], unit="W/MK"),
            psi_g_bottom=InputItem(column=psi_g_columns["bottom"], unit="W/MK"),
            psi_g_top=InputItem(column=psi_g_columns["top"], unit="W/MK"),
            psi_i_left=InputItem(column=psi_i["left"], unit="W/MK"),
            psi_i_right=InputItem(column=psi_i["right"], unit="W/MK"),
            psi_i_bottom=InputItem(column=psi_i["bottom"], unit="W/MK"),
            psi_i_top=InputItem(column=psi_i["top"], unit="W/MK"),
        ),
    )


def _make_components_shape(frames: ComponentsFrames):
    """Wrap a ComponentsFrames in a minimal object that FrameRow expects as `shape`."""

    class _FakeComponents:
        def __init__(self, frames):
            self.frames = frames

    return _FakeComponents(frames)


def _make_construction(
    psi_g: dict[str, float],
    psi_i: dict[str, float] | None = None,
) -> PhxConstructionWindow:
    """Build a PhxConstructionWindow with specified per-side psi values."""
    psi_i = psi_i or {"left": 0.0, "right": 0.0, "bottom": 0.0, "top": 0.0}
    con = PhxConstructionWindow()
    con.frame_left = PhxWindowFrameElement(psi_glazing=psi_g["left"], psi_install=psi_i["left"])
    con.frame_right = PhxWindowFrameElement(psi_glazing=psi_g["right"], psi_install=psi_i["right"])
    con.frame_bottom = PhxWindowFrameElement(psi_glazing=psi_g["bottom"], psi_install=psi_i["bottom"])
    con.frame_top = PhxWindowFrameElement(psi_glazing=psi_g["top"], psi_install=psi_i["top"])
    return con


def _items_for_column_range(xl_items, column: str):
    """Return XlItems whose xl_range starts with the given column letters."""
    return [item for item in xl_items if item.xl_range.rstrip("0123456789") == column]


# -- Tests: psi_glazing -------------------------------------------------------


class TestPsiGlazingSameColumn:
    """PHPP 10.x: all four psi_g fields map to the same column."""

    SAME_COL = {"left": "IR", "right": "IR", "bottom": "IR", "top": "IR"}

    def test_uniform_values_writes_that_value(self, reset_class_counters):
        """When all four psi_g values are identical, the written value should equal that value."""
        shape = _make_components_shape(_make_frames_shape(self.SAME_COL))
        con = _make_construction(psi_g={"left": 0.04, "right": 0.04, "bottom": 0.04, "top": 0.04})
        row = FrameRow(shape=shape, phx_construction=con)
        xl_items = row.create_xl_items("Components", 10)

        psi_g_items = _items_for_column_range(xl_items, "IR")
        assert len(psi_g_items) == 1, f"Expected 1 psi_g item for same-column, got {len(psi_g_items)}"
        assert psi_g_items[0]._write_value == pytest.approx(0.04)

    def test_non_uniform_values_writes_average(self, reset_class_counters):
        """When four different psi_g values map to the same column, write their simple average."""
        shape = _make_components_shape(_make_frames_shape(self.SAME_COL))
        con = _make_construction(psi_g={"left": 0.005, "right": 0.014, "bottom": 0.001, "top": 0.005})
        row = FrameRow(shape=shape, phx_construction=con)
        xl_items = row.create_xl_items("Components", 10)

        psi_g_items = _items_for_column_range(xl_items, "IR")
        expected_avg = (0.005 + 0.014 + 0.001 + 0.005) / 4.0
        assert len(psi_g_items) == 1, f"Expected 1 psi_g item for same-column, got {len(psi_g_items)}"
        assert psi_g_items[0]._write_value == pytest.approx(expected_avg)


class TestPsiGlazingDifferentColumns:
    """PHPP 9.x: each psi_g field maps to a different column."""

    DIFF_COL = {"left": "IU", "right": "IV", "bottom": "IW", "top": "IX"}

    def test_non_uniform_values_writes_individual(self, reset_class_counters):
        """When psi_g fields map to different columns, write each value individually."""
        shape = _make_components_shape(_make_frames_shape(self.DIFF_COL))
        con = _make_construction(psi_g={"left": 0.005, "right": 0.014, "bottom": 0.001, "top": 0.005})
        row = FrameRow(shape=shape, phx_construction=con)
        xl_items = row.create_xl_items("Components", 10)

        left_items = _items_for_column_range(xl_items, "IU")
        right_items = _items_for_column_range(xl_items, "IV")
        bottom_items = _items_for_column_range(xl_items, "IW")
        top_items = _items_for_column_range(xl_items, "IX")

        assert len(left_items) == 1
        assert left_items[0]._write_value == pytest.approx(0.005)
        assert len(right_items) == 1
        assert right_items[0]._write_value == pytest.approx(0.014)
        assert len(bottom_items) == 1
        assert bottom_items[0]._write_value == pytest.approx(0.001)
        assert len(top_items) == 1
        assert top_items[0]._write_value == pytest.approx(0.005)


# -- Tests: psi_install -------------------------------------------------------


class TestPsiInstallSharedColumns:
    """PHPP 10.x: psi_i_left and psi_i_right share column JZ; bottom (KB) and top (KA) are separate."""

    PSI_G_SAME = {"left": "IR", "right": "IR", "bottom": "IR", "top": "IR"}
    PSI_I_MIXED = {"left": "JZ", "right": "JZ", "bottom": "KB", "top": "KA"}

    def test_shared_left_right_writes_average(self, reset_class_counters):
        """Left and right psi_i share a column — should write their average, not just right."""
        shape = _make_components_shape(_make_frames_shape(self.PSI_G_SAME, self.PSI_I_MIXED))
        con = _make_construction(
            psi_g={"left": 0.04, "right": 0.04, "bottom": 0.04, "top": 0.04},
            psi_i={"left": 0.01, "right": 0.03, "bottom": 0.05, "top": 0.02},
        )
        row = FrameRow(shape=shape, phx_construction=con)
        xl_items = row.create_xl_items("Components", 10)

        jz_items = _items_for_column_range(xl_items, "JZ")
        kb_items = _items_for_column_range(xl_items, "KB")
        ka_items = _items_for_column_range(xl_items, "KA")

        assert len(jz_items) == 1, f"Expected 1 item for shared JZ column, got {len(jz_items)}"
        assert jz_items[0]._write_value == pytest.approx((0.01 + 0.03) / 2.0)
        assert len(kb_items) == 1
        assert kb_items[0]._write_value == pytest.approx(0.05)
        assert len(ka_items) == 1
        assert ka_items[0]._write_value == pytest.approx(0.02)


class TestPsiInstallDifferentColumns:
    """PHPP 9.x: all four psi_i fields map to different columns."""

    PSI_G_DIFF = {"left": "IU", "right": "IV", "bottom": "IW", "top": "IX"}
    PSI_I_DIFF = {"left": "IY", "right": "IZ", "bottom": "JA", "top": "JB"}

    def test_all_different_writes_individual(self, reset_class_counters):
        shape = _make_components_shape(_make_frames_shape(self.PSI_G_DIFF, self.PSI_I_DIFF))
        con = _make_construction(
            psi_g={"left": 0.04, "right": 0.04, "bottom": 0.04, "top": 0.04},
            psi_i={"left": 0.01, "right": 0.03, "bottom": 0.05, "top": 0.02},
        )
        row = FrameRow(shape=shape, phx_construction=con)
        xl_items = row.create_xl_items("Components", 10)

        assert len(_items_for_column_range(xl_items, "IY")) == 1
        assert _items_for_column_range(xl_items, "IY")[0]._write_value == pytest.approx(0.01)
        assert len(_items_for_column_range(xl_items, "IZ")) == 1
        assert _items_for_column_range(xl_items, "IZ")[0]._write_value == pytest.approx(0.03)
        assert len(_items_for_column_range(xl_items, "JA")) == 1
        assert _items_for_column_range(xl_items, "JA")[0]._write_value == pytest.approx(0.05)
        assert len(_items_for_column_range(xl_items, "JB")) == 1
        assert _items_for_column_range(xl_items, "JB")[0]._write_value == pytest.approx(0.02)
