# -*- Python Version: 3.10 -*-

"""H1 profiler tests — run against the in-memory xl_typing doubles (no live Excel)."""

import profiling

from PHX.xl import xl_data, xl_typing


class Mock_XL_Framework(xl_typing.xl_Framework_Protocol):
    def __init__(self):
        self.books = xl_typing.xl_Books_Protocol()
        self.books.active.sheets.storage = {
            "Sheet1": xl_typing.xl_Sheet_Protocol(name="Sheet1"),
            "Sheet2": xl_typing.xl_Sheet_Protocol(name="Sheet2"),
        }
        self.apps = xl_typing.xl_apps_Protocol()


# -----------------------------------------------------------------------------
# -- Layer 1: ProfiledXLConnection


def test_profiled_connection_behaves_like_xl_connection():
    conn = profiling.ProfiledXLConnection(xl_framework=Mock_XL_Framework())

    xl_item = xl_data.XlItem("Sheet1", "A1", 42)
    conn.write_xl_item(xl_item)
    assert conn.get_sheet_by_name("Sheet1").range("A1").value == 42
    assert conn.get_data("Sheet1", "A1") == 42


def test_profiled_connection_records_calls_with_detail():
    conn = profiling.ProfiledXLConnection(xl_framework=Mock_XL_Framework())
    conn.records.clear()

    conn.write_xl_item(xl_data.XlItem("Sheet1", "B2", "hello"))
    conn.write_xl_item(xl_data.XlItem("Sheet2", "C3", 1))  # the mock double has no value until written
    conn.get_data("Sheet2", "C3")

    methods = [r.method for r in conn.records]
    assert "write_xl_item" in methods
    assert "get_data" in methods
    assert all(r.duration >= 0.0 for r in conn.records)

    write_record = next(r for r in conn.records if r.method == "write_xl_item")
    assert "Sheet1:B2" in write_record.detail
    read_record = next(r for r in conn.records if r.method == "get_data")
    assert "Sheet2" in read_record.detail and "C3" in read_record.detail


def test_profiled_connection_records_nested_facade_calls():
    conn = profiling.ProfiledXLConnection(xl_framework=Mock_XL_Framework())
    conn.records.clear()

    # -- write_xl_item internally calls get_sheet_by_name on self.
    conn.write_xl_item(xl_data.XlItem("Sheet1", "A1", 1))
    methods = [r.method for r in conn.records]
    assert "get_sheet_by_name" in methods
    assert "write_xl_item" in methods


def test_method_summary_aggregation():
    conn = profiling.ProfiledXLConnection(xl_framework=Mock_XL_Framework())
    conn.records.clear()

    for i in range(3):
        conn.write_xl_item(xl_data.XlItem("Sheet1", f"A{i + 1}", i))

    summary = {row["method"]: row for row in conn.method_summary()}
    assert summary["write_xl_item"]["calls"] == 3
    assert summary["write_xl_item"]["total_s"] >= 0.0

    report = conn.profile_report()
    assert report["total_facade_calls"] == len(conn.records)
    assert len(report["hot_spots_top20"]) <= 20


def test_unprofiled_methods_are_not_recorded():
    conn = profiling.ProfiledXLConnection(xl_framework=Mock_XL_Framework())
    conn.records.clear()

    assert conn.find_row(2, [1, 2, 3]) == 1
    assert conn.records == []


# -----------------------------------------------------------------------------
# -- Layer 2: CountingFrameworkProxy


def _proxied_connection():
    from PHX.xl.xl_app import XLConnection

    counter = profiling.OpCounter()
    framework = profiling.CountingFrameworkProxy(Mock_XL_Framework(), counter)
    return XLConnection(xl_framework=framework), counter


def test_counting_proxy_counts_write_events():
    conn, counter = _proxied_connection()
    conn.write_xl_item(xl_data.XlItem("Sheet1", "A1", 42))

    assert counter.counts[("range.value.set", "Sheet1")] == 1
    assert counter.total_round_trips() >= 1
    # -- ...and the underlying write actually landed.
    assert conn.get_sheet_by_name("Sheet1").range("A1").value == 42


def test_counting_proxy_counts_read_events_per_sheet():
    conn, counter = _proxied_connection()
    conn.write_xl_item(xl_data.XlItem("Sheet1", "A1", 1))
    conn.get_data("Sheet1", "A1")
    conn.get_data("Sheet1", "A1")

    assert counter.counts[("range.value.get", "Sheet1")] == 2


def test_counting_proxy_counts_cell_loop_inside_facade_method():
    """The whole point of the deep layer: catch per-row loops inside one facade call."""
    conn, counter = _proxied_connection()
    for row in range(1, 6):
        conn.write_xl_item(xl_data.XlItem("Sheet1", f"A{row}", f"val-{row}"))
    counter.counts.clear()

    found_row = conn.get_row_num_of_value_in_column("Sheet1", 1, 5, "A", "val-4")
    assert found_row == 4
    # -- One facade call, but FOUR low-level value reads (rows 1..4).
    assert counter.counts[("range.value.get", "Sheet1")] == 4


def test_counting_proxy_counts_app_toggles_and_calculate():
    conn, counter = _proxied_connection()
    with conn.in_silent_mode():
        pass

    # -- 3 toggles on entry + 3 on exit, + the exit calculate().
    assert sum(n for (op, _), n in counter.counts.items() if op == "app.toggle.set") == 6
    assert counter.counts[("app.calculate", "-")] == 1


def test_sheet_name_reads_do_not_scale_with_facade_calls():
    """Regression guard for the Tier-1 worksheet-names cache: before the cache,
    every 'get_sheet_by_name' call re-read ALL sheet names live (~97% of an
    export's round trips). One sweep of the workbook is the allowed maximum."""
    conn, counter = _proxied_connection()
    for i in range(50):
        conn.write_xl_item(xl_data.XlItem("Sheet1", f"A{i + 1}", i))

    name_reads = sum(n for (op, _), n in counter.counts.items() if op == "sheet.name.get")
    assert name_reads <= 2  # the mock workbook has 2 sheets: one full sweep, ever


def test_counting_proxy_report_shape():
    conn, counter = _proxied_connection()
    conn.write_xl_item(xl_data.XlItem("Sheet1", "A1", 1))
    report = counter.report()

    assert report["total_round_trips"] >= 1
    ops = {row["op"] for row in report["by_op"]}
    assert "range.value.set" in ops
    assert any(row["sheet"] == "Sheet1" for row in report["round_trips_by_sheet"])
