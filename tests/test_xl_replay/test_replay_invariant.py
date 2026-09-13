# -*- Python Version: 3.10 -*-

"""The record/replay invariant test (plan doc 04, section 2).

Replays the full production PHPP write-sequence against the in-memory fake
workbook (seeded from a recorded live run) and asserts that the final written
cell-state matches the recorded golden state EXACTLY.

The Tier-1 batching refactors (T1.2/T1.3) change HOW cells are written - this
test proves they do not change WHAT ends up in the workbook. Because the fake
resolves every read against cell-state (not a call log), the fixture survives
cell-loop -> block-read/write refactors.

Accepted limitation (per the plan): the fake cannot catch ordering bugs that
only matter under live recalc - the live H2 read-back check covers those.

To (re-)record the fixture: 'python scripts/perf/record_replay_fixture.py'.
"""

import json
import pathlib

import pytest

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.hbjson_to_phpp import write_phx_project_to_phpp
from PHX.PHPP import phpp_app
from PHX.xl.xl_app import XLConnection
from tests.test_xl_replay.fake_xl_framework import FakeXLFramework

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"
FIXTURE_FILE = FIXTURES_DIR / "single_zone_replay.json"
HBJSON_FILE = FIXTURES_DIR / "Single_Zone.hbjson"
FOUNDATION_FIXTURE_FILE = pathlib.Path(__file__).parent / "_private" / "single_zone_slab_on_grade_replay.json"
FOUNDATION_HBJSON_FILE = FIXTURES_DIR / "Single_Zone_Slab_On_Grade.hbjson"


def _diff_cell_states(result: dict, golden: dict) -> list[str]:
    """Human-readable diffs between two {sheet: {addr: value}} states."""
    diffs = []
    for sheet in sorted(set(result) | set(golden)):
        result_cells = result.get(sheet, {})
        golden_cells = golden.get(sheet, {})
        for addr in sorted(set(result_cells) | set(golden_cells), key=lambda a: (len(a), a)):
            if addr not in golden_cells:
                diffs.append(f"{sheet}!{addr}: EXTRA write {result_cells[addr]!r}")
            elif addr not in result_cells:
                diffs.append(f"{sheet}!{addr}: MISSING write (golden: {golden_cells[addr]!r})")
            elif result_cells[addr] != golden_cells[addr]:
                diffs.append(f"{sheet}!{addr}: {result_cells[addr]!r} != golden {golden_cells[addr]!r}")
    return diffs


def test_full_export_replay_matches_golden_cell_state(reset_class_counters) -> None:
    # -- Fail (never skip) if the fixture is missing: a silent skip would turn
    # -- off the write-path regression gate without anyone noticing in CI.
    assert FIXTURE_FILE.exists(), (
        f"Replay fixture not found: {FIXTURE_FILE}. It is versioned in-repo; "
        "re-record with 'python scripts/perf/record_replay_fixture.py' if it was removed intentionally."
    )
    _assert_replay_matches_golden(FIXTURE_FILE, HBJSON_FILE)


@pytest.mark.skipif(not FOUNDATION_FIXTURE_FILE.exists(), reason="private fixture absent (see _private/MANIFEST.md)")
def test_foundation_export_replay_matches_golden_cell_state(reset_class_counters) -> None:
    # -- 'Single_Zone.hbjson' has no foundation, so the fixture above never reaches the
    # -- 'Ground' writer. This one does; its seed is read from the licensed PHPP
    # -- template, so it lives in the gitignored '_private/' folder and skips without it.
    _assert_replay_matches_golden(FOUNDATION_FIXTURE_FILE, FOUNDATION_HBJSON_FILE)


def _assert_replay_matches_golden(_fixture_file: pathlib.Path, _hbjson_file: pathlib.Path) -> None:
    fixture = json.loads(_fixture_file.read_text())

    # -- Build the reference PhxProject (deterministic: counters are reset).
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(_hbjson_file)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True)

    # -- Replay the production write sequence against the fake workbook.
    fake_xl = FakeXLFramework(
        sheet_names=fixture["sheet_names"],
        seed=fixture["seed"],
        epoch_deltas=fixture["epoch_deltas"],
        named_ranges={
            "Climate": {
                "Klima_Region": "D9",
                "Klima_Region2": "D10",
                "Klima_Standort": "D12",
                "Klimadaten_Muster": "D67",
                "Klimadaten_Muster_Quelle": "E76",
            }
        },
    )
    connection = XLConnection(xl_framework=fake_xl)
    phpp_conn = phpp_app.PHPPConnection(connection)

    with connection.in_silent_mode():
        connection.unprotect_all_sheets()
        write_phx_project_to_phpp(phpp_conn, phx_project)

    # -- THE invariant: identical final written cell-state, exactly.
    diffs = _diff_cell_states(fake_xl.written_state(), fixture["golden_writes"])
    assert not diffs, f"{len(diffs)} cell-state differences vs golden:\n" + "\n".join(f"  {d}" for d in diffs[:50])

    # -- ...and identical cell/font color application.
    result_colors = json.loads(json.dumps(fake_xl.color_state()))  # tuples -> lists, like the fixture
    color_diffs = _diff_cell_states(result_colors, fixture["golden_colors"])
    assert not color_diffs, f"{len(color_diffs)} color differences vs golden:\n" + "\n".join(
        f"  {d}" for d in color_diffs[:50]
    )
