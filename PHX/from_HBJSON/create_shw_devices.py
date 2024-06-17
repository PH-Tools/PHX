# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to create PHX-Service Hot Water objects from Honeybee-PH-HVAC Hot-Water"""

from honeybee_phhvac import hot_water_devices, hot_water_piping

from PHX.model import hvac
from PHX.model.enums.hvac import PhxHotWaterPipingInchDiameterType, PhxHotWaterPipingMaterial, PhxHotWaterTankType
from PHX.model.hvac import piping

# -- Storage ------------------------------------------------------------------


def build_phx_hw_tank(_ph_hvac_tank: hot_water_devices.PhHvacHotWaterTank) -> hvac.PhxHotWaterTank:
    """Returns a new PHX Hot-Water Tank based on the Honeybee-PH-HVAC Hot Water Tank input.

    Arguments:
    ----------
        * _ph_hvac_tank: The Honeybee-PH-HVAC Hot-Water tank to use as the source.

    Returns:
    --------
        * The new PHX-Hot-Water-Tank.
    """

    phx_tank = hvac.PhxHotWaterTank()

    phx_tank.display_name = _ph_hvac_tank.display_name
    phx_tank.quantity = _ph_hvac_tank.quantity

    phx_tank.params.tank_type = PhxHotWaterTankType.from_hbph_type(_ph_hvac_tank.tank_type)
    phx_tank.params.in_conditioned_space = _ph_hvac_tank.in_conditioned_space

    phx_tank.params.solar_connection = _ph_hvac_tank.solar_connection
    phx_tank.params.solar_losses = _ph_hvac_tank.solar_losses

    phx_tank.params.storage_capacity = _ph_hvac_tank.storage_capacity
    phx_tank.params.storage_loss_rate = _ph_hvac_tank.storage_loss_rate

    phx_tank.params.standby_losses = _ph_hvac_tank.standby_losses
    phx_tank.params.standby_fraction = _ph_hvac_tank.standby_fraction

    phx_tank.params.room_temp = _ph_hvac_tank.room_temp
    phx_tank.params.water_temp = _ph_hvac_tank.water_temp

    return phx_tank


def build_phx_hw_storage(_ph_hvac_tank: hot_water_devices.PhHvacHotWaterTank) -> hvac.PhxHotWaterTank:
    """Returns a new PHX Hot-Water Storage Tank based on the Honeybee-PH-HVAC Hot Water Tank input.

    Arguments:
    ----------
        * _ph_hvac_tank: The Honeybee-PH-HVAC Hot-Water tank to use as the source.

    Returns:
    --------
        * The new Water Storage Tank.
    """

    phx_storage_tank = build_phx_hw_tank(_ph_hvac_tank)

    return phx_storage_tank


# -- Heaters ------------------------------------------------------------------


def build_phx_hw_heater(
    _ph_hvac_heater: hot_water_devices.PhHvacHotWaterHeater,
) -> hvac.AnyPhxHotWaterHeater:
    """Returns a new PHX Hot-Water Heater based on the Honeybee-PH-HVAC Hot Water Heater input.

    Arguments:
    ----------
        * _ph_hvac_heater: The Honeybee-PH-HVAC Hot-Water heater to use as the source for the PHX Heater.

    Returns:
    --------
        * The new PHX-Hot-Water-Heater.
    """

    # -- Get the right constructor based on the type of Honeybee-PH-HVAC heater
    heaters = {
        "PhHvacHotWaterHeaterElectric": hvac.PhxHeaterElectric,
        "PhHvacHotWaterHeaterBoiler": hvac.PhxHeaterBoilerFossil,
        "PhHvacHotWaterHeaterBoilerWood": hvac.PhxHeaterBoilerWood,
        "PhHvacHotWaterHeaterDistrict": hvac.PhxHeaterDistrictHeat,
        "PhHvacHotWaterHeaterHeatPump_Annual": hvac.PhxHeatPumpAnnual,
        "PhHvacHotWaterHeaterHeatPump_Monthly": hvac.PhxHeatPumpMonthly,
        "PhHvacHotWaterHeaterHeatPump_Inside": hvac.PhxHeatPumpHotWater,
    }

    # -- Build the basic heater and set basic data
    heater_class = heaters[_ph_hvac_heater.__class__.__name__]
    phx_hw_heater = heater_class()
    phx_hw_heater.display_name = _ph_hvac_heater.display_name

    # -- Pull out all the detailed data which varies depending on the 'type'
    for attr_name in vars(phx_hw_heater).keys():
        try:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            setattr(phx_hw_heater, attr_name, getattr(_ph_hvac_heater, attr_name))
        except AttributeError:
            pass

    for attr_name in vars(phx_hw_heater.params).keys():
        try:
            if attr_name.startswith("_"):
                attr_name = attr_name[1:]
            setattr(phx_hw_heater.params, attr_name, getattr(_ph_hvac_heater, attr_name))
        except AttributeError:
            pass

    phx_hw_heater.usage_profile.dhw_heating = True

    return phx_hw_heater


