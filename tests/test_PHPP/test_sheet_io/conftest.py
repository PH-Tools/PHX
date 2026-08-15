# -*- Python Version: 3.10 -*-

"""Shared helpers for the PHPP sheet-IO tests.

The IO controllers are driven entirely by the localization shape files, so
most tests here need to load one - and the locator tests need to sweep all of
them, so that a new localization cannot silently escape coverage.
"""

from pathlib import Path

from PHX.PHPP.phpp_localization.shape_model import PhppShape

SHAPE_DIR = Path("PHX", "PHPP", "phpp_localization")

#: Every localization shipped with PHX. Parametrize over this rather than
#: hard-coding a single file, so an eighth shape file is covered on arrival.
SHAPE_FILENAMES = (
    "EN_9_6A.json",
    "EN_9_7IP.json",
    "EN_10_3.json",
    "EN_10_4A.json",
    "EN_10_4IP.json",
    "EN_10_6.json",
    "EN_10_6IP.json",
)


def load_shape(_filename: str = "EN_10_6.json") -> PhppShape:
    """Return the full PhppShape for one localization file."""
    return PhppShape.model_validate_json((SHAPE_DIR / _filename).read_bytes())
