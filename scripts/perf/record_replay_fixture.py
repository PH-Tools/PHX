# -*- Python Version: 3.10 -*-

"""Record a live HBJSON -> PHPP export into a replay fixture (plan doc 04, section 2).

Wraps xlwings with a recording proxy and runs the production write sequence
against a SCRATCH COPY of the PHPP template. Every read and write is decomposed
into per-cell entries:

    * seed          - each cell's value as FIRST read (the pre-write state)
    * epoch_deltas  - values first seen after each 'calculate()' (recalc results)
    * golden_writes - the final written cell-state (what the export produced)
    * golden_colors - per-cell [range_color, font_color] sets

The fixture drives 'tests/test_xl_replay/test_replay_invariant.py': the same
export replayed against the in-memory fake must reproduce 'golden_writes'
EXACTLY. Because the fake resolves any read against cell-state, the fixture
survives read/write-batching refactors (T1.2/T1.3) - which is the point.

MANUAL-INVOCATION ONLY. Never run while a production export is in progress.

Usage:
    python scripts/perf/record_replay_fixture.py [--yes]
        [--hbjson tests/test_xl_replay/fixtures/Single_Zone.hbjson]
        [--out tests/test_xl_replay/fixtures/single_zone_replay.json]
"""

import argparse
import json
import pathlib
import sys
import time
from typing import Any

import perf_paths

REPO_ROOT = perf_paths.REPO_ROOT
sys.path.insert(0, str(REPO_ROOT))

from tests.test_xl_replay.fake_xl_framework import (  # noqa: E402
    cell_name,
    normalize_value,
    parse_range,
)

DEFAULT_HBJSON = REPO_ROOT / "tests" / "test_xl_replay" / "fixtures" / "Single_Zone.hbjson"
DEFAULT_OUT = REPO_ROOT / "tests" / "test_xl_replay" / "fixtures" / "single_zone_replay.json"


# -----------------------------------------------------------------------------
# -- Recording state


