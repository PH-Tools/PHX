# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP "IHG non-res" worksheet."""

from __future__ import annotations
from typing import List, Optional

from PHX.xl import xl_data
from PHX.xl.xl_data import col_offset
from PHX.PHPP.phpp_model import uvalues_constructor
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_app


class IhgNonRes:
    """IO Controller for the PHPP "IHG non-res" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.IhgNonRes):
        self.xl = _xl
        self.shape = _shape
