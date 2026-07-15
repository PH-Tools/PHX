# -*- Python Version: 3.10 -*-

"""H2 spec-engine and compare-mode tests — run against an in-memory fake reader."""

import pytest
import readback_verify


class FakeReader:
    """WorkbookReader over a {sheet: {address: value}} dict."""

    def __init__(self, data: dict[str, dict[str, object]]):
        self.data = data
        self.column_read_count = 0

    def read_cell(self, sheet, address):
        return self.data.get(sheet, {}).get(address)

    def read_column(self, sheet, col, row_start, row_end):
        self.column_read_count += 1
        sheet_data = self.data.get(sheet, {})
        return [sheet_data.get(f"{col}{row}") for row in range(row_start, row_end + 1)]


VERIFICATION_DATA = {
    "Verification": {
        "G35": "Treated floor area",
        "I35": 120.5,
        "G36": "Heating demand",
        "I36": 14.2,
        "G43": "Pressurisation test result n50",
        "I43": 0.55,
    }
}


# -----------------------------------------------------------------------------
# -- Spec entry kinds


def test_cell_entry():
    reader = FakeReader(VERIFICATION_DATA)
    spec = [{"name": "tfa", "kind": "cell", "sheet": "Verification", "address": "I35"}]
    assert readback_verify.extract(reader, spec) == {"tfa": 120.5}


def test_locator_cell_contains_match():
    reader = FakeReader(VERIFICATION_DATA)
    spec = [
        {
            "name": "heating_demand",
            "kind": "locator_cell",
            "sheet": "Verification",
            "locator_col": "G",
            "locator_string": "Heating demand",
            "value_col": "I",
            "row_start": 20,
            "row_end": 80,
        }
    ]
    assert readback_verify.extract(reader, spec) == {"heating_demand": 14.2}


def test_locator_cell_with_row_offset():
    reader = FakeReader({"Sheet1": {"A5": "My Label", "B7": 99}})
    spec = [
        {
            "name": "offset_value",
            "kind": "locator_cell",
            "sheet": "Sheet1",
            "locator_col": "A",
            "locator_string": "My Label",
            "value_col": "B",
            "row_offset": 2,
            "row_end": 10,
        }
    ]
    assert readback_verify.extract(reader, spec) == {"offset_value": 99}


def test_locator_cell_not_found_reports_error():
    reader = FakeReader(VERIFICATION_DATA)
    spec = [
        {
            "name": "missing",
            "kind": "locator_cell",
            "sheet": "Verification",
            "locator_col": "G",
            "locator_string": "No Such Label",
            "value_col": "I",
            "row_end": 50,
        }
    ]
    result = readback_verify.extract(reader, spec)
    assert str(result["missing"]).startswith("#ERROR")


BLOCK_DATA = {
    "Areas": {
        "K10": "Area input",
        "L11": "Wall North",
        "T11": 25.0,
        "L12": "Wall South",
        "T12": 30.0,
        "L13": "Roof",
        "T13": "not-a-number",
        # -- row 14 is blank
        "K15": "Thermal bridge input",
        "L16": "TB-01",  # below the stop row: must NOT be counted in the surfaces block
    }
}


def test_block_count_stops_at_next_section_header():
    reader = FakeReader(BLOCK_DATA)
    spec = [
        {
            "name": "surface_count",
            "kind": "block_count",
            "sheet": "Areas",
            "header_col": "K",
            "header_string": "Area input",
            "value_col": "L",
            "max_rows": 50,
            "stop_col": "K",
            "stop_string": "Thermal bridge input",
        }
    ]
    assert readback_verify.extract(reader, spec) == {"surface_count": 3}


def test_block_sum_ignores_non_numeric():
    reader = FakeReader(BLOCK_DATA)
    spec = [
        {
            "name": "area_sum",
            "kind": "block_sum",
            "sheet": "Areas",
            "header_col": "K",
            "header_string": "Area input",
            "value_col": "T",
            "max_rows": 50,
            "stop_col": "K",
            "stop_string": "Thermal bridge input",
        }
    ]
    assert readback_verify.extract(reader, spec) == {"area_sum": 55.0}


def test_block_count_numeric_only_skips_text_headers():
    reader = FakeReader({"Windows": {"L5": "Windows and entrance doors", "L7": "Quan-", "L9": 1, "L10": 2}})
    spec = [
        {
            "name": "window_rows",
            "kind": "block_count",
            "sheet": "Windows",
            "header_col": "L",
            "header_string": "Windows and entrance doors",
            "value_col": "L",
            "numeric_only": True,
            "max_rows": 20,
        }
    ]
    assert readback_verify.extract(reader, spec) == {"window_rows": 2}


