# -*- Python Version: 3.10 -*-

"""Write METr JSON text to a file."""

import pathlib


def write_metr_json_file(
    _file_path: str | pathlib.Path,
    _json_text: str,
) -> None:
    """Write METr JSON text to a file (UTF-8, no BOM).

    Arguments:
    ----------
        * _file_path (str | pathlib.Path): The target file path.
        * _json_text (str): The JSON text to write.

    Returns:
    --------
        * None
    """
    file_path = pathlib.Path(_file_path)
    file_path.write_text(_json_text, encoding="utf-8")
