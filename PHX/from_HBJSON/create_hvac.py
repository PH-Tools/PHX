# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions to create PHX-HVAC objects from Honeybee-Energy-PH HVAC"""

from typing import Callable, Dict, TypeVar, Union

from honeybee_phhvac import _base, ducting, heat_pumps, heating, supportive_device, ventilation
from honeybee_phhvac.renewable_devices import PhPhotovoltaicDevice, PhRenewableEnergyDevice

from PHX.model import hvac
from PHX.model.enums.hvac import PhxSupportiveDeviceType, PhxVentDuctType
from PHX.model.hvac.heat_pumps import AnyPhxHeatPump
from PHX.model.hvac.heating import AnyPhxHeater
from PHX.model.hvac.renewable_devices import AnyRenewableDevice, PhxDevicePhotovoltaic
from PHX.model.hvac.ventilation import AnyPhxVentilation

T = TypeVar("T", bound=Union[AnyPhxVentilation, AnyPhxHeater, AnyPhxHeatPump])


def _transfer_attributes(_hbeph_obj: _base._PhHVACBase, _phx_obj: T) -> T:
    """Copy the common attributes from a Honeybee-Energy-PH obj to a PHX-object

    Arguments:
    ---------
        * _hbeph_obj (_base._PhHVACBase): A Honeybee-Energy-PH HVAC Object.
        * _phx_obj (mech_equip.PhxMechanicalEquipment): A PHX-Mechanical
            Equipment object.

    Returns:
    --------
        * (mech_equip.PhxMechanicalEquipment): The input PHX Mechanical Equipment
            object, with its attribute values set to match the Honeybee-PH object.
    """

    # -- Copy the base scope attributes from HB->PHX
    hb_attrs = {attr_name for attr_name in dir(_hbeph_obj) if not attr_name.startswith("_")}
    phx_base_attrs = {attr_name for attr_name in dir(_phx_obj) if not attr_name.startswith("_")}

    for attr_nm in hb_attrs.intersection(phx_base_attrs):
        setattr(_phx_obj, attr_nm, getattr(_hbeph_obj, attr_nm))

    # -- Also copy attrs to PHX.params for objects which have them
    if _phx_obj.params:
        phx_params_attrs = {attr_name for attr_name in dir(_phx_obj.params) if not attr_name.startswith("_")}
        for attr_nm in hb_attrs.intersection(phx_params_attrs):
            setattr(_phx_obj.params, attr_nm, getattr(_hbeph_obj, attr_nm))

    return _phx_obj


# -----------------------------------------------------------------------------
# -- Ventilation


def _default_ventilator_name(_hr: float, _mr: float) -> str:
    """Return a Ventilation Unit name

    Arguments:
    ----------
        * _hr (float): The Heat Recovery efficiency of the unit.
        * _mr (float): The Moisture Recovery efficiency of the unit.
    Returns:
    --------
        * (str)
    """
    return f"Ventilator: {_hr*100 :0.0f}%-HR, {_mr*100 :0.0f}%-MR"


def build_phx_ventilator(
    _hbeph_vent_sys: ventilation.PhVentilationSystem,
) -> hvac.PhxDeviceVentilator:
    """Returns a new Fresh-Air Ventilator built from the hb-energy hvac parameters.

    This will look at the Space's Host-Room .properties.energy.hvac for data.

    Arguments:
    ----------
        *_hbeph_vent (ventilation.PhVentilationSystem): The Honeybee-PH Ventilation System
            to build the PHX-Ventilation from.

    Returns:
    --------
        * (mech_equip.Ventilator): The new Passive House Ventilator created.
    """

    phx_vent = hvac.PhxDeviceVentilator()
    _id_num = phx_vent.id_num  # preserver so 'transfer_attributes' doesn't kill it...

    if not _hbeph_vent_sys.ventilation_unit:
        return phx_vent
    phx_vent = _transfer_attributes(_hbeph_vent_sys, phx_vent)
    phx_vent = _transfer_attributes(_hbeph_vent_sys.ventilation_unit, phx_vent)

    # -- Sort out the Display name to use
    if not _hbeph_vent_sys.ventilation_unit:
        ventilator_name = _default_ventilator_name(0.0, 0.0)
    elif _hbeph_vent_sys.ventilation_unit.display_name == "_unnamed_ventilator_":
        ventilator_name = _default_ventilator_name(
            _hbeph_vent_sys.ventilation_unit.sensible_heat_recovery,
            _hbeph_vent_sys.ventilation_unit.latent_heat_recovery,
        )
    else:
        ventilator_name = _hbeph_vent_sys.ventilation_unit.display_name

    phx_vent.display_name = ventilator_name
    phx_vent.id_num = _id_num

    return phx_vent


