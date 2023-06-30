# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

from dataclasses import asdict
from rich import print
from typing import Any, Dict, List, Optional, Union, Tuple
import sys

from PHX.model.building import PhxBuilding, PhxZone
from PHX.model.certification import PhxPhiusCertification, PhxPhBuildingData
from PHX.model.constructions import (
    PhxConstructionOpaque,
    PhxConstructionWindow,
    PhxLayer,
    PhxMaterial,
    PhxWindowFrameElement,
)
from PHX.model.components import (
    PhxComponentAperture,
    PhxComponentOpaque,
    PhxComponentThermalBridge,
    PhxApertureElement,
)
from PHX.model.enums.building import (
    ComponentFaceType,
    ComponentExposureExterior,
    ComponentFaceOpacity,
    ComponentColor,
    ThermalBridgeType,
    SpecificHeatCapacity,
)
from PHX.model.enums import hvac as hvac_enums
from PHX.model.enums.phius_certification import (
    PhiusCertificationProgram,
    PhiusCertificationBuildingCategoryType,
    PhiusCertificationBuildingUseType,
    PhiusCertificationBuildingStatus,
    PhiusCertificationBuildingType,
)
from PHX.model.enums.phx_site import (
    SiteSelection,
    SiteClimateSelection,
    SiteEnergyFactorSelection,
)
from PHX.model.geometry import PhxVertix, PhxPolygon, PhxVector, PhxPlane
from PHX.model.spaces import PhxSpace
from PHX.model.schedules.ventilation import (
    PhxScheduleVentilation,
    Vent_UtilPeriods,
    Vent_OperatingPeriod,
)
from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from PHX.model.phx_site import (
    PhxSite,
    PhxClimate,
    PhxGround,
    PhxSiteEnergyFactors,
    PhxPEFactor,
    PhxCO2Factor,
)
from PHX.model.project import PhxProject, PhxProjectData, ProjectData_Agent, PhxVariant
from PHX.model.hvac.collection import PhxZoneCoverage
from PHX.model.programs.occupancy import PhxProgramOccupancy
from PHX.model.programs.ventilation import PhxProgramVentilation
from PHX.model.hvac.ventilation import (
    PhxDeviceVentilator,
    AnyPhxExhaustVent,
    PhxExhaustVentilatorRangeHood,
    PhxExhaustVentilatorDryer,
    PhxExhaustVentilatorUserDefined,
)
from PHX.model.hvac.heating import (
    PhxHeaterBoilerFossil,
    PhxHeaterBoilerWood,
    PhxHeaterDistrictHeat,
    PhxHeaterElectric,
    PhxHeaterHeatPumpAnnual,
    PhxHeaterHeatPumpCombined,
    PhxHeaterHeatPumpMonthly,
    PhxHeaterHeatPumpHotWater,
    PhxHeaterHeatPump,
    PhxHeaterBoiler,
)
from PHX.model.hvac.water import PhxHotWaterTank
from PHX.model.hvac.renewable_devices import PhxDevicePhotovoltaic
from PHX.model.enums.elec_equip import ElectricEquipmentType
from PHX.model.elec_equip import (
    PhxElectricalDevice,
    PhxDeviceDishwasher,
    PhxDeviceCooktop,
    PhxDeviceClothesWasher,
    PhxDeviceClothesDryer,
    PhxDeviceRefrigerator,
    PhxDeviceFreezer,
    PhxDeviceFridgeFreezer,
    PhxDeviceCooktop,
    PhxDeviceCustomElec,
    PhxDeviceMEL,
    PhxDeviceLightingInterior,
    PhxDeviceLightingExterior,
    PhxDeviceLightingGarage,
    PhxDeviceCustomLighting,
    PhxDeviceCustomMEL,
)


# ----------------------------------------------------------------------
# -- Conversion Functions


def as_phx_obj(_data: Dict[str, Any], _schema_name, **kwargs) -> Any:
    """Find the right class-builder from the module and pass along the data to it.

    Args:
        _data (Dict[str, Any]): The data to be passed to the class-builder.
        _schema_name ([type]): The name of the class-builder to be used.
        kwargs: Any additional arguments to be passed to the class-builder.
    Returns:
        A new PHX object built from the input data
    """
    builder = getattr(sys.modules[__name__], f"_{_schema_name}")
    return builder(_data, **kwargs)


def optional_float(_input) -> Union[float, Any]:
    """If input is None, return that. Otherwise, cast to float."""
    if not _input or _input == "None":
        return None
    return float(_input)


def optional_str(_input) -> Union[str, Any]:
    """If input is None, return that. Otherwise, cast to str."""
    if not _input or _input == "None":
        return ""
    return str(_input)


def str_bool(_input) -> bool:
    return str(_input).upper() == "TRUE"


# ----------------------------------------------------------------------
# -- Project


def _PhxProject(_data: Dict[str, Any]) -> PhxProject:
    phx_obj = PhxProject()
    phx_obj.data_version = _data["DataVersion"]
    phx_obj.unit_system = _data["UnitSystem"]
    phx_obj.program_version = _data["ProgramVersion"]
    phx_obj.scope = _data["Scope"]
    phx_obj.visualized_geometry = _data["DimensionsVisualizedGeometry"]

    phx_obj.project_data = as_phx_obj(_data["ProjectData"], "PhxProjectData")

    # ----------------------------------------------------------------------
    # -- Build all the type collections firs
    for window_type_dict in _data["WindowTypes"]:
        new_window = as_phx_obj(window_type_dict, "PhxConstructionWindow")
        # -- Be sure to use the identifier as the key so the Component
        # -- lookup works properly. We don't use the name here since
        # -- wufi doesn't enforce unique names like HB does.
        phx_obj.add_new_window_type(new_window, _key=new_window.identifier)

    for opaque_type_dict in _data["Assemblies"]:
        new_opaque: PhxConstructionOpaque = as_phx_obj(
            opaque_type_dict, "PhxConstructionOpaque"
        )
        # -- Be sure to use the identifier as the key so the Component
        # -- lookup works properly. We don't use the name here since
        # -- wufi doesn't enforce unique names like HB does.
        phx_obj.add_assembly_type(new_opaque, _key=new_opaque.identifier)

    # TODO: phx_obj.shade_types = as_phx_obj("SolarProtectionTypes", _data)

    for vent_pattern_dict in _data["UtilisationPatternsVentilation"]:
        new_pattern = as_phx_obj(vent_pattern_dict, "PhxScheduleVentilation")
        phx_obj.utilization_patterns_ventilation.add_new_util_pattern(new_pattern)

    for vent_pattern_dict in _data["UtilizationPatternsPH"]:
        new_pattern = as_phx_obj(vent_pattern_dict, "PhxScheduleOccupancy")
        phx_obj.utilization_patterns_occupancy.add_new_util_pattern(new_pattern)

    # ----------------------------------------------------------------------
    # -- Build all the actual Variants
    for variant_dict in _data["Variants"]:
        new_variant = as_phx_obj(variant_dict, "PhxVariant", _phx_project_host=phx_obj)
        phx_obj.add_new_variant(new_variant)

    return phx_obj


