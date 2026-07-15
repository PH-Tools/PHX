# -*- Python Version: 3.10 -*-

"""Shared path/config resolution for the Tier-0 perf scripts.

Resolution order for each input file:
    1. Command-line argument (handled by each script)
    2. Environment variable ('PHX_TEST_PHPP' / 'PHX_TEST_HBJSON')
    3. 'config.local.json' next to this file (gitignored)
    4. The packet defaults in 'plans/20260714/excel-interop-refactor/test_files/'

GROUND RULES (from the Tier-0 plan):
    * NEVER open the PHPP template for a write-run. Always work on a scratch copy.
    * All live-Excel scripts are manual-invocation only. Never run one while a
      production export is in progress.
"""

import json
import pathlib
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKET_DIR = REPO_ROOT / "plans" / "20260714" / "excel-interop-refactor"
TEST_FILES_DIR = PACKET_DIR / "test_files"
BASELINES_DIR = pathlib.Path(__file__).resolve().parent / "baselines"
LOCAL_CONFIG_FILE = pathlib.Path(__file__).resolve().parent / "config.local.json"

DEFAULT_PHPP = TEST_FILES_DIR / "PHPP_EN_V10.6_Empty.xlsx"
DEFAULT_HBJSON = TEST_FILES_DIR / "Single_Zone.hbjson"

# -- Scratch dir lives under 'plans/' which is gitignored, so licensed PHPP
# -- copies can never leak into the public repo.
DEFAULT_SCRATCH_DIR = PACKET_DIR / "scratch"

MINIMUM_EXCEL_BUILD = "16.102.2"


def _local_config() -> dict[str, str]:
    if LOCAL_CONFIG_FILE.exists():
        return json.loads(LOCAL_CONFIG_FILE.read_text())
    return {}


def _resolve(cli_value: str | None, env_var: str, config_key: str, default: pathlib.Path) -> pathlib.Path:
    import os

    if cli_value:
        return pathlib.Path(cli_value).expanduser().resolve()
    if env_value := os.environ.get(env_var):
        return pathlib.Path(env_value).expanduser().resolve()
    if config_value := _local_config().get(config_key):
        return pathlib.Path(config_value).expanduser().resolve()
    return default


def resolve_phpp_path(cli_value: str | None = None) -> pathlib.Path:
    """Return the PHPP template path (never open this for writing)."""
    path = _resolve(cli_value, "PHX_TEST_PHPP", "phpp", DEFAULT_PHPP)
    if not path.exists():
        sys.exit(f"Error: PHPP template not found: {path}")
    return path


def resolve_hbjson_path(cli_value: str | None = None) -> pathlib.Path:
    """Return the source HBJSON path."""
    path = _resolve(cli_value, "PHX_TEST_HBJSON", "hbjson", DEFAULT_HBJSON)
    if not path.exists():
        sys.exit(f"Error: HBJSON file not found: {path}")
    return path


def resolve_scratch_dir(cli_value: str | None = None) -> pathlib.Path:
    """Return (and create) the scratch working directory."""
    path = _resolve(cli_value, "PHX_PERF_SCRATCH", "scratch", DEFAULT_SCRATCH_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_scratch_copy(template: pathlib.Path, scratch_dir: pathlib.Path, label: str) -> pathlib.Path:
    """Copy the PHPP template into the scratch dir and return the copy's path.

    The template itself is never opened — every write-run targets the copy.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = scratch_dir / f"{template.stem}__{label}__{stamp}{template.suffix}"
    shutil.copy2(template, target)
    return target


def preopen_workbook_macos(_path: pathlib.Path, _timeout_s: int = 90) -> None:
    """Open a workbook via LaunchServices ('open -a') and wait until Excel has it.

    On macOS, a freshly-launched Excel can silently refuse an automation-initiated
    'books.open()' (sandbox file-access: error -1728 'object does not exist').
    Opening via LaunchServices counts as user-initiated, so it always succeeds;
    xlwings' 'books.open()' then simply attaches to the already-open workbook.
    """
    import time

    if platform.system() != "Darwin":
        return
    subprocess.run(["open", "-a", "Microsoft Excel", str(_path)], check=True)
    probe = 'with timeout of 8 seconds\ntell application "Microsoft Excel" to get name of every workbook\nend timeout'
    for _ in range(_timeout_s):
        result = subprocess.run(["osascript", "-e", probe], capture_output=True, text=True, timeout=20)
        if _path.name in result.stdout:
            return
        time.sleep(1)
    raise TimeoutError(f"Excel did not open '{_path.name}' within {_timeout_s}s.")


def get_excel_version_macos() -> str | None:
    """Return the installed Excel version string (macOS only), or None."""
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemVersion", "-raw", "/Applications/Microsoft Excel.app"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        version = result.stdout.strip().strip('"')
        return version or None
    except Exception:
        return None


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split(".") if p.isdigit())


def check_excel_build(version: str | None) -> str:
    """Return a T0.1 verdict string for the installed Excel build."""
    if not version:
        return "unknown (could not read Excel version)"
    if _version_tuple(version) >= _version_tuple(MINIMUM_EXCEL_BUILD):
        return f"OK ({version} >= {MINIMUM_EXCEL_BUILD})"
    return f"TOO OLD ({version} < {MINIMUM_EXCEL_BUILD} — update Excel before benchmarking)"


def environment_metadata() -> dict[str, Any]:
    """Collect machine/OS/Excel metadata for baseline reports (T0.1)."""
    excel_version = get_excel_version_macos()
    meta: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "excel_version": excel_version,
        "excel_build_check": check_excel_build(excel_version),
    }
    if platform.system() == "Darwin":
        meta["macos_version"] = platform.mac_ver()[0]
    try:
        import xlwings

        meta["xlwings_version"] = xlwings.__version__
    except Exception:
        meta["xlwings_version"] = None
    return meta


def confirm_live_excel_run(assume_yes: bool) -> None:
    """Interactive guard: refuse to automate Excel without explicit confirmation.

    Live-Excel scripts must never run while a production export is in progress.
    """
    if assume_yes:
        return
    print(
        "\nThis script will automate Microsoft Excel.\n"
        "Do NOT continue if any PHPP export or other Excel automation is currently running.\n"
    )
    answer = input("Continue? [y/N] ").strip().lower()
    if answer not in ("y", "yes"):
        sys.exit("Aborted.")
