# -*- Python Version: 3.10 -*-

"""An in-memory fake of the xlwings framework surface used by 'XLConnection'.

This is the replay half of the record/replay regression strategy for the
Tier-1 batching refactor (plan doc 04, section 2): it models a workbook as
per-sheet CELL STATE, so *any* read - single cell, column block, or 2D range -
resolves against the same state. That makes the replay robust to refactors
that change HOW cells are read/written (cell loops -> block reads) while
verifying WHAT ends up in the workbook.

Semantics intentionally mirror xlwings/Excel where the export relies on them:
    * writing a leading-apostrophe string ("'Name") stores plain text ("Name")
    * numbers are stored as floats (Excel doubles); bools stay bool
    * writing None clears a cell
    * a 1D list writes ACROSS a row; 'transpose=True' writes DOWN a column
    * single-cell reads return a scalar; 1D ranges a flat list; 2D a list of rows
    * '.end("up"/"left")' jumps to the last used cell (Ctrl-arrow)
    * 'calculate()' applies the next recorded post-recalc read-delta ("epoch")
      to cells the run has not itself written

The fixture seeding format matches what 'scripts/perf/record_replay_fixture.py'
records from a live run.
"""

import re
from typing import Any

MAXROW = 1_048_576
MAXCOL = 16_384

_ADDRESS_RE = re.compile(r"^\$?([A-Za-z]{1,3})\$?([0-9]+)$")


# -----------------------------------------------------------------------------
# -- Address math


def col_to_num(_col: str) -> int:
    """'A' -> 1, 'Z' -> 26, 'AA' -> 27, 'IH' -> 242 ..."""
    num = 0
    for char in _col.upper():
        num = num * 26 + (ord(char) - ord("A")) + 1
    return num


def num_to_col(_num: int) -> str:
    letters = ""
    while _num:
        _num, rem = divmod(_num - 1, 26)
        letters = chr(rem + ord("A")) + letters
    return letters


def parse_cell(_addr: str) -> tuple[int, int]:
    """'B12' (or '$B$12') -> (col=2, row=12)."""
    match = _ADDRESS_RE.match(_addr.strip())
    if not match:
        raise ValueError(f"Cannot parse cell address: '{_addr}'")
    return col_to_num(match.group(1)), int(match.group(2))


def cell_name(_col: int, _row: int) -> str:
    return f"{num_to_col(_col)}{_row}"


def parse_range(_addr: str) -> tuple[int, int, int, int]:
    """Parse a range address -> (col1, row1, col2, row2), normalized (c1<=c2, r1<=r2).

    Supports 'B12', 'A1:C5', full columns 'A:A', and full rows '5:5'.
    """
    addr = _addr.replace("$", "").strip()
    if ":" not in addr:
        col, row = parse_cell(addr)
        return col, row, col, row

    part_1, part_2 = addr.split(":")
    if part_1.isalpha() and part_2.isalpha():  # -- full columns: "A:A"
        col_1, col_2 = col_to_num(part_1), col_to_num(part_2)
        return min(col_1, col_2), 1, max(col_1, col_2), MAXROW
    if part_1.isdigit() and part_2.isdigit():  # -- full rows: "5:5"
        row_1, row_2 = int(part_1), int(part_2)
        return 1, min(row_1, row_2), MAXCOL, max(row_1, row_2)

    col_1, row_1 = parse_cell(part_1)
    col_2, row_2 = parse_cell(part_2)
    return min(col_1, col_2), min(row_1, row_2), max(col_1, col_2), max(row_1, row_2)


# -----------------------------------------------------------------------------
# -- Value normalization (what Excel stores for what we write)


def normalize_value(_value: Any) -> Any:
    """Return the 'as stored by Excel' form of a written value."""
    if isinstance(_value, bool) or _value is None:
        return _value
    if isinstance(_value, (int, float)):
        return float(_value)
    if isinstance(_value, str):
        if _value.startswith("'"):  # -- text-forcing prefix is not stored
            _value = _value[1:]
        return _value if _value != "" else None  # -- empty text reads back as an empty cell
    return _value