class Recording:
    def __init__(self):
        self.epoch = 0
        self.seed: dict[str, dict[str, Any]] = {}
        self.epoch_deltas: list[dict[str, dict[str, Any]]] = []
        self.golden_writes: dict[str, dict[str, Any]] = {}
        self.golden_colors: dict[str, dict[str, Any]] = {}
        # -- what a replay would currently return for each cell (reads only)
        self._known: dict[tuple[str, str], Any] = {}
        self._written: set[tuple[str, str]] = set()
        self.conflicts: list[str] = []
        self.skipped_reads: list[str] = []
        self.odd_types: list[str] = []

    def _current_epoch_store(self) -> dict[str, dict[str, Any]]:
        if self.epoch == 0:
            return self.seed
        while len(self.epoch_deltas) < self.epoch:
            self.epoch_deltas.append({})
        return self.epoch_deltas[self.epoch - 1]

    def _jsonable(self, sheet: str, addr: str, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        self.odd_types.append(f"{sheet}!{addr}: {type(value).__name__} = {value!r}")
        return str(value)

    def record_read_cell(self, sheet: str, addr: str, value: Any) -> None:
        key = (sheet, addr)
        if key in self._written:
            return  # -- reads of our own writes replay from the write overlay
        value = self._jsonable(sheet, addr, value)
        if key not in self._known:
            if value is not None:  # -- unseeded cells read as None in the fake
                self._current_epoch_store().setdefault(sheet, {})[addr] = value
            self._known[key] = (self.epoch, value)
        else:
            known_epoch, known_value = self._known[key]
            if known_value == value:
                return
            if known_epoch == self.epoch:
                self.conflicts.append(f"{sheet}!{addr}: read '{known_value}' then '{value}' within epoch {self.epoch}")
            self._current_epoch_store().setdefault(sheet, {})[addr] = value
            self._known[key] = (self.epoch, value)

    def record_write(self, sheet: str, span: tuple[int, int, int, int], value: Any, transpose: bool) -> None:
        from tests.test_xl_replay.fake_xl_framework import decompose_write

        for (col, row), cell_value in decompose_write(span, value, transpose).items():
            addr = cell_name(col, row)
            self.golden_writes.setdefault(sheet, {})[addr] = self._jsonable(sheet, addr, cell_value)
            self._written.add((sheet, addr))

    def record_raw_write(self, sheet: str, span: tuple[int, int, int, int], value: Any) -> None:
        from tests.test_xl_replay.fake_xl_framework import decompose_raw_write

        for (col, row), cell_value in decompose_raw_write(span, value).items():
            addr = cell_name(col, row)
            self.golden_writes.setdefault(sheet, {})[addr] = self._jsonable(sheet, addr, cell_value)
            self._written.add((sheet, addr))

    def record_color(self, sheet: str, span: tuple[int, int, int, int], color: Any, slot: int) -> None:
        col_1, row_1, col_2, row_2 = span
        for row in range(row_1, row_2 + 1):
            for col in range(col_1, col_2 + 1):
                addr = cell_name(col, row)
                entry = self.golden_colors.setdefault(sheet, {}).setdefault(addr, [None, None])
                entry[slot] = list(color) if isinstance(color, tuple) else color

    def record_read_span(self, sheet: str, span: tuple[int, int, int, int], result: Any, transpose: bool) -> None:
        """Decompose a read result back onto per-cell entries."""
        col_1, row_1, col_2, row_2 = span
        n_rows, n_cols = row_2 - row_1 + 1, col_2 - col_1 + 1

        # -- normalize the result into 2D rows matching the span
        if not isinstance(result, list):
            rows_2d = [[result]]
        elif result and isinstance(result[0], list):
            rows_2d = [list(r) for r in result]
        elif n_rows == 1:
            rows_2d = [list(result)]
        elif n_cols == 1:
            rows_2d = [[v] for v in result]
        else:
            self.skipped_reads.append(f"{sheet}!{cell_name(col_1, row_1)}: ambiguous 1D result for 2D span")
            return

        if transpose:
            rows_2d = [list(r) for r in zip(*rows_2d)]

        if len(rows_2d) != n_rows or any(len(r) != n_cols for r in rows_2d):
            # -- e.g. xlwings #1924 error-cell drop: positions unknowable - skip.
            self.skipped_reads.append(
                f"{sheet}!{cell_name(col_1, row_1)}: result shape {len(rows_2d)}x{len(rows_2d[0]) if rows_2d else 0}"
                f" != span {n_rows}x{n_cols}"
            )
            return

        for row_offset, row_values in enumerate(rows_2d):
            for col_offset, value in enumerate(row_values):
                self.record_read_cell(sheet, cell_name(col_1 + col_offset, row_1 + row_offset), value)

    def on_calculate(self) -> None:
        self.epoch += 1


# -----------------------------------------------------------------------------
# -- Recording proxies (address-aware wrappers around the real xlwings graph)


class _Rec:
    def __init__(self, raw, recording: Recording):
        object.__setattr__(self, "_raw", raw)
        object.__setattr__(self, "_rec", recording)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_raw"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_raw"), name, value)


