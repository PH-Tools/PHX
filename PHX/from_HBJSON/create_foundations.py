# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to build PHX-Foundations from HBPH source objects."""

from typing import Dict

from honeybee_ph.foundations import PhFoundation

from PHX.model import ground
from PHX.model.enums.foundations import FoundationType


def create_phx_foundation_from_hbph(
    _hbph_foundation: PhFoundation,
) -> ground.PhxFoundation:
    """Return a new PhxFoundation object with attributes based on a source HBPH-Foundation.

    Arguments:
    ----------
        *

    Returns:
    --------
        * (PhxFoundation)
    """

    phx_foundation_type_map: Dict[str, ground.PhxFoundationTypes] = {
        "PhHeatedBasement": ground.PhxHeatedBasement,
        "PhUnheatedBasement": ground.PhxUnHeatedBasement,
        "PhSlabOnGrade": ground.PhxSlabOnGrade,
        "PhVentedCrawlspace": ground.PhxVentedCrawlspace,
        "PhFoundation": ground.PhxFoundation,
    }
    new_phx_foundation = phx_foundation_type_map[_hbph_foundation.__class__.__name__]()
    new_phx_foundation.display_name = _hbph_foundation.display_name
    new_phx_foundation.foundation_type_num = FoundationType(_hbph_foundation.foundation_type.number)

    # -- Pull out all the PH attributes and set the PHX ones to match.
    for attr_name in vars(_hbph_foundation).keys():
        if str(attr_name).startswith("_"):
            attr_name = attr_name[1:]

        try:
            # try and set any Enums by number first...
            setattr(new_phx_foundation, attr_name, getattr(_hbph_foundation, attr_name).number)
        except AttributeError:
            # ... then just set copy over any non-Enum values
            try:
                setattr(new_phx_foundation, attr_name, getattr(_hbph_foundation, attr_name))
            except KeyError:
                raise
            except Exception as e:
                msg = f"\n\tError setting attribute '{attr_name}' on '{new_phx_foundation.__class__.__name__}'?"
                raise Exception(msg)

    return new_phx_foundation
