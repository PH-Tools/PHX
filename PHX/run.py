# coding=utf-8
# -*- Python Version: 2.7 -*-

"""Module for reading in HBJSON and converting to PHX-Model.

Running the 'convert_hbjson_to_PHX' function will call a new subprocess using the 
Ladybug Tools Python 3.7 interpreter.
"""

from __future__ import division

import os
import subprocess

try:
    from typing import Any, Dict, List, Tuple, Union
except ImportError:
    pass  # Python 2.7

try:  # import the core honeybee dependencies
    from honeybee.config import folders as hb_folders
except ImportError as e:
    raise ImportError("\nFailed to import honeybee:\n\t{}".format(e))


def _run_subprocess(commands):
    # type: (List[str]) -> Tuple[Any, Any]
    """Run a python subprocess.Popen, using the supplied commands

    Arguments:
    ----------
        * commands: (List[str]): A list of the commands to pass to Popen

    Returns:
    --------
        * Tuple:
            - [0]: stdout
            - [1]: stderr
    """
    # -- Create a new PYTHONHOME to avoid the Rhino-8 issues
    CUSTOM_ENV = os.environ.copy()
    CUSTOM_ENV["PYTHONHOME"] = ""

    use_shell = True if os.name == "nt" else False

    process = subprocess.Popen(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=use_shell,
        env=CUSTOM_ENV,
    )

    stdout, stderr = process.communicate()

    if stderr:
        if "Defaulting to Windows directory." in str(stderr):
            print("WARNING: {}".format(stderr))
        else:
            print(stderr)
            raise Exception(stderr)

    for _ in str(stdout).split("\\n"):
        print(_)

    return stdout, stderr


def _run_subprocess_from_shell(commands):
    # type: (List[str]) -> Tuple[Any, Any]
    """Run a python subprocess.Popen THROUGH a MacOS terminal via a shell, using the supplied commands.

    When talking to Excel on MacOS it is necessary to run through a Terminal since Rhino
    cannot get the right 'permissions' to interact with Excel. This is a workaround and not
    required on Windows OS.

    Arguments:
    ----------
        * _commands: (List[str]): A list of the commands to pass to Popen

    Returns:
    --------
        * Tuple:
            - [0]: stdout
            - [1]: stderr
    """

    # -- Create a new PYTHONHOME to avoid the Rhino-8 issues
    CUSTOM_ENV = os.environ.copy()
    CUSTOM_ENV["PYTHONHOME"] = ""

    use_shell = True if os.name == "nt" else False

    # -- Make sure the files are executable
    shell_file = commands[0]
    try:
        subprocess.check_call(["chmod", "u+x", shell_file])
    except Exception as e:
        print("Failed to make the shell file executable: {}".format(e))
        raise e

    python_script_path = commands[3]
    try:
        subprocess.check_call(["chmod", "u+x", python_script_path])
    except Exception as e:
        print("Failed to make the python script executable: {}".format(e))
        raise e

    process = subprocess.Popen(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=use_shell,
        env=CUSTOM_ENV,
    )

    stdout, stderr = process.communicate()

    if stderr:
        if "Defaulting to Windows directory." in str(stderr):
            print("Warning: {}".format(stderr))
        else:
            raise Exception(stderr)

    for _ in str(stdout).split("\\n"):
        print(_)

    return stdout, stderr


