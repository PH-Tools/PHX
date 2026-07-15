import pytest

from PHX.xl import xl_app, xl_data, xl_typing

# -- Mock XL Framework --------------------------------------------------------


class Mock_XL_Framework(xl_typing.xl_Framework_Protocol):
    def __init__(self):
        self.books = xl_typing.xl_Books_Protocol()
        self.books.active.sheets.storage = {
            "Sheet1": xl_typing.xl_Sheet_Protocol(name="Sheet1"),
            "Sheet2": xl_typing.xl_Sheet_Protocol(name="Sheet2"),
        }
        self.apps = xl_typing.xl_apps_Protocol()


# -----------------------------------------------------------------------------


def test_xl_app_default():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)
    assert app


# -----------------------------------------------------------------------------
# Workbook


def test_xl_app_get_WorkBook_success():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)
    assert app.wb


def test_xl_app_get_WorkBook_fail():
    mock_xw = Mock_XL_Framework()

    mock_xw.books = None  # type: ignore #<--------- This should cause the error

    with pytest.raises(Exception):
        xl_app.XLConnection(xl_framework=mock_xw)


# -----------------------------------------------------------------------------
# App / Sheet Operations


def test_xl_app_silent_mode():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)
    assert app.wb.app.screen_updating
    assert app.wb.app.display_alerts
    assert app.wb.app.calculation == "automatic"

    with app.in_silent_mode():
        assert not app.wb.app.screen_updating
        assert not app.wb.app.display_alerts
        assert app.wb.app.calculation == "manual"

    assert app.wb.app.screen_updating
    assert app.wb.app.display_alerts
    assert app.wb.app.calculation == "automatic"


def test_xl_app_unprotect_all_sheets():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    for sheet in app.wb.sheets:
        assert sheet.protected

    app.unprotect_all_sheets()

    for sheet in app.wb.sheets:
        assert not sheet.protected


def test_xl_app_create_new_worksheet() -> None:
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    # -- Make sure the sheet isn't in the book to start
    new_sheet_name = "A Test Worksheet"
    assert new_sheet_name not in app.wb.sheets

    # -- Add the sheet
    app.create_new_worksheet(new_sheet_name)
    assert new_sheet_name in app.wb.sheets


def test_xl_app_create_new_worksheet_already_in_raises_ValueError() -> None:
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    new_sheet_name = "A Test Worksheet"
    assert new_sheet_name not in app.wb.sheets
    assert len(app.wb.sheets) == 2

    app.create_new_worksheet(new_sheet_name)
    app.create_new_worksheet(new_sheet_name)  # Add again
    app.create_new_worksheet(new_sheet_name)  # Add again
    assert new_sheet_name in app.wb.sheets
    assert len(app.wb.sheets) == 3  # only added the sheet once


def test_xl_app_worksheet_names_are_cached():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    assert app.worksheet_names == {"SHEET1", "SHEET2"}

    # -- A sheet added behind the facade's back is NOT seen (the cache is only
    # -- invalidated by the facade's own sheet-mutating methods).
    app.wb.sheets.storage["Sneaky"] = xl_typing.xl_Sheet_Protocol(name="Sneaky")
    assert app.worksheet_names == {"SHEET1", "SHEET2"}

    # -- The uncached primitive still reads live.
    assert "SNEAKY" in app.get_upper_case_worksheet_names()


def test_xl_app_create_new_worksheet_invalidates_names_cache():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    assert app.worksheet_names == {"SHEET1", "SHEET2"}  # prime the cache
    app.create_new_worksheet("A New Sheet")
    assert "A NEW SHEET" in app.worksheet_names

    # -- ...and the new sheet is immediately usable through the facade.
    assert app.get_sheet_by_name("A New Sheet") is not None


def test_xl_app_get_sheet_by_name():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    assert app.get_sheet_by_name("Sheet1") is not None

    with pytest.raises(KeyError):
        app.get_sheet_by_name("Not a Name")


# -----------------------------------------------------------------------------
# Column-read caching


