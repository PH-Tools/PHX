# -*- Python Version: 3.10 -*-

"""H1: Round-trip profiler for the PHX Excel interop layer.

Two independent layers (use either or both):

1. 'ProfiledXLConnection' — a drop-in 'XLConnection' subclass that times every
   public facade method call: (method, detail, duration). Method-level view:
   which facade operations dominate. Note: nested facade calls (a method that
   calls another facade method on 'self') are each recorded, so cumulative
   times of different methods can overlap.

2. 'CountingFrameworkProxy' — wraps the injected xl-framework (xlwings) and
   counts the actual low-level primitive events ('range.value' get/set,
   '.end()', 'calculate()', app toggles ...). This catches the loops *inside*
   facade methods (e.g. 'get_row_num_of_value_in_column' per-row reads) that
   method-level timing under-counts. Each counted event approximates one
   AppleEvent/COM round trip.

Both are profiling-only instruments used by 'scripts/perf/profile_export.py';
they are NOT shipped with the PHX package and must never be used in production
export runs.
"""

import inspect
import json
import pathlib
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from PHX.xl.xl_app import XLConnection

# -----------------------------------------------------------------------------
# -- Layer 1: method-level timing


@dataclass
class CallRecord:
    """A single timed facade-method call."""

    method: str
    detail: str
    duration: float
    t_start: float


# -- Facade members that never produce an Excel round trip (pure Python).
_UNPROFILED_METHODS = {"output", "find_row", "in_silent_mode"}

# -- Argument names worth echoing into the record 'detail' field.
_DETAIL_ARG_NAMES = (
    "_sheet_name",
    "sheet_name",
    "_range",
    "_range_address",
    "_col",
    "col",
    "_row",
    "_row_number",
    "_row_start",
    "row_start",
    "_row_end",
    "row_end",
    "_col_start",
    "_col_end",
    "find",
)


class ProfiledXLConnection(XLConnection):
    """An XLConnection that records (method, detail, duration) for every public call."""

    def __init__(self, *args, **kwargs):
        self.records: list[CallRecord] = []
        self._profile_t0 = time.perf_counter()
        super().__init__(*args, **kwargs)
        self._install_wrappers()

    def _install_wrappers(self) -> None:
        for name in dir(XLConnection):
            if name.startswith("_") or name in _UNPROFILED_METHODS:
                continue
            static_attr = inspect.getattr_static(XLConnection, name)
            if isinstance(static_attr, property) or not callable(static_attr):
                continue
            bound = getattr(self, name)
            object.__setattr__(self, name, self._timed(name, bound))

    def _timed(self, name: str, bound_method):
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return bound_method(*args, **kwargs)
            finally:
                self.records.append(
                    CallRecord(
                        method=name,
                        detail=self._describe(bound_method, args, kwargs),
                        duration=time.perf_counter() - t0,
                        t_start=t0 - self._profile_t0,
                    )
                )

        return wrapper

    @staticmethod
    def _describe(bound_method, args, kwargs) -> str:
        try:
            bound = inspect.signature(bound_method).bind(*args, **kwargs)
        except TypeError:
            return ""
        parts = []
        for param_name, value in bound.arguments.items():
            # -- XlItem / XLItem_List arguments carry their own address info.
            if hasattr(value, "sheet_name") and hasattr(value, "xl_range"):
                parts.append(f"{value.sheet_name}:{value.xl_range}")
            elif param_name in _DETAIL_ARG_NAMES:
                parts.append(f"{param_name}={value}")
        return ", ".join(parts)

    # -- Reporting ------------------------------------------------------------

    def method_summary(self) -> list[dict[str, Any]]:
        """Aggregate records per method: call count + cumulative time, sorted by time."""
        by_method: dict[str, list[CallRecord]] = {}
        for record in self.records:
            by_method.setdefault(record.method, []).append(record)
        rows = [
            {
                "method": method,
                "calls": len(records),
                "total_s": round(sum(r.duration for r in records), 4),
                "mean_ms": round(1000 * sum(r.duration for r in records) / len(records), 2),
                "max_ms": round(1000 * max(r.duration for r in records), 2),
            }
            for method, records in by_method.items()
        ]
        return sorted(rows, key=lambda r: r["total_s"], reverse=True)

    def hot_spots(self, n: int = 20) -> list[dict[str, Any]]:
        """The n slowest individual calls."""
        slowest = sorted(self.records, key=lambda r: r.duration, reverse=True)[:n]
        return [{"method": r.method, "detail": r.detail, "duration_ms": round(1000 * r.duration, 2)} for r in slowest]

    def profile_report(self) -> dict[str, Any]:
        return {
            "total_facade_calls": len(self.records),
            "total_recorded_s": round(sum(r.duration for r in self.records), 3),
            "by_method": self.method_summary(),
            "hot_spots_top20": self.hot_spots(20),
        }


