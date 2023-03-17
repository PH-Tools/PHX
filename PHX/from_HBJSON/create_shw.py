# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions to create PHX-Service Hot Water objects from Honeybee-Energy-PH SHW"""

from honeybee_energy_ph.hvac import hot_water

from PHX.model.enums.hvac import PhxHotWaterTankType
from PHX.model import hvac
from PHX.model.hvac import piping

# -- Storage --


def build_phx_hw_tank(_hbph_tank: hot_water.PhSHWTank) -> hvac.PhxHotWaterTank:
    """Returns a new PHX Hot-Water Tank based on the Honeybee-PH Hot Water Tank input.

    Arguments:
    ----------
        * _hbph_heater (hot_water.PhSHWTank): The Honeybee-PH Hot-Water tank
            to use as the source.

    Returns:
    --------
        * mech_equip.PhxHotWaterTank: The new PHX-Hot-Water-Tank.
    """

    phx_tank = hvac.PhxHotWaterTank()

    phx_tank.display_name = _hbph_tank.display_name
    phx_tank.quantity = _hbph_tank.quantity

    phx_tank.params.tank_type = PhxHotWaterTankType.from_hbph_type(_hbph_tank.tank_type)
    phx_tank.params.in_conditioned_space = _hbph_tank.in_conditioned_space

    phx_tank.params.solar_connection = _hbph_tank.solar_connection
    phx_tank.params.solar_losses = _hbph_tank.solar_losses

    phx_tank.params.storage_capacity = _hbph_tank.storage_capacity
    phx_tank.params.storage_loss_rate = _hbph_tank.storage_loss_rate

    phx_tank.params.standby_losses = _hbph_tank.standby_losses
    phx_tank.params.standby_fraction = _hbph_tank.standby_fraction

    phx_tank.params.room_temp = _hbph_tank.room_temp
    phx_tank.params.water_temp = _hbph_tank.water_temp

    return phx_tank


def build_phx_hw_storage(_hbph_tank: hot_water.PhSHWTank) -> hvac.PhxHotWaterTank:
    """

    Arguments:
    ----------
        * _hbph_heater (hot_water.PhSHWTank): The Honeybee-PH Hot-Water tank
            to use as the source.

    Returns:
    --------
        * (mech.PhxHotWaterTank): The new Water Storage SubSystem.
    """

    phx_storage_tank = build_phx_hw_tank(_hbph_tank)

    # TODO: Distribution...

    return phx_storage_tank


# -- Heaters ----


def build_phx_hw_heater(
    _hbph_heater: hot_water.PhHotWaterHeater,
) -> hvac.AnyPhxHotWaterHeater:
    """Returns a new PHX Hot-Water Heater based on the Honeybee-PH Hot Water Heater input.

    Arguments:
    ----------
        * _hbph_heater (hot_water.PhHotWaterHeater): The Honeybee-PH Hot-Water heater
            to use as the source for the PHX Heater.

    Returns:
    --------
        * (hvac.PhxHeatingDevice): The new PHX-Hot-Water-Heater.
    """

    # -- Get the right constructor based on the type of heater
    heaters = {
        "PhSHWHeaterElectric": hvac.PhxHeaterElectric,
        "PhSHWHeaterBoiler": hvac.PhxHeaterBoilerFossil,
        "PhSHWHeaterBoilerWood": hvac.PhxHeaterBoilerWood,
        "PhSHWHeaterDistrict": hvac.PhxHeaterDistrictHeat,
        "PhSHWHeaterHeatPump": hvac.PhxHeaterHeatPumpHotWater,
    }

    # -- Build the basic heater and set basic data
    heater_class = heaters[_hbph_heater.__class__.__name__]
    phx_hw_heater = heater_class()
    phx_hw_heater.display_name = _hbph_heater.display_name

    # -- Pull out all the detailed data which varies depending on the 'type'
    for attr_name in vars(phx_hw_heater).keys():
        try:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            setattr(phx_hw_heater, attr_name, getattr(_hbph_heater, attr_name))
        except AttributeError:
            pass

    for attr_name in vars(phx_hw_heater.params).keys():
        try:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            setattr(phx_hw_heater.params, attr_name, getattr(_hbph_heater, attr_name))
        except AttributeError:
            pass

    phx_hw_heater.usage_profile.dhw_heating = True

    return phx_hw_heater


# -- Piping ----


def build_phx_piping(_hbph_pipe: hot_water.PhPipeElement) -> hvac.PhxPipeElement:
    """Create a new PHX Water Pipe based on an input Honeybee-PH Water Pipe.

    Arguments:
    ----------
        * _hbph_pipe: (hot_water.PhPipeElement): The Honeybee-PH Pipe to use as
            the source.

    Returns:
    --------
        * (piping.PhxPipeElement): The new PhxPipeElement created.
    """

    phx_pipe = piping.PhxPipeElement(_hbph_pipe.identifier, _hbph_pipe.display_name)
    for segment in _hbph_pipe.segments:
        phx_pipe.add_segment(
            piping.PhxPipeSegment(
                segment.identifier,
                segment.display_name,
                segment.geometry,
                segment.diameter_m,
                segment.insulation_thickness_m,
                segment.insulation_conductivity,
                segment.insulation_reflective,
                segment.insulation_quality,
                segment.daily_period,
            )
        )

    return phx_pipe
