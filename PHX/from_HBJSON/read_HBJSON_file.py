# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for importing / converting Honeybee Models into PHX Models"""

# -- Dev Note: Required to import all the base packages to run the __init__ startup routines
# -- which ensures that .ph properties slot is added to all HB Objects. This must be done before
# -- running read_hb_json to ensure there is a place for all the .ph properties to go.

# -----------------------------------------------------------------------------
# -- Dev Note: Do not remove v ------------------------------------------------

import json
import logging
import os
import pathlib
from typing import Dict

import honeybee
import honeybee_energy
import honeybee_energy_ph
import honeybee_ph
from honeybee import model

# -- Dev Note: Do not remove ^ ------------------------------------------------
# -----------------------------------------------------------------------------


logger = logging.getLogger()


class HBJSONModelReadError(Exception):
    def __init__(self, _in) -> None:
        self.message = (
            f"HBJSONModelReadError: Can only convert a Honeybee 'Model' to WUFI XML.\n"
            f"Got a Honeybee object of type: {_in}."
        )

        super(HBJSONModelReadError, self).__init__(self.message)


def read_hb_json_from_file(_file_address: pathlib.Path) -> Dict:
    """Read in the HBJSON file and return it as a python dictionary.

    Arguments:
    ----------
        _file_address (pathlib.Path): A valid file path for the HBJSON file to read.

    Returns:
    --------
        Dict: The HBJSON dictionary, read in from the HBJSON file.
    """

    if not os.path.isfile(_file_address):
        msg = f"FileNotFoundError: {_file_address} is not a valid file path?"
        e = FileNotFoundError(msg)
        logger.critical(e)
        raise e

    with open(_file_address) as json_file:
        data = json.load(json_file)

    if data.get("type", None) != "Model":
        e = HBJSONModelReadError(data.get("type", None))
        logger.critical(e.message)
        raise e
    else:
        return data


def convert_hbjson_dict_to_hb_model(_data: Dict) -> model.Model:
    """Convert an HBJSON python dictionary into an HB-Model

    Arguments:
    ----------
        _data (Dict): An HBJSON dictionary with all the model information.

    Returns:
    --------
        model.Model: A Honeybee Model, rebuilt from the HBJSON file.
    """
    hb_model: model.Model = model.Model.from_dict(_data)
    logger.info(f"Converting HB-Model from {hb_model.units} to Meters.")
    hb_model.convert_to_units("Meters")
    return hb_model
