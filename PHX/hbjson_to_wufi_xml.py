# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Run script to convert an HBJSON file over to WUFI XML format."""

import glob
import logging
import os
import pathlib
import sys
from datetime import datetime
from typing import List, Tuple, Union

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_WUFI_XML import _bug_fixes, xml_builder, xml_txt_to_file


class InputFileError(Exception):
    def __init__(self, path) -> None:
        self.msg = f"\nError: Cannot find HBJSON file: {path}"
        super().__init__(self.msg)


def resolve_paths(_args: List[str]) -> Tuple[pathlib.Path, pathlib.Path]:
    """Sort out the file input and output paths. Make the output directory if needed.

    Arguments:
    ----------
        * _args (Tuple): sys.args Tuple of inputs.

    Returns:
    --------
        * Tuple
            - [1] (str): The HBJSON Source file path.
            - [2] (str): The WUFI XML Target file name.
            - [3] (str): The WUFI XML Target directory path.
    """

    print("> Resolving file paths...")
    src = pathlib.Path(_args[1])
    if not src.exists():
        raise InputFileError(src)

    target_file = f"{_args[2]}.xml"
    target_dir = pathlib.Path(_args[3])

    if not target_dir.exists():
        os.mkdir(target_dir)

    target = pathlib.Path(target_dir, target_file)

    return src, target


def group_components(_args: List[str]) -> bool:
    """Return the 'group_components' boolean from the sys.args Tuple.

    Arguments:
    ----------
        * _args (Tuple): sys.args Tuple of inputs.
            - [4] (str): "True" or "False" string.

    Returns:
    --------
        * bool: True if the user wants to group components.
    """
    return _args[4].lower() == "true"


def merge_faces(_args: List[str]) -> Union[bool, float]:
    """Return the 'merge_faces' as bool | float from the sys.args Tuple.

    Arguments:
    ----------
        * _args (Tuple): sys.args Tuple of inputs.
            - [5] (str): "True", "False", or float value as a string.

    Returns:
    --------
        * bool | float: True, False, or a float value for the tolerance.
    """
    if _args[5].lower() == "true":
        return True
    elif _args[5].lower() == "false":
        return False
    else:
        return float(_args[5])


def merge_spaces_by_erv(_args: List[str]) -> bool:
    """Return the 'merge_spaces_by_erv' boolean from the sys.args Tuple.

    Arguments:
    ----------
        * _args (Tuple): sys.args Tuple of inputs.
            - [6] (str): "True" or "False" string.

    Returns:
    --------
        * bool: True if the user wants to group components.
    """
    return _args[6].lower() == "true"


def log_level(_args: List[str]) -> int:
    """Return the log_level from the sys.args Tuple.

    Arguments:
    ----------
        * _args (Tuple): sys.args Tuple of inputs.
            - [6] (str): "0", "10", "22", "30" .....

    Returns:
    --------
        * int: The logging level.
    """
    try:
        return int(_args[7])
    except Exception:
        return 0


def remove_old_logs(directory: pathlib.Path, max_files: int = 10):
    """Remove old log files from the directory.

    Arguments:
    ----------
        * directory (pathlib.Path): The directory to remove the old logs from.
        * max_files (int): The maximum number of log files to keep.

    Returns:
    --------
        * None
    """

    all_log_files = glob.glob(os.path.join(directory, "*.log"))
    if len(all_log_files) > max_files:
        sorted_files = sorted(all_log_files, key=os.path.getmtime)
        oldest_log_file = sorted_files[0]
        os.remove(oldest_log_file)


def setup_logging_dir(_source_file_path: pathlib.Path) -> pathlib.Path:
    """Return logging directory. Create it if needed.

    Arguments:
    ----------
        * _source_file_path (pathlib.Path): The base directory to create the logging directory in.

    Returns:
    --------
        * pathlib.Path: The logging directory.
    """
    log_dir = _source_file_path.parent / "PHX_Logs"

    if not log_dir.exists():
        os.mkdir(log_dir)

    return log_dir


def startup_logging(_log_level: int) -> logging.Logger:
    """Setup the logging. Create a new dir if needed..

    Arguments:
    ----------
        * _log_level (int): The logging level.

    Returns:
    --------
        * logging.Logger: The root logger.
    """

    logger = logging.getLogger()  # Root Logger
    logger.setLevel(_log_level)

    # -- Set Format
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")

    # -- Setup the STDERR log stream-handler for stderr
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # -- Setup the STDOUT log stream-handler for stdout
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if _log_level > 0:
        # -- Find the right path, create if needed. Clean up old logs.
        log_path = setup_logging_dir(SOURCE_FILE)
        remove_old_logs(log_path, 10)

        # -- Setup the log file-handle
        file_handler = logging.FileHandler(log_path / f"PHX_{current_time}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"> LOGGING TO: {log_path / 'PHX.log'}")

    return logger


if __name__ == "__main__":
    print("- " * 50)

    # --- Input / Output file Path
    # -------------------------------------------------------------------------
    SOURCE_FILE, TARGET_FILE_XML = resolve_paths(sys.argv)
    GROUP_COMPONENTS = group_components(sys.argv)
    MERGE_FACES = merge_faces(sys.argv)
    MERGE_SPACES_BY_ERV = merge_spaces_by_erv(sys.argv)
    LOG_LEVEL = log_level(sys.argv)

    ## -- Setup the logging
    logger = startup_logging(LOG_LEVEL)
    logger.info(f"Logging with log-level: {LOG_LEVEL}")
    logger.info(f"Group Components: {GROUP_COMPONENTS}")
    logger.info(f"Merging Faces: {MERGE_FACES}")
    logger.info(f"Merging Spaces by ERV: {MERGE_SPACES_BY_ERV}")

    # --- Read in the existing HB_JSON and re-build the HB Objects
    # -------------------------------------------------------------------------
    logger.info(f"> Reading in the HBJSON file: ./{SOURCE_FILE}")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(SOURCE_FILE)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # --- Generate the WUFI Project file.
    logger.info(f'> Generating the PHX-Project from the Honeybee-Model: "{hb_model}"')
    phx_Project = create_project.convert_hb_model_to_PhxProject(
        hb_model,
        _group_components=GROUP_COMPONENTS,
        _merge_faces=MERGE_FACES,
        _merge_spaces_by_erv=MERGE_SPACES_BY_ERV,
    )

    # --- Apply the WUFI-Passive Cooling Bug fix (200 KW limit)
    phx_Project = _bug_fixes.split_cooling_into_multiple_systems(phx_Project)

    # --- Output the WUFI Project as an XML Text File
    # -------------------------------------------------------------------------
    logger.info(f'> Generating XML Text for the PHX-Project: "{phx_Project}"')
    xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_Project)

    logger.info(f"> Saving the XML file to: ./{TARGET_FILE_XML}")
    xml_txt_to_file.write_XML_text_file(TARGET_FILE_XML, xml_txt)