def convert_hbjson_to_WUFI_XML(
    _hbjson_file,
    _save_file_name,
    _save_folder,
    _group_components=True,
    _merge_faces=False,
    _merge_spaces_by_erv=False,
    _log_level=0,
    *args,
    **kwargs
):
    # type: (str, str, str, bool, Union[bool, float], bool, int, List, Dict) -> tuple[str, str, str, str]
    """Read in an hbjson file and output a new WUFI XML file in the designated location.

    Arguments:
    ---------
        * _hbjson (str): File path to an HBJSON file to be read in and converted to a PHX-Model.
        * _save_file_name (str): The XML filename.
        * _save_folder (str): The folder to save the new XML file in.
        * _group_components (bool): Group components by construction? Default=True
        * _merge_faces (bool | float): Merge together faces of the same type and touching? If
            a number is provided, it will be used as the tolerance when merging faces. Default=False
        * _merge_spaces_by_erv (bool): Merge spaces that are connected by ERVs? Default=False
        * _log_level (int): Set the logging level for the subprocess. Default=0
        * args (List): Additional arguments to pass to the subprocess.
        * kwargs (Dict): Additional keyword arguments to pass to the subprocess.

    Returns:
    --------
        * tuple
            - [0] (str): The path to the output XML file.
            - [1] (str): The output xml filename.
            - [2] (str): The stdout from the subprocess.
            - [3] (str): The stderr from the subprocess.
    """

    # -- Specify the path to the subprocess python script to run
    run_file_path = os.path.join(hb_folders.python_package_path, "PHX", "hbjson_to_wufi_xml.py")

    # -- check the file paths
    assert os.path.isfile(_hbjson_file), "No HBJSON file found at {}.".format(_hbjson_file)
    assert os.path.isfile(run_file_path), "No Python file to run found at: {}".format(run_file_path)

    # -------------------------------------------------------------------------
    # -- Read in the HBJSON, convert to WUFI XML
    print("Using python interpreter: '{}'".format(hb_folders.python_exe_path))
    print("Running py script: '{}' Using HBJSON file: '{}'".format(run_file_path, _hbjson_file))
    commands = [
        hb_folders.python_exe_path,
        run_file_path,
        _hbjson_file,
        _save_file_name,
        _save_folder,
        str(_group_components),
        str(_merge_faces),
        str(_merge_spaces_by_erv),
        str(_log_level),
    ]
    stdout, stderr = _run_subprocess(commands)

    # -------------------------------------------------------------------------
    # -- return the dir and filename of the xml created
    return _save_folder, _save_file_name, stdout, stderr


def write_hbjson_to_phpp(_hbjson_file, _lbt_python_site_packages_path, _activate_variants="False"):
    # type: (str, str, str) -> Tuple[Any, Any]
    """Read in an hbjson file and write out to a PHPP file.

    Arguments:
    ---------
        * _hbjson (str): File path to an HBJSON file to be read in and converted to a PHX-Model.

        * _lbt_python_site_packages_path (str): The full path to the LBT Python-3 Site-packages
            folder where PHX and Honeybee-PH are installed

        * _activate_variants (str): Default="False". Set True if you would like to
            connect all of the various PHPP inputs to the 'Variants' worksheet. This
            is used when testing various combinations of attributes during the
            early design phase. Note that if activated, any inputs will get overwritten
            when the connection to the 'Variants' worksheet is made.
            Note: Args must be strings, not actual boolean True/False.
    Returns:
    --------
        * Tuple:
            - [0]: stdout
            - [1]: stderr
    """

    # -- Specify the path to the subprocess python script to run
    run_file_path = os.path.join(hb_folders.python_package_path, "PHX", "hbjson_to_phpp.py")

    # -- check the file paths
    if not os.path.isfile(_hbjson_file):
        raise Exception("\nNo HBJSON file found at {}?".format(_hbjson_file))
    if not os.path.isfile(run_file_path):
        raise Exception("\nNo Python file to run found at: {}?".format(run_file_path))
    if not os.path.exists(_lbt_python_site_packages_path):
        raise Exception("\nNo Python site_packages folder found at: {}?".format(_lbt_python_site_packages_path))

    # -------------------------------------------------------------------------
    # -- Read in the HBJSON, write out to PHPP
    if os.name == "nt":
        commands = [
            hb_folders.python_exe_path,
            run_file_path,
            _hbjson_file,
            _lbt_python_site_packages_path,
            _activate_variants,
        ]
        stdout, stderr = _run_subprocess(commands)
    else:
        # -- If on MacOS, run the subprocess through a shell
        # -- and another terminal window in order to connect to Excel.
        # -- This is a workaround for the permissions issue on MacOS.
        # -- See:
        # -- https://discourse.mcneel.com/t/python-subprocess-permissions-error-on-mac-os-1743/142830/6
        # -- Find the file paths to run
        shell_file = os.path.join(_lbt_python_site_packages_path, "PHX", "_hbjson_to_phpp.sh")
        execution_root = os.path.join(_lbt_python_site_packages_path, "PHX")
        python_path = hb_folders.python_exe_path
        python_script_path = os.path.join(_lbt_python_site_packages_path, "PHX", "hbjson_to_phpp.py")
        hbjson_file = _hbjson_file
        # -- Build up the commands to run
        commands = [
            shell_file,
            execution_root,
            python_path,
            python_script_path,
            hbjson_file,
            _activate_variants,
        ]
        stdout, stderr = _run_subprocess_from_shell(commands)

    return stdout, stderr
