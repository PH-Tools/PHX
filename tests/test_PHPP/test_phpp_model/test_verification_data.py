# -*- Python Version: 3.10 -*-

"""Tests for PHX.PHPP.phpp_model.verification_data.VerificationInput."""

import json
from pathlib import Path

import pytest

from PHX.model.certification import PhxSetpoints
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import verification_data


def _verification_shape() -> shape_model.Verification:
    shape_path = Path(__file__).resolve().parents[3] / "PHX" / "PHPP" / "phpp_localization" / "EN_10_6.json"
    with open(shape_path) as shape_file:
        return shape_model.Verification(**json.load(shape_file)["VERIFICATION"])


@pytest.mark.parametrize("mechanical_cooling, expected", [(False, ""), (True, "x")])
def test_mechanical_cooling_writes_phpp_flag(mechanical_cooling, expected):
    shape = _verification_shape()
    setpoints = PhxSetpoints(mechanical_cooling=mechanical_cooling)
    item = verification_data.VerificationInput.item(
        shape=shape,
        input_type="mechanical_cooling",
        input_data="x" if setpoints.mechanical_cooling else "",
    )

    assert item.create_xl_item("Verification", 1).write_value == expected
