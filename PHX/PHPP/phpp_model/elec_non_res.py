# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""The data from an existing PHPP Non-Res Lighting Entry row."""

from dataclasses import dataclass
import re
from typing import List, Optional, Dict

from PHX.xl import xl_data
from PHX.PHPP.phpp_localization import shape_model


@dataclass
class ExistingLightingRow:
    shape: shape_model.ElecNonRes
    data: list

    @property
    def room_name(self) -> str:
        col_letter = str(self.shape.lighting_rows.inputs.room_zone_name)
        col_number_as_index = xl_data.xl_ord(col_letter) - 65
        return self.data[col_number_as_index]

    @property
    def utilization_profile_phpp_id(self) -> str:
        col_letter = str(self.shape.lighting_rows.inputs.utilization_profile)
        col_number_as_index = xl_data.xl_ord(col_letter) - 65
        return self.data[col_number_as_index]

    @property
    def utilization_profile_number(self) -> str:
        phpp_id = self.utilization_profile_phpp_id
        pattern = r"(\d+)-(.*)"

        match = re.search(pattern, phpp_id)
        if match:
            return match.group(1)
        else:
            msg = f"Error: Unexpected utilization profile name format? '{phpp_id}'"
            raise Exception(msg)

    @property
    def utilization_profile_name(self) -> str:
        phpp_id = self.utilization_profile_phpp_id
        pattern = r"(\d+)-(.*)"

        match = re.search(pattern, phpp_id)
        if match:
            return str(match.group(2))
        else:
            msg = f"Error: Unexpected utilization profile name format? '{phpp_id}'"
            raise Exception(msg)

    @property
    def installed_power(self) -> str:
        col_letter = str(self.shape.lighting_rows.inputs.installed_power)
        col_number_as_index = xl_data.xl_ord(col_letter) - 65
        return self.data[col_number_as_index]
