# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions to create PHX-HVAC objects from Honeybee-Energy-PH HVAC"""

from typing import TypeVar, Union

from honeybee_energy_ph.hvac import ventilation, heating, cooling, _base, ducting
from PHX.model.enums.hvac import PhxVentDuctType
from PHX.model import hvac
from PHX.model.hvac.heating import AnyPhxHeater
from PHX.model.hvac.ventilation import AnyPhxVentilation
from PHX.model.hvac.cooling import AnyPhxCooling

T = TypeVar("T", bound=Union[AnyPhxVentilation, AnyPhxHeater, AnyPhxCooling])


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
    hb_attrs = {
        attr_name for attr_name in dir(_hbeph_obj) if not attr_name.startswith("_")
    }
    phx_base_attrs = {
        attr_name for attr_name in dir(_phx_obj) if not attr_name.startswith("_")
    }

    for attr_nm in hb_attrs.intersection(phx_base_attrs):
        setattr(_phx_obj, attr_nm, getattr(_hbeph_obj, attr_nm))

    # -- Also copy attrs to PHX.params for objects which have them
    if _phx_obj.params:
        phx_params_attrs = {
            attr_name
            for attr_name in dir(_phx_obj.params)
            if not attr_name.startswith("_")
        }
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

    phx_duct.duct_type = PhxVentDuctType(_hbph_duct.duct_type,)

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
                hbph_duct_segment.insulation_reflective
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
    phx_device = phx_device_classes[_hbeph_exhaust_vent.device_class_name](
        _hbeph_exhaust_vent
    )
    return phx_device


# -----------------------------------------------------------------------------
# -- Heating


def build_phx_heating_electric(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterElectric:
    phx_obj = hvac.PhxHeaterElectric()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_fossil_boiler(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterBoilerFossil:
    phx_obj = hvac.PhxHeaterBoilerFossil()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_wood_boiler(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterBoilerWood:
    phx_obj = hvac.PhxHeaterBoilerWood()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_district(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterDistrictHeat:
    phx_obj = hvac.PhxHeaterDistrictHeat()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_hp_annual(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterHeatPumpAnnual:
    phx_obj = hvac.PhxHeaterHeatPumpAnnual()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_hp_monthly(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterHeatPumpMonthly:
    phx_obj = hvac.PhxHeaterHeatPumpMonthly()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_hp_combined(
    _hbeph_heater: heating.PhHeatingSystem,
) -> hvac.PhxHeaterHeatPumpCombined:
    phx_obj = hvac.PhxHeaterHeatPumpCombined()
    phx_obj = _transfer_attributes(_hbeph_heater, phx_obj)
    phx_obj.usage_profile.space_heating = True
    return phx_obj


def build_phx_heating_device(_htg_sys: heating.PhHeatingSystem) -> hvac.PhxHeatingDevice:
    """Returns a new PHX-Heating-Device based on an input Honeybee-PH Heating System.

    Arguments:
    ----------
        * _htg_sys (heating.PhHeatingSystem): The Honeybee-PH Heating System to build
            the new PHX Heating system from.

    Returns:
    --------
        * (mech.heating.PhxHeatingDevice): The new PHX Heating System created.
    """

    # -- Mapping Honeybee-PH -> PHX types
    phx_heater_classes = {
        "PhHeatingDirectElectric": build_phx_heating_electric,
        "PhHeatingFossilBoiler": build_phx_heating_fossil_boiler,
        "PhHeatingWoodBoiler": build_phx_heating_wood_boiler,
        "PhHeatingDistrict": build_phx_heating_district,
        "PhHeatingHeatPumpAnnual": build_phx_heating_hp_annual,
        "PhHeatingHeatPumpRatedMonthly": build_phx_heating_hp_monthly,
        "PhHeatingHeatPumpCombined": build_phx_heating_hp_combined,
    }

    # -- Get and build the right heater equipment type
    phx_heater = phx_heater_classes[_htg_sys.heating_type](_htg_sys)
    return phx_heater


def build_phx_heating_sys(_htg_sys: heating.PhHeatingSystem) -> hvac.AnyPhxHeater:
    """

    Arguments:
    ----------
        * _htg_sys (heating.PhHeatingSystem): The Honeybee-PH Heating System to build
            the new PHX Heating system from.

    Returns:
    --------
        * (mech.PhxHeatingDevice):
    """

    phx_htg_device = build_phx_heating_device(_htg_sys)

    # TODO: Distribution...

    return phx_htg_device


# -----------------------------------------------------------------------------
# --- Cooling


def build_phx_cooling_ventilation(
    _hbeph_cooling: cooling.PhCoolingSystem,
) -> hvac.PhxCoolingVentilation:
    phx_obj = hvac.PhxCoolingVentilation()
    phx_obj = _transfer_attributes(_hbeph_cooling, phx_obj)
    phx_obj.usage_profile.cooling = True
    return phx_obj


def build_phx_cooling_recirculation(
    _hbeph_cooling: cooling.PhCoolingSystem,
) -> hvac.PhxCoolingRecirculation:
    phx_obj = hvac.PhxCoolingRecirculation()
    phx_obj = _transfer_attributes(_hbeph_cooling, phx_obj)
    phx_obj.usage_profile.cooling = True
    return phx_obj


def build_phx_cooling_dehumidification(
    _hbeph_cooling: cooling.PhCoolingSystem,
) -> hvac.PhxCoolingDehumidification:
    phx_obj = hvac.PhxCoolingDehumidification()
    phx_obj = _transfer_attributes(_hbeph_cooling, phx_obj)
    phx_obj.usage_profile.cooling = True
    return phx_obj


def build_phx_cooling_panel(
    _hbeph_cooling: cooling.PhCoolingSystem,
) -> hvac.PhxCoolingPanel:
    phx_obj = hvac.PhxCoolingPanel()
    phx_obj = _transfer_attributes(_hbeph_cooling, phx_obj)
    phx_obj.usage_profile.cooling = True
    return phx_obj


def build_phx_cooling_device(_clg_sys: cooling.PhCoolingSystem) -> hvac.PhxCoolingDevice:
    """Returns a new PHX-Cooling-Device based on an input Honeybee-PH cooling System.

    Arguments:
    ----------
        * _clg_sys (cooling.PhCoolingSystem): The Honeybee-PH Cooling-System to build
            the new PHX-Cooling-System from.

    Returns:
    --------
        * (mech.cooling.PhxHeatingDevice): The new PHX cooling System created.
    """

    # -- Mapping Honeybee-PH -> PHX types
    phx_cooling_classes = {
        "PhCoolingVentilation": build_phx_cooling_ventilation,
        "PhCoolingRecirculation": build_phx_cooling_recirculation,
        "PhCoolingDehumidification": build_phx_cooling_dehumidification,
        "PhCoolingPanel": build_phx_cooling_panel,
    }

    # -- Get and build the right heater equipment type
    phx_cooling = phx_cooling_classes[_clg_sys.cooling_class_name](_clg_sys)
    return phx_cooling


def build_phx_cooling_sys(_htg_sys: cooling.PhCoolingSystem) -> hvac.AnyPhxCooling:
    """

    Arguments:
    ----------
        * _htg_sys (cooling.PhCoolingSystem): The Honeybee-PH cooling System to build
            the new PHX cooling system from.

    Returns:
    --------
        * (mech.PhxCoolingDevice):
    """

    phx_htg_device = build_phx_cooling_device(_htg_sys)

    # TODO: Distribution...

    return phx_htg_device