def _PhxProjectData(_data: Dict[str, Any]) -> PhxProjectData:
    phx_obj = PhxProjectData()
    phx_obj.project_date = optional_str(_data["Date_Project"])
    phx_obj.owner_is_client = _data["OwnerIsClient"]
    phx_obj.year_constructed = int(_data["Year_Construction"])
    phx_obj.image = _data["WhiteBackgroundPictureBuilding"]

    phx_obj.customer = ProjectData_Agent(
        optional_str(_data["Customer_Name"]),
        optional_str(_data["Customer_Street"]),
        optional_str(_data["Customer_Locality"]),
        optional_str(_data["Customer_PostalCode"]),
        optional_str(_data["Customer_Tel"]),
        optional_str(_data["Customer_Email"]),
    )
    phx_obj.building = ProjectData_Agent(
        optional_str(_data["Building_Name"]),
        optional_str(_data["Building_Street"]),
        optional_str(_data["Building_Locality"]),
        optional_str(_data["Building_PostalCode"]),
    )
    phx_obj.owner = ProjectData_Agent(
        optional_str(_data["Owner_Name"]),
        optional_str(_data["Owner_Street"]),
        optional_str(_data["Owner_Locality"]),
        optional_str(_data["Owner_PostalCode"]),
    )
    phx_obj.designer = ProjectData_Agent(
        optional_str(_data["Responsible_Name"]),
        optional_str(_data["Responsible_Street"]),
        optional_str(_data["Responsible_Locality"]),
        optional_str(_data["Responsible_PostalCode"]),
        optional_str(_data["Responsible_Tel"]),
        optional_str(_data["Responsible_LicenseNr"]),
        optional_str(_data["Responsible_Email"]),
    )

    return phx_obj


# ----------------------------------------------------------------------
# -- Envelope Types


def _PhxConstructionWindow(_data: Dict[str, Any]) -> PhxConstructionWindow:
    phx_obj = PhxConstructionWindow()
    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.identifier = str(_data["IdentNr"])
    phx_obj.display_name = str(_data["Name"])
    phx_obj.use_detailed_uw = str_bool(_data["Uw_Detailed"])
    phx_obj.use_detailed_frame = str_bool(_data["GlazingFrameDetailed"])

    phx_obj.u_value_window = float(_data["U_Value"])
    phx_obj.u_value_glass = float(_data["U_Value_Glazing"])
    phx_obj.u_value_frame = float(_data["U_Value_Frame"])

    phx_obj.glass_mean_emissivity = float(_data["MeanEmissivity"])
    phx_obj.glass_g_value = float(_data["g_Value"])

    phx_obj.frame_top = PhxWindowFrameElement(
        float(_data["Frame_Width_Top"]),
        float(_data["Frame_U_Top"]),
        float(_data["Glazing_Psi_Top"]),
        float(_data["Frame_Psi_Top"]),
    )
    phx_obj.frame_right = PhxWindowFrameElement(
        float(_data["Frame_Width_Right"]),
        float(_data["Frame_U_Right"]),
        float(_data["Glazing_Psi_Right"]),
        float(_data["Frame_Psi_Right"]),
    )
    phx_obj.frame_bottom = PhxWindowFrameElement(
        float(_data["Frame_Width_Bottom"]),
        float(_data["Frame_U_Bottom"]),
        float(_data["Glazing_Psi_Bottom"]),
        float(_data["Frame_Psi_Bottom"]),
    )
    phx_obj.frame_left = PhxWindowFrameElement(
        float(_data["Frame_Width_Left"]),
        float(_data["Frame_U_Left"]),
        float(_data["Glazing_Psi_Left"]),
        float(_data["Frame_Psi_Left"]),
    )

    return phx_obj


def _PhxConstructionOpaque(_data: Dict[str, Any]) -> PhxConstructionOpaque:
    phx_obj = PhxConstructionOpaque()
    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.identifier = str(_data["IdentNr"])
    phx_obj.display_name = str(_data["Name"])
    phx_obj.layer_order = int(_data["Order_Layers"])
    phx_obj.grid_kind = int(_data["Grid_Kind"])
    for layer in _data["Layers"]:
        new_layer = as_phx_obj(layer, "PhxLayer")
        phx_obj.layers.append(new_layer)

    return phx_obj


def _PhxLayer(_data: Dict[str, Any]) -> PhxLayer:
    phx_obj = PhxLayer()
    phx_obj.thickness_m = float(_data["Thickness"])
    new_mat = as_phx_obj(_data["Material"], "PhxMaterial")
    phx_obj.add_material(new_mat)

    return phx_obj


def _PhxMaterial(_data: Dict[str, Any]) -> PhxMaterial:
    phx_obj = PhxMaterial()
    phx_obj.display_name = _data["Name"]
    phx_obj.conductivity = float(_data["ThermalConductivity"])
    phx_obj.density = float(_data["BulkDensity"])
    phx_obj.porosity = float(_data["Porosity"])
    phx_obj.heat_capacity = float(_data["HeatCapacity"])
    phx_obj.water_vapor_resistance = float(_data["WaterVaporResistance"])
    phx_obj.reference_water = float(_data["ReferenceW"])
    return phx_obj


# ----------------------------------------------------------------------
# -- Utilization Patterns


def _PhxScheduleVentilation(_data: Dict[str, Any]) -> PhxScheduleVentilation:
    phx_obj = PhxScheduleVentilation()

    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.name = _data["Name"]
    phx_obj.identifier = str(_data["IdentNr"])
    phx_obj.operating_days = float(_data["OperatingDays"])
    phx_obj.operating_weeks = float(_data["OperatingWeeks"])
    phx_obj.operating_periods.high.period_operating_hours = float(_data["Maximum_DOS"])
    phx_obj.operating_periods.high.period_operation_speed = float(_data["Maximum_PDF"])
    phx_obj.operating_periods.standard.period_operating_hours = float(
        _data["Standard_DOS"]
    )
    phx_obj.operating_periods.standard.period_operation_speed = float(
        _data["Standard_PDF"]
    )
    phx_obj.operating_periods.basic.period_operating_hours = float(_data["Basic_DOS"])
    phx_obj.operating_periods.basic.period_operation_speed = float(_data["Basic_PDF"])
    phx_obj.operating_periods.minimum.period_operating_hours = float(_data["Minimum_DOS"])
    phx_obj.operating_periods.minimum.period_operation_speed = float(_data["Minimum_PDF"])
    return phx_obj


def _PhxScheduleOccupancy(_data: Dict[str, Any]) -> PhxScheduleOccupancy:
    phx_obj = PhxScheduleOccupancy()
    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.identifier = str(_data["IdentNr"])
    phx_obj.display_name = str(_data["Name"])
    phx_obj.start_hour = float(_data["BeginUtilization"])
    phx_obj.end_hour = float(_data["EndUtilization"])
    phx_obj.annual_utilization_days = float(_data["AnnualUtilizationDays"])
    phx_obj.relative_utilization_factor = float(_data["RelativeAbsenteeism"])

    return phx_obj


