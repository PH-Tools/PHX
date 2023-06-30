# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Valid 'types' for Building Elements."""

from enum import Enum


class ElectricEquipmentType(Enum):
    DISHWASHER = 1
    CLOTHES_WASHER = 2
    CLOTHES_DRYER = 3
    REFRIGERATOR = 4
    FREEZER = 5
    FRIDGE_FREEZER = 6
    COOKING = 7
    CUSTOM = 11
    MEL = 13
    LIGHTING_INTERIOR = 14
    LIGHTING_EXTERIOR = 15
    LIGHTING_GARAGE = 16
    CUSTOM_LIGHTING = 17
    CUSTOM_MEL = 18