def test_get_single_column_data_is_cached():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet = app.get_sheet_by_name("Sheet1")
    sheet.range("A1:A5").value = ["a", "b", "c", "d", "e"]
    assert app.get_single_column_data("Sheet1", "A", 1, 5) == ["a", "b", "c", "d", "e"]

    # -- Change the cell values behind the facade's back: the cached read wins.
    sheet.range("A1:A5").value = ["x", "x", "x", "x", "x"]
    assert app.get_single_column_data("Sheet1", "A", 1, 5) == ["a", "b", "c", "d", "e"]


def test_get_single_column_data_returns_a_copy_not_the_cache():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    app.get_sheet_by_name("Sheet1").range("A1:A3").value = ["a", "b", "c"]
    first = app.get_single_column_data("Sheet1", "A", 1, 3)
    first.append("MUTATED")
    assert app.get_single_column_data("Sheet1", "A", 1, 3) == ["a", "b", "c"]


def test_write_invalidates_only_that_sheets_column_cache():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet_1 = app.get_sheet_by_name("Sheet1")
    sheet_2 = app.get_sheet_by_name("Sheet2")
    sheet_1.range("A1:A3").value = ["a", "b", "c"]
    sheet_2.range("A1:A3").value = ["d", "e", "f"]
    app.get_single_column_data("Sheet1", "A", 1, 3)  # prime both caches
    app.get_single_column_data("Sheet2", "A", 1, 3)

    sheet_1.range("A1:A3").value = ["new", "new", "new"]
    sheet_2.range("A1:A3").value = ["new", "new", "new"]
    app.write_xl_item(xl_data.XlItem("Sheet1", "C1", 42))

    assert app.get_single_column_data("Sheet1", "A", 1, 3) == ["new", "new", "new"]  # invalidated
    assert app.get_single_column_data("Sheet2", "A", 1, 3) == ["d", "e", "f"]  # still cached


def test_calculate_invalidates_all_column_caches():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet_1 = app.get_sheet_by_name("Sheet1")
    sheet_1.range("A1:A3").value = ["a", "b", "c"]
    app.get_single_column_data("Sheet1", "A", 1, 3)

    sheet_1.range("A1:A3").value = ["recalced", "recalced", "recalced"]
    app.calculate()
    assert app.get_single_column_data("Sheet1", "A", 1, 3) == ["recalced", "recalced", "recalced"]


def test_in_silent_mode_exit_invalidates_column_caches():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet_1 = app.get_sheet_by_name("Sheet1")
    sheet_1.range("A1:A3").value = ["a", "b", "c"]
    with app.in_silent_mode():
        app.get_single_column_data("Sheet1", "A", 1, 3)
        sheet_1.range("A1:A3").value = ["post-calc", "post-calc", "post-calc"]
    # -- exiting silent-mode recalculates: the cache must not serve stale data.
    assert app.get_single_column_data("Sheet1", "A", 1, 3) == ["post-calc", "post-calc", "post-calc"]


# -----------------------------------------------------------------------------
# Searching


def test_get_row_num_of_value_in_column_block_read():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet = app.get_sheet_by_name("Sheet1")
    sheet.range("A1:A5").value = ["a", "b", "c", None, "e"]

    assert app.get_row_num_of_value_in_column("Sheet1", 1, 5, "A", "c") == 3
    assert app.get_row_num_of_value_in_column("Sheet1", 1, 5, "A", None) == 4  # blank-cell search
    assert app.get_row_num_of_value_in_column("Sheet1", 1, 5, "A", "zzz") is None


def test_get_row_num_of_value_in_column_respects_row_start_offset():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet = app.get_sheet_by_name("Sheet1")
    sheet.range("A10:A12").value = ["x", "y", "target"]

    assert app.get_row_num_of_value_in_column("Sheet1", 10, 12, "A", "target") == 12


def test_get_row_num_of_value_in_column_single_row_range():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet = app.get_sheet_by_name("Sheet1")
    sheet.range("A3:A3").value = "target"  # single-cell reads return a scalar

    assert app.get_row_num_of_value_in_column("Sheet1", 3, 3, "A", "target") == 3
    assert app.get_row_num_of_value_in_column("Sheet1", 3, 3, "A", "other") is None


