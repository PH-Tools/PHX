from pathlib import Path

import pytest

from PHX.PHPP.phpp_localization.load import get_shape_filepath
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.phpp_model.version import PHPPVersion


@pytest.mark.parametrize(
    "version",
    [
        PHPPVersion("9", "6A", "EN"),
        PHPPVersion("9", "7IP", "EN"),
        PHPPVersion("10", "3", "EN"),
        PHPPVersion("10", "4A", "EN"),
        PHPPVersion("10", "4IP", "EN"),
    ],
)
def test_load_all_shape_files(version) -> None:
    shape_file_dir = Path("PHX", "PHPP", "phpp_localization")
    phpp_shape_filepath = get_shape_filepath(version, shape_file_dir)
    phpp_shape = PhppShape.parse_file(phpp_shape_filepath)
    assert phpp_shape is not None