def build_phx_duct(_hbph_duct: ducting.PhDuctElement, _vent_unit_id: int) -> hvac.PhxDuctElement:
    """Return a new PHX Ventilation Duct based on an HB-PH Duct.

    Arguments:
    ----------
        * _hbph_duct (ducting.PhDuctElement): The HB-PH DuctElement to use as
            the source.
        * _vent_unit_id (int): The ID-Number of the ventilation unit this duct
            is assigned to.

    Returns:
    --------
        * (hvac.PhxDuctElement)
    """

    phx_duct = hvac.PhxDuctElement(
        _hbph_duct.identifier,
        _hbph_duct.display_name,
        _vent_unit_id,
    )

    phx_duct.duct_type = PhxVentDuctType(
        _hbph_duct.duct_type,
    )

    for hbph_duct_segment in _hbph_duct.segments:
        phx_duct.add_segment(
            hvac.PhxDuctSegment(
                hbph_duct_segment.identifier,
                hbph_duct_segment.display_name,
                hbph_duct_segment.geometry,
                hbph_duct_segment.diameter,
                hbph_duct_segment.height,
                hbph_duct_segment.width,
                hbph_duct_segment.insulation_thickness,
                hbph_duct_segment.insulation_conductivity,
                hbph_duct_segment.insulation_reflective,
            )
        )

    return phx_duct


def build_phx_exh_vent_dryer(
    _hbeph_exhaust_vent: ventilation.ExhaustVentDryer,
) -> hvac.PhxExhaustVentilatorDryer:
    """Create a new PHX Exhaust Vent (Dryer) based on the attributes of an HBPH-Vent Dryer

    Arguments:
    ----------
        * _hbeph_exhaust_vent (ventilation.ExhaustVentDryer): The HBPH Exhaust Vent. Device.

    Returns:
    --------
        * (hvac.PhxExhaustVentilatorDryer): The new PHX Exhaust Vent Device (Dryer)
    """

    obj = hvac.PhxExhaustVentilatorDryer()
    obj.display_name = _hbeph_exhaust_vent.display_name
    obj.params.exhaust_flow_rate_m3h = _hbeph_exhaust_vent.exhaust_flow_rate_m3s * 60 * 60
    return obj


def build_phx_exh_vent_kitchen_vent(
    _hbeph_exhaust_vent: ventilation.ExhaustVentKitchenHood,
) -> hvac.PhxExhaustVentilatorRangeHood:
    """Create a new PHX Exhaust Vent (Kitchen Hood) based on the attributes of an HBPH-Vent Kitchen Hood

    Arguments:
    ----------
        * _hbeph_exhaust_vent (ventilation.ExhaustVentKitchenHood): The HBPH Exhaust Vent. Device.

    Returns:
    --------
        * (hvac.PhxExhaustVentilatorRangeHood): The new PHX Exhaust Vent Device (Dryer)
    """

    obj = hvac.PhxExhaustVentilatorRangeHood()
    obj.display_name = _hbeph_exhaust_vent.display_name
    obj.params.exhaust_flow_rate_m3h = _hbeph_exhaust_vent.exhaust_flow_rate_m3s * 60 * 60
    return obj


def build_phx_exh_vent_use_defined(
    _hbeph_exhaust_vent: ventilation.ExhaustVentUserDefined,
) -> hvac.PhxExhaustVentilatorUserDefined:
    """Create a new PHX Exhaust Vent (User Defined) based on the attributes of an HBPH-Vent User Defined

    Arguments:
    ----------
        * _hbeph_exhaust_vent (ventilation.ExhaustVentUserDefined): The HBPH Exhaust Vent. Device.

    Returns:
    --------
        * (hvac.PhxExhaustVentilatorUserDefined): The new PHX Exhaust Vent Device (Dryer)
    """

    obj = hvac.PhxExhaustVentilatorUserDefined()
    obj.display_name = _hbeph_exhaust_vent.display_name
    obj.params.exhaust_flow_rate_m3h = _hbeph_exhaust_vent.exhaust_flow_rate_m3s * 60 * 60
    obj.params.annual_runtime_minutes = _hbeph_exhaust_vent.annual_runtime_minutes
    return obj