def decompose_write(
    _range_span: tuple[int, int, int, int],
    _value: Any,
    _transpose: bool = False,
) -> dict[tuple[int, int], Any]:
    """Map a written value onto per-cell entries, anchored at the range's top-left.

    Mirrors xlwings write semantics: scalar -> one cell; 1D list -> across the
    row (or down the column with transpose); 2D list -> block of rows.
    """
    col_1, row_1 = _range_span[0], _range_span[1]
    cells: dict[tuple[int, int], Any] = {}

    if isinstance(_value, (list, tuple)):
        if _value and isinstance(_value[0], (list, tuple)):  # -- 2D
            rows_2d = [list(row) for row in _value]
            if _transpose:
                rows_2d = [list(row) for row in zip(*rows_2d)]
            for row_offset, row_values in enumerate(rows_2d):
                for col_offset, value in enumerate(row_values):
                    cells[(col_1 + col_offset, row_1 + row_offset)] = normalize_value(value)
        else:  # -- 1D
            if _transpose:  # -- down the column
                for row_offset, value in enumerate(_value):
                    cells[(col_1, row_1 + row_offset)] = normalize_value(value)
            else:  # -- across the row
                for col_offset, value in enumerate(_value):
                    cells[(col_1 + col_offset, row_1)] = normalize_value(value)
    else:
        cells[(col_1, row_1)] = normalize_value(_value)

    return cells


def decompose_raw_write(
    _range_span: tuple[int, int, int, int],
    _value: Any,
) -> dict[tuple[int, int], Any]:
    """Map a 'raw_value' write onto per-cell entries.

    Mirrors the appscript 'value.set' semantics the raw path hits on macOS:
    a scalar broadcasts to every cell in the range, and a 2D list must match
    the range's shape exactly (the converter's anchor-expansion has already
    happened Python-side). Anything else is a bug in the raw-write shim, so
    it raises instead of guessing.
    """
    col_1, row_1, col_2, row_2 = _range_span
    n_rows, n_cols = row_2 - row_1 + 1, col_2 - col_1 + 1
    cells: dict[tuple[int, int], Any] = {}

    if isinstance(_value, (list, tuple)):
        if not (_value and isinstance(_value[0], (list, tuple))):
            raise ValueError(f"raw_value writes must be a scalar or a 2D list, got: {_value!r}")
        if len(_value) != n_rows or any(len(row) != n_cols for row in _value):
            raise ValueError(f"raw_value 2D shape {_value!r} does not match the {n_rows}x{n_cols} range.")
        for row_offset, row_values in enumerate(_value):
            for col_offset, value in enumerate(row_values):
                cells[(col_1 + col_offset, row_1 + row_offset)] = normalize_value(value)
        return cells

    if _value is None:
        raise ValueError("raw_value writes must not contain None (the shim converts None to '').")
    for row in range(row_1, row_2 + 1):
        for col in range(col_1, col_2 + 1):
            cells[(col, row)] = normalize_value(_value)
    return cells


# -----------------------------------------------------------------------------
# -- The fake xlwings object graph


class FakeFont:
    def __init__(self, _range: "FakeRange"):
        self._range = _range

    def __setattr__(self, name, value):
        if name == "color":
            _range = self.__dict__["_range"]
            for col, row in _range.iter_cells():
                _range.sheet.font_colors[(col, row)] = value
            return
        object.__setattr__(self, name, value)