# ----------------------------------------------------------------------
# -- Variants


def _PhxVariant(_data: Dict[str, Any], _phx_project_host: PhxProject) -> PhxVariant:
    phx_obj = PhxVariant()

    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.name = optional_str(_data["Name"])
    phx_obj.remarks = optional_str(_data["Remarks"])
    phx_obj.plugin = optional_str(_data["PlugIn"])
    phx_obj.phius_cert = as_phx_obj(_data["PassivehouseData"], "PhxPhiusCertification")
    phx_obj.site = as_phx_obj(_data["ClimateLocation"], "PhxSite")

    phx_obj.building = as_phx_obj(
        {"Building": _data["Building"], "Graphics_3D": _data["Graphics_3D"]},
        "PhxBuilding",
        _phx_project_host=_phx_project_host,
    )

    for system_data_dict in _data["HVAC"]["Systems"]:
        phx_obj.mech_systems.display_name = system_data_dict["Name"]
        phx_obj.mech_systems.id_num = int(system_data_dict["IdentNr"])
        phx_obj.mech_systems.zone_coverage = as_phx_obj(
            system_data_dict["ZonesCoverage"][0], "PhxZoneCoverage"
        )

        for device_data_dict in system_data_dict["Devices"]:
            new_device = as_phx_obj(device_data_dict, "PhxMechanicalDevice")
            phx_obj.mech_systems.add_new_mech_device(new_device.identifier, new_device)

    return phx_obj


# ----------------------------------------------------------------------
# -- Building & Geometry


def _get_compo_dicts_by_type(
    _data: List[Dict],
) -> Tuple[List[Dict[str, Dict]], List[Dict[str, Dict]]]:
    """Helper function to sort the component dictionaries by type.

    Args:
        _data (List[Dict]): The list of component dictionaries.
    Returns:
        Tuple[List[Dict], List[Dict]]: The sorted lists of component dictionaries.
        - [0] = List of opaque component dicts
        - [1] = List of aperture components dicts
    """

    ap_dicts: List[Dict] = []
    opaque_dicts: List[Dict] = []
    for d in _data:
        if ComponentFaceOpacity(int(d["Type"])) == ComponentFaceOpacity.TRANSPARENT:
            ap_dicts.append(d)
        else:
            opaque_dicts.append(d)
    return opaque_dicts, ap_dicts


def _PhxBuilding(_data: Dict[str, Any], _phx_project_host: PhxProject) -> PhxBuilding:
    phx_obj = PhxBuilding()

    # ------------------------------------------------------------------
    # -- First, build all the vertices and polygons needed by the Components
    geom_dict = _data["Graphics_3D"]
    vertix_dict: Dict[int, PhxVertix] = {
        int(v["IdentNr"]): as_phx_obj(v, "PhxVertix") for v in geom_dict["Vertices"]
    }
    polygon_dict: Dict[int, PhxPolygon] = {
        int(v["IdentNr"]): as_phx_obj(v, "PhxPolygon", _vertix_dict=vertix_dict)
        for v in geom_dict["Polygons"]
    }

    # ------------------------------------------------------------------
    # -- Build the Components
    opaque_compo_dicts, ap_compo_dicts = _get_compo_dicts_by_type(
        _data["Building"]["Components"]
    )

    # -- Build all of the Aperture Components first
    aperture_dict: Dict[Tuple[int, ...], PhxComponentAperture] = {}
    for component_dict in ap_compo_dicts:
        component: PhxComponentAperture = as_phx_obj(
            component_dict,
            "PhxComponentAperture",
            _polygons=polygon_dict,
            _window_types=_phx_project_host.window_types,
        )
        aperture_dict[component.polygon_ids_sorted] = component

    # -- Build all of the Opaque Components
    for component_dict in opaque_compo_dicts:
        component = as_phx_obj(
            component_dict,
            "PhxComponentOpaque",
            _polygons=polygon_dict,
            _assembly_types=_phx_project_host.assembly_types,
            _aperture_dict=aperture_dict,
        )
        phx_obj.add_component(component)

    # ------------------------------------------------------------------
    # -- Build and add the Zones
    for zone_data_dict in _data["Building"]["Zones"]:
        new_zone = as_phx_obj(
            zone_data_dict, "PhxZone", _phx_project_host=_phx_project_host
        )
        phx_obj.add_zone(new_zone)

    return phx_obj


def _PhxVertix(_data: Dict[str, Any]) -> PhxVertix:
    phx_obj = PhxVertix()
    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.x = float(_data["X"])
    phx_obj.y = float(_data["Y"])
    phx_obj.z = float(_data["Z"])
    return phx_obj


def _PhxPolygon(
    _data: Dict[str, Any], _vertix_dict: Dict[int, PhxVertix] = {}
) -> PhxPolygon:
    surface_normal = PhxVector(
        float(_data["NormalVectorX"]),
        float(_data["NormalVectorY"]),
        float(_data["NormalVectorZ"]),
    )

    # ----------------------------------------------------------------------
    # TODO: calculate the area, center and plane?
    area = 0.0
    center = PhxVertix(0, 0, 0)
    plane = PhxPlane(
        surface_normal,
        center,
        PhxVector(0, 0, 0),
        PhxVector(0, 0, 0),
    )
    # ----------------------------------------------------------------------

    phx_obj = PhxPolygon(
        _display_name=_data["IdentNr"],
        _area=area,
        center=center,
        normal_vector=surface_normal,
        plane=plane,
    )
    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj._vertices = [_vertix_dict[int(v_id)] for v_id in _data["IdentNrPoints"]]
    for i in _data["IdentNrPolygonsInside"]:
        phx_obj.child_polygon_ids.append(int(i))
    return phx_obj


def _PhxComponentAperture(
    _data: Dict[str, Any],
    _polygons: Dict[int, Any],
    _window_types: Dict[str, PhxConstructionWindow],
) -> PhxComponentAperture:
    phx_obj = PhxComponentAperture(_host=None)  # type: ignore

    phx_obj.display_name = str(_data["Name"])
    phx_obj.face_type = ComponentFaceType.WINDOW
    phx_obj.face_opacity = ComponentFaceOpacity(int(_data["Type"]))
    phx_obj.color_interior = ComponentColor(int(_data["IdentNrColorI"]))
    phx_obj.color_exterior = ComponentColor(int(_data["IdentNrColorE"]))
    phx_obj.exposure_interior = int(_data["InnerAttachment"])
    phx_obj.exposure_exterior = ComponentExposureExterior(int(_data["OuterAttachment"]))
    phx_obj.interior_attachment_id = int(_data["IdentNr_ComponentInnerSurface"])

    phx_obj.window_type_id_num = int(_data["IdentNrWindowType"])
    phx_obj.window_type = _window_types[_data["IdentNrWindowType"]]

    phx_obj.install_depth = float(_data["DepthWindowReveal"])
    phx_obj.default_monthly_shading_correction_factor = float(
        _data["DefaultCorrectionShadingMonth"]
    )

    # phx_obj.variant_type_name = str() ?? What is this for?

    for i, poly_id in enumerate(_data["IdentNrPolygons"]):
        polygon = _polygons[int(poly_id)]
        new_ap_element = PhxApertureElement(_host=phx_obj)
        new_ap_element.display_name = f"{phx_obj.display_name} - {i}"
        new_ap_element.polygon = polygon
        phx_obj.add_element(new_ap_element)

    return phx_obj


