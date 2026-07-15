# -*- Python Version: 3.10 -*-

"""Unit tests for the in-memory fake xl-framework itself."""

import pytest

from tests.test_xl_replay import fake_xl_framework as fake


def _framework(**kwargs) -> fake.FakeXLFramework:
    return fake.FakeXLFramework(sheet_names=["Areas", "Windows"], **kwargs)


# -----------------------------------------------------------------------------
# -- Address math


@pytest.mark.parametrize(
    "col,num",
    [("A", 1), ("Z", 26), ("AA", 27), ("AZ", 52), ("IH", 242), ("XFD", 16384)],
)
def test_col_num_round_trip(col, num):
    assert fake.col_to_num(col) == num
    assert fake.num_to_col(num) == col


@pytest.mark.parametrize(
    "addr,span",
    [
        ("B12", (2, 12, 2, 12)),
        ("$B$12", (2, 12, 2, 12)),
        ("A1:C5", (1, 1, 3, 5)),
        ("C5:A1", (1, 1, 3, 5)),  # normalized
        ("A:A", (1, 1, 1, fake.MAXROW)),
        ("5:5", (1, 5, fake.MAXCOL, 5)),
        ("IH13:II20", (242, 13, 243, 20)),
    ],
)
def test_parse_range(addr, span):
    assert fake.parse_range(addr) == span


# -----------------------------------------------------------------------------
# -- Value normalization


@pytest.mark.parametrize(
    "raw,stored",
    [
        (12, 12.0),
        (12.5, 12.5),
        (True, True),
        (None, None),
        ("hello", "hello"),
        ("'ForcedText", "ForcedText"),  # apostrophe prefix is not stored
        ("", None),  # empty text reads back as empty cell
        ("'", None),
    ],
)
def test_normalize_value(raw, stored):
    assert fake.normalize_value(raw) == stored


# -----------------------------------------------------------------------------
# -- Read / write semantics


def test_scalar_write_and_read():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = 12
    assert sheet.range("L41").value == 12.0
    assert sheet.range("Z99").value is None


def test_1d_list_writes_across_the_row():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = ["a", "b", "c"]
    assert sheet.range("L41").value == "a"
    assert sheet.range("M41").value == "b"
    assert sheet.range("N41").value == "c"


def test_1d_list_with_transpose_writes_down_the_column():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").options(transpose=True).value = ["a", "b", "c"]
    assert sheet.range("L41").value == "a"
    assert sheet.range("L42").value == "b"
    assert sheet.range("L43").value == "c"


def test_2d_write_and_block_read():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = [[1, 2], [3, 4], [5, 6]]
    assert sheet.range("L41:M43").value == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]


def test_column_block_read_returns_flat_list():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").options(transpose=True).value = ["a", "b", "c"]
    assert sheet.range("L40:L44").value == [None, "a", "b", "c", None]


def test_row_block_read_returns_flat_list():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = ["a", "b"]
    assert sheet.range("K41:N41").value == [None, "a", "b", None]


def test_read_with_transpose_returns_columns():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("A1").value = [[1, 2], [3, 4]]
    assert sheet.range("A1:B2").options(transpose=True).value == [[1.0, 3.0], [2.0, 4.0]]


def test_read_with_ndim_2_forces_2d():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("A1").options(transpose=True).value = [1, 2, 3]
    assert sheet.range("A1:A3").options(ndim=2).value == [[1.0], [2.0], [3.0]]


def test_write_none_clears_cell():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = "something"
    sheet.range("L41").value = None
    assert sheet.range("L41").value is None


def test_end_up_finds_last_used_row():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = "x"
    sheet.range("L99").value = "y"

    bottom = sheet.range(f"L{fake.MAXROW}")
    assert bottom.end("up").row == 99
    assert sheet.range("L50").end("up").row == 41  # from mid-column
    assert sheet.range(f"A{fake.MAXROW}").end("up").row == 1  # empty column


def test_end_left_finds_last_used_column():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("D7").value = "x"
    last_col_cell = sheet.range(f"{fake.num_to_col(fake.MAXCOL)}7")
    assert last_col_cell.end("left").column == 4


def test_last_cell_address_of_full_column():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    rng = sheet.range("L:L")
    assert rng.last_cell.address == f"$L${fake.MAXROW}"
    # -- and the address can be parsed back by sheet.range()
    assert sheet.range(rng.last_cell.address).row == fake.MAXROW


# -----------------------------------------------------------------------------
# -- Seeding, epochs, written-state


def test_seeded_values_are_readable():
    xl = _framework(seed={"Areas": {"K31": "Area input", "L34": "Treated floor area"}})
    sheet = xl.books.active.sheets["Areas"]
    assert sheet.range("K31").value == "Area input"
    assert sheet.range("K30:K32").value == [None, "Area input", None]


def test_epoch_delta_applied_on_calculate_but_not_over_written_cells():
    xl = _framework(
        seed={"Areas": {"Q10": None}},
        epoch_deltas=[{"Areas": {"Q10": "01ud", "L41": "recalced-formula"}}],
    )
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = "written-by-phx"

    xl.books.active.app.calculate()
    assert sheet.range("Q10").value == "01ud"  # recalc-computed value appears
    assert sheet.range("L41").value == "written-by-phx"  # writes are never clobbered

    xl.books.active.app.calculate()  # extra recalcs with no recorded delta are fine


def test_written_state_reports_only_written_cells():
    xl = _framework(seed={"Areas": {"K31": "seeded"}})
    sheet = xl.books.active.sheets["Areas"]
    sheet.range("L41").value = ["'MyWall", 12]
    xl.books.active.sheets["Windows"].range("N23").value = None

    assert xl.written_state() == {
        "Areas": {"L41": "MyWall", "M41": 12.0},
        "Windows": {"N23": None},
    }


def test_color_state_tracks_range_and_font_colors():
    xl = _framework()
    sheet = xl.books.active.sheets["Areas"]
    rng = sheet.range("L41")
    rng.color = (255, 0, 0)
    rng.font.color = (0, 0, 255)
    assert xl.color_state() == {"Areas": {"L41": [(255, 0, 0), (0, 0, 255)]}}


# -----------------------------------------------------------------------------
# -- Works as an XLConnection framework


def test_xl_connection_end_to_end_on_fake():
    from PHX.xl import xl_app, xl_data

    xl = _framework(seed={"Areas": {"K31": "Area input"}})
    conn = xl_app.XLConnection(xl_framework=xl)

    assert conn.worksheet_names == {"AREAS", "WINDOWS"}
    assert conn.get_single_column_data("Areas", "K", 30, 32) == [None, "Area input", None]
    assert conn.get_row_num_of_value_in_column("Areas", 1, 40, "K", "Area input") == 31

    conn.write_xl_item(xl_data.XlItem("Areas", "L41", "'MyWall"))
    assert conn.get_data("Areas", "L41") == "MyWall"
    assert conn.get_last_used_row_num_in_column("Areas", "L") == 41

    with conn.in_silent_mode():
        pass  # toggles + exit-calculate must not raise on the fake