# -----------------------------------------------------------------------------
# -- Layer 2: framework-level event counting


class OpCounter:
    """Counts low-level framework events, keyed by (operation, sheet)."""

    # -- Ops that (approximately) fire one AppleEvent/COM round trip each.
    ROUND_TRIP_OPS = {
        "range.value.get",
        "range.value.set",
        "range.raw_value.get",
        "range.end",
        "range.color.set",
        "range.font.color.set",
        "sheet.clear",
        "sheet.clear_contents",
        "sheet.clear_formats",
        "sheet.autofit",
        "sheet.api",
        "sheet.name.get",
        "app.calculate",
        "app.toggle.set",
        "book.open",
        "book.add",
    }

    def __init__(self):
        self.counts: Counter[tuple[str, str]] = Counter()

    def hit(self, op: str, sheet: str = "-") -> None:
        self.counts[(op, sheet)] += 1

    def total_round_trips(self) -> int:
        return sum(n for (op, _), n in self.counts.items() if op in self.ROUND_TRIP_OPS)

    def by_op(self) -> list[dict[str, Any]]:
        totals: Counter[str] = Counter()
        for (op, _), n in self.counts.items():
            totals[op] += n
        return [{"op": op, "count": n, "is_round_trip": op in self.ROUND_TRIP_OPS} for op, n in totals.most_common()]

    def by_sheet(self) -> list[dict[str, Any]]:
        totals: Counter[str] = Counter()
        for (op, sheet), n in self.counts.items():
            if op in self.ROUND_TRIP_OPS:
                totals[sheet] += n
        return [{"sheet": sheet, "round_trips": n} for sheet, n in totals.most_common()]

    def report(self) -> dict[str, Any]:
        return {
            "total_round_trips": self.total_round_trips(),
            "by_op": self.by_op(),
            "round_trips_by_sheet": self.by_sheet(),
        }


class _Wrapped:
    """Base for delegating proxies: unknown attributes pass through to the raw object."""

    def __init__(self, raw, counter: OpCounter):
        object.__setattr__(self, "_raw", raw)
        object.__setattr__(self, "_counter", counter)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_raw"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_raw"), name, value)


class RangeProxy(_Wrapped):
    """Counts value get/set, '.end()' and color/format events on a Range."""

    def __init__(self, raw, counter: OpCounter, sheet: str):
        super().__init__(raw, counter)
        object.__setattr__(self, "_sheet", sheet)

    def __getattr__(self, name):
        raw, counter, sheet = self._unpack()
        if name in ("value", "raw_value"):
            counter.hit(f"range.{name}.get", sheet)
            return getattr(raw, name)
        if name == "last_cell":
            counter.hit("range.last_cell", sheet)
            return RangeProxy(raw.last_cell, counter, sheet)
        if name == "font":
            return _FontProxy(raw.font, counter, sheet)
        return getattr(raw, name)

    def __setattr__(self, name, value):
        raw, counter, sheet = self._unpack()
        if name in ("value", "raw_value"):
            counter.hit(f"range.{name}.set", sheet)
        elif name == "color":
            counter.hit("range.color.set", sheet)
        setattr(raw, name, value)

    def _unpack(self):
        return (
            object.__getattribute__(self, "_raw"),
            object.__getattribute__(self, "_counter"),
            object.__getattribute__(self, "_sheet"),
        )

    def options(self, *args, **kwargs):
        raw, counter, sheet = self._unpack()
        return RangeProxy(raw.options(*args, **kwargs), counter, sheet)

    def offset(self, *args, **kwargs):
        raw, counter, sheet = self._unpack()
        return RangeProxy(raw.offset(*args, **kwargs), counter, sheet)

    def end(self, *args, **kwargs):
        raw, counter, sheet = self._unpack()
        counter.hit("range.end", sheet)
        return RangeProxy(raw.end(*args, **kwargs), counter, sheet)


class _FontProxy(_Wrapped):
    def __init__(self, raw, counter: OpCounter, sheet: str):
        super().__init__(raw, counter)
        object.__setattr__(self, "_sheet", sheet)

    def __setattr__(self, name, value):
        if name == "color":
            object.__getattribute__(self, "_counter").hit(
                "range.font.color.set", object.__getattribute__(self, "_sheet")
            )
        setattr(object.__getattribute__(self, "_raw"), name, value)


