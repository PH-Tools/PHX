# -*- Python Version: 3.10 -*-

"""Class for managing PHPP Version data."""

import re

# -- easyPH workbooks append an edition tag to the version string on 'Data', eg:
# --     "10.6 easyPHv3"      (SI)
# --     "10.6 easyPHv3 IP"   (IP)
# -- while a standard PHPP reads "10.6" or "10.6 IP". The tag identifies the easyPH
# -- edition, not a different shapefile: easyPH is a standard PHPP plus an 'easyPH'
# -- input worksheet, so it uses the same localization shape as its base version.
EASYPH_EDITION_TAG = re.compile(r"\s*easyPH\s*v?\d*(?:\.\d+)*\s*", re.IGNORECASE)


def strip_easyph_edition_tag(_raw_version_id: str) -> str:
    """Remove any 'easyPH' edition tag from a raw PHPP version string.

    Leaves everything else untouched, so the unit-system suffix that selects the
    shapefile survives:

        "10.6 easyPHv3"     -> "10.6"        -> EN_10_6.json
        "10.6 easyPHv3 IP"  -> "10.6 IP"     -> EN_10_6IP.json
        "10.6"              -> "10.6"        (unchanged)

    Without this, `PHPPVersion` builds a `number_minor` of "6EASYPHV3" and the
    shapefile lookup fails on a filename that does not exist.
    """
    return EASYPH_EDITION_TAG.sub(" ", str(_raw_version_id)).strip()


class PHPPVersion:
    """Manage the PHPP Version number and language information."""

    def __init__(self, _number_major: str, _number_minor: str, _language: str):
        self.number_major = self.clean_input(_number_major)
        self.number_minor = self.clean_input(_number_minor)
        self.language = self.clean_input(_language)

    def clean_input(self, _input):
        """Upper, strip, replace spaces."""
        return str(_input).upper().strip().replace(" ", "").replace(".", "_")

    def number(self) -> str:
        """Return the full version number (ie: "9.6", "10.4", etc..)"""
        return f"{self.number_major}.{self.number_minor}"