class RecRange(_Rec):
    def __init__(self, raw, recording: Recording, sheet: str, span: tuple[int, int, int, int], transpose=False):
        super().__init__(raw, recording)
        object.__setattr__(self, "_sheet", sheet)
        object.__setattr__(self, "_span", span)
        object.__setattr__(self, "_transpose", transpose)

    def _parts(self):
        get = object.__getattribute__
        return get(self, "_raw"), get(self, "_rec"), get(self, "_sheet"), get(self, "_span"), get(self, "_transpose")

    def __getattr__(self, name):
        raw, rec, sheet, span, transpose = self._parts()
        if name == "value":
            result = raw.value
            rec.record_read_span(sheet, span, result, transpose)
            return result
        if name == "raw_value":
            # -- raw values skip the converter; recording them would poison the
            # -- fixture with engine-native types. Not supported.
            raise NotImplementedError("RecRange does not support 'raw_value' reads.")
        if name == "last_cell":
            col_2, row_2 = span[2], span[3]
            return RecRange(raw.last_cell, rec, sheet, (col_2, row_2, col_2, row_2))
        if name == "font":
            return RecFont(raw.font, rec, sheet, span)
        return getattr(raw, name)

    def __setattr__(self, name, value):
        raw, rec, sheet, span, transpose = self._parts()
        if name == "value":
            rec.record_write(sheet, span, value, transpose)
            raw.value = value
            return
        if name == "raw_value":
            # -- raw writes are pre-shaped Python-side (xl_data.prepare_raw_write),
            # -- so their cell decomposition is exact - safe to record.
            rec.record_raw_write(sheet, span, value)
            raw.raw_value = value
            return
        if name == "color":
            rec.record_color(sheet, span, value, slot=0)
            raw.color = value
            return
        setattr(raw, name, value)

    def options(self, *args, **kwargs) -> "RecRange":
        raw, rec, sheet, span, transpose = self._parts()
        return RecRange(raw.options(*args, **kwargs), rec, sheet, span, kwargs.get("transpose", transpose))

    def offset(self, row_offset: int = 0, column_offset: int = 0) -> "RecRange":
        raw, rec, sheet, span, transpose = self._parts()
        col_1, row_1, col_2, row_2 = span
        shifted = (col_1 + column_offset, row_1 + row_offset, col_2 + column_offset, row_2 + row_offset)
        return RecRange(raw.offset(row_offset, column_offset), rec, sheet, shifted, transpose)

    def end(self, direction: str) -> "RecRange":
        raw, rec, sheet, span, transpose = self._parts()
        result = raw.end(direction)
        return RecRange(result, rec, sheet, parse_range(str(result.address)))


class RecFont(_Rec):
    def __init__(self, raw, recording: Recording, sheet: str, span):
        super().__init__(raw, recording)
        object.__setattr__(self, "_sheet", sheet)
        object.__setattr__(self, "_span", span)

    def __setattr__(self, name, value):
        get = object.__getattribute__
        if name == "color":
            get(self, "_rec").record_color(get(self, "_sheet"), get(self, "_span"), value, slot=1)
        setattr(get(self, "_raw"), name, value)


class RecSheet(_Rec):
    def __init__(self, raw, recording: Recording):
        super().__init__(raw, recording)
        object.__setattr__(self, "_name", str(raw.name))

    def range(self, cell1: str, cell2: str | None = None) -> RecRange:
        get = object.__getattribute__
        raw, rec = get(self, "_raw"), get(self, "_rec")
        addr = f"{cell1}:{cell2}" if cell2 else str(cell1)
        return RecRange(raw.range(addr), rec, get(self, "_name"), parse_range(addr))


class RecSheets(_Rec):
    def __getitem__(self, key):
        get = object.__getattribute__
        return RecSheet(get(self, "_raw")[key], get(self, "_rec"))

    def __iter__(self):
        get = object.__getattribute__
        for sheet in get(self, "_raw"):
            yield RecSheet(sheet, get(self, "_rec"))

    def __len__(self):
        return len(object.__getattribute__(self, "_raw"))

    def __contains__(self, key):
        return key in object.__getattribute__(self, "_raw")


class RecApp(_Rec):
    def calculate(self):
        get = object.__getattribute__
        get(self, "_rec").on_calculate()
        return get(self, "_raw").calculate()


class RecBook(_Rec):
    def __getattr__(self, name):
        get = object.__getattribute__
        if name == "sheets":
            return RecSheets(get(self, "_raw").sheets, get(self, "_rec"))
        if name == "app":
            return RecApp(get(self, "_raw").app, get(self, "_rec"))
        return getattr(get(self, "_raw"), name)