class FakeRange:
    """A rectangular range on a FakeSheet."""

    def __init__(self, sheet: "FakeSheet", span: tuple[int, int, int, int], ndim=None, transpose=False):
        self.__dict__.update(sheet=sheet, span=span, ndim=ndim, transpose=transpose)

    # -- geometry -------------------------------------------------------------

    @property
    def row(self) -> int:
        return self.span[1]

    @property
    def column(self) -> int:
        return self.span[0]

    @property
    def address(self) -> str:
        col_1, row_1, col_2, row_2 = self.span
        if (col_1, row_1) == (col_2, row_2):
            return f"${num_to_col(col_1)}${row_1}"
        return f"${num_to_col(col_1)}${row_1}:${num_to_col(col_2)}${row_2}"

    @property
    def columns(self) -> list:
        col_1, _, col_2, _ = self.span
        return [None] * (col_2 - col_1 + 1)

    @property
    def rows(self) -> list:
        _, row_1, _, row_2 = self.span
        return [None] * (row_2 - row_1 + 1)

    @property
    def last_cell(self) -> "FakeRange":
        col_2, row_2 = self.span[2], self.span[3]
        return FakeRange(self.sheet, (col_2, row_2, col_2, row_2))

    def iter_cells(self):
        col_1, row_1, col_2, row_2 = self.span
        for row in range(row_1, row_2 + 1):
            for col in range(col_1, col_2 + 1):
                yield col, row

    def options(self, *args, **kwargs) -> "FakeRange":
        return FakeRange(
            self.sheet,
            self.span,
            ndim=kwargs.get("ndim", self.ndim),
            transpose=kwargs.get("transpose", self.transpose),
        )

    def offset(self, row_offset: int = 0, column_offset: int = 0) -> "FakeRange":
        col_1, row_1, col_2, row_2 = self.span
        return FakeRange(
            self.sheet,
            (col_1 + column_offset, row_1 + row_offset, col_2 + column_offset, row_2 + row_offset),
            ndim=self.ndim,
            transpose=self.transpose,
        )

    def end(self, direction: str) -> "FakeRange":
        """Ctrl-arrow: jump from this cell to the last used cell in a direction."""
        col, row = self.span[0], self.span[1]
        if direction in ("up", "u"):
            used_rows = [r for (c, r), v in self.sheet.cells.items() if c == col and r <= row and v not in (None, "")]
            target_row = max(used_rows) if used_rows else 1
            return FakeRange(self.sheet, (col, target_row, col, target_row))
        if direction in ("left", "l"):
            used_cols = [c for (c, r), v in self.sheet.cells.items() if r == row and c <= col and v not in (None, "")]
            target_col = max(used_cols) if used_cols else 1
            return FakeRange(self.sheet, (target_col, row, target_col, row))
        raise NotImplementedError(f"FakeRange.end('{direction}') is not supported.")

    # -- data -----------------------------------------------------------------

    def _read_cell(self, col: int, row: int) -> Any:
        return self.sheet.cells.get((col, row))

    def __getattr__(self, name):
        if name == "value":
            return self._compose_value()
        if name == "font":
            return FakeFont(self)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "value":
            written = decompose_write(self.span, value, self.transpose)
            self.sheet.write_cells(written)
            return
        if name == "raw_value":
            self.sheet.write_cells(decompose_raw_write(self.span, value))
            return
        if name == "color":
            for col, row in self.iter_cells():
                self.sheet.cell_colors[(col, row)] = value
            return
        self.__dict__[name] = value

    def _compose_value(self) -> Any:
        col_1, row_1, col_2, row_2 = self.span
        rows_2d = [[self._read_cell(col, row) for col in range(col_1, col_2 + 1)] for row in range(row_1, row_2 + 1)]

        if self.transpose:
            rows_2d = [list(row) for row in zip(*rows_2d)]

        n_rows, n_cols = len(rows_2d), len(rows_2d[0])
        if self.ndim and self.ndim >= 2:
            return rows_2d
        if n_rows == 1 and n_cols == 1:
            value = rows_2d[0][0]
            return [value] if self.ndim == 1 else value
        if n_rows == 1:  # -- single horizontal row
            return rows_2d[0]
        if n_cols == 1:  # -- single vertical column
            return [row[0] for row in rows_2d]
        return rows_2d


class _FakeAPIRows:
    def __getitem__(self, key):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def group(self, *args, **kwargs) -> None:
        return None

    def Group(self, *args, **kwargs) -> None:
        return None


class _FakeOutline:
    def show_levels(self, *args, **kwargs) -> None:
        return None


class FakeAPI:
    """The '.api' escape hatch: protect/group/outline calls are no-ops."""

    def __init__(self, sheet: "FakeSheet"):
        self.sheet = sheet
        self.rows = _FakeAPIRows()
        self.outline_object = _FakeOutline()

    def unprotect(self) -> None:
        self.sheet.protected = False

    def Unprotect(self) -> None:
        self.sheet.protected = False

    def Rows(self, *args, **kwargs):
        return self.rows


class FakeSheet:
    def __init__(self, name: str, seed: dict[str, Any] | None = None):
        self.name = name
        self.protected = True
        # -- {(col, row): value} - the current cell state
        self.cells: dict[tuple[int, int], Any] = {}
        # -- {(col, row): value} - only the cells written DURING the run
        self.written: dict[tuple[int, int], Any] = {}
        self.cell_colors: dict[tuple[int, int], Any] = {}
        self.font_colors: dict[tuple[int, int], Any] = {}
        for addr, value in (seed or {}).items():
            self.cells[parse_cell(addr)] = value

    def range(self, cell1: str, cell2: str | None = None) -> FakeRange:
        addr = f"{cell1}:{cell2}" if cell2 else cell1
        return FakeRange(self, parse_range(addr))

    def write_cells(self, _cells: dict[tuple[int, int], Any]) -> None:
        for key, value in _cells.items():
            self.written[key] = value
            if value is None:
                self.cells.pop(key, None)
            else:
                self.cells[key] = value

    def apply_seed_delta(self, _delta: dict[str, Any]) -> None:
        """Overlay recorded post-recalc values onto cells this run has NOT written."""
        for addr, value in _delta.items():
            key = parse_cell(addr)
            if key not in self.written:
                self.cells[key] = value

    @property
    def api(self) -> FakeAPI:
        return FakeAPI(self)

    def clear_contents(self) -> None:
        self.cells.clear()

    def clear_formats(self) -> None:
        self.cell_colors.clear()
        self.font_colors.clear()

    def clear(self) -> None:
        self.clear_contents()
        self.clear_formats()

    def activate(self) -> None: ...

    def autofit(self, *args, **kwargs) -> None: ...

    def delete(self) -> None: ...