def build_phx_exhaust_vent_device(
    _hbeph_exhaust_vent: ventilation._ExhaustVentilatorBase,
) -> hvac.AnyPhxExhaustVent:
    """Build a new PHX Exhaust Ventilation Mechanical Device.

    Arguments:
    ----------
        *_hbeph_exhaust_vent (ventilation._ExhaustVentilatorBase): The Honeybee-PH
            Exhaust Ventilation Device to build the PHX-Ventilation Device from.

    Returns:
    --------
        * (mech.AnyPhxExhaustVent): A new PHX Exhaust ventilation device.
    """

    # -- Mapping Honeybee-PH -> PHX types
    phx_device_classes = {
        "ExhaustVentDryer": build_phx_exh_vent_dryer,
        "ExhaustVentKitchenHood": build_phx_exh_vent_kitchen_vent,
        "ExhaustVentUserDefined": build_phx_exh_vent_use_defined,
    }

    # -- Get and build the right device type
    phx_device = phx_device_classes[_hbeph_exhaust_vent.device_class_name](_hbeph_exhaust_vent)
    return phx_device


# -----------------------------------------------------------------------------
# -- Heating


def build_phx_heating_electric(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterElectric:
    phx_obj = hvac.PhxHeaterElectric()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbeph_heater.percent_coverage
    return phx_obj


def build_phx_heating_fossil_boiler(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterBoilerFossil:
    phx_obj = hvac.PhxHeaterBoilerFossil()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbeph_heater.percent_coverage
    return phx_obj


def build_phx_heating_wood_boiler(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterBoilerWood:
    phx_obj = hvac.PhxHeaterBoilerWood()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbeph_heater.percent_coverage
    return phx_obj


def build_phx_heating_district(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterDistrictHeat:
    phx_obj = hvac.PhxHeaterDistrictHeat()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbeph_heater.percent_coverage
    return phx_obj


def build_phx_heating_device(_htg_sys: heating.PhHeatingSystem) -> hvac.PhxHeatingDevice:
    """Returns a new PHX-Heating-Device based on an input Honeybee-PH Heating System."""

    # -- Mapping Honeybee-PH -> PHX types
    phx_heater_classes: Dict[str, Callable[[heating.PhHeatingSystem], hvac.PhxHeatingDevice]] = {
        "PhHeatingDirectElectric": build_phx_heating_electric,
        "PhHeatingFossilBoiler": build_phx_heating_fossil_boiler,
        "PhHeatingWoodBoiler": build_phx_heating_wood_boiler,
        "PhHeatingDistrict": build_phx_heating_district,
    }

    # -- Get and build the right heater equipment type
    phx_heater = phx_heater_classes[_htg_sys.heating_type](_htg_sys)
    return phx_heater


def build_phx_heating_sys(_htg_sys: heating.PhHeatingSystem) -> hvac.PhxHeatingDevice:
    """Build a new PHX-Heating-Device Device from a Honeybee-PH Heating System."""

    phx_htg_device = build_phx_heating_device(_htg_sys)

    # TODO: Distribution...

    return phx_htg_device


# -----------------------------------------------------------------------------
# -- Heat Pumps


def hbph_heat_pump_has_cooling(_hbph_heat_pump: heat_pumps.PhHeatPumpSystem) -> bool:
    """Return True if the input Honeybee-PH Heat-Pump System has any type of cooling enabled."""
    return any(
        [
            _hbph_heat_pump.cooling_params.ventilation.used,
            _hbph_heat_pump.cooling_params.recirculation.used,
            _hbph_heat_pump.cooling_params.dehumidification.used,
            _hbph_heat_pump.cooling_params.panel.used,
        ]
    )


def build_phx_heat_pump_cooling_params(
    _hbph_heat_pump: heat_pumps.PhHeatPumpSystem,
) -> hvac.PhxCoolingParams:
    """Return a new PHX Cooling Params object based on an input Honeybee-PH Heat-Pump System."""

    new_params_obj = hvac.PhxCoolingParams()

    new_params_obj.ventilation = build_phx_cooling_ventilation_params(_hbph_heat_pump.cooling_params.ventilation)
    new_params_obj.recirculation = build_phx_cooling_recirculation_params(_hbph_heat_pump.cooling_params.recirculation)
    new_params_obj.dehumidification = build_phx_cooling_dehumidification_params(
        _hbph_heat_pump.cooling_params.dehumidification
    )
    new_params_obj.panel = build_phx_cooling_panel_params(_hbph_heat_pump.cooling_params.panel)

    return new_params_obj


def build_phx_heating_hp_annual(
    _hbph_heat_pump: heat_pumps.PhHeatPumpSystem,
) -> hvac.PhxHeatPumpAnnual:
    """Returns a new Annual PHX-Heat-Pump-Device based on an input Honeybee-PH Heat-Pump System."""

    phx_obj = hvac.PhxHeatPumpAnnual()
    phx_obj = _transfer_attributes(_hbph_heat_pump, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbph_heat_pump.percent_coverage

    if hbph_heat_pump_has_cooling(_hbph_heat_pump):
        phx_obj.usage_profile.cooling_percent = _hbph_heat_pump.cooling_params.percent_coverage
        phx_obj.params_cooling = build_phx_heat_pump_cooling_params(_hbph_heat_pump)

    return phx_obj


def build_phx_heating_hp_monthly(
    _hbph_heat_pump: heat_pumps.PhHeatPumpSystem,
) -> hvac.PhxHeatPumpMonthly:
    """Returns a new Monthly PHX-Heat-Pump-Device based on an input Honeybee-PH Heat-Pump System."""

    phx_obj = hvac.PhxHeatPumpMonthly()
    phx_obj = _transfer_attributes(_hbph_heat_pump, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbph_heat_pump.percent_coverage

    if hbph_heat_pump_has_cooling(_hbph_heat_pump):
        phx_obj.usage_profile.cooling_percent = _hbph_heat_pump.cooling_params.percent_coverage
        phx_obj.params_cooling = build_phx_heat_pump_cooling_params(_hbph_heat_pump)

    return phx_obj


def build_phx_heating_hp_combined(
    _hbph_heat_pump: heat_pumps.PhHeatPumpSystem,
) -> hvac.PhxHeatPumpCombined:
    """Returns a new Combined PHX-Heat-Pump-Device based on an input Honeybee-PH Heat-Pump System."""

    phx_obj = hvac.PhxHeatPumpCombined()
    phx_obj = _transfer_attributes(_hbph_heat_pump, phx_obj)
    phx_obj.usage_profile.space_heating_percent = _hbph_heat_pump.percent_coverage

    if hbph_heat_pump_has_cooling(_hbph_heat_pump):
        phx_obj.usage_profile.cooling_percent = _hbph_heat_pump.cooling_params.percent_coverage
        phx_obj.params_cooling = build_phx_heat_pump_cooling_params(_hbph_heat_pump)

    return phx_obj


def build_phx_heat_pump_device(
    _hbph_heat_pump: heat_pumps.PhHeatPumpSystem,
) -> hvac.PhxHeatPumpDevice:
    """Returns a new PHX-He"at-Pump-Device based on an input Honeybee-PH Heat-Pump System."""

    # -- Mapping Honeybee-PH -> PHX types
    phx_heat_pump_classes: Dict[str, Callable[[heat_pumps.PhHeatPumpSystem], hvac.PhxHeatPumpDevice]] = {
        "PhHeatPumpAnnual": build_phx_heating_hp_annual,
        "PhHeatPumpRatedMonthly": build_phx_heating_hp_monthly,
        "PhHeatPumpCombined": build_phx_heating_hp_combined,
    }

    # -- Get and build the right heater equipment type
    phx_heat_pump = phx_heat_pump_classes[_hbph_heat_pump.heat_pump_class_name](_hbph_heat_pump)
    return phx_heat_pump


def build_phx_heat_pump_sys(
    _hbph_heat_pump: heat_pumps.PhHeatPumpSystem,
) -> hvac.PhxHeatPumpDevice:
    """Build a new PHX-Heat-Pump-Device Device from a Honeybee-PH Heat-Pump System."""

    phx_htg_device = build_phx_heat_pump_device(_hbph_heat_pump)

    return phx_htg_device


# -----------------------------------------------------------------------------
# --- Cooling Parameters for Heat Pumps


def _transfer_cooling_attributes(_hbph_params, _phx_params):
    """Copy the common attributes from a Honeybee-PH Cooling-Params obj to a PHX-Cooling-Params object"""
    # -- Copy the base scope attributes from HBPH->PHX
    hb_attrs = {attr_name for attr_name in dir(_hbph_params) if not attr_name.startswith("_")}
    phx_base_attrs = {attr_name for attr_name in dir(_phx_params) if not attr_name.startswith("_")}

    for attr_nm in hb_attrs.intersection(phx_base_attrs):
        setattr(_phx_params, attr_nm, getattr(_hbph_params, attr_nm))

    return _phx_params


def build_phx_cooling_ventilation_params(
    _hbph_cooling_params: heat_pumps.PhHeatPumpCoolingParams_Ventilation,
) -> hvac.PhxCoolingVentilationParams:
    """Build a new PHX Cooling Ventilation Params object from a Honeybee-PH Cooling Ventilation Params object."""

    phx_obj = hvac.PhxCoolingVentilationParams()
    phx_obj = _transfer_cooling_attributes(_hbph_cooling_params, phx_obj)
    return phx_obj


def build_phx_cooling_recirculation_params(
    _hbph_cooling_params: heat_pumps.PhHeatPumpCoolingParams_Recirculation,
) -> hvac.PhxCoolingRecirculationParams:
    """Build a new PHX-Cooling-Recirculation-Params object from a Honeybee-PH Cooling-Params object."""

    phx_obj = hvac.PhxCoolingRecirculationParams()
    phx_obj = _transfer_cooling_attributes(_hbph_cooling_params, phx_obj)
    return phx_obj


def build_phx_cooling_dehumidification_params(
    _hbph_cooling_params: heat_pumps.PhHeatPumpCoolingParams_Dehumidification,
) -> hvac.PhxCoolingDehumidificationParams:
    """Build a new PHX-Cooling-Dehumidification-Params object from a Honeybee-PH Cooling-Params object."""

    phx_obj = hvac.PhxCoolingDehumidificationParams()
    phx_obj = _transfer_cooling_attributes(_hbph_cooling_params, phx_obj)
    return phx_obj


def build_phx_cooling_panel_params(
    _hbph_cooling_params: heat_pumps.PhHeatPumpCoolingParams_Panel,
) -> hvac.PhxCoolingPanelParams:
    """Build a new PHX-Cooling-Panel-Params object from a Honeybee-PH Cooling-Params object."""

    phx_obj = hvac.PhxCoolingPanelParams()
    phx_obj = _transfer_cooling_attributes(_hbph_cooling_params, phx_obj)
    return phx_obj


# -----------------------------------------------------------------------------
# --- Supportive Devices


def build_phx_supportive_device(
    _hbph_supportive_device: supportive_device.PhSupportiveDevice,
) -> hvac.PhxSupportiveDevice:
    """Build a new PhxSupportiveDevice Device based on a HBPH PhSupportiveDevice."""
    phx_device = hvac.PhxSupportiveDevice()

    # -- basics
    phx_device.identifier = _hbph_supportive_device.identifier
    phx_device.display_name = _hbph_supportive_device.display_name
    phx_device.device_type = PhxSupportiveDeviceType(_hbph_supportive_device.device_type)
    phx_device.quantity = _hbph_supportive_device.quantity

    # -- params
    phx_device.params.in_conditioned_space = _hbph_supportive_device.in_conditioned_space
    phx_device.params.norm_energy_demand_W = _hbph_supportive_device.norm_energy_demand_W
    phx_device.params.annual_period_operation_khrs = _hbph_supportive_device.annual_period_operation_khrs

    return phx_device


# -----------------------------------------------------------------------------
# -- Renewable Devices


def build_phx_photovoltaic_device(_hbph_d: PhPhotovoltaicDevice) -> PhxDevicePhotovoltaic:
    """Build a new PhxPhotovoltaicDevice Device from a Honeybee-PH Photovoltaic Device."""
    d = PhxDevicePhotovoltaic()
    d.display_name = _hbph_d.display_name
    d.params.photovoltaic_renewable_energy = _hbph_d.photovoltaic_renewable_energy
    d.params.onsite_utilization_factor = _hbph_d.utilization_factor
    d.params.array_size = _hbph_d.array_size
    return d


def build_phx_renewable_device(_device: PhRenewableEnergyDevice) -> AnyRenewableDevice:
    """Build a new PHX-Renewable-Device Device from a Honeybee-PH Renewable-Device."""
    # -- Mapping Honeybee-PH -> PHX types
    phx_renewable_classes = {
        "PhPhotovoltaicDevice": build_phx_photovoltaic_device,
    }

    # -- Get and build the right heater equipment type
    phx_device = phx_renewable_classes[_device.device_typename](_device)  # type: ignore
    return phx_device
