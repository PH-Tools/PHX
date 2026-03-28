# -*- Python Version: 3.10 -*-

"""Run script to convert an HBJSON file over to METr JSON format."""

import glob
import logging
import os
import pathlib
import sys
from datetime import datetime

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_METr_JSON import metr_builder, metr_json_to_file


class InputFileError(Exception):
    def __init__(self, path) -> None:
        self.msg = f"\nError: Cannot find HBJSON file: {path}"
        super().__init__(self.msg)


def resolve_paths(_args: list[str]) -> tuple[pathlib.Path, pathlib.Path]:
    """Sort out the file input and output paths. Make the output directory if needed.

    Arguments:
    ----------
        * _args: sys.argv list of inputs.
            - [1] (str): The HBJSON source file path.
            - [2] (str): The METr JSON target file name (without extension).
            - [3] (str): The METr JSON target directory path.

    Returns:
    --------
        * Tuple[pathlib.Path, pathlib.Path]: (source, target) file paths.
    """
    src = pathlib.Path(_args[1])
    if not src.exists():
        raise InputFileError(src)

    target_file = f"{_args[2]}.json"
    target_dir = pathlib.Path(_args[3])

    if not target_dir.exists():
        os.mkdir(target_dir)

    target = pathlib.Path(target_dir, target_file)
    return src, target


def group_components(_args: list[str]) -> bool:
    """Return the 'group_components' boolean from sys.argv[4]."""
    try:
        return _args[4].lower() == "true"
    except IndexError:
        return True


def merge_faces(_args: list[str]) -> bool | float:
    """Return the 'merge_faces' as bool | float from sys.argv[5]."""
    try:
        val = _args[5].lower()
    except IndexError:
        return False

    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        return float(val)


def merge_spaces_by_erv(_args: list[str]) -> bool:
    """Return the 'merge_spaces_by_erv' boolean from sys.argv[6]."""
    try:
        return _args[6].lower() == "true"
    except IndexError:
        return False


def merge_exhaust_vent_devices(_args: list[str]) -> bool:
    """Return the 'merge_exhaust_vent_devices' boolean from sys.argv[7]."""
    try:
        return _args[7].lower() == "true"
    except IndexError:
        return False


def log_level(_args: list[str]) -> int:
    """Return the log_level from sys.argv[8]."""
    try:
        return int(_args[8])
    except Exception:
        return 0


def remove_old_logs(directory: pathlib.Path, max_files: int = 10):
    """Remove old log files from the directory."""
    all_log_files = glob.glob(os.path.join(directory, "*.log"))
    if len(all_log_files) > max_files:
        sorted_files = sorted(all_log_files, key=os.path.getmtime)
        oldest_log_file = sorted_files[0]
        os.remove(oldest_log_file)


def setup_logging_dir(_source_file_path: pathlib.Path) -> pathlib.Path:
    """Return logging directory. Create it if needed."""
    log_dir = _source_file_path.parent / "PHX_Logs"
    if not log_dir.exists():
        os.mkdir(log_dir)
    return log_dir


def startup_logging(_log_level: int) -> logging.Logger:
    """Setup the logging. Route INFO/DEBUG to stdout, ERROR/CRITICAL to stderr.

    This is critical for Grasshopper subprocess compatibility — run.py treats
    any stderr content as a fatal error.
    """
    logger = logging.getLogger()
    logger.setLevel(_log_level)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")

    # -- STDERR handler: ERROR and CRITICAL only
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # -- STDOUT handler: INFO, DEBUG, WARNING (exclude ERROR/CRITICAL)
    class StdoutFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.ERROR

    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(StdoutFilter())
    logger.addHandler(stdout_handler)
    log_path = None

    if _log_level > 0:
        log_path = setup_logging_dir(SOURCE_FILE)
        remove_old_logs(log_path, 10)

        file_handler = logging.FileHandler(log_path / f"PHX_{current_time}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_path / f'PHX_{current_time}.log'}")

    return logger


if __name__ == "__main__":
    # --- Input / Output file paths
    SOURCE_FILE, TARGET_FILE = resolve_paths(sys.argv)
    GROUP_COMPONENTS = group_components(sys.argv)
    MERGE_FACES = merge_faces(sys.argv)
    MERGE_SPACES_BY_ERV = merge_spaces_by_erv(sys.argv)
    MERGE_EXHAUST_VENT_DEVICES = merge_exhaust_vent_devices(sys.argv)
    LOG_LEVEL = log_level(sys.argv)

    # --- Setup logging
    logger = startup_logging(LOG_LEVEL)
    logger.info(f"Logging with log-level: {LOG_LEVEL}")
    logger.info(f"Group Components: {GROUP_COMPONENTS}")
    logger.info(f"Merging Faces: {MERGE_FACES}")
    logger.info(f"Merging Spaces by ERV: {MERGE_SPACES_BY_ERV}")
    logger.info(f"Merging Exhaust Ventilation Devices: {MERGE_EXHAUST_VENT_DEVICES}")

    # --- Read in the existing HB_JSON and re-build the HB Objects
    logger.info(f"> Reading in the HBJSON file: ./{SOURCE_FILE}")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(SOURCE_FILE)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # --- Generate the PHX Project
    logger.info(f'> Generating the PHX-Project from the Honeybee-Model: "{hb_model}"')
    phx_project = create_project.convert_hb_model_to_PhxProject(
        hb_model,
        _group_components=GROUP_COMPONENTS,
        _merge_faces=MERGE_FACES,
        _merge_spaces_by_erv=MERGE_SPACES_BY_ERV,
        _merge_exhaust_vent_devices=MERGE_EXHAUST_VENT_DEVICES,
    )

    # --- Output the METr JSON
    logger.info(f'> Generating METr JSON for the PHX-Project: "{phx_project}"')
    metr_json_text = metr_builder.generate_metr_json_text(phx_project)

    logger.info(f"> Saving the METr JSON file to: ./{TARGET_FILE}")
    metr_json_to_file.write_metr_json_file(TARGET_FILE, metr_json_text)
    logger.info("> Finished conversion of HBJSON to METr JSON.")
