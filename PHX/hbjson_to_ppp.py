# -*- Python Version: 3.10 -*-

"""Run script to convert an HBJSON file to PPP format."""

import logging
import os
import pathlib
import sys

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_PPP import ppp_builder, ppp_txt_to_file


class InputFileError(Exception):
    def __init__(self, path) -> None:
        self.msg = f"\nError: Cannot find HBJSON file: {path}"
        super().__init__(self.msg)


def resolve_paths(_args: list[str]) -> tuple[pathlib.Path, pathlib.Path]:
    """Sort out the file input and output paths.

    Arguments:
    ----------
        * _args: sys.argv list.
            - [1] (str): Source HBJSON file path.
            - [2] (str): Target file name (without extension).
            - [3] (str): Target directory path.

    Returns:
    --------
        * Tuple[pathlib.Path, pathlib.Path]: (source, target) paths.
    """
    src = pathlib.Path(_args[1])
    if not src.exists():
        raise InputFileError(src)

    target_file = f"{_args[2]}.ppp"
    target_dir = pathlib.Path(_args[3])

    if not target_dir.exists():
        os.mkdir(target_dir)

    target = pathlib.Path(target_dir, target_file)
    return src, target


def group_components(_args: list[str]) -> bool:
    """Return the 'group_components' boolean from sys.argv."""
    try:
        return _args[4].lower() == "true"
    except (IndexError, AttributeError):
        return True


def merge_faces(_args: list[str]) -> bool | float:
    """Return the 'merge_faces' value from sys.argv."""
    try:
        val = _args[5].lower()
        if val == "true":
            return True
        elif val == "false":
            return False
        else:
            return float(val)
    except (IndexError, AttributeError, ValueError):
        return False


def merge_spaces_by_erv(_args: list[str]) -> bool:
    """Return the 'merge_spaces_by_erv' boolean from sys.argv."""
    try:
        return _args[6].lower() == "true"
    except (IndexError, AttributeError):
        return False


def merge_exhaust_vent_devices(_args: list[str]) -> bool:
    """Return the 'merge_exhaust_vent_devices' boolean from sys.argv."""
    try:
        return _args[7].lower() == "true"
    except (IndexError, AttributeError):
        return False


if __name__ == "__main__":
    # --- Input / Output file paths
    SOURCE_FILE, TARGET_FILE_PPP = resolve_paths(sys.argv)
    GROUP_COMPONENTS = group_components(sys.argv)
    MERGE_FACES = merge_faces(sys.argv)
    MERGE_SPACES_BY_ERV = merge_spaces_by_erv(sys.argv)
    MERGE_EXHAUST_VENT_DEVICES = merge_exhaust_vent_devices(sys.argv)

    # --- Setup logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

    # --- Read in the HBJSON and build HB Objects
    logger.info(f"> Reading HBJSON file: {SOURCE_FILE}")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(SOURCE_FILE)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # --- Generate the PHX Project
    logger.info(f'> Generating PHX-Project from Honeybee-Model: "{hb_model}"')
    phx_project = create_project.convert_hb_model_to_PhxProject(
        hb_model,
        _group_components=GROUP_COMPONENTS,
        _merge_faces=MERGE_FACES,
        _merge_spaces_by_erv=MERGE_SPACES_BY_ERV,
        _merge_exhaust_vent_devices=MERGE_EXHAUST_VENT_DEVICES,
    )

    # --- Build and write the PPP file
    logger.info("> Building PPP file...")
    ppp_file = ppp_builder.build_ppp_file(phx_project)

    logger.info(f"> Writing PPP file to: {TARGET_FILE_PPP}")
    ppp_txt_to_file.write_ppp_file(TARGET_FILE_PPP, ppp_file)
    logger.info("> Done.")