def test_block_count_numeric_filter_col_excludes_special_rows():
    """Areas pattern: user entry rows have a numeric 'Area no.' in K; the
    sub-header and the built-in special rows (TFA, window areas...) do not."""
    reader = FakeReader(
        {
            "Areas": {
                "K30": "Area input",
                "K31": "Area no.",  # sub-header
                "L31": "Building assembly description",
                "L32": "Treated floor area",  # special row: no number in K
                "K33": "1",
                "L33": "Wall North",
                "T33": 25.0,
                "K34": "2",
                "L34": "Wall South",
                "T34": 30.0,
                "K35": "3",  # numbered slot left empty by the user
            }
        }
    )
    base = {
        "kind": "block_count",
        "sheet": "Areas",
        "header_col": "K",
        "header_string": "Area input",
        "filter_col": "K",
        "filter_kind": "numeric",
        "max_rows": 20,
    }
    spec = [
        dict(base, name="count", value_col="L"),
        dict(base, name="area_sum", kind="block_sum", value_col="T"),
    ]
    assert readback_verify.extract(reader, spec) == {"count": 2, "area_sum": 55.0}


def test_block_count_contains_filter_col():
    """Components pattern: user slots have '...ud' IDs; library rows do not."""
    reader = FakeReader(
        {
            "Components": {
                "IH13": "01ud",
                "II13": "My Glazing",
                "IH14": "02ud",
                "IH20": "Some library header",
                "II20": "Library Glazing A",
            }
        }
    )
    spec = [
        {
            "name": "glazing_count",
            "kind": "block_count",
            "sheet": "Components",
            "start_row": 13,
            "value_col": "II",
            "filter_col": "IH",
            "filter_kind": "contains",
            "filter_value": "ud",
            "max_rows": 20,
        }
    ]
    assert readback_verify.extract(reader, spec) == {"glazing_count": 1}


def test_block_count_with_fixed_start_row():
    reader = FakeReader({"Components": {"II13": "Glazing-A", "II14": "Glazing-B"}})
    spec = [
        {
            "name": "glazing_count",
            "kind": "block_count",
            "sheet": "Components",
            "start_row": 13,
            "value_col": "II",
            "max_rows": 20,
        }
    ]
    assert readback_verify.extract(reader, spec) == {"glazing_count": 2}


def test_caching_reader_memoizes_column_reads():
    reader = FakeReader(VERIFICATION_DATA)
    spec = [
        {
            "name": f"entry_{i}",
            "kind": "locator_cell",
            "sheet": "Verification",
            "locator_col": "G",
            "locator_string": label,
            "value_col": "I",
            "row_start": 20,
            "row_end": 80,
        }
        for i, label in enumerate(["Treated floor area", "Heating demand", "Pressurisation test result n50"])
    ]
    results = readback_verify.extract(reader, spec)
    assert len(results) == 3
    assert reader.column_read_count == 1  # one G20:G80 read serves all three locators


def test_unknown_kind_reports_error():
    result = readback_verify.extract(FakeReader({}), [{"name": "bad", "kind": "nope"}])
    assert str(result["bad"]).startswith("#ERROR")


# -----------------------------------------------------------------------------
# -- Compare mode


def test_compare_equal_extracts():
    a = {"x": 1.0, "y": "hello", "z": None}
    assert readback_verify.compare(a, dict(a)) == []


def test_compare_within_tolerance():
    a = {"heating": 14.200000}
    b = {"heating": 14.200001}
    assert readback_verify.compare(a, b, rtol=1e-6) == []
    assert len(readback_verify.compare(a, b, rtol=1e-9, atol=0.0)) == 1


def test_compare_numeric_string_vs_number():
    # openpyxl and xlwings may type the same cell differently.
    assert readback_verify.compare({"n": "42.0"}, {"n": 42}) == []


def test_compare_reports_missing_keys_and_mismatches():
    diffs = readback_verify.compare({"a": 1, "b": "x"}, {"b": "y", "c": 3})
    assert len(diffs) == 3  # 'a' missing from second, 'b' mismatch, 'c' missing from first
    assert any("'a'" in d for d in diffs)
    assert any("'b'" in d for d in diffs)
    assert any("'c'" in d for d in diffs)


# -----------------------------------------------------------------------------
# -- The shipped spec file


def test_default_spec_file_is_valid():
    import json

    spec = json.loads(readback_verify.DEFAULT_SPEC.read_text())["entries"]
    assert len(spec) > 10
    names = [entry["name"] for entry in spec]
    assert len(names) == len(set(names)), "spec entry names must be unique"
    valid_kinds = {"cell", "locator_cell", "block_count", "block_sum"}
    for entry in spec:
        assert entry["kind"] in valid_kinds
        assert "sheet" in entry


@pytest.mark.live_excel
def test_live_extract_smoke():
    """Placeholder: live xlwings extract is exercised manually via the CLI."""