# -- Piping -------------------------------------------------------------------


def build_phx_pipe_element(_ph_hvac_pipe: hot_water_piping.PhHvacPipeElement) -> hvac.PhxPipeElement:
    """Create single PHX-PipeElement based on an input Honeybee-PH-HVAC PipeElement.

    Arguments:
    ----------
        * _ph_hvac_pipe: The Honeybee-PH-HVAC Pipe to use as the source.

    Returns:
    --------
        * The new PHX Pipe Element created.
    """

    phx_pipe = piping.PhxPipeElement(_ph_hvac_pipe.identifier, _ph_hvac_pipe.display_name)
    for segment in _ph_hvac_pipe.segments:
        phx_pipe.add_segment(
            piping.PhxPipeSegment(
                segment.identifier,
                segment.display_name,
                segment.geometry,
                PhxHotWaterPipingMaterial(segment.material.number),
                segment.diameter_m,
                segment.insulation_thickness_m,
                segment.insulation_conductivity,
                segment.insulation_reflective,
                segment.insulation_quality,
                segment.daily_period,
                segment.water_temp_c,
            )
        )

    return phx_pipe


def build_phx_branch_pipe(_ph_hvac_branch: hot_water_piping.PhHvacPipeBranch) -> hvac.PhxPipeBranch:
    """Create new PHX-Branch-Pipe based on an input Honeybee-PH-HVAC Branch-Pipe.

    Arguments:
    ----------
        * _ph_hvac_branch: The Honeybee-PH-HVAC Branch-Pipe to use as the source.

    Returns:
    --------
        * The new PHX-Branch created.
    """

    phx_pipe_branch = piping.PhxPipeBranch(_ph_hvac_branch.identifier, _ph_hvac_branch.display_name)
    for segment in _ph_hvac_branch.segments:
        phx_pipe_branch.pipe_element.add_segment(
            piping.PhxPipeSegment(
                segment.identifier,
                segment.display_name,
                segment.geometry,
                PhxHotWaterPipingMaterial(segment.material.number),
                segment.diameter_m,
                segment.insulation_thickness_m,
                segment.insulation_conductivity,
                segment.insulation_reflective,
                segment.insulation_quality,
                segment.daily_period,
                segment.water_temp_c,
            )
        )

    for fixture in _ph_hvac_branch.fixtures:
        phx_pipe_branch.add_fixture(build_phx_pipe_element(fixture))

    return phx_pipe_branch


def build_phx_trunk_pipe(_ph_hvac_trunk: hot_water_piping.PhHvacPipeTrunk) -> hvac.PhxPipeTrunk:
    """Create new PHX-Trunk based on an input Honeybee-PH-HVAC Trunk-Pipe.

    Arguments:
    ----------
        * _ph_hvac_trunk: The Honeybee-PH-HVAC Trunk-Pipe to use as the source.

    Returns:
    --------
        * The new PHX-Trunk created.
    """

    phx_pipe_trunk = piping.PhxPipeTrunk(_ph_hvac_trunk.identifier, _ph_hvac_trunk.display_name)
    phx_pipe_trunk.multiplier = _ph_hvac_trunk.multiplier
    phx_pipe_trunk.pipe_element.display_name = f"{_ph_hvac_trunk.display_name}-PIPE"
    for segment in _ph_hvac_trunk.segments:
        phx_pipe_trunk.pipe_element.add_segment(
            piping.PhxPipeSegment(
                segment.identifier,
                segment.display_name,
                segment.geometry,
                PhxHotWaterPipingMaterial(segment.material.number),
                segment.diameter_m,
                segment.insulation_thickness_m,
                segment.insulation_conductivity,
                segment.insulation_reflective,
                segment.insulation_quality,
                segment.daily_period,
                segment.water_temp_c,
            )
        )

    for branch in _ph_hvac_trunk.branches:
        phx_pipe_trunk.add_branch(build_phx_branch_pipe(branch))

    return phx_pipe_trunk