def _PhxComponentOpaque(
    _data: Dict[str, Any],
    _polygons: Dict[int, Any],
    _assembly_types: Dict[str, PhxConstructionOpaque],
    _aperture_dict: Dict[Tuple[int, ...], PhxComponentAperture],
) -> PhxComponentOpaque:
    # -- Build either an opaque or transparent component
    phx_obj = PhxComponentOpaque()

    phx_obj._id_num = int(_data["IdentNr"])
    phx_obj.display_name = _data["Name"]
    phx_obj.face_opacity = ComponentFaceOpacity(int(_data["Type"]))
    phx_obj.color_interior = ComponentColor(int(_data["IdentNrColorI"]))
    phx_obj.color_exterior = ComponentColor(int(_data["IdentNrColorE"]))
    phx_obj.exposure_interior = int(_data["InnerAttachment"])
    phx_obj.exposure_exterior = ComponentExposureExterior(int(_data["OuterAttachment"]))
    phx_obj.interior_attachment_id = int(_data["IdentNr_ComponentInnerSurface"])

    phx_obj.add_polygons([_polygons[int(i)] for i in _data["IdentNrPolygons"]])
    if phx_obj.polygons:
        face_normal_angle_off_vertical = phx_obj.polygons[0].angle_from_horizontal
        phx_obj.face_type = ComponentFaceType.by_angle(face_normal_angle_off_vertical)

    # -- Add the Apertures
    # -- For each polygon, see if it has any children polygons? If so, find the
    # -- aperture element associated with the child polygon, and add it to the component.
    for poly in phx_obj.polygons:
        for child_id in poly.child_polygon_ids:
            for k, v in _aperture_dict.items():
                if child_id in k:
                    phx_obj.add_aperture(v)

    phx_obj.assembly_type_id_num = int(_data["IdentNrAssembly"])
    if phx_obj.assembly_type_id_num != -1:
        # -- -1 indicates a shade component without an assembly type
        phx_obj.assembly = _assembly_types[_data["IdentNrAssembly"]]

    return phx_obj


def _PhxComponentThermalBridge(_data: Dict[str, Any]) -> PhxComponentThermalBridge:
    phx_obj = PhxComponentThermalBridge()

    phx_obj.quantity = 1.0
    phx_obj.display_name = _data["Name"]
    phx_obj.group_number = ThermalBridgeType(int(_data["Type"]) * -1)
    phx_obj.length = float(_data["Length"])
    phx_obj.psi_value = float(_data["PsiValue"])

    return phx_obj


# ----------------------------------------------------------------------
# -- Site & Climate


def _PhxPhiusCertification(_data: Dict[str, Any]) -> PhxPhiusCertification:
    phx_obj = PhxPhiusCertification()
    phx_obj.use_monthly_shading = str_bool(_data["UseWUFIMeanMonthShading"])

    # no idea why PH_BuildingData is a list?....
    bldg_data_dict = _data["PH_Buildings"][0]
    phx_obj.ph_building_data = as_phx_obj(bldg_data_dict, "PhxPhBuildingData")

    # ----------------------------------------------------------------------
    # --- Certification Criteria
    criteria = phx_obj.phius_certification_criteria
    criteria.ph_selection_target_data = int(_data["PH_SelectionTargetData"])
    criteria.phius_annual_heating_demand = float(_data["AnnualHeatingDemand"])
    criteria.phius_annual_cooling_demand = float(_data["AnnualCoolingDemand"])
    criteria.phius_peak_heating_load = float(_data["PeakHeatingLoad"])
    criteria.phius_peak_cooling_load = float(_data["PeakCoolingLoad"])

    # ----------------------------------------------------------------------
    # --- Certification Settings
    settings = phx_obj.phius_certification_settings
    settings.phius_building_certification_program = PhiusCertificationProgram(
        int(_data["PH_CertificateCriteria"])
    )
    settings.phius_building_category_type = PhiusCertificationBuildingCategoryType(
        int(bldg_data_dict["BuildingCategory"])
    )
    settings.phius_building_use_type = PhiusCertificationBuildingUseType(
        int(bldg_data_dict["OccupancyTypeResidential"])
    )
    settings.phius_building_status = PhiusCertificationBuildingStatus(
        int(bldg_data_dict["BuildingStatus"])
    )
    settings.phius_building_type = PhiusCertificationBuildingType(
        int(bldg_data_dict["BuildingType"])
    )

    return phx_obj


def _PhxPhBuildingData(_data: Dict[str, Any]) -> PhxPhBuildingData:
    phx_obj = PhxPhBuildingData()
    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.num_of_units = int(_data["NumberUnits"])
    phx_obj.num_of_floors = int(_data["CountStories"])
    phx_obj.occupancy_setting_method = int(_data["OccupancySettingMethod"])
    phx_obj.airtightness_q50 = float(_data["EnvelopeAirtightnessCoefficient"])
    phx_obj.setpoints.winter = float(_data["IndoorTemperature"])
    phx_obj.setpoints.summer = float(_data["OverheatingTemperatureThreshold"])
    phx_obj.mech_room_temp = float(_data["MechanicalRoomTemperature"])
    phx_obj.non_combustible_materials = str_bool(_data["NonCombustibleMaterials"])
    phx_obj.summer_hrv_bypass_mode = hvac_enums.PhxSummerBypassMode(
        int(_data["SummerHRVHumidityRecovery"])
    )

    # TODO: phx_obj.foundations =

    return phx_obj


def _PhxSite(_data: Dict[str, Any]) -> PhxSite:
    phx_obj = PhxSite()
    phx_obj.selection = SiteSelection(int(_data["Selection"]))

    phx_obj.location.latitude = float(_data["Latitude_DB"])
    phx_obj.location.longitude = float(_data["Longitude_DB"])
    phx_obj.location.site_elevation = optional_float(_data["HeightNN_DB"])
    phx_obj.location.hours_from_UTC = int(_data["dUTC_DB"])

    ph_climate_data = _data["PH_ClimateLocation"]
    phx_obj.location.climate_zone = int(ph_climate_data["ClimateZone"])
    phx_obj.climate = as_phx_obj(ph_climate_data, "PhxClimate")
    phx_obj.ground = as_phx_obj(ph_climate_data, "PhxGround")
    phx_obj.energy_factors = as_phx_obj(ph_climate_data, "PhxSiteEnergyFactors")

    return phx_obj


