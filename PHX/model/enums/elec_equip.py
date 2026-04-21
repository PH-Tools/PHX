# -*- Python Version: 3.10 -*-

"""Valid 'types' for Building Elements."""

from enum import Enum


class ElectricEquipmentType(Enum):
    """Classification of electrical equipment and appliance types.

    Values:
        DISHWASHER: Automatic dishwasher.
        CLOTHES_WASHER: Clothes washing machine.
        CLOTHES_DRYER: Clothes dryer.
        REFRIGERATOR: Refrigerator (no freezer compartment).
        FREEZER: Standalone freezer.
        FRIDGE_FREEZER: Combined refrigerator-freezer unit.
        COOKING: Cooking appliance (range, oven, cooktop).
        CUSTOM: User-defined appliance type.
        MEL: Miscellaneous electric load.
        LIGHTING_INTERIOR: Interior lighting.
        LIGHTING_EXTERIOR: Exterior lighting.
        LIGHTING_GARAGE: Garage lighting.
        CUSTOM_LIGHTING: User-defined lighting type.
        CUSTOM_MEL: User-defined miscellaneous electric load.
    """

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