class SheetProxy(_Wrapped):
    def __init__(self, raw, counter: OpCounter):
        super().__init__(raw, counter)
        object.__setattr__(self, "_name_cache", None)

    @property
    def _sheet_name(self) -> str:
        # -- Lazy + cached: reading '.name' is itself a live round trip, so only
        # -- do it once per proxy. NOT counted - it is the proxy's own labeling
        # -- overhead, not something the production code path does.
        cached = object.__getattribute__(self, "_name_cache")
        if cached is not None:
            return cached
        try:
            name = str(object.__getattribute__(self, "_raw").name)
        except Exception:
            name = "?"
        object.__setattr__(self, "_name_cache", name)
        return name

    def __getattr__(self, name):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        if name == "name":
            counter.hit("sheet.name.get", "-")
            return raw.name
        if name == "api":
            counter.hit("sheet.api", self._sheet_name)
            return raw.api
        if name in ("clear", "clear_contents", "clear_formats", "autofit", "activate", "delete"):
            counter.hit(f"sheet.{name}", self._sheet_name)
            return getattr(raw, name)
        return getattr(raw, name)

    def range(self, *args, **kwargs):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        counter.hit("sheet.range.construct", self._sheet_name)
        return RangeProxy(raw.range(*args, **kwargs), counter, self._sheet_name)


class SheetsProxy(_Wrapped):
    def __getitem__(self, key):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        return SheetProxy(raw[key], counter)

    def __iter__(self):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        for sheet in raw:
            yield SheetProxy(sheet, counter)

    def __len__(self):
        return len(object.__getattribute__(self, "_raw"))

    def __contains__(self, key):
        return key in object.__getattribute__(self, "_raw")

    def add(self, *args, **kwargs):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        counter.hit("sheets.add", "-")
        return SheetProxy(raw.add(*args, **kwargs), counter)


class AppProxy(_Wrapped):
    def __setattr__(self, name, value):
        counter = object.__getattribute__(self, "_counter")
        if name in ("screen_updating", "display_alerts", "calculation", "visible"):
            counter.hit("app.toggle.set", "-")
        setattr(object.__getattribute__(self, "_raw"), name, value)

    def calculate(self):
        counter = object.__getattribute__(self, "_counter")
        counter.hit("app.calculate", "-")
        return object.__getattribute__(self, "_raw").calculate()


class BookProxy(_Wrapped):
    def __getattr__(self, name):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        if name == "sheets":
            return SheetsProxy(raw.sheets, counter)
        if name == "app":
            return AppProxy(raw.app, counter)
        return getattr(raw, name)


class BooksProxy(_Wrapped):
    def __getattr__(self, name):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        if name == "active":
            return BookProxy(raw.active, counter)
        return getattr(raw, name)

    def open(self, *args, **kwargs):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        counter.hit("book.open", "-")
        return BookProxy(raw.open(*args, **kwargs), counter)

    def add(self, *args, **kwargs):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        counter.hit("book.add", "-")
        return BookProxy(raw.add(*args, **kwargs), counter)


class CountingFrameworkProxy(_Wrapped):
    """Wraps the xl framework module (xlwings) and counts primitive events.

    Usage:
        counter = OpCounter()
        conn = XLConnection(xl_framework=CountingFrameworkProxy(xw, counter), ...)
        ... run the export ...
        print(counter.report())
    """

    def __init__(self, raw_framework, counter: OpCounter):
        super().__init__(raw_framework, counter)

    @property
    def counter(self) -> OpCounter:
        return object.__getattribute__(self, "_counter")

    def __getattr__(self, name):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        if name in ("books", "Books"):
            return BooksProxy(getattr(raw, name), counter)
        return getattr(raw, name)

    def Range(self, *args, **kwargs):
        raw = object.__getattribute__(self, "_raw")
        counter = object.__getattribute__(self, "_counter")
        counter.hit("framework.Range.construct", "(active)")
        return RangeProxy(raw.Range(*args, **kwargs), counter, "(active)")


# -----------------------------------------------------------------------------
# -- Report output


def write_profile_json(
    path: pathlib.Path,
    meta: dict[str, Any],
    wall_time_s: float,
    connection: ProfiledXLConnection,
    counter: OpCounter | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Dump a combined profile report to JSON."""
    report: dict[str, Any] = {
        "meta": meta,
        "wall_time_s": round(wall_time_s, 2),
        "facade": connection.profile_report(),
    }
    if counter is not None:
        report["framework_events"] = counter.report()
    if extra:
        report.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