def _PhxClimate(_data: Dict[str, Any]) -> PhxClimate:
    phx_obj = PhxClimate()

    phx_obj.station_elevation = float(_data["HeightNNWeatherStation"])
    phx_obj.selection = SiteClimateSelection(int(_data["Selection"]))
    phx_obj.daily_temp_swing = float(_data["DailyTemperatureSwingSummer"])
    phx_obj.avg_wind_speed = float(_data["AverageWindSpeed"])

    phx_obj.temperature_air = [float(_) for _ in _data["TemperatureMonthly"]]
    phx_obj.temperature_dewpoint = [float(_) for _ in _data["DewPointTemperatureMonthly"]]
    phx_obj.temperature_sky = [float(_) for _ in _data["SkyTemperatureMonthly"]]

    phx_obj.radiation_north = [float(_) for _ in _data["NorthSolarRadiationMonthly"]]
    phx_obj.radiation_east = [float(_) for _ in _data["EastSolarRadiationMonthly"]]
    phx_obj.radiation_south = [float(_) for _ in _data["SouthSolarRadiationMonthly"]]
    phx_obj.radiation_west = [float(_) for _ in _data["WestSolarRadiationMonthly"]]
    phx_obj.radiation_global = [float(_) for _ in _data["GlobalSolarRadiationMonthly"]]

    phx_obj.peak_heating_1.temperature_air = float(_data["TemperatureHeating1"])
    phx_obj.peak_heating_1.radiation_north = float(_data["NorthSolarRadiationHeating1"])
    phx_obj.peak_heating_1.radiation_east = float(_data["EastSolarRadiationHeating1"])
    phx_obj.peak_heating_1.radiation_south = float(_data["SouthSolarRadiationHeating1"])
    phx_obj.peak_heating_1.radiation_west = float(_data["WestSolarRadiationHeating1"])
    phx_obj.peak_heating_1.radiation_global = float(_data["GlobalSolarRadiationHeating1"])

    phx_obj.peak_heating_2.temperature_air = float(_data["TemperatureHeating1"])
    phx_obj.peak_heating_2.radiation_north = float(_data["NorthSolarRadiationHeating2"])
    phx_obj.peak_heating_2.radiation_east = float(_data["EastSolarRadiationHeating2"])
    phx_obj.peak_heating_2.radiation_south = float(_data["SouthSolarRadiationHeating2"])
    phx_obj.peak_heating_2.radiation_west = float(_data["WestSolarRadiationHeating2"])
    phx_obj.peak_heating_2.radiation_global = float(_data["GlobalSolarRadiationHeating2"])

    phx_obj.peak_cooling_1.temperature_air = float(_data["TemperatureCooling"])
    phx_obj.peak_cooling_1.radiation_north = float(_data["NorthSolarRadiationCooling"])
    phx_obj.peak_cooling_1.radiation_east = float(_data["EastSolarRadiationCooling"])
    phx_obj.peak_cooling_1.radiation_south = float(_data["SouthSolarRadiationCooling"])
    phx_obj.peak_cooling_1.radiation_west = float(_data["WestSolarRadiationCooling"])
    phx_obj.peak_cooling_1.radiation_global = float(_data["GlobalSolarRadiationCooling"])

    phx_obj.peak_cooling_2.temperature_air = float(_data["TemperatureCooling2"])
    phx_obj.peak_cooling_2.radiation_north = float(_data["NorthSolarRadiationCooling2"])
    phx_obj.peak_cooling_2.radiation_east = float(_data["EastSolarRadiationCooling2"])
    phx_obj.peak_cooling_2.radiation_south = float(_data["SouthSolarRadiationCooling2"])
    phx_obj.peak_cooling_2.radiation_west = float(_data["WestSolarRadiationCooling2"])
    phx_obj.peak_cooling_2.radiation_global = float(_data["GlobalSolarRadiationCooling2"])

    return phx_obj


def _PhxGround(_data: Dict[str, Any]) -> PhxGround:
    phx_obj = PhxGround()
    phx_obj.ground_thermal_conductivity = float(_data["GroundThermalConductivity"])
    phx_obj.ground_heat_capacity = float(_data["GroundHeatCapacitiy"])
    phx_obj.ground_density = float(_data["GroundDensity"])
    phx_obj.depth_groundwater = float(_data["DepthGroundwater"])
    phx_obj.flow_rate_groundwater = float(_data["FlowRateGroundwater"])
    return phx_obj


def _PhxSiteEnergyFactors(_data: Dict[str, Any]) -> PhxSiteEnergyFactors:
    _wufi_order = [
        "OIL",
        "NATURAL_GAS",
        "LPG",
        "HARD_COAL",
        "WOOD",
        "ELECTRICITY_MIX",
        "ELECTRICITY_PV",
        "HARD_COAL_CGS_70_CHP",
        "HARD_COAL_CGS_35_CHP",
        "HARD_COAL_CGS_0_CHP",
        "GAS_CGS_70_CHP",
        "GAS_CGS_35_CHP",
        "GAS_CGS_0_CHP",
        "OIL_CGS_70_CHP",
        "OIL_CGS_35_CHP",
        "OIL_CGS_0_CHP",
    ]

    phx_obj = PhxSiteEnergyFactors()
    phx_obj.selection_pe_co2_factor = SiteEnergyFactorSelection(
        int(_data["SelectionPECO2Factor"])
    )
    phx_obj.pe_factors = {
        fuel_name: PhxPEFactor(optional_float(_), "kWh/kWh", fuel_name)
        for fuel_name, _ in zip(_wufi_order, _data["PEFactorsUserDef"])
    }
    phx_obj.co2_factors = {
        fuel_name: PhxCO2Factor(optional_float(_), "g/kWh", fuel_name)
        for fuel_name, _ in zip(_wufi_order, _data["CO2FactorsUserDef"])
    }

    return phx_obj


# ----------------------------------------------------------------------
# -- Zones


def _PhxZone(_data: Dict[str, Any], _phx_project_host: PhxProject) -> PhxZone:
    def _spec_cap_WH_m2k(_input):
        if _input <= 60.0:
            return 1
        elif _input <= 132.0:
            return 2
        else:
            return 3

    phx_obj = PhxZone()

    phx_obj.id_num = int(_data["IdentNr"])
    phx_obj.display_name = str(_data["Name"])
    phx_obj.volume_gross = float(_data["GrossVolume"])
    phx_obj.volume_net = float(_data["NetVolume"])
    phx_obj.weighted_net_floor_area = float(_data["FloorArea"])
    phx_obj.clearance_height = float(_data["ClearanceHeight"])
    phx_obj.res_occupant_quantity = float(_data["OccupantQuantityUserDef"])
    phx_obj.res_number_bedrooms = int(_data["NumberBedrooms"])
    phx_obj.specific_heat_capacity = SpecificHeatCapacity(
        _spec_cap_WH_m2k(float(_data["SpecificHeatCapacity"]))
    )

    phx_obj.spaces = [
        as_phx_obj(
            {"RoomsVentilation": rm_data, "LoadsPersonsPH": load_data},
            "PhxSpace",
            _phx_project_host=_phx_project_host,
        )
        for rm_data, load_data in zip(_data["RoomsVentilation"], _data["LoadsPersonsPH"])
    ]

    for vent_dict_data in _data["ExhaustVents"]:
        new_phx_exhaust = as_phx_obj(vent_dict_data, "PhxExhaustVent")
        phx_obj.exhaust_ventilator_collection.add_new_ventilator(
            new_phx_exhaust.identifier, new_phx_exhaust
        )

    for device_dict_data in _data["HomeDevice"]:
        new_phx_home_device = as_phx_obj(device_dict_data, "PhxHomeDevice")
        phx_obj.elec_equipment_collection.add_new_device(
            new_phx_home_device.identifier, new_phx_home_device
        )

    for i, brige_dict_data in enumerate(_data["ThermalBridges"]):
        new_phx_tb = as_phx_obj(brige_dict_data, "PhxComponentThermalBridge")
        new_phx_tb.identifier = f"ThermalBridge_{i :03}"
        phx_obj.add_thermal_bridge(new_phx_tb)

    # -- Ignore these for now
    # phx_obj.res_number_dwellings = int(_data["IdentNr"])
    # phx_obj.lighting = None

    return phx_obj