class RecBooks(_Rec):
    def __getattr__(self, name):
        get = object.__getattribute__
        if name == "active":
            return RecBook(get(self, "_raw").active, get(self, "_rec"))
        return getattr(get(self, "_raw"), name)

    def open(self, *args, **kwargs):
        get = object.__getattribute__
        return RecBook(get(self, "_raw").open(*args, **kwargs), get(self, "_rec"))


class RecordingFrameworkProxy(_Rec):
    def __getattr__(self, name):
        get = object.__getattribute__
        if name in ("books", "Books"):
            return RecBooks(getattr(get(self, "_raw"), name), get(self, "_rec"))
        return getattr(get(self, "_raw"), name)

    def Range(self, *args, **kwargs):
        # -- module-level Range is only used for address geometry (no data)
        return object.__getattribute__(self, "_raw").Range(*args, **kwargs)


# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hbjson", default=str(DEFAULT_HBJSON))
    parser.add_argument("--phpp", help="PHPP template (default: packet EN v10.6 empty). Never written to.")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    hbjson_path = pathlib.Path(args.hbjson).resolve()
    if not hbjson_path.exists():
        sys.exit(f"Error: HBJSON not found: {hbjson_path}")
    phpp_template = perf_paths.resolve_phpp_path(args.phpp)
    scratch_dir = perf_paths.resolve_scratch_dir(None)

    perf_paths.confirm_live_excel_run(args.yes)

    print(f"Reading HBJSON: {hbjson_path.name} ...")
    from PHX.from_HBJSON import create_project, read_HBJSON_file

    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(hbjson_path)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True)

    scratch_copy = perf_paths.make_scratch_copy(phpp_template, scratch_dir, "record")
    print(f"Scratch copy: {scratch_copy}")
    perf_paths.preopen_workbook_macos(scratch_copy)

    import xlwings as xw

    from PHX.hbjson_to_phpp import write_phx_project_to_phpp
    from PHX.PHPP import phpp_app
    from PHX.xl.xl_app import XLConnection

    recording = Recording()
    connection = XLConnection(
        xl_framework=RecordingFrameworkProxy(xw, recording),
        xl_file_path=scratch_copy,
    )
    sheet_names = [str(sheet.name) for sheet in connection.wb.sheets]
    phpp_conn = phpp_app.PHPPConnection(connection)

    print("Recording export ...")
    t0 = time.perf_counter()
    with connection.in_silent_mode():
        connection.unprotect_all_sheets()
        write_phx_project_to_phpp(phpp_conn, phx_project)
    print(f"Export recorded in {time.perf_counter() - t0:.1f} s.")

    fixture = {
        "meta": {
            **perf_paths.environment_metadata(),
            "hbjson": hbjson_path.name,
            "phpp_template": phpp_template.name,
            "recorded_with": "scripts/perf/record_replay_fixture.py",
        },
        "sheet_names": sheet_names,
        "seed": recording.seed,
        "epoch_deltas": recording.epoch_deltas,
        "golden_writes": recording.golden_writes,
        "golden_colors": recording.golden_colors,
        "conflicts": recording.conflicts,
        "skipped_reads": recording.skipped_reads,
        "odd_types": recording.odd_types,
    }
    out_path = pathlib.Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fixture, indent=1))

    n_written = sum(len(cells) for cells in recording.golden_writes.values())
    n_seed = sum(len(cells) for cells in recording.seed.values())
    print(f"Wrote fixture -> {out_path.relative_to(REPO_ROOT)}")
    print(f"  golden write-cells: {n_written} | seed cells: {n_seed} | epochs: {recording.epoch}")
    for label, items in (
        ("CONFLICTS", recording.conflicts),
        ("SKIPPED READS", recording.skipped_reads),
        ("ODD TYPES", recording.odd_types),
    ):
        if items:
            print(f"  WARNING - {label} ({len(items)}):")
            for item in items[:10]:
                print(f"    - {item}")

    connection.wb.close()
    print("Closed scratch workbook.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
