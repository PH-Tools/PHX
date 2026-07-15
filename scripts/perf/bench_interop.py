# -*- Python Version: 3.10 -*-

"""T0.2: Microbenchmark raw interop primitives — xlwings vs xlwings raw_value vs raw appscript.

Measures per-operation latency on a scratch workbook so we can localize the
Tahoe slowdown: how much is OS-level AppleEvent cost (raw appscript pays it
too — unavoidable) vs the xlwings converter layer (avoidable)?

Ops per backend:
    * N x single-cell read
    * N x single-cell write
    * 1 x block read  (BLOCK_SIZE x 1 cells)
    * 1 x block write (BLOCK_SIZE x 1 cells)
    * 20 x '.end()' (Ctrl-Up) calls

MANUAL-INVOCATION ONLY. Never run while a production export is in progress.
The benchmark uses a NEW scratch workbook (never a PHPP) and closes it without
saving when done.

Usage:
    python scripts/perf/bench_interop.py [--n 100] [--block 1000] [--yes]
        [--backends xlwings,xlwings-raw,appscript] [--label my-machine]
"""

import argparse
import json
import platform
import statistics
import sys
import time
from typing import Any, Callable

import perf_paths

N_END_CALLS = 20


def _time_each(fn: Callable[[int], Any], n: int) -> list[float]:
    """Run fn(i) n times, returning per-call durations in seconds."""
    durations = []
    for i in range(n):
        t0 = time.perf_counter()
        fn(i)
        durations.append(time.perf_counter() - t0)
    return durations


def _stats(durations: list[float]) -> dict[str, float]:
    ms = sorted(d * 1000 for d in durations)
    return {
        "n": len(ms),
        "total_s": round(sum(ms) / 1000, 4),
        "mean_ms": round(statistics.fmean(ms), 3),
        "median_ms": round(statistics.median(ms), 3),
        "p95_ms": round(ms[max(0, int(len(ms) * 0.95) - 1)], 3),
        "max_ms": round(ms[-1], 3),
    }


def _run_ops(ops: list[tuple[str, Callable[[int], Any], int]]) -> dict[str, Any]:
    """Time each named op; an op that raises is recorded as an error, not fatal."""
    results: dict[str, Any] = {}
    for name, fn, n in ops:
        try:
            results[name] = _stats(_time_each(fn, n))
        except Exception as e:
            results[name] = {"error": repr(e)}
    return results


# -----------------------------------------------------------------------------
# -- Backends. Each works on the given xlwings Sheet ('appscript' goes through
# -- 'sheet.api' so it reuses the same workbook/connection).


def run_xlwings(sheet, n: int, block: int, raw: bool = False) -> dict[str, Any]:
    def write_cell(i: int):
        rng = sheet.range(f"A{i + 1}")
        if raw:
            rng.raw_value = float(i)
        else:
            rng.value = float(i)

    def read_cell(i: int):
        rng = sheet.range(f"A{i + 1}")
        return rng.raw_value if raw else rng.value

    def write_block(_: int):
        if raw:
            # raw_value expects the engine's native 2D shape.
            sheet.range(f"C1:C{block}").raw_value = tuple((float(i),) for i in range(block))
        else:
            sheet.range("C1").options(transpose=True).value = [float(i) for i in range(block)]

    def read_block(_: int):
        rng = sheet.range(f"C1:C{block}")
        return rng.raw_value if raw else rng.value

    def end_call(_: int):
        return sheet.range("A1048576").end("up").row

    return _run_ops(
        [
            ("write_cell", write_cell, n),  # write first so reads see data
            ("read_cell", read_cell, n),
            ("write_block", write_block, 1),
            ("read_block", read_block, 1),
            ("end_call", end_call, N_END_CALLS),
        ]
    )


def run_appscript(sheet, n: int, block: int) -> dict[str, Any]:
    """Raw appscript through 'sheet.api' — AppleEvent cost without the xlwings
    converter layer. macOS only."""
    from appscript import k

    api = sheet.api  # the appscript worksheet reference

    def write_cell(i: int):
        api.cells[f"E{i + 1}"].value.set(float(i))

    def read_cell(i: int):
        return api.cells[f"E{i + 1}"].value.get()

    def write_block(_: int):
        api.ranges[f"G1:G{block}"].value.set([[float(i)] for i in range(block)])

    def read_block(_: int):
        return api.ranges[f"G1:G{block}"].value.get()

    def end_call(_: int):
        return api.cells["E1048576"].get_end(direction=k.toward_the_top).first_row_index.get()

    return _run_ops(
        [
            ("write_cell", write_cell, n),
            ("read_cell", read_cell, n),
            ("write_block", write_block, 1),
            ("read_block", read_block, 1),
            ("end_call", end_call, N_END_CALLS),
        ]
    )


# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=100, help="Single-cell op repetitions (default 100).")
    parser.add_argument("--block", type=int, default=1000, help="Block op size in cells (default 1000).")
    parser.add_argument(
        "--backends",
        default="xlwings,xlwings-raw,appscript",
        help="Comma-separated: xlwings, xlwings-raw, appscript.",
    )
    parser.add_argument("--label", default=platform.node().split(".")[0], help="Label for the baseline file.")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    perf_paths.confirm_live_excel_run(args.yes)
    meta = perf_paths.environment_metadata()
    print(f"Excel build check (T0.1): {meta['excel_build_check']}")

    import xlwings as xw

    backends = [b.strip() for b in args.backends.split(",") if b.strip()]
    if platform.system() != "Darwin" and "appscript" in backends:
        print("Skipping 'appscript' backend (macOS only).")
        backends.remove("appscript")

    # -- A NEW scratch workbook. Never a PHPP; closed without saving at exit.
    if not xw.apps:
        xw.App(visible=True, add_book=False)
    workbook = xw.books.add()
    sheet = workbook.sheets[0]
    print(f"Benchmarking on scratch workbook '{workbook.name}' ...")

    results: dict[str, Any] = {}
    try:
        for backend in backends:
            print(f"\n--- backend: {backend}")
            if backend == "xlwings":
                results[backend] = run_xlwings(sheet, args.n, args.block, raw=False)
            elif backend == "xlwings-raw":
                results[backend] = run_xlwings(sheet, args.n, args.block, raw=True)
            elif backend == "appscript":
                results[backend] = run_appscript(sheet, args.n, args.block)
            else:
                print(f"Unknown backend '{backend}' — skipped.")
                continue

            for op, op_stats in results[backend].items():
                if "error" in op_stats:
                    print(f"  {op:<12} ERROR: {op_stats['error']}")
                else:
                    print(
                        f"  {op:<12} n={op_stats['n']:<5} mean={op_stats['mean_ms']:>9.3f} ms"
                        f"   total={op_stats['total_s']:.3f} s"
                    )
    finally:
        try:
            workbook.close()
        except Exception as e:
            print(f"Note: could not close scratch workbook ({e}) — close it manually, do NOT save.")

    payload = {"meta": meta, "config": {"n": args.n, "block": args.block}, "results": results}
    out_path = perf_paths.BASELINES_DIR / f"bench_interop__{args.label}__{meta['timestamp'].replace(':', '-')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote baseline -> {out_path.relative_to(perf_paths.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