class FakeSheets:
    """Sheet lookup is case-insensitive, like Excel's."""

    def __init__(self, sheets: list[FakeSheet]):
        self.storage: dict[str, FakeSheet] = {sheet.name: sheet for sheet in sheets}

    def __getitem__(self, key) -> FakeSheet:
        if isinstance(key, int):
            return list(self.storage.values())[key]
        for name, sheet in self.storage.items():
            if name.upper() == str(key).upper():
                return sheet
        raise KeyError(key)

    def __iter__(self):
        yield from self.storage.values()

    def __len__(self) -> int:
        return len(self.storage)

    def __contains__(self, key) -> bool:
        return any(name.upper() == str(key).upper() for name in self.storage)

    def add(self, name=None, before=None, after=None) -> FakeSheet:
        if name in self:
            raise ValueError(f"Sheet '{name}' already exists.")
        new_sheet = FakeSheet(str(name))
        self.storage[str(name)] = new_sheet
        return new_sheet


class FakeApp:
    def __init__(self, book: "FakeBook"):
        self._book = book
        self.screen_updating = True
        self.display_alerts = True
        self.calculation = "automatic"
        self.visible = True

    def calculate(self) -> None:
        self._book.framework.apply_next_epoch()


class FakeBook:
    def __init__(self, framework: "FakeXLFramework", name: str, sheets: list[FakeSheet]):
        self.framework = framework
        self.name = name
        self.fullname = name
        self.sheets = FakeSheets(sheets)
        self.app = FakeApp(self)

    def save(self, *args, **kwargs) -> None: ...

    def close(self) -> None: ...


class FakeBooks:
    def __init__(self, book: FakeBook):
        self.active = book
        self.count = 1

    def open(self, _path) -> FakeBook:
        return self.active

    def add(self) -> FakeBook:
        return self.active


class FakeApps:
    count = 1

    def add(self):
        raise NotImplementedError("The Fake XL framework cannot start applications.")


class FakeXLFramework:
    """Drop-in 'xl_framework' for XLConnection, seeded from a recorded fixture.

    Arguments:
    ----------
        * sheet_names: (list[str]) Every worksheet name in the recorded workbook.
        * seed: ({sheet: {addr: value}}) Cell values as first-read during the
            recorded run (the pre-write state).
        * epoch_deltas: (list[{sheet: {addr: value}}]) Per-'calculate()' read
            deltas: values first seen AFTER the Nth recalc. Applied in order,
            skipping any cell this run has already written.
    """

    def __init__(
        self,
        sheet_names: list[str],
        seed: dict[str, dict[str, Any]] | None = None,
        epoch_deltas: list[dict[str, dict[str, Any]]] | None = None,
        book_name: str = "FAKE_PHPP.xlsx",
    ):
        seed = seed or {}
        sheets = [FakeSheet(name, seed.get(name)) for name in sheet_names]
        self._book = FakeBook(self, book_name, sheets)
        self.books = FakeBooks(self._book)
        self.apps = FakeApps()
        self._epoch_deltas = list(epoch_deltas or [])
        self._epoch = 0

    def apply_next_epoch(self) -> None:
        if self._epoch < len(self._epoch_deltas):
            for sheet_name, delta in self._epoch_deltas[self._epoch].items():
                if sheet_name in self._book.sheets:
                    self._book.sheets[sheet_name].apply_seed_delta(delta)
        self._epoch += 1

    def Range(self, _addr: str) -> FakeRange:
        # -- Module-level 'xw.Range()' is only used for address geometry
        # -- (.column / len(.columns)) - bind it to a throw-away sheet.
        return FakeRange(FakeSheet("__geometry__"), parse_range(_addr))

    # -- Inspection -----------------------------------------------------------

    def written_state(self) -> dict[str, dict[str, Any]]:
        """Return {sheet: {addr: value}} for every cell written during the run."""
        return {
            sheet.name: {cell_name(*key): value for key, value in sorted(sheet.written.items())}
            for sheet in self._book.sheets
            if sheet.written
        }

    def color_state(self) -> dict[str, dict[str, Any]]:
        """Return {sheet: {addr: [range_color, font_color]}} for colored cells."""
        state: dict[str, dict[str, Any]] = {}
        for sheet in self._book.sheets:
            colored = sorted(set(sheet.cell_colors) | set(sheet.font_colors))
            if colored:
                state[sheet.name] = {
                    cell_name(*key): [sheet.cell_colors.get(key), sheet.font_colors.get(key)] for key in colored
                }
        return state
