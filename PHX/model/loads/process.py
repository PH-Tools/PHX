# -*- Python Version: 3.10 -*-

"""PHX Process Load: an annual-energy line item (non-residential 'Process loads')."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhxProcessLoad:
    """One non-residential process-load line item, carried as annual electric energy.

    Written to WUFI-Passive 'ProcessLoadsPH' and METr 'lProces'. PHX builds these for
    Phius non-residential buildings from the Honeybee-Energy ElectricEquipment and
    Process loads, so each line is the total for its row (quantity stays 1).

    Attributes:
        display_name (str): Line-item name shown in WUFI / METr.
        annual_energy_kwh (float): Total annual electric energy for the row [kWh/yr].
        quantity (int): Number of units. Default: 1.
        include_in_source_energy (bool): Count the row in site and source energy totals. Default: True.
        increase_source_energy_allowance (bool): Raise the source-energy allowance by this row. Default: False.
        inside_thermal_envelope (bool): The row's heat is an internal gain. Default: True.
        power_rating_w (float): Optional power rating [W]. Default: 0.0.
        annual_use_hours (float): Optional annual use hours [h]. Default: 0.0.
        comment (str): Free-text note, e.g. the Honeybee source of the row. Default: "".
    """

    display_name: str = "__unnamed_process_load__"
    annual_energy_kwh: float = 0.0
    quantity: int = 1
    include_in_source_energy: bool = True
    increase_source_energy_allowance: bool = False
    inside_thermal_envelope: bool = True
    power_rating_w: float = 0.0
    annual_use_hours: float = 0.0
    comment: str = ""
