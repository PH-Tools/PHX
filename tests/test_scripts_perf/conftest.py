# -*- Python Version: 3.10 -*-

"""Make the (non-packaged) 'scripts/perf/' modules importable for these tests."""

import pathlib
import sys

SCRIPTS_PERF_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "perf"
if str(SCRIPTS_PERF_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PERF_DIR))
