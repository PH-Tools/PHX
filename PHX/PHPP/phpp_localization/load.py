# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions for finding / loading the right PHPP-ShapeFile."""


import pathlib
import os

from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.phpp_model import version
from PHX.xl import xl_app


def phpp_version_as_file_name(version: version.PHPPVersion):
    """Return the version as a file-name."""
    return f"{version.language}_{version.number_major}_{version.number_minor}"


def get_shape_filepath(version: version.PHPPVersion, _shape_file_directory: pathlib.Path):
    """Returns the path to the PHPP Shape File based on the language and PHPP version found.

    Arguments:
    ----------
        * _xl (xl_app.XLConnection): The XL connection to use to find the version data.
        * _shape_file_directory ():

    Returns:
    --------
        * (pathlib.Path): The path to the correct PHPP Shape File.
    """
    shape_file_name = phpp_version_as_file_name(version)
    shape_file_name = f"{shape_file_name}.json"
    shape_file_path = pathlib.Path(_shape_file_directory, shape_file_name)

    if not os.path.exists(shape_file_path):
        raise FileNotFoundError(
            f'\n\tError: The PHPP shapefile "{shape_file_path}" was not found?'
        )

    return shape_file_path


def get_phpp_shape(_xl: xl_app.XLConnection, version: version.PHPPVersion) -> PhppShape:
    """Return the PhppShape Object."""

    shape_file_dir = pathlib.Path(__file__).parent
    phpp_shape_filepath = get_shape_filepath(version, shape_file_dir)
    _xl.output(f"Loading PHPP Shapefile:\n\t{phpp_shape_filepath}")
    phpp_shape = PhppShape.parse_file(phpp_shape_filepath)

    return phpp_shape