def _PhxSpace(
    _data: Dict[str, Dict[str, Any]], _phx_project_host: PhxProject
) -> PhxSpace:
    rm_data = _data["RoomsVentilation"]
    load_data = _data["LoadsPersonsPH"]

    phx_obj = PhxSpace()

    # phx_obj.id_num = int(_data[""])
    phx_obj.display_name = str(rm_data["Name"])
    phx_obj.wufi_type = int(rm_data["Type"])
    phx_obj.quantity = int(rm_data["Quantity"])
    phx_obj.floor_area = float(rm_data["AreaRoom"])
    phx_obj.weighted_floor_area = float(rm_data["AreaRoom"])
    phx_obj.clear_height = float(rm_data["ClearRoomHeight"])

    # -- Ventilation Unit (ERV) number
    phx_obj.vent_unit_id_num = int(rm_data["IdentNrVentilationUnit"])

    # -- Ventilation Schedule
    project_util_pat_ven = _phx_project_host.utilization_patterns_ventilation
    vent_pattern_id = rm_data["IdentNrUtilizationPatternVent"]
    phx_obj.ventilation.schedule = project_util_pat_ven[vent_pattern_id]
    phx_obj.ventilation.load.flow_extract = float(rm_data["DesignVolumeFlowRateExhaust"])
    phx_obj.ventilation.load.flow_supply = float(rm_data["DesignVolumeFlowRateSupply"])

    #  -- Occupancy Schedule and Load
    project_util_pat_occ = _phx_project_host.utilization_patterns_occupancy
    occ_pattern_id = load_data["IdentNrUtilizationPattern"]
    phx_obj.occupancy.schedule = project_util_pat_occ[occ_pattern_id]
    phx_obj.peak_occupancy = float(load_data["NumberOccupants"])

    # TODO: -------
    # phx_obj.lighting = None
    # phx_obj.electric_equipment = None

    return phx_obj


# ----------------------------------------------------------------------
# -- Mechanicals


def _PhxZoneCoverage(_data: Dict[str, Any]) -> PhxZoneCoverage:
    phx_obj = PhxZoneCoverage()

    phx_obj.zone_num = float(_data["IdentNrZone"])
    phx_obj.heating = float(_data["CoverageHeating"])
    phx_obj.cooling = float(_data["CoverageCooling"])
    phx_obj.ventilation = float(_data["CoverageVentilation"])
    phx_obj.humidification = float(_data["CoverageHumidification"])
    phx_obj.dehumidification = float(_data["CoverageDehumidification"])

    return phx_obj


def _PhxMechanicalDevice(_data: Dict[str, Any]) -> Any:
    device_type_builders = {
        hvac_enums.SystemType.VENTILATION: "PhxDevice_Ventilation",
        hvac_enums.SystemType.ELECTRIC: "PhxDevice_Electric",
        hvac_enums.SystemType.BOILER: "PhxDevice_Boiler",
        hvac_enums.SystemType.DISTRICT_HEAT: "PhxDevice_DistrictHeat",
        hvac_enums.SystemType.HEAT_PUMP: "PhxDevice_HeatPump",
        hvac_enums.SystemType.WATER_STORAGE: "PhxDevice_WaterStorage",
        hvac_enums.SystemType.PHOTOVOLTAIC: "PhxDevice_Photovoltaic",
    }

    device_type = hvac_enums.SystemType(int(_data["SystemType"]))
    builder_class = device_type_builders[device_type]

    # -- Pass the data off to the correct device builder class
    return as_phx_obj(_data, builder_class)


def _PhxDevice_Ventilation(_data: Dict[str, Any]) -> PhxDeviceVentilator:
    phx_obj = PhxDeviceVentilator()

    # TODO: params

    return phx_obj


def _PhxDevice_Electric(_data: Dict[str, Any]) -> PhxHeaterElectric:
    return PhxHeaterElectric()


def _PhxDevice_Boiler(_data: Dict[str, Any]) -> PhxHeaterBoiler:
    boiler_builders = {
        hvac_enums.PhxFuelType.NATURAL_GAS: "PhxHeaterBoilerFossil",
        hvac_enums.PhxFuelType.OIL: "PhxHeaterBoilerFossil",
        hvac_enums.PhxFuelType.WOOD_LOG: "PhxHeaterBoilerWood",
        hvac_enums.PhxFuelType.WOOD_PELLET: "PhxHeaterBoilerWood",
    }
    boiler_type = hvac_enums.PhxFuelType(
        int(_data["PH_Parameters"]["EnergySourceBoilerType"])
    )
    return as_phx_obj(_data, boiler_builders[boiler_type])


def _PhxHeaterBoilerFossil(_data: Dict[str, Any]) -> PhxHeaterBoilerFossil:
    phx_obj = PhxHeaterBoilerFossil()
    phx_obj.params.fuel = int(_data["PH_Parameters"]["EnergySourceBoilerType"])
    phx_obj.params.condensing = str_bool(_data["PH_Parameters"]["CondensingBoiler"])
    phx_obj.params.in_conditioned_space = str_bool(
        _data["PH_Parameters"]["InConditionedSpace"]
    )
    phx_obj.params.effic_at_30_percent_load = float(
        _data["PH_Parameters"]["BoilerEfficiency30"]
    )
    phx_obj.params.effic_at_nominal_load = float(
        _data["PH_Parameters"]["BoilerEfficiencyNominalOutput"]
    )
    phx_obj.params.avg_rtrn_temp_at_30_percent_load = float(
        _data["PH_Parameters"]["AverageReturnTemperatureMeasured30Load"]
    )
    phx_obj.params.avg_temp_at_70C_55C = float(
        _data["PH_Parameters"]["AverageBoilerTemperatureDesign70_55"]
    )
    phx_obj.params.avg_temp_at_55C_45C = float(
        _data["PH_Parameters"]["AverageBoilerTemperatureDesign55_45"]
    )
    phx_obj.params.avg_temp_at_32C_28C = float(
        _data["PH_Parameters"]["AverageBoilerTemperatureDesign35_28"]
    )
    phx_obj.params.standby_loss_at_70C = optional_float(
        _data["PH_Parameters"]["StandbyHeatLossBoiler70"]
    )
    phx_obj.params.rated_capacity = float(_data["PH_Parameters"]["MaximalBoilerPower"])
    return phx_obj


