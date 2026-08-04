from pathlib import Path

import pytest

from PHX.PHPP.phpp_localization.load import get_shape_filepath
from PHX.PHPP.phpp_model.version import PHPPVersion, strip_easyph_edition_tag


@pytest.mark.parametrize(
    "raw_version_id,expected",
    [
        # -- easyPH tags the edition onto the version string on the 'Data' worksheet
        ("10.6 easyPHv3", "10.6"),
        ("10.6 easyPHv3 IP", "10.6 IP"),
        ("10.6easyPHv3", "10.6"),
        ("10.6 EASYPHV3", "10.6"),
        ("10.6 easyPH", "10.6"),
        # -- standard PHPP version strings are left alone
        ("10.6", "10.6"),
        ("10.6 IP", "10.6 IP"),
        ("10.4A", "10.4A"),
        ("9.6a", "9.6a"),
    ],
)
def test_strip_easyph_edition_tag(raw_version_id, expected) -> None:
    assert strip_easyph_edition_tag(raw_version_id) == expected


@pytest.mark.parametrize(
    "raw_version_id,expected_minor",
    [
        ("10.6 easyPHv3", "6"),
        ("10.6 easyPHv3 IP", "6IP"),
    ],
)
def test_easyph_version_parses_to_its_base_version(raw_version_id, expected_minor) -> None:
    """An easyPH workbook must resolve to its base PHPP version, not to a new one.

    Without stripping the tag, `number_minor` becomes "6EASYPHV3" and the shapefile
    lookup asks for a file that does not exist.
    """
    ver_major, ver_minor = strip_easyph_edition_tag(raw_version_id).split(".")
    phpp_version = PHPPVersion(ver_major, ver_minor, "EN")

    assert phpp_version.number_major == "10"
    assert phpp_version.number_minor == expected_minor


@pytest.mark.parametrize(
    "raw_version_id",
    [
        "10.6 easyPHv3",
        "10.6 easyPHv3 IP",
    ],
)
def test_easyph_versions_resolve_to_a_real_shape_file(raw_version_id) -> None:
    """The end-to-end failure this fixes: an easyPH workbook raised FileNotFoundError
    from `get_shape_filepath` before any read or write could happen."""
    ver_major, ver_minor = strip_easyph_edition_tag(raw_version_id).split(".")
    phpp_version = PHPPVersion(ver_major, ver_minor, "EN")

    shape_file_dir = Path("PHX", "PHPP", "phpp_localization")

    assert get_shape_filepath(phpp_version, shape_file_dir).exists()
