# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions for finding / loading the right PHPP-ShapeFile."""


import pathlib
import os
from typing import Tuple

from PHX.xl import xl_app
from PHX.xl.xl_typing import xl_Sheet_Protocol
from PHX.PHPP.phpp_localization.shape_model import PhppShape


def get_data_worksheet(_xl: xl_app.XLConnection) -> xl_Sheet_Protocol:
    """Return the 'Data' worksheet from the active PHPP file, support English, German, Spanish."""
    worksheet_names = _xl.get_worksheet_names()
    for worksheet_name in ["Data", "Daten", "Datos"]:
        if worksheet_name in worksheet_names:
            return _xl.get_sheet_by_name(worksheet_name)

    raise Exception(
        f"Error: Cannot fine a 'Data' worksheet in the Excel file: {_xl.wb.name}?"
    )


def get_phpp_version(
    _xl: xl_app.XLConnection,
    _search_col: str = "A",
    _row_start: int = 1,
    _row_end: int = 10,
) -> Tuple[str, str]:
    """Find the PHPP Version and Language of the active xl-file.

    Arguments:
    ----------
        * _xl (xl_app.XLConnection):
        * _search_col (str)
        * _row_start (int) default=1
        * _row_end (int) default=10

    Returns:
    --------
        * (Tuple[str, str]): The Version number and Language of the Active PHPP.
    """

    # -- Find the right 'Data' worksheet
    data_worksheet: xl_Sheet_Protocol = get_data_worksheet(_xl)

    # -- Pull the search Column data from the Active XL Instance
    data = _xl.get_single_column_data(
        _sheet_name=data_worksheet.name,
        _col=_search_col,
        _row_start=_row_start,
        _row_end=_row_end,
    )

    for i, xl_rang_data in enumerate(data, start=_row_start):
        if str(xl_rang_data).upper().strip().replace(" ", "").startswith("PHPP"):
            data_row = i
            break
    else:
        raise Exception(
            f"Error: Cannot determine the PHPP Version? Expected 'PHPP' in"
            "col: {_search_col} of the {data_worksheet.name} worksheet?"
        )

    # -- Pull the search row data from the Active XL Instance
    data = _xl.get_single_row_data(data_worksheet.name, data_row)
    data = [_ for _ in data if _ is not None and _ is not ""]

    # -- Find the right Versions number
    version = str(data[1]).upper().strip().replace(" ", "").replace(".", "_")

    # - Figure out the PHPP language
    language_search_data = {
        "1-PE-FAKTOREN": "DE",
        "1-FACTORES EP": "ES",
        "1-PE-FACTORS": "EN",
    }
    language = None
    for search_string in language_search_data.keys():
        if search_string in str(data[-1]).upper().strip():
            language = language_search_data[search_string]
            language = language.strip().replace(" ", "_").replace(".", "_")
            break
    if not language:
        raise Exception(
            "Error: Cannot determine the PHPP language? Only English, German and Spanish are supported."
        )

    return version, language


def get_shape_filepath(_xl: xl_app.XLConnection, _shape_file_directory: pathlib.Path):
    """Returns the path to the PHPP Shape File based on the language and PHPP version found.

    Arguments:
    ----------
        * _xl (xl_app.XLConnection): The XL connection to use to find the version data.
        * _shape_file_directory ():

    Returns:
    --------
        * (pathlib.Path): The path to the correct PHPP Shape File.
    """
    phpp_version, phpp_language = get_phpp_version(_xl)
    shape_file_name = f"{phpp_language}_{phpp_version}.json"
    shape_file_path = pathlib.Path(_shape_file_directory, shape_file_name)

    if not os.path.exists(shape_file_path):
        raise FileNotFoundError(
            f'\n\tError: The PHPP shapefile "{shape_file_path}" was not found?'
        )

    return shape_file_path


def get_phpp_shape(_xl: xl_app.XLConnection) -> PhppShape:
    """Return the PhppShape Object."""

    shape_file_dir = pathlib.Path(__file__).parent
    phpp_shape_filepath = get_shape_filepath(_xl, shape_file_dir)
    print(f"Loading PHPP Shapefile:\n\t{phpp_shape_filepath}")
    phpp_shape = PhppShape.parse_file(phpp_shape_filepath)

    return phpp_shape