def _PhxHeaterBoilerWood(_data: Dict[str, Any]) -> PhxHeaterBoilerWood:
    phx_obj = PhxHeaterBoilerWood()

    return phx_obj


def _PhxDevice_DistrictHeat(_data: Dict[str, Any]) -> PhxHeaterDistrictHeat:
    return PhxHeaterDistrictHeat()


def _PhxDevice_HeatPump(_data: Dict[str, Any]) -> PhxHeaterHeatPump:
    hp_builders = {
        hvac_enums.HeatPumpType.COMBINED: "PhxDevice_HeatPump_Combined",
        hvac_enums.HeatPumpType.ANNUAL: "PhxDevice_HeatPump_Annual",
        hvac_enums.HeatPumpType.RATED_MONTHLY: "PhxDevice_HeatPump_RatedMonthly",
        hvac_enums.HeatPumpType.HOT_WATER: "PhxDevice_HeatPump_HotWater",
    }
    hp_type = hvac_enums.HeatPumpType(int(_data["PH_Parameters"]["HPType"]))
    builder_class = hp_builders[hp_type]
    return as_phx_obj(_data, builder_class)


def _PhxDevice_HeatPump_Combined(_data: Dict[str, Any]) -> PhxHeaterHeatPumpCombined:
    phx_obj = PhxHeaterHeatPumpCombined()
    return phx_obj


def _PhxDevice_HeatPump_Annual(_data: Dict[str, Any]) -> PhxHeaterHeatPumpAnnual:
    phx_obj = PhxHeaterHeatPumpAnnual()
    phx_obj.params.annual_COP = optional_float(_data["PH_Parameters"]["AnnualCOP"])
    phx_obj.params.total_system_perf_ratio = optional_float(
        _data["PH_Parameters"]["TotalSystemPerformanceRatioHeatGenerator"]
    )
    return phx_obj


def _PhxDevice_HeatPump_RatedMonthly(_data: Dict[str, Any]) -> PhxHeaterHeatPumpMonthly:
    phx_obj = PhxHeaterHeatPumpMonthly()
    phx_obj.params.COP_1 = optional_float(_data["PH_Parameters"]["RatedCOP1"])
    phx_obj.params.COP_2 = optional_float(_data["PH_Parameters"]["RatedCOP2"])
    phx_obj.params.ambient_temp_1 = optional_float(
        _data["PH_Parameters"]["AmbientTemperature1"]
    )
    phx_obj.params.ambient_temp_2 = optional_float(
        _data["PH_Parameters"]["AmbientTemperature2"]
    )
    return phx_obj


def _PhxDevice_HeatPump_HotWater(_data: Dict[str, Any]) -> PhxHeaterHeatPumpHotWater:
    phx_obj = PhxHeaterHeatPumpHotWater()
    phx_obj.params.annual_COP = optional_float(_data["PH_Parameters"]["AnnualCOP"])
    phx_obj.params.annual_system_perf_ratio = optional_float(
        _data["PH_Parameters"]["TotalSystemPerformanceRatioHeatGenerator"]
    )
    phx_obj.params.annual_energy_factor = optional_float(
        _data["PH_Parameters"]["HPWH_EF"]
    )
    return phx_obj


def _PhxDevice_WaterStorage(_data: Dict[str, Any]) -> PhxHotWaterTank:
    phx_obj = PhxHotWaterTank()
    phx_obj.quantity = int(_data["PH_Parameters"]["QauntityWS"])
    phx_obj.params.display_name = _data["Name"]
    phx_obj.params.input_option = hvac_enums.PhxHotWaterInputOptions(
        int(_data["PH_Parameters"]["InputOption"])
    )
    phx_obj.params.in_conditioned_space = str_bool(
        _data["PH_Parameters"]["InConditionedSpace"]
    )
    phx_obj.params.storage_loss_rate = optional_float(
        _data["PH_Parameters"]["AverageHeatReleaseStorage"]
    )
    phx_obj.params.storage_capacity = optional_float(
        _data["PH_Parameters"]["SolarThermalStorageCapacity"]
    )
    phx_obj.params.standby_losses = optional_float(
        _data["PH_Parameters"]["StorageLossesStandby"]
    )
    phx_obj.params.room_temp = optional_float(_data["PH_Parameters"]["TankRoomTemp"])
    phx_obj.params.water_temp = optional_float(
        _data["PH_Parameters"]["TypicalStorageWaterTemperature"]
    )
    return phx_obj


def _PhxDevice_Photovoltaic(_data: Dict[str, Any]) -> PhxDevicePhotovoltaic:
    phx_obj = PhxDevicePhotovoltaic()
    phx_obj.params.location_type = int(_data["PH_Parameters"]["SelectionLocation"])
    phx_obj.params.onsite_utilization_type = int(
        _data["PH_Parameters"]["SelectionOnSiteUtilization"]
    )
    phx_obj.params.utilization_type = int(_data["PH_Parameters"]["SelectionUtilization"])
    phx_obj.params.array_size = float(_data["PH_Parameters"]["ArraySizePV"])
    phx_obj.params.photovoltaic_renewable_energy = float(
        _data["PH_Parameters"]["PhotovoltaicRenewableEnergy"]
    )
    phx_obj.params.onsite_utilization_factor = float(
        _data["PH_Parameters"]["OnsiteUtilization"]
    )
    phx_obj.params.auxiliary_energy = float(_data["PH_Parameters"]["AuxiliaryEnergy"])
    phx_obj.params.auxiliary_energy_DHW = float(
        _data["PH_Parameters"]["AuxiliaryEnergyDHW"]
    )
    phx_obj.params.in_conditioned_space = str_bool(
        _data["PH_Parameters"]["InConditionedSpace"]
    )

    return phx_obj


# ----------------------------------------------------------------------
# -- Exhause Ventilators


def _PhxExhaustVent(_data: Dict[str, Any]) -> AnyPhxExhaustVent:
    exhaust_vent_builders = {
        hvac_enums.PhxExhaustVentType.KITCHEN_HOOD: "PhxExhaustVent_KitchenHood",
        hvac_enums.PhxExhaustVentType.DRYER: "PhxExhaustVent_Dryer",
        hvac_enums.PhxExhaustVentType.USER_DEFINED: "PhxExhaustVent_UserDefined",
    }
    vent_type = hvac_enums.PhxExhaustVentType(int(_data["Type"]))
    return as_phx_obj(_data, exhaust_vent_builders[vent_type])


def _PhxExhaustVent_KitchenHood(_data: Dict[str, Any]) -> PhxExhaustVentilatorRangeHood:
    phx_obj = PhxExhaustVentilatorRangeHood()
    phx_obj.params.annual_runtime_minutes = float(_data["ExhaustVolumeFlowRate"])
    phx_obj.params.exhaust_flow_rate_m3h = float(_data["RunTimePerYear"])
    return phx_obj


