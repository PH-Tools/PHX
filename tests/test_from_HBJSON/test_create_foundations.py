# -*- Python Version: 3.10 -*-

"""Tests for PHX.from_HBJSON.create_foundations: the PHPP 10 Ground fields survive HBJSON -> PHX."""

import pytest
from honeybee_ph import foundations

from PHX.from_HBJSON.create_foundations import create_phx_foundation_from_hbph
from PHX.model import ground

INTERIOR_WALL = {"interior_wall_to_heated_area_m2": 12.5, "interior_wall_to_heated_u_value": 0.35}
CRAWLSPACE_WIND = {"wind_velocity_at_10m_m_s": 5.5, "wind_shield_factor": 0.02}


@pytest.mark.parametrize(
    "hbph_class, phx_class, fields",
    [
        (foundations.PhSlabOnGrade, ground.PhxSlabOnGrade, INTERIOR_WALL),
        (foundations.PhUnheatedBasement, ground.PhxUnHeatedBasement, INTERIOR_WALL),
        (foundations.PhVentedCrawlspace, ground.PhxVentedCrawlspace, {**INTERIOR_WALL, **CRAWLSPACE_WIND}),
    ],
)
def test_phpp10_ground_fields_survive_hbjson_to_phx(hbph_class, phx_class, fields):
    hbph_foundation = hbph_class()
    for name, value in fields.items():
        setattr(hbph_foundation, name, value)
    # -- Round-trip through the HBJSON dict, as a file read would.
    hbph_foundation = hbph_class.from_dict(hbph_foundation.to_dict())

    phx_foundation = create_phx_foundation_from_hbph(hbph_foundation)

    assert isinstance(phx_foundation, phx_class)
    for name, value in fields.items():
        assert getattr(phx_foundation, name) == value


def test_heated_basement_gains_no_interior_wall_fields():
    phx_foundation = create_phx_foundation_from_hbph(foundations.PhHeatedBasement())

    assert isinstance(phx_foundation, ground.PhxHeatedBasement)
    assert not hasattr(phx_foundation, "interior_wall_to_heated_area_m2")
    assert not hasattr(phx_foundation, "interior_wall_to_heated_u_value")
