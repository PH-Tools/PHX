# -*- Python Version: 3.10 -*-

"""T0.3 / T0.5: Profile a real HBJSON -> PHPP export and capture golden read-back state.

Runs the exact production write sequence ('PHX.hbjson_to_phpp.write_phx_project_to_phpp')
against a SCRATCH COPY of the PHPP template, instrumented with:

    * H1a ProfiledXLConnection  — per-facade-method call counts + timing
    * H1b CountingFrameworkProxy (--deep) — actual low-level round-trip counts

MANUAL-INVOCATION ONLY. Never run while a production export is in progress.
The PHPP template is never opened — a copy is made in the scratch dir first.

Usage:
    # Quick smoke pass (Single_Zone is the default HBJSON):
    python scripts/perf/profile_export.py --yes

    # The real T0.3 baseline (deep counting + golden read-back capture):
    python scripts/perf/profile_export.py --hbjson <...>/Linde_Home.hbjson --deep --golden --label linde

Deliverables land in 'scripts/perf/baselines/':
    profile__<label>__<ts>.json          - profile report (+ round-trip counts with --deep)
    golden_readback__<label>.json        - H2 key-cell extract (with --golden; T0.5)
"""

import argparse
import json
import sys
import time

import perf_paths
import profiling
import readback_verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hbjson", help="Source HBJSON (default: packet Single_Zone.hbjson).")
    parser.add_argument("--phpp", help="PHPP template .xlsx (default: packet EN v10.6 empty). Never written to.")
    parser.add_argument("--scratch", help="Scratch dir for the working copy (default: packet scratch/).")
    parser.add_argument("--deep", action="store_true", help="Also count low-level framework events (H1b).")
    parser.add_argument("--golden", action="store_true", help="Save the workbook + capture H2 golden read-back (T0.5).")
    parser.add_argument("--save", action="store_true", help="Save the scratch workbook at the end.")
    parser.add_argument("--close", action="store_true", help="Close the scratch workbook when done.")
    parser.add_argument("--label", default="run", help="Label used in output file names.")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    hbjson_path = perf_paths.resolve_hbjson_path(args.hbjson)
    phpp_template = perf_paths.resolve_phpp_path(args.phpp)
    scratch_dir = perf_paths.resolve_scratch_dir(args.scratch)

    perf_paths.confirm_live_excel_run(args.yes)
    meta = perf_paths.environment_metadata()
    meta["hbjson"] = str(hbjson_path)
    meta["phpp_template"] = str(phpp_template)
    print(f"Excel build check (T0.1): {meta['excel_build_check']}")

    # -- Build the PhxProject first (offline — no Excel involved).
    print(f"Reading HBJSON: {hbjson_path.name} ...")
    from PHX.from_HBJSON import create_project, read_HBJSON_file

    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(hbjson_path)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True)

    # -- NEVER open the template itself: work on a scratch copy.
    scratch_copy = perf_paths.make_scratch_copy(phpp_template, scratch_dir, args.label)
    print(f"Scratch copy: {scratch_copy}")
    perf_paths.preopen_workbook_macos(scratch_copy)

    import xlwings as xw

    from PHX.hbjson_to_phpp import write_phx_project_to_phpp
    from PHX.PHPP import phpp_app

    counter = None
    framework = xw
    if args.deep:
        counter = profiling.OpCounter()
        framework = profiling.CountingFrameworkProxy(xw, counter)

    connection = profiling.ProfiledXLConnection(xl_framework=framework, xl_file_path=scratch_copy)
    phpp_conn = phpp_app.PHPPConnection(connection)
    print(f"Connected: {connection.wb.fullname} (PHPP {phpp_conn.version})")

    print("Running export ...")
    t0 = time.perf_counter()
    with connection.in_silent_mode():
        connection.unprotect_all_sheets()
        write_phx_project_to_phpp(phpp_conn, phx_project)
    wall_time = time.perf_counter() - t0
    print(f"Export complete in {wall_time:.1f} s ({len(connection.records)} facade calls).")

    # -- Reports
    perf_paths.BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    stamp = meta["timestamp"].replace(":", "-")
    profile_path = perf_paths.BASELINES_DIR / f"profile__{args.label}__{stamp}.json"
    profiling.write_profile_json(profile_path, meta, wall_time, connection, counter)
    print(f"Wrote profile -> {profile_path.relative_to(perf_paths.REPO_ROOT)}")

    print("\nTop facade methods by cumulative time:")
    for row in connection.method_summary()[:10]:
        print(
            f"  {row['method']:<38} calls={row['calls']:<6} total={row['total_s']:>8.2f} s   mean={row['mean_ms']:.1f} ms"
        )
    if counter:
        print(f"\nTotal low-level round trips: {counter.total_round_trips()}")
        for row in counter.by_op()[:10]:
            marker = "*" if row["is_round_trip"] else " "
            print(f"  {marker} {row['op']:<28} x{row['count']}")

    # -- T0.5: golden read-back capture (requires a saved file for openpyxl).
    if args.golden or args.save:
        connection.wb.save()
        print(f"Saved workbook: {scratch_copy}")
    if args.golden:
        spec = json.loads(readback_verify.DEFAULT_SPEC.read_text())["entries"]
        reader = readback_verify.OpenpyxlReader(scratch_copy)
        values = readback_verify.extract(reader, spec)
        golden_path = perf_paths.BASELINES_DIR / f"golden_readback__{args.label}.json"
        golden_path.write_text(
            json.dumps({"source": str(scratch_copy), "meta": meta, "values": values}, indent=2, default=str)
        )
        print(f"Wrote golden read-back -> {golden_path.relative_to(perf_paths.REPO_ROOT)}")
        errors = [k for k, v in values.items() if isinstance(v, str) and v.startswith("#ERROR")]
        if errors:
            print(f"WARNING: {len(errors)} read-back entries failed: {', '.join(errors)}", file=sys.stderr)

    if args.close:
        connection.wb.close()
        print("Closed scratch workbook.")
    else:
        print("Scratch workbook left open for inspection (close it manually; never 'save as' over the template).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