def _PhxExhaustVent_Dryer(_data: Dict[str, Any]):
    phx_obj = PhxExhaustVentilatorDryer()
    phx_obj.params.annual_runtime_minutes = float(_data["ExhaustVolumeFlowRate"])
    phx_obj.params.exhaust_flow_rate_m3h = float(_data["RunTimePerYear"])
    return phx_obj


def _PhxExhaustVent_UserDefined(_data: Dict[str, Any]):
    phx_obj = PhxExhaustVentilatorUserDefined()
    phx_obj.params.annual_runtime_minutes = float(_data["ExhaustVolumeFlowRate"])
    phx_obj.params.exhaust_flow_rate_m3h = float(_data["RunTimePerYear"])
    return phx_obj


# ----------------------------------------------------------------------
# -- Electrical Devices


def _PhxHomeDevice(_data: Dict[str, Any]) -> PhxElectricalDevice:
    device_builders = {
        ElectricEquipmentType.DISHWASHER: "PhxDeviceDishwasher",
        ElectricEquipmentType.CLOTHES_WASHER: "PhxDeviceClothesWasher",
        ElectricEquipmentType.CLOTHES_DRYER: "PhxDeviceClothesDryer",
        ElectricEquipmentType.REFRIGERATOR: "PhxDeviceRefrigerator",
        ElectricEquipmentType.FREEZER: "PhxDeviceFreezer",
        ElectricEquipmentType.FRIDGE_FREEZER: "PhxDeviceFridgeFreezer",
        ElectricEquipmentType.COOKING: "PhxDeviceCooktop",
        ElectricEquipmentType.CUSTOM: "PhxDeviceCustomElec",
        ElectricEquipmentType.MEL: "PhxDeviceMEL",
        ElectricEquipmentType.LIGHTING_INTERIOR: "PhxDeviceLightingInterior",
        ElectricEquipmentType.LIGHTING_EXTERIOR: "PhxDeviceLightingExterior",
        ElectricEquipmentType.LIGHTING_GARAGE: "PhxDeviceLightingGarage",
        ElectricEquipmentType.CUSTOM_LIGHTING: "PhxDeviceCustomLighting",
        ElectricEquipmentType.CUSTOM_MEL: "PhxDeviceCustomMEL",
    }
    device_type = ElectricEquipmentType(int(_data["Type"]))
    phx_obj: PhxElectricalDevice = as_phx_obj(_data, device_builders[device_type])

    # -- Set all the common parameters
    phx_obj.comment = _data["Comment"]
    phx_obj.reference_quantity = int(_data["ReferenceQuantity"])
    phx_obj.quantity = int(_data["Quantity"])
    phx_obj.in_conditioned_space = str_bool(_data["InConditionedSpace"])
    phx_obj.reference_energy_norm = int(_data["ReferenceEnergyDemandNorm"])
    phx_obj.energy_demand = float(_data["EnergyDemandNorm"])
    phx_obj.energy_demand_per_use = float(_data["EnergyDemandNormUse"])
    phx_obj.combined_energy_factor = float(_data["CEF_CombinedEnergyFactor"])

    return phx_obj


def _PhxDeviceDishwasher(_data: Dict[str, Any]) -> PhxDeviceDishwasher:
    phx_obj = PhxDeviceDishwasher()
    phx_obj.water_connection = int(_data["Connection"])
    phx_obj.capacity_type = int(_data["DishwasherCapacityPreselection"])
    phx_obj.capacity = float(_data["DishwasherCapacityInPlace"])
    return phx_obj


def _PhxDeviceClothesWasher(_data: Dict[str, Any]) -> PhxDeviceClothesWasher:
    phx_obj = PhxDeviceClothesWasher()
    phx_obj.water_connection = int(_data["Connection"])
    phx_obj.utilization_factor = float(_data["UtilizationFactor"])
    phx_obj.capacity = float(_data["CapacityClothesWasher"])
    phx_obj.modified_energy_factor = float(_data["MEF_ModifiedEnergyFactor"])
    return phx_obj


def _PhxDeviceClothesDryer(_data: Dict[str, Any]) -> PhxDeviceClothesDryer:
    phx_obj = PhxDeviceClothesDryer()
    phx_obj.dryer_type = int(_data["Dryer_Choice"])
    phx_obj.gas_consumption = float(_data["GasConsumption"])
    phx_obj.gas_efficiency_factor = float(_data["EfficiencyFactorGas"])
    phx_obj.field_utilization_factor_type = int(
        _data["FieldUtilizationFactorPreselection"]
    )
    phx_obj.field_utilization_factor = float(_data["FieldUtilizationFactor"])
    return phx_obj


def _PhxDeviceRefrigerator(_data: Dict[str, Any]) -> PhxDeviceRefrigerator:
    phx_obj = PhxDeviceRefrigerator()
    return phx_obj


def _PhxDeviceFreezer(_data: Dict[str, Any]) -> PhxDeviceFreezer:
    phx_obj = PhxDeviceFreezer()
    return phx_obj


def _PhxDeviceFridgeFreezer(_data: Dict[str, Any]) -> PhxDeviceFridgeFreezer:
    phx_obj = PhxDeviceFridgeFreezer()
    return phx_obj


def _PhxDeviceCooktop(_data: Dict[str, Any]) -> PhxDeviceCooktop:
    phx_obj = PhxDeviceCooktop()
    phx_obj.cooktop_type = int(_data["CookingWith"])
    return phx_obj


def _PhxDeviceCustomElec(_data: Dict[str, Any]) -> PhxDeviceCustomElec:
    phx_obj = PhxDeviceCustomElec()
    return phx_obj


def _PhxDeviceMEL(_data: Dict[str, Any]) -> PhxDeviceMEL:
    phx_obj = PhxDeviceMEL()
    return phx_obj


def _PhxDeviceLightingInterior(_data: Dict[str, Any]) -> PhxDeviceLightingInterior:
    phx_obj = PhxDeviceLightingInterior()
    phx_obj.frac_high_efficiency = float(_data["FractionHightEfficiency"])
    return phx_obj


def _PhxDeviceLightingExterior(_data: Dict[str, Any]) -> PhxDeviceLightingExterior:
    phx_obj = PhxDeviceLightingExterior()
    phx_obj.frac_high_efficiency = float(_data["FractionHightEfficiency"])
    return phx_obj


def _PhxDeviceLightingGarage(_data: Dict[str, Any]) -> PhxDeviceLightingGarage:
    phx_obj = PhxDeviceLightingGarage()
    phx_obj.frac_high_efficiency = float(_data["FractionHightEfficiency"])
    return phx_obj


def _PhxDeviceCustomLighting(_data: Dict[str, Any]) -> PhxDeviceCustomLighting:
    phx_obj = PhxDeviceCustomLighting()

    return phx_obj


def _PhxDeviceCustomMEL(_data: Dict[str, Any]) -> PhxDeviceCustomMEL:
    phx_obj = PhxDeviceCustomMEL()

    return phx_obj