def test_get_row_num_of_value_in_column_bad_rows_raises_error():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    with pytest.raises(xl_app.ReadRowsError):
        app.get_row_num_of_value_in_column("Sheet1", 5, 1, "A", "x")


def test_get_row_num_of_value_in_column_falls_back_when_block_read_drops_cells():
    """xlwings #1924: macOS block reads can silently drop error cells, shifting
    positions. A short list must trigger the per-cell fallback scan."""
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    sheet = app.get_sheet_by_name("Sheet1")
    sheet.range("A1:A3").value = ["a", "target"]  # short: simulates a dropped error cell
    for row, value in enumerate(["a", "#REF!", "target"], start=1):
        sheet.range(f"A{row}").value = value

    # -- The naive scan of the short block would return row 2; the per-cell
    # -- fallback must find the true row 3.
    assert app.get_row_num_of_value_in_column("Sheet1", 1, 3, "A", "target") == 3


# -----------------------------------------------------------------------------
# Writing


@pytest.mark.parametrize("test_input", [100_000, 1, 0, -1, -100_000])
def test_xl_app_write_int_value(test_input):
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    xl_item = xl_data.XlItem("Sheet1", "A1", test_input)
    app.write_xl_item(xl_item)

    _sheet = app.get_sheet_by_name("Sheet1")
    _range = _sheet.range("A1")
    assert _range.value == test_input

    assert app.get_sheet_by_name("Sheet1").range("A1").value == test_input


@pytest.mark.parametrize("test_input", ["test", "another", ""])
def test_xl_app_write_string_value(test_input):
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    xl_item = xl_data.XlItem("Sheet1", "A1", test_input)
    app.write_xl_item(xl_item)

    assert app.get_sheet_by_name("Sheet1").range("A1").value == test_input


def test_xl_app_write_list_of_ints():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    xl_item = xl_data.XlItem("Sheet1", "A1", [1, 2, 3, 4])
    app.write_xl_item(xl_item)

    # -- On macOS the raw-write path targets the full block address, with the
    # -- values pre-shaped to a 2D row (ints as floats - see 'prepare_raw_write').
    assert app.get_sheet_by_name("Sheet1").range("A1:D1").value == [[1.0, 2.0, 3.0, 4.0]]


def test_write_raw_path_guards():
    """Items that rely on '.value' converter behavior must stay off the raw path."""
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    assert app._use_raw_write(xl_data.XlItem("Sheet1", "A1", 42))
    assert app._use_raw_write(xl_data.XlItem("Sheet1", "A1", [1, 2, 3]))
    # -- colored items: the color-write offsets anchor to the converter's range
    assert not app._use_raw_write(
        xl_data.XlItem("Sheet1", "A1", 42, range_color=(1, 2, 3), font_color=(4, 5, 6))
    )
    # -- multi-cell addresses use '.value' scalar-broadcast (ie: block clears)
    assert not app._use_raw_write(xl_data.XlItem("Sheet1", "A1:D10", None))
    # -- empty lists are silently skipped by the converter - keep that behavior
    assert not app._use_raw_write(xl_data.XlItem("Sheet1", "A1", []))


def test_write_colored_item_takes_legacy_path_and_colors_cells():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    xl_item = xl_data.XlItem("Sheet1", "A1", 42, range_color=(1, 2, 3), font_color=(4, 5, 6))
    app.write_xl_item(xl_item)

    _range = app.get_sheet_by_name("Sheet1").range("A1")
    assert _range.value == 42
    assert _range.color == (1, 2, 3)


def test_xl_app_write_raise_Attribute_error():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    xl_item = None  # Not an Excel Item
    with pytest.raises(AttributeError):
        app.write_xl_item(xl_item)


def test_xl_app_write_raise_WriteValue_error():
    mock_xw = Mock_XL_Framework()
    app = xl_app.XLConnection(xl_framework=mock_xw)

    xl_item = xl_data.XlItem(None, "A1", [1, 2, 3, 4])  # Bad Excel Item
    with pytest.raises(xl_app.WriteValueError):
        app.write_xl_item(xl_item)
