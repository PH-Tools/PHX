# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "Use non-res" worksheet."""

from __future__ import annotations

from typing import List, Optional

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import uvalues_constructor
from PHX.xl import xl_app, xl_data
from PHX.xl.xl_data import col_offset


class UseNonRes:
    """IO Controller for the PHPP "Use non-res" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.UseNonRes):
        self.xl = _xl
        self.shape = _shape
