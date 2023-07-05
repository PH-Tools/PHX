# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

from dataclasses import asdict
from rich import print
from typing import Any, Dict, List, Optional, Tuple
import sys

from PHX.from_WUFI_XML import wufi_file_schema as wufi_xml

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
from PHX.model.enums.foundations import (
    FoundationType,
    CalculationSetting,
    PerimeterInsulationPosition,
)
from PHX.model.ground import (
    PhxFoundation,
    PhxHeatedBasement,
    PhxUnHeatedBasement,
    PhxSlabOnGrade,
    PhxVentedCrawlspace,
)
from PHX.model.spaces import PhxSpace
from PHX.model.shades import PhxWindowShade
from PHX.model.schedules.ventilation import (
    PhxScheduleVentilation,
    Vent_UtilPeriods,
    Vent_OperatingPeriod,
)
from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from PHX.model.schedules.lighting import PhxScheduleLighting
from PHX.model.phx_site import (
    PhxSite,
    PhxClimate,
    PhxGround,
    PhxSiteEnergyFactors,
    PhxPEFactor,
    PhxCO2Factor,
)
from PHX.model.project import (
    PhxProject,
    PhxProjectData,
    ProjectData_Agent,
    PhxVariant,
    WufiPlugin,
)
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
# -- Conversion Function


def as_phx_obj(_model, _schema_name, **kwargs) -> Any:
    """Find the right class-builder from the module and pass along the data to it.

    Args:
        _model (Any): The Pydantic (BaseModel) item to be converted.
        _schema_name ([type]): The name of the class-builder to be used.
        kwargs: Any additional arguments to be passed to the class-builder.
    Returns:
        A new PHX object built from the input data
    """
    builder = getattr(sys.modules[__name__], f"_{_schema_name}")
    return builder(_model, **kwargs)


# ----------------------------------------------------------------------
# -- Project


def _PhxProject(_model: wufi_xml.WUFIplusProject) -> PhxProject:
    phx_obj = PhxProject()
    phx_obj.data_version = _model.DataVersion
    phx_obj.unit_system = _model.UnitSystem
    phx_obj.program_version = _model.ProgramVersion
    phx_obj.scope = _model.Scope
    phx_obj.visualized_geometry = _model.DimensionsVisualizedGeometry

    phx_obj.project_data = as_phx_obj(_model.ProjectData, "PhxProjectData")

    # ----------------------------------------------------------------------
    # -- Build all the type collections first
    for window_type_data in _model.WindowTypes:
        new_window = as_phx_obj(window_type_data, "PhxConstructionWindow")
        # -- Be sure to use the identifier as the key so the Component
        # -- lookup works properly. We don't use the name here since
        # -- wufi doesn't enforce unique names like HB does.
        phx_obj.add_new_window_type(new_window, _key=new_window.identifier)

    for assembly_data in _model.Assemblies:
        new_opaque: PhxConstructionOpaque = as_phx_obj(
            assembly_data, "PhxConstructionOpaque"
        )
        # -- Be sure to use the identifier as the key so the Component
        # -- lookup works properly. We don't use the name here since
        # -- wufi doesn't enforce unique names like HB does.
        phx_obj.add_assembly_type(new_opaque, _key=new_opaque.identifier)

    for shade_type_data in _model.SolarProtectionTypes or []:
        new_shade: PhxWindowShade = as_phx_obj(shade_type_data, "PhxWindowShade")
        # -- Be sure to use the identifier as the key so the Component
        # -- lookup works properly. We don't use the name here since
        # -- wufi doesn't enforce unique names like HB does.
        phx_obj.add_new_shade_type(new_shade, _key=new_shade.identifier)

    for vent_pattern_data in _model.UtilisationPatternsVentilation:
        new_pattern = as_phx_obj(vent_pattern_data, "PhxScheduleVentilation")
        phx_obj.utilization_patterns_ventilation.add_new_util_pattern(new_pattern)

    for vent_pattern_data in _model.UtilizationPatternsPH:
        new_pattern = as_phx_obj(vent_pattern_data, "PhxScheduleOccupancy")
        phx_obj.utilization_patterns_occupancy.add_new_util_pattern(new_pattern)

    # ----------------------------------------------------------------------
    # -- Build all the actual Variants
    for variant_dict in _model.Variants:
        new_variant = as_phx_obj(variant_dict, "PhxVariant", _phx_project_host=phx_obj)
        phx_obj.add_new_variant(new_variant)

    return phx_obj


def _PhxProjectData(_model: wufi_xml.ProjectData) -> PhxProjectData:
    phx_obj = PhxProjectData()
    # phx_obj.project_date = _model.Date_Project
    phx_obj.owner_is_client = _model.OwnerIsClient
    phx_obj.year_constructed = int(_model.Year_Construction)
    phx_obj.image = _model.WhiteBackgroundPictureBuilding

    phx_obj.customer = ProjectData_Agent(
        _model.Customer_Name,
        _model.Customer_Street,
        _model.Customer_Locality,
        _model.Customer_PostalCode,
        _model.Customer_Tel,
        _model.Customer_Email,
    )
    phx_obj.building = ProjectData_Agent(
        _model.Building_Name,
        _model.Building_Street,
        _model.Building_Locality,
        _model.Building_PostalCode,
    )
    phx_obj.owner = ProjectData_Agent(
        _model.Owner_Name,
        _model.Owner_Street,
        _model.Owner_Locality,
        _model.Owner_PostalCode,
    )
    phx_obj.designer = ProjectData_Agent(
        _model.Responsible_Name,
        _model.Responsible_Street,
        _model.Responsible_Locality,
        _model.Responsible_PostalCode,
        _model.Responsible_Tel,
        _model.Responsible_LicenseNr,
        _model.Responsible_Email,
    )

    return phx_obj


# ----------------------------------------------------------------------
# -- Envelope Types


def _PhxConstructionWindow(_t: wufi_xml.WindowType) -> PhxConstructionWindow:
    phx_obj = PhxConstructionWindow()
    phx_obj.id_num = _t.IdentNr
    phx_obj.identifier = str(_t.IdentNr)
    phx_obj.display_name = _t.Name
    phx_obj.use_detailed_uw = _t.Uw_Detailed
    phx_obj.use_detailed_frame = _t.GlazingFrameDetailed

    phx_obj.u_value_window = _t.U_Value
    phx_obj.u_value_glass = _t.U_Value_Glazing
    phx_obj.u_value_frame = _t.U_Value_Frame

    phx_obj.glass_mean_emissivity = _t.MeanEmissivity
    phx_obj.glass_g_value = _t.g_Value

    phx_obj.frame_top = PhxWindowFrameElement(
        float(_t.Frame_Width_Top),
        float(_t.Frame_U_Top),
        float(_t.Glazing_Psi_Top),
        float(_t.Frame_Psi_Top),
    )
    phx_obj.frame_right = PhxWindowFrameElement(
        float(_t.Frame_Width_Right),
        float(_t.Frame_U_Right),
        float(_t.Glazing_Psi_Right),
        float(_t.Frame_Psi_Right),
    )
    phx_obj.frame_bottom = PhxWindowFrameElement(
        float(_t.Frame_Width_Bottom),
        float(_t.Frame_U_Bottom),
        float(_t.Glazing_Psi_Bottom),
        float(_t.Frame_Psi_Bottom),
    )
    phx_obj.frame_left = PhxWindowFrameElement(
        float(_t.Frame_Width_Left),
        float(_t.Frame_U_Left),
        float(_t.Glazing_Psi_Left),
        float(_t.Frame_Psi_Left),
    )

    return phx_obj


def _PhxConstructionOpaque(_data: wufi_xml.Assembly) -> PhxConstructionOpaque:
    phx_obj = PhxConstructionOpaque()
    phx_obj.id_num = _data.IdentNr
    phx_obj.identifier = str(_data.IdentNr)
    phx_obj.display_name = _data.Name
    phx_obj.layer_order = _data.Order_Layers
    phx_obj.grid_kind = _data.Grid_Kind
    for layer in _data.Layers:
        new_layer = as_phx_obj(layer, "PhxLayer")
        phx_obj.layers.append(new_layer)

    return phx_obj


def _PhxLayer(_data: wufi_xml.Layer) -> PhxLayer:
    phx_obj = PhxLayer()
    phx_obj.thickness_m = _data.Thickness
    new_mat = as_phx_obj(_data.Material, "PhxMaterial")
    phx_obj.add_material(new_mat)

    return phx_obj


def _PhxMaterial(_data: wufi_xml.Material) -> PhxMaterial:
    phx_obj = PhxMaterial()
    phx_obj.display_name = _data.Name
    phx_obj.conductivity = _data.ThermalConductivity
    phx_obj.density = _data.BulkDensity
    phx_obj.porosity = _data.Porosity
    phx_obj.heat_capacity = _data.HeatCapacity
    phx_obj.water_vapor_resistance = _data.WaterVaporResistance
    phx_obj.reference_water = _data.ReferenceWaterContent
    return phx_obj


def _PhxWindowShade(_data: wufi_xml.SolarProtectionType) -> PhxWindowShade:
    phx_obj = PhxWindowShade()
    phx_obj.id_num = _data.IdentNr
    phx_obj.identifier = str(_data.IdentNr)
    phx_obj.display_name = _data.Name
    phx_obj.operation_mode = _data.OperationMode
    phx_obj.reduction_factor = _data.MaxRedFactorRadiation or 1.0
    return phx_obj


# ----------------------------------------------------------------------
# -- Utilization Patterns


def _PhxScheduleVentilation(
    _data: wufi_xml.UtilizationPatternVent,
) -> PhxScheduleVentilation:
    phx_obj = PhxScheduleVentilation()

    phx_obj.id_num = _data.IdentNr
    phx_obj.name = _data.Name
    phx_obj.identifier = str(_data.IdentNr)
    phx_obj.operating_days = _data.OperatingDays
    phx_obj.operating_weeks = _data.OperatingWeeks
    phx_obj.operating_periods.high.period_operating_hours = _data.Maximum_DOS
    phx_obj.operating_periods.high.period_operation_speed = _data.Maximum_PDF
    phx_obj.operating_periods.standard.period_operating_hours = _data.Standard_DOS
    phx_obj.operating_periods.standard.period_operation_speed = _data.Standard_PDF
    phx_obj.operating_periods.basic.period_operating_hours = _data.Basic_DOS
    phx_obj.operating_periods.basic.period_operation_speed = _data.Basic_PDF
    phx_obj.operating_periods.minimum.period_operating_hours = _data.Minimum_DOS
    phx_obj.operating_periods.minimum.period_operation_speed = _data.Minimum_PDF
    return phx_obj


def _PhxScheduleOccupancy(_data: wufi_xml.UtilizationPattern) -> PhxScheduleOccupancy:
    phx_obj = PhxScheduleOccupancy()
    phx_obj.id_num = _data.IdentNr
    phx_obj.identifier = str(_data.IdentNr)
    phx_obj.display_name = _data.Name
    phx_obj.start_hour = _data.BeginUtilization
    phx_obj.end_hour = _data.EndUtilization
    phx_obj.annual_utilization_days = _data.AnnualUtilizationDays
    phx_obj.relative_utilization_factor = _data.RelativeAbsenteeism

    return phx_obj


# ----------------------------------------------------------------------
# -- Variants


def _WufiPlugin(_model: wufi_xml.Plugin) -> WufiPlugin:
    phx_obj = WufiPlugin()
    if not _model:
        return phx_obj

    phx_obj.insert_plugin = bool(_model.InsertPlugIn)
    phx_obj.name_dll = _model.Name_dll
    phx_obj.status_plugin = _model.StatusPlugIn
    return phx_obj


def _PhxVariant(_data: wufi_xml.Variant, _phx_project_host: PhxProject) -> PhxVariant:
    phx_obj = PhxVariant()

    phx_obj.id_num = _data.IdentNr
    phx_obj.name = _data.Name
    phx_obj.remarks = _data.Remarks
    phx_obj.plugin = as_phx_obj(_data.PlugIn, "WufiPlugin")
    phx_obj.phius_cert = as_phx_obj(_data.PassivehouseData, "PhxPhiusCertification")
    phx_obj.site = as_phx_obj(_data.ClimateLocation, "PhxSite")

    phx_obj.building = as_phx_obj(
        (_data.Building, _data.Graphics_3D),
        "PhxBuilding",
        _phx_project_host=_phx_project_host,
    )

    for system_data_dict in _data.HVAC.Systems:
        phx_obj.mech_systems.display_name = system_data_dict.Name
        phx_obj.mech_systems.id_num = system_data_dict.IdentNr
        phx_obj.mech_systems.zone_coverage = as_phx_obj(
            system_data_dict.ZonesCoverage[0], "PhxZoneCoverage"
        )

        for device_data_dict in system_data_dict.Devices:
            new_device = as_phx_obj(device_data_dict, "PhxMechanicalDevice")
            phx_obj.mech_systems.add_new_mech_device(new_device.identifier, new_device)

    return phx_obj


# ----------------------------------------------------------------------
# -- Building & Geometry


def _get_compo_data_by_type(
    _data: List[wufi_xml.Component],
) -> Tuple[List[wufi_xml.Component], List[wufi_xml.Component]]:
    """Helper function to sort the component dictionaries by type.

    Args:
        _data (List[Dict]): The list of component dictionaries.
    Returns:
        Tuple[List[Dict], List[Dict]]: The sorted lists of component dictionaries.
        - [0] = List of opaque component dicts
        - [1] = List of aperture components dicts
    """

    ap_dicts: List[wufi_xml.Component] = []
    opaque_dicts: List[wufi_xml.Component] = []
    for d in _data:
        if ComponentFaceOpacity(d.Type) == ComponentFaceOpacity.TRANSPARENT:
            ap_dicts.append(d)
        else:
            opaque_dicts.append(d)
    return opaque_dicts, ap_dicts


def _PhxBuilding(
    _data: Tuple[wufi_xml.Building, wufi_xml.Graphics_3D],
    _phx_project_host: PhxProject,
) -> PhxBuilding:
    phx_obj = PhxBuilding()

    # ------------------------------------------------------------------
    # -- First, build all the vertices and polygons needed by the Components
    bldg_data, geom_data = _data
    vertix_dict: Dict[int, PhxVertix] = {
        v.IdentNr: as_phx_obj(v, "PhxVertix") for v in geom_data.Vertices
    }
    polygon_dict: Dict[int, PhxPolygon] = {
        v.IdentNr: as_phx_obj(v, "PhxPolygon", _vertix_dict=vertix_dict)
        for v in geom_data.Polygons
    }

    # ------------------------------------------------------------------
    # -- Build the Components
    opaque_compo_dicts, ap_compo_dicts = _get_compo_data_by_type(bldg_data.Components)

    # -- Build all of the Aperture Components first
    aperture_dict: Dict[Tuple[int, ...], PhxComponentAperture] = {}
    for component_dict in ap_compo_dicts:
        ap_component: PhxComponentAperture = as_phx_obj(
            component_dict,
            "PhxComponentAperture",
            _polygons=polygon_dict,
            _window_types=_phx_project_host.window_types,
        )
        aperture_dict[ap_component.polygon_ids_sorted] = ap_component

    # -- Build all of the Opaque Components
    for component_dict in opaque_compo_dicts:
        op_component: PhxComponentOpaque = as_phx_obj(
            component_dict,
            "PhxComponentOpaque",
            _polygons=polygon_dict,
            _assembly_types=_phx_project_host.assembly_types,
            _aperture_dict=aperture_dict,
        )
        phx_obj.add_component(op_component)

    # ------------------------------------------------------------------
    # -- Build and add the Zones
    for zone_data_dict in bldg_data.Zones:
        new_zone = as_phx_obj(
            zone_data_dict, "PhxZone", _phx_project_host=_phx_project_host
        )
        phx_obj.add_zone(new_zone)

    return phx_obj


def _PhxVertix(_data: wufi_xml.Vertix) -> PhxVertix:
    phx_obj = PhxVertix()
    phx_obj.id_num = _data.IdentNr
    phx_obj.x = _data.X
    phx_obj.y = _data.Y
    phx_obj.z = _data.Z
    return phx_obj


def _PhxPolygon(
    _data: wufi_xml.Polygon, _vertix_dict: Dict[int, PhxVertix] = {}
) -> PhxPolygon:
    surface_normal = PhxVector(
        float(_data.NormalVectorX),
        float(_data.NormalVectorY),
        float(_data.NormalVectorZ),
    )

    # ----------------------------------------------------------------------
    plane = PhxPlane(
        normal_vector=surface_normal,
        origin=PhxVertix(0, 0, 0),  # temp. value
        x=PhxVector(0, 0, 0),  # temp. value
        y=PhxVector(0, 0, 0),  # temp. value
    )
    # ----------------------------------------------------------------------

    phx_obj = PhxPolygon(
        _display_name=str(_data.IdentNr),
        _area=None,
        _center=None,
        normal_vector=plane.normal_vector,
        plane=plane,
    )
    phx_obj.id_num = _data.IdentNr
    phx_obj._vertices = [_vertix_dict[_.IdentNr] for _ in _data.IdentNrPoints]
    if _data.IdentNrPolygonsInside:
        for _ in _data.IdentNrPolygonsInside:
            phx_obj.child_polygon_ids.append(_.IdentNr)

    # -- Figure out the Polygon Plane's x, y, and origin values based on the vertices
    phx_obj.plane.origin = phx_obj.vertices[0]
    phx_obj.plane.x = PhxVector.from_2_points(phx_obj.vertices[0], phx_obj.vertices[1])
    phx_obj.plane.y = phx_obj.plane.x.rotate_around(phx_obj.plane.normal_vector, 90)

    # -- Make sure to do this, otherwise area won't work properly.
    phx_obj.plane.x.unitize()
    phx_obj.plane.y.unitize()

    return phx_obj


def _PhxComponentAperture(
    _data: wufi_xml.Component,
    _polygons: Dict[int, PhxPolygon],
    _window_types: Dict[str, PhxConstructionWindow],
) -> PhxComponentAperture:
    phx_obj = PhxComponentAperture(_host=None)  # type: ignore

    phx_obj.display_name = _data.Name
    phx_obj.face_type = ComponentFaceType.WINDOW
    phx_obj.face_opacity = ComponentFaceOpacity(_data.Type)
    phx_obj.color_interior = ComponentColor(_data.IdentNrColorI)
    phx_obj.color_exterior = ComponentColor(_data.IdentNrColorE)
    phx_obj.exposure_interior = _data.InnerAttachment
    phx_obj.exposure_exterior = ComponentExposureExterior(_data.OuterAttachment)

    if _data.IdentNr_ComponentInnerSurface:
        phx_obj.interior_attachment_id = _data.IdentNr_ComponentInnerSurface

    if _data.IdentNrWindowType:
        phx_obj.window_type = _window_types[str(_data.IdentNrWindowType)]
        phx_obj.window_type.id_num_shade = _data.IdentNrSolarProtection

    phx_obj.install_depth = _data.DepthWindowReveal
    phx_obj.default_monthly_shading_correction_factor = (
        _data.DefaultCorrectionShadingMonth
    )

    for i, poly_id in enumerate(_data.IdentNrPolygons):
        polygon = _polygons[poly_id.IdentNr]
        new_ap_element = PhxApertureElement(_host=phx_obj)
        new_ap_element.display_name = f"{phx_obj.display_name} - {i}"
        new_ap_element.polygon = polygon  # TODO: make a to_rect method for polygons....
        phx_obj.add_element(new_ap_element)

    return phx_obj


def _PhxComponentOpaque(
    _data: wufi_xml.Component,
    _polygons: Dict[int, PhxPolygon],
    _assembly_types: Dict[str, PhxConstructionOpaque],
    _aperture_dict: Dict[Tuple[int, ...], PhxComponentAperture],
) -> PhxComponentOpaque:
    # -- Build either an opaque or transparent component
    phx_obj = PhxComponentOpaque()

    phx_obj._id_num = _data.IdentNr
    phx_obj.display_name = _data.Name
    phx_obj.face_opacity = ComponentFaceOpacity(_data.Type)
    phx_obj.color_interior = ComponentColor(_data.IdentNrColorI)
    phx_obj.color_exterior = ComponentColor(_data.IdentNrColorE)
    phx_obj.exposure_interior = _data.InnerAttachment
    phx_obj.exposure_exterior = ComponentExposureExterior(_data.OuterAttachment)

    if _data.IdentNr_ComponentInnerSurface:
        phx_obj.interior_attachment_id = _data.IdentNr_ComponentInnerSurface

    phx_obj.add_polygons([_polygons[i.IdentNr] for i in _data.IdentNrPolygons])
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

    if _data.IdentNrAssembly:
        phx_obj.assembly_type_id_num = _data.IdentNrAssembly
        if phx_obj.assembly_type_id_num != -1:
            # -- -1 indicates a shade component without an assembly type
            phx_obj.assembly = _assembly_types[str(_data.IdentNrAssembly)]

    return phx_obj


def _PhxComponentThermalBridge(
    _data: wufi_xml.ThermalBridge,
) -> PhxComponentThermalBridge:
    phx_obj = PhxComponentThermalBridge()

    phx_obj.quantity = 1.0
    phx_obj.display_name = _data.Name
    phx_obj.group_number = ThermalBridgeType(_data.Type * -1)
    phx_obj.length = _data.Length
    phx_obj.psi_value = _data.PsiValue

    return phx_obj


# ----------------------------------------------------------------------
# -- Foundations


def _PhxHeatedBasement(_data: wufi_xml.FoundationInterface) -> PhxHeatedBasement:
    phx_obj = PhxHeatedBasement()
    phx_obj.display_name = _data.Name
    phx_obj.foundation_type_num = _data.FloorSlabType

    phx_obj.floor_slab_area_m2 = _data.FloorSlabArea
    phx_obj.floor_slab_exposed_perimeter_m = _data.FloorSlabPerimeter
    phx_obj.floor_slab_u_value = _data.U_ValueBasementSlab
    phx_obj.slab_depth_below_grade_m = _data.DepthBasementBelowGroundSurface
    phx_obj.basement_wall_u_value = _data.U_ValueBasementWall
    return phx_obj


def _PhxUnHeatedBasement(_data: wufi_xml.FoundationInterface) -> PhxUnHeatedBasement:
    phx_obj = PhxUnHeatedBasement()
    phx_obj.display_name = _data.Name
    phx_obj.foundation_type_num = _data.FloorSlabType

    phx_obj.slab_depth_below_grade_m = _data.DepthBasementBelowGroundSurface
    phx_obj.basement_wall_height_above_grade_m = _data.HeightBasementWallAboveGrade
    phx_obj.floor_ceiling_area_m2 = _data.FloorSlabArea
    phx_obj.floor_slab_u_value = _data.U_ValueBasementSlab
    phx_obj.floor_ceiling_area_m2 = _data.FloorCeilingArea
    phx_obj.ceiling_u_value = _data.U_ValueCeilingToUnheatedCellar
    phx_obj.basement_wall_uValue_below_grade = _data.U_ValueBasementWall
    phx_obj.basement_wall_uValue_above_grade = _data.U_ValueWallAboveGround
    phx_obj.floor_slab_exposed_perimeter_m = _data.FloorSlabPerimeter
    phx_obj.basement_volume_m3 = _data.BasementVolume
    return phx_obj


def _PhxSlabOnGrade(_data: wufi_xml.FoundationInterface) -> PhxSlabOnGrade:
    phx_obj = PhxSlabOnGrade()
    phx_obj.display_name = _data.Name
    phx_obj.foundation_type_num = _data.FloorSlabType

    phx_obj.floor_slab_area_m2 = _data.FloorSlabArea
    phx_obj.floor_slab_u_value = _data.U_ValueBasementSlab
    phx_obj.floor_slab_exposed_perimeter_m = _data.FloorSlabPerimeter
    phx_obj.perim_insulation_position = _data.PositionPerimeterInsulation
    phx_obj.perim_insulation_width_or_depth_m = _data.PerimeterInsulationWidthDepth
    phx_obj.perim_insulation_thickness_m = _data.ThicknessPerimeterInsulation
    phx_obj.perim_insulation_conductivity = _data.ConductivityPerimeterInsulation
    return phx_obj


def _PhxVentedCrawlspace(_data: wufi_xml.FoundationInterface) -> PhxVentedCrawlspace:
    phx_obj = PhxVentedCrawlspace()
    phx_obj.display_name = _data.Name
    phx_obj.foundation_type_num = _data.FloorSlabType

    phx_obj.crawlspace_floor_slab_area_m2 = _data.FloorCeilingArea
    phx_obj.ceiling_above_crawlspace_u_value = _data.U_ValueCeilingToUnheatedCellar
    phx_obj.crawlspace_floor_exposed_perimeter_m = _data.FloorSlabPerimeter
    phx_obj.crawlspace_wall_height_above_grade_m = _data.HeightBasementWallAboveGrade
    phx_obj.crawlspace_floor_u_value = _data.U_ValueCrawlspaceFloor
    phx_obj.crawlspace_vent_opening_are_m2 = _data.CrawlspaceVentOpenings
    phx_obj.crawlspace_wall_u_value = _data.U_ValueWallAboveGround
    return phx_obj


def _PhxFoundation(_data: wufi_xml.FoundationInterface) -> PhxFoundation:
    foundation_type_builders = {
        FoundationType.HEATED_BASEMENT: "PhxHeatedBasement",
        FoundationType.UNHEATED_BASEMENT: "PhxUnHeatedBasement",
        FoundationType.SLAB_ON_GRADE: "PhxSlabOnGrade",
        FoundationType.VENTED_CRAWLSPACE: "PhxVentedCrawlspace",
    }

    device_type = FoundationType(_data.FloorSlabType)
    builder_class = foundation_type_builders[device_type]

    # -- Pass the data off to the correct foundation builder class
    return as_phx_obj(_data, builder_class)


# ----------------------------------------------------------------------
# -- Site & Climate


def _PhxPhiusCertification(_data: wufi_xml.PassivehouseData) -> PhxPhiusCertification:
    phx_obj = PhxPhiusCertification()
    phx_obj.use_monthly_shading = _data.UseWUFIMeanMonthShading

    # no idea why PH_BuildingData is a list?....
    bldg_data = _data.PH_Buildings[0]
    phx_obj.ph_building_data = as_phx_obj(bldg_data, "PhxPhBuildingData")

    # ----------------------------------------------------------------------
    # --- Certification Criteria
    criteria = phx_obj.phius_certification_criteria
    criteria.ph_selection_target_data = _data.PH_SelectionTargetData
    criteria.phius_annual_heating_demand = _data.AnnualHeatingDemand
    criteria.phius_annual_cooling_demand = _data.AnnualCoolingDemand
    criteria.phius_peak_heating_load = _data.PeakHeatingLoad
    criteria.phius_peak_cooling_load = _data.PeakCoolingLoad

    # ----------------------------------------------------------------------
    # --- Certification Settings
    settings = phx_obj.phius_certification_settings
    settings.phius_building_certification_program = PhiusCertificationProgram(
        _data.PH_CertificateCriteria
    )
    settings.phius_building_category_type = PhiusCertificationBuildingCategoryType(
        bldg_data.BuildingCategory
    )
    if bldg_data.OccupancyTypeResidential:
        settings.phius_building_use_type = PhiusCertificationBuildingUseType(
            bldg_data.OccupancyTypeResidential
        )
    settings.phius_building_status = PhiusCertificationBuildingStatus(
        bldg_data.BuildingStatus
    )
    settings.phius_building_type = PhiusCertificationBuildingType(bldg_data.BuildingType)

    return phx_obj


def _PhxPhBuildingData(_data: wufi_xml.PH_Building) -> PhxPhBuildingData:
    phx_obj = PhxPhBuildingData()
    phx_obj.id_num = _data.IdentNr
    phx_obj.num_of_units = _data.NumberUnits
    phx_obj.num_of_floors = _data.CountStories
    phx_obj.occupancy_setting_method = _data.OccupancySettingMethod
    phx_obj.airtightness_q50 = _data.EnvelopeAirtightnessCoefficient
    phx_obj.setpoints.winter = _data.IndoorTemperature
    phx_obj.setpoints.summer = _data.OverheatingTemperatureThreshold
    phx_obj.mech_room_temp = _data.MechanicalRoomTemperature
    phx_obj.non_combustible_materials = _data.NonCombustibleMaterials
    phx_obj.summer_hrv_bypass_mode = hvac_enums.PhxSummerBypassMode(
        _data.SummerHRVHumidityRecovery
    )

    for foundation_data in _data.FoundationInterfaces or []:
        phx_obj.add_foundation(as_phx_obj(foundation_data, "PhxFoundation"))

    return phx_obj


def _PhxSite(_data: wufi_xml.ClimateLocation) -> PhxSite:
    phx_obj = PhxSite()
    phx_obj.selection = SiteSelection(_data.Selection)

    ph_climate_data = _data.PH_ClimateLocation
    if ph_climate_data:
        phx_obj.location.latitude = ph_climate_data.Latitude
        phx_obj.location.longitude = ph_climate_data.Longitude
        phx_obj.location.hours_from_UTC = ph_climate_data.dUTC
        phx_obj.location.site_elevation = ph_climate_data.HeightNNBuilding
        phx_obj.location.climate_zone = ph_climate_data.ClimateZone

    phx_obj.climate = as_phx_obj(ph_climate_data, "PhxClimate")
    phx_obj.ground = as_phx_obj(ph_climate_data, "PhxGround")
    phx_obj.energy_factors = as_phx_obj(ph_climate_data, "PhxSiteEnergyFactors")

    return phx_obj


def _PhxClimate(_data: wufi_xml.PH_ClimateLocation) -> PhxClimate:
    def _monthly_values(_in) -> List[float]:
        values = []
        for i in range(12):
            try:
                val = round(getattr(_in[i], "Item", 0.0), 2)
            except IndexError:
                val = 0.0
            values.append(val)
        return values

    phx_obj = PhxClimate()

    phx_obj.station_elevation = _data.HeightNNWeatherStation
    phx_obj.selection = SiteClimateSelection(_data.Selection)
    phx_obj.daily_temp_swing = _data.DailyTemperatureSwingSummer
    phx_obj.avg_wind_speed = _data.AverageWindSpeed

    phx_obj.temperature_air = _monthly_values(_data.TemperatureMonthly)
    phx_obj.temperature_dewpoint = _monthly_values(_data.DewPointTemperatureMonthly)
    phx_obj.temperature_sky = _monthly_values(_data.SkyTemperatureMonthly)
    phx_obj.radiation_north = _monthly_values(_data.NorthSolarRadiationMonthly)
    phx_obj.radiation_east = _monthly_values(_data.EastSolarRadiationMonthly)
    phx_obj.radiation_south = _monthly_values(_data.SouthSolarRadiationMonthly)
    phx_obj.radiation_west = _monthly_values(_data.WestSolarRadiationMonthly)
    phx_obj.radiation_global = _monthly_values(_data.GlobalSolarRadiationMonthly)

    phx_obj.peak_heating_1.temperature_air = _data.TemperatureHeating1
    phx_obj.peak_heating_1.radiation_north = _data.NorthSolarRadiationHeating1
    phx_obj.peak_heating_1.radiation_east = _data.EastSolarRadiationHeating1
    phx_obj.peak_heating_1.radiation_south = _data.SouthSolarRadiationHeating1
    phx_obj.peak_heating_1.radiation_west = _data.WestSolarRadiationHeating1
    phx_obj.peak_heating_1.radiation_global = _data.GlobalSolarRadiationHeating1

    phx_obj.peak_heating_2.temperature_air = _data.TemperatureHeating2
    phx_obj.peak_heating_2.radiation_north = _data.NorthSolarRadiationHeating2
    phx_obj.peak_heating_2.radiation_east = _data.EastSolarRadiationHeating2
    phx_obj.peak_heating_2.radiation_south = _data.SouthSolarRadiationHeating2
    phx_obj.peak_heating_2.radiation_west = _data.WestSolarRadiationHeating2
    phx_obj.peak_heating_2.radiation_global = _data.GlobalSolarRadiationHeating2

    phx_obj.peak_cooling_1.temperature_air = _data.TemperatureCooling
    phx_obj.peak_cooling_1.radiation_north = _data.NorthSolarRadiationCooling
    phx_obj.peak_cooling_1.radiation_east = _data.EastSolarRadiationCooling
    phx_obj.peak_cooling_1.radiation_south = _data.SouthSolarRadiationCooling
    phx_obj.peak_cooling_1.radiation_west = _data.WestSolarRadiationCooling
    phx_obj.peak_cooling_1.radiation_global = _data.GlobalSolarRadiationCooling

    phx_obj.peak_cooling_2.temperature_air = _data.TemperatureCooling2
    phx_obj.peak_cooling_2.radiation_north = _data.NorthSolarRadiationCooling2
    phx_obj.peak_cooling_2.radiation_east = _data.EastSolarRadiationCooling2
    phx_obj.peak_cooling_2.radiation_south = _data.SouthSolarRadiationCooling2
    phx_obj.peak_cooling_2.radiation_west = _data.WestSolarRadiationCooling2
    phx_obj.peak_cooling_2.radiation_global = _data.GlobalSolarRadiationCooling2

    return phx_obj


def _PhxGround(_data: wufi_xml.PH_ClimateLocation) -> PhxGround:
    phx_obj = PhxGround()
    phx_obj.ground_thermal_conductivity = _data.GroundThermalConductivity
    phx_obj.ground_heat_capacity = _data.GroundHeatCapacitiy
    phx_obj.ground_density = _data.GroundDensity
    phx_obj.depth_groundwater = _data.DepthGroundwater
    phx_obj.flow_rate_groundwater = _data.FlowRateGroundwater
    return phx_obj


def _PhxSiteEnergyFactors(_data: wufi_xml.PH_ClimateLocation) -> PhxSiteEnergyFactors:
    _wufi_order = (
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
    )

    phx_obj = PhxSiteEnergyFactors()
    phx_obj.selection_pe_co2_factor = SiteEnergyFactorSelection(
        _data.SelectionPECO2Factor
    )

    for name, factor in zip(_wufi_order, _data.PEFactorsUserDef):
        phx_obj.pe_factors[name] = PhxPEFactor(factor.__root__, "kWh/kWh", name)

    for name, factor in zip(_wufi_order, _data.CO2FactorsUserDef):
        phx_obj.co2_factors[name] = PhxCO2Factor(factor.__root__, "g/kWh", name)

    return phx_obj


# ----------------------------------------------------------------------
# -- Zones


def _PhxZone(_data: wufi_xml.Zone, _phx_project_host: PhxProject) -> PhxZone:
    def _spec_cap_WH_m2k(_input):
        if _input <= 60.0:
            return 1
        elif _input <= 132.0:
            return 2
        else:
            return 3

    phx_obj = PhxZone()

    phx_obj.id_num = _data.IdentNr
    phx_obj.display_name = _data.Name
    phx_obj.volume_gross = _data.GrossVolume
    phx_obj.volume_net = _data.NetVolume
    phx_obj.weighted_net_floor_area = _data.FloorArea
    phx_obj.clearance_height = _data.ClearanceHeight
    phx_obj.res_occupant_quantity = _data.OccupantQuantityUserDef
    phx_obj.res_number_bedrooms = _data.NumberBedrooms
    phx_obj.specific_heat_capacity = SpecificHeatCapacity(
        _spec_cap_WH_m2k(_data.SpecificHeatCapacity)
    )

    # ----------------------------------------------------------------------
    # -- Create all the spaces from the XML "RoomsVentilation" data
    for space_ventilation_data in _data.RoomsVentilation:
        phx_obj.spaces.append(
            as_phx_obj(
                space_ventilation_data,
                "PhxSpace",
                _phx_project_host=_phx_project_host,
            )
        )

    # -- Try and add in any occupancy, lighting loads to the spaces, if they exist.
    # -- Will try and find a load with a matching name.
    occupancy_load_data = {d.Name: d for d in _data.LoadsPersonsPH or []}
    lighting_load_data = {d.Name: d for d in _data.LoadsLightingsPH or []}
    for space in phx_obj.spaces:
        space = _add_occupancy_data_to_space(
            space, _phx_project_host, occupancy_load_data.get(space.display_name, None)
        )
        space = _add_lighting_data_to_space(
            space, _phx_project_host, lighting_load_data.get(space.display_name, None)
        )

    # ----------------------------------------------------------------------
    # -- Add in any devices and thermal bridges as well.
    for vent_dict_data in _data.ExhaustVents or []:
        new_phx_exhaust = as_phx_obj(vent_dict_data, "PhxExhaustVent")
        phx_obj.exhaust_ventilator_collection.add_new_ventilator(
            new_phx_exhaust.identifier, new_phx_exhaust
        )

    for device_dict_data in _data.HomeDevice or []:
        new_phx_home_device = as_phx_obj(device_dict_data, "PhxHomeDevice")
        phx_obj.elec_equipment_collection.add_new_device(
            new_phx_home_device.identifier, new_phx_home_device
        )

    for i, bridge_dict_data in enumerate(_data.ThermalBridges or []):
        new_phx_tb = as_phx_obj(bridge_dict_data, "PhxComponentThermalBridge")
        new_phx_tb.identifier = f"ThermalBridge_{i :03}"
        phx_obj.add_thermal_bridge(new_phx_tb)

    return phx_obj


def _add_occupancy_data_to_space(
    _space: PhxSpace,
    _phx_project_host: PhxProject,
    _occupancy_data: Optional[wufi_xml.LoadPerson],
) -> PhxSpace:
    """Add occupancy data to a space, if any is supplied."""
    if not _occupancy_data:
        return _space

    project_util_pat_occ = _phx_project_host.utilization_patterns_occupancy
    occ_pattern_id = _occupancy_data.IdentNrUtilizationPattern
    _space.occupancy.schedule = project_util_pat_occ[str(occ_pattern_id)]
    _space.peak_occupancy = _occupancy_data.NumberOccupants

    return _space


def _add_lighting_data_to_space(
    _space: PhxSpace,
    _phx_project_host: PhxProject,
    _lighting_data: Optional[wufi_xml.LoadsLighting],
) -> PhxSpace:
    """Add lighting data to a space, if any is supplied."""
    if not _lighting_data:
        return _space

    # -- Get the right Lighting Utilization Pattern
    project_util_pat_lighting = _phx_project_host.utilization_patterns_lighting
    lighting_pattern_id = _lighting_data.RoomCategory

    # -- Ensure that the lighting pattern is in the project collection. If
    # -- not, create a new one based on the full-load lighting hours.
    if not project_util_pat_lighting.key_is_in_collection(lighting_pattern_id):
        new_schedule = PhxScheduleLighting.from_annual_operating_hours(
            _lighting_data.LightingFullLoadHours
        )
        new_schedule.display_name = _lighting_data.Name
        new_schedule.id_num = int(lighting_pattern_id)
        new_schedule.identifier = str(lighting_pattern_id)
        project_util_pat_lighting.add_new_util_pattern(new_schedule)

    # -- Assign the pattern to the space.
    _space.lighting.schedule = project_util_pat_lighting[str(lighting_pattern_id)]

    # -- Set the lighting load for the space.
    _space.lighting.load.installed_w_per_m2 = _lighting_data.InstalledLightingPower

    return _space


def _PhxSpace(_data: wufi_xml.Room, _phx_project_host: PhxProject) -> PhxSpace:
    phx_obj = PhxSpace()

    # phx_obj.id_num = int(_data."])   phx_obj.display_name = _data.Name
    phx_obj.wufi_type = _data.Type
    phx_obj.quantity = _data.Quantity
    phx_obj.floor_area = _data.AreaRoom
    phx_obj.weighted_floor_area = _data.AreaRoom
    phx_obj.clear_height = _data.ClearRoomHeight

    # -- Ventilation Unit (ERV) number
    phx_obj.vent_unit_id_num = _data.IdentNrVentilationUnit

    # -- Ventilation Schedule and Load
    project_util_pat_ven = _phx_project_host.utilization_patterns_ventilation
    vent_pattern_id = _data.IdentNrUtilizationPatternVent
    phx_obj.ventilation.schedule = project_util_pat_ven[str(vent_pattern_id)]
    phx_obj.ventilation.load.flow_extract = _data.DesignVolumeFlowRateExhaust
    phx_obj.ventilation.load.flow_supply = _data.DesignVolumeFlowRateSupply

    return phx_obj


# ----------------------------------------------------------------------
# -- Mechanicals


def _PhxZoneCoverage(_data: wufi_xml.ZoneCoverage) -> PhxZoneCoverage:
    phx_obj = PhxZoneCoverage()

    phx_obj.zone_num = _data.IdentNrZone
    phx_obj.heating = _data.CoverageHeating
    phx_obj.cooling = _data.CoverageCooling
    phx_obj.ventilation = _data.CoverageVentilation
    phx_obj.humidification = _data.CoverageHumidification
    phx_obj.dehumidification = _data.CoverageDehumidification

    return phx_obj


def _PhxMechanicalDevice(_data: wufi_xml.Device) -> Any:
    device_type_builders = {
        hvac_enums.SystemType.VENTILATION: "PhxDevice_Ventilation",
        hvac_enums.SystemType.ELECTRIC: "PhxDevice_Electric",
        hvac_enums.SystemType.BOILER: "PhxDevice_Boiler",
        hvac_enums.SystemType.DISTRICT_HEAT: "PhxDevice_DistrictHeat",
        hvac_enums.SystemType.HEAT_PUMP: "PhxDevice_HeatPump",
        hvac_enums.SystemType.WATER_STORAGE: "PhxDevice_WaterStorage",
        hvac_enums.SystemType.PHOTOVOLTAIC: "PhxDevice_Photovoltaic",
    }

    device_type = hvac_enums.SystemType(_data.SystemType)
    builder_class = device_type_builders[device_type]

    # -- Pass the data off to the correct device builder class
    return as_phx_obj(_data, builder_class)


def _PhxDevice_Ventilation(_data: wufi_xml.Device) -> PhxDeviceVentilator:
    phx_obj = PhxDeviceVentilator()
    phx_obj.display_name = _data.Name
    phx_obj.id_num = _data.IdentNr
    phx_obj.identifier = str(_data.IdentNr)

    phx_obj.params.sensible_heat_recovery = _data.HeatRecovery
    phx_obj.params.latent_heat_recovery = _data.MoistureRecovery
    if _data.PH_Parameters:
        phx_obj.params.quantity = _data.PH_Parameters.Quantity
        phx_obj.params.electric_efficiency = _data.PH_Parameters.ElectricEfficiency
        phx_obj.params.frost_protection_reqd = _data.PH_Parameters.FrostProtection
        phx_obj.params.temperature_below_defrost_used = (
            _data.PH_Parameters.TemperatureBelowDefrostUsed
        )

    return phx_obj


def _PhxDevice_Electric(_data: wufi_xml.Device) -> PhxHeaterElectric:
    return PhxHeaterElectric()


def _PhxDevice_Boiler(_data: wufi_xml.Device) -> Optional[PhxHeaterBoiler]:
    boiler_builders = {
        hvac_enums.PhxFuelType.NATURAL_GAS: "PhxHeaterBoilerFossil",
        hvac_enums.PhxFuelType.OIL: "PhxHeaterBoilerFossil",
        hvac_enums.PhxFuelType.WOOD_LOG: "PhxHeaterBoilerWood",
        hvac_enums.PhxFuelType.WOOD_PELLET: "PhxHeaterBoilerWood",
    }
    if not _data.PH_Parameters:
        return None

    boiler_type = hvac_enums.PhxFuelType(_data.PH_Parameters.EnergySourceBoilerType)
    return as_phx_obj(_data, boiler_builders[boiler_type])


def _PhxHeaterBoilerFossil(_data: wufi_xml.Device) -> PhxHeaterBoilerFossil:
    phx_obj = PhxHeaterBoilerFossil()
    if not _data.PH_Parameters:
        return phx_obj

    phx_obj.params.fuel = _data.PH_Parameters.EnergySourceBoilerType
    phx_obj.params.condensing = _data.PH_Parameters.CondensingBoiler
    phx_obj.params.in_conditioned_space = _data.PH_Parameters.InConditionedSpace
    phx_obj.params.effic_at_30_percent_load = _data.PH_Parameters.BoilerEfficiency30
    phx_obj.params.effic_at_nominal_load = (
        _data.PH_Parameters.BoilerEfficiencyNominalOutput
    )
    phx_obj.params.avg_rtrn_temp_at_30_percent_load = (
        _data.PH_Parameters.AverageReturnTemperatureMeasured30Load
    )
    phx_obj.params.avg_temp_at_70C_55C = (
        _data.PH_Parameters.AverageBoilerTemperatureDesign70_55
    )
    phx_obj.params.avg_temp_at_55C_45C = (
        _data.PH_Parameters.AverageBoilerTemperatureDesign55_45
    )
    phx_obj.params.avg_temp_at_32C_28C = (
        _data.PH_Parameters.AverageBoilerTemperatureDesign35_28
    )
    phx_obj.params.standby_loss_at_70C = _data.PH_Parameters.StandbyHeatLossBoiler70
    phx_obj.params.rated_capacity = _data.PH_Parameters.MaximalBoilerPower
    return phx_obj


def _PhxHeaterBoilerWood(_data: wufi_xml.Device) -> PhxHeaterBoilerWood:
    phx_obj = PhxHeaterBoilerWood()

    return phx_obj


def _PhxDevice_DistrictHeat(_data: wufi_xml.Device) -> PhxHeaterDistrictHeat:
    return PhxHeaterDistrictHeat()


def _PhxDevice_HeatPump(_data: wufi_xml.Device) -> Optional[PhxHeaterHeatPump]:
    hp_builders = {
        hvac_enums.HeatPumpType.COMBINED: "PhxDevice_HeatPump_Combined",
        hvac_enums.HeatPumpType.ANNUAL: "PhxDevice_HeatPump_Annual",
        hvac_enums.HeatPumpType.RATED_MONTHLY: "PhxDevice_HeatPump_RatedMonthly",
        hvac_enums.HeatPumpType.HOT_WATER: "PhxDevice_HeatPump_HotWater",
    }
    if _data.PH_Parameters and _data.PH_Parameters.HPType:
        hp_type = hvac_enums.HeatPumpType(_data.PH_Parameters.HPType)
        builder_class = hp_builders[hp_type]
        return as_phx_obj(_data, builder_class)
    else:
        return None


def _PhxDevice_HeatPump_Combined(_data: wufi_xml.Device) -> PhxHeaterHeatPumpCombined:
    phx_obj = PhxHeaterHeatPumpCombined()
    return phx_obj


def _PhxDevice_HeatPump_Annual(_data: wufi_xml.Device) -> PhxHeaterHeatPumpAnnual:
    phx_obj = PhxHeaterHeatPumpAnnual()
    if not _data.PH_Parameters:
        return phx_obj

    phx_obj.params.annual_COP = _data.PH_Parameters.AnnualCOP
    phx_obj.params.total_system_perf_ratio = (
        _data.PH_Parameters.TotalSystemPerformanceRatioHeatGenerator
    )
    return phx_obj


def _PhxDevice_HeatPump_RatedMonthly(_data: wufi_xml.Device) -> PhxHeaterHeatPumpMonthly:
    phx_obj = PhxHeaterHeatPumpMonthly()
    if not _data.PH_Parameters:
        return phx_obj

    phx_obj.params.COP_1 = _data.PH_Parameters.RatedCOP1
    phx_obj.params.COP_2 = _data.PH_Parameters.RatedCOP2
    phx_obj.params.ambient_temp_1 = _data.PH_Parameters.AmbientTemperature1
    phx_obj.params.ambient_temp_2 = _data.PH_Parameters.AmbientTemperature2
    return phx_obj


def _PhxDevice_HeatPump_HotWater(_data: wufi_xml.Device) -> PhxHeaterHeatPumpHotWater:
    phx_obj = PhxHeaterHeatPumpHotWater()
    if not _data.PH_Parameters:
        return phx_obj

    phx_obj.params.annual_COP = _data.PH_Parameters.AnnualCOP
    phx_obj.params.annual_system_perf_ratio = (
        _data.PH_Parameters.TotalSystemPerformanceRatioHeatGenerator
    )
    phx_obj.params.annual_energy_factor = _data.PH_Parameters.HPWH_EF
    return phx_obj


def _PhxDevice_WaterStorage(_data: wufi_xml.Device) -> PhxHotWaterTank:
    phx_obj = PhxHotWaterTank()
    if not _data.PH_Parameters:
        return phx_obj

    phx_obj.quantity = _data.PH_Parameters.QauntityWS
    phx_obj.params.display_name = _data.Name
    phx_obj.params.input_option = hvac_enums.PhxHotWaterInputOptions(
        _data.PH_Parameters.InputOption
    )
    phx_obj.params.in_conditioned_space = _data.PH_Parameters.InConditionedSpace
    phx_obj.params.storage_loss_rate = _data.PH_Parameters.AverageHeatReleaseStorage

    phx_obj.params.storage_capacity = _data.PH_Parameters.SolarThermalStorageCapacity
    phx_obj.params.standby_losses = _data.PH_Parameters.StorageLossesStandby
    phx_obj.params.room_temp = _data.PH_Parameters.TankRoomTemp
    phx_obj.params.water_temp = _data.PH_Parameters.TypicalStorageWaterTemperature
    return phx_obj


def _PhxDevice_Photovoltaic(_data: wufi_xml.Device) -> PhxDevicePhotovoltaic:
    phx_obj = PhxDevicePhotovoltaic()
    if not _data.PH_Parameters:
        return phx_obj

    phx_obj.params.location_type = _data.PH_Parameters.SelectionLocation
    phx_obj.params.onsite_utilization_type = (
        _data.PH_Parameters.SelectionOnSiteUtilization
    )

    phx_obj.params.utilization_type = _data.PH_Parameters.SelectionUtilization
    phx_obj.params.array_size = _data.PH_Parameters.ArraySizePV
    phx_obj.params.photovoltaic_renewable_energy = (
        _data.PH_Parameters.PhotovoltaicRenewableEnergy
    )

    phx_obj.params.onsite_utilization_factor = _data.PH_Parameters.OnsiteUtilization
    phx_obj.params.auxiliary_energy = _data.PH_Parameters.AuxiliaryEnergy
    phx_obj.params.auxiliary_energy_DHW = _data.PH_Parameters.AuxiliaryEnergyDHW
    phx_obj.params.in_conditioned_space = _data.PH_Parameters.InConditionedSpace

    return phx_obj


# ----------------------------------------------------------------------
# -- Exhaust Ventilators


def _PhxExhaustVent(_data: wufi_xml.ExhaustVent) -> AnyPhxExhaustVent:
    exhaust_vent_builders = {
        hvac_enums.PhxExhaustVentType.KITCHEN_HOOD: "PhxExhaustVent_KitchenHood",
        hvac_enums.PhxExhaustVentType.DRYER: "PhxExhaustVent_Dryer",
        hvac_enums.PhxExhaustVentType.USER_DEFINED: "PhxExhaustVent_UserDefined",
    }
    vent_type = hvac_enums.PhxExhaustVentType(_data.Type)
    return as_phx_obj(_data, exhaust_vent_builders[vent_type])


def _PhxExhaustVent_KitchenHood(
    _data: wufi_xml.ExhaustVent,
) -> PhxExhaustVentilatorRangeHood:
    phx_obj = PhxExhaustVentilatorRangeHood()
    phx_obj.params.annual_runtime_minutes = _data.RunTimePerYear
    phx_obj.params.exhaust_flow_rate_m3h = _data.ExhaustVolumeFlowRate
    return phx_obj


def _PhxExhaustVent_Dryer(_data: wufi_xml.ExhaustVent) -> PhxExhaustVentilatorDryer:
    phx_obj = PhxExhaustVentilatorDryer()
    phx_obj.params.annual_runtime_minutes = _data.RunTimePerYear
    phx_obj.params.exhaust_flow_rate_m3h = _data.ExhaustVolumeFlowRate
    return phx_obj


def _PhxExhaustVent_UserDefined(
    _data: wufi_xml.ExhaustVent,
) -> PhxExhaustVentilatorUserDefined:
    phx_obj = PhxExhaustVentilatorUserDefined()
    phx_obj.params.annual_runtime_minutes = _data.RunTimePerYear
    phx_obj.params.exhaust_flow_rate_m3h = _data.ExhaustVolumeFlowRate
    return phx_obj


# ----------------------------------------------------------------------
# -- Electrical Devices


def _PhxHomeDevice(_data: wufi_xml.H_Device) -> PhxElectricalDevice:
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
    device_type = ElectricEquipmentType(_data.Type)
    phx_obj: PhxElectricalDevice = as_phx_obj(_data, device_builders[device_type])

    # -- Set all the common parameters
    phx_obj.comment = _data.Comment
    phx_obj.reference_quantity = _data.ReferenceQuantity
    phx_obj.quantity = _data.Quantity
    phx_obj.in_conditioned_space = _data.InConditionedSpace
    phx_obj.reference_energy_norm = _data.ReferenceEnergyDemandNorm
    phx_obj.energy_demand = _data.EnergyDemandNorm
    phx_obj.energy_demand_per_use = _data.EnergyDemandNormUse
    phx_obj.combined_energy_factor = _data.CEF_CombinedEnergyFactor

    return phx_obj


def _PhxDeviceDishwasher(_data: wufi_xml.H_Device) -> PhxDeviceDishwasher:
    phx_obj = PhxDeviceDishwasher()
    phx_obj.water_connection = _data.Connection
    phx_obj.capacity_type = _data.DishwasherCapacityPreselection
    phx_obj.capacity = _data.DishwasherCapacityInPlace
    return phx_obj


def _PhxDeviceClothesWasher(_data: wufi_xml.H_Device) -> PhxDeviceClothesWasher:
    phx_obj = PhxDeviceClothesWasher()
    phx_obj.water_connection = _data.Connection
    phx_obj.utilization_factor = _data.UtilizationFactor
    phx_obj.capacity = _data.CapacityClothesWasher
    phx_obj.modified_energy_factor = _data.MEF_ModifiedEnergyFactor
    return phx_obj


def _PhxDeviceClothesDryer(_data: wufi_xml.H_Device) -> PhxDeviceClothesDryer:
    phx_obj = PhxDeviceClothesDryer()
    phx_obj.dryer_type = _data.Dryer_Choice or 4
    phx_obj.gas_consumption = _data.GasConsumption
    phx_obj.gas_efficiency_factor = _data.EfficiencyFactorGas
    phx_obj.field_utilization_factor_type = _data.FieldUtilizationFactorPreselection
    phx_obj.field_utilization_factor = _data.FieldUtilizationFactor
    return phx_obj


def _PhxDeviceRefrigerator(_data: wufi_xml.H_Device) -> PhxDeviceRefrigerator:
    phx_obj = PhxDeviceRefrigerator()
    return phx_obj


def _PhxDeviceFreezer(_data: wufi_xml.H_Device) -> PhxDeviceFreezer:
    phx_obj = PhxDeviceFreezer()
    return phx_obj


def _PhxDeviceFridgeFreezer(_data: wufi_xml.H_Device) -> PhxDeviceFridgeFreezer:
    phx_obj = PhxDeviceFridgeFreezer()
    return phx_obj


def _PhxDeviceCooktop(_data: wufi_xml.H_Device) -> PhxDeviceCooktop:
    phx_obj = PhxDeviceCooktop()
    phx_obj.cooktop_type = _data.CookingWith
    return phx_obj


def _PhxDeviceCustomElec(_data: wufi_xml.H_Device) -> PhxDeviceCustomElec:
    phx_obj = PhxDeviceCustomElec()
    return phx_obj


def _PhxDeviceMEL(_data: wufi_xml.H_Device) -> PhxDeviceMEL:
    phx_obj = PhxDeviceMEL()
    return phx_obj


def _PhxDeviceLightingInterior(_data: wufi_xml.H_Device) -> PhxDeviceLightingInterior:
    phx_obj = PhxDeviceLightingInterior()
    phx_obj.frac_high_efficiency = _data.FractionHightEfficiency
    return phx_obj


def _PhxDeviceLightingExterior(_data: wufi_xml.H_Device) -> PhxDeviceLightingExterior:
    phx_obj = PhxDeviceLightingExterior()
    phx_obj.frac_high_efficiency = _data.FractionHightEfficiency
    return phx_obj


def _PhxDeviceLightingGarage(_data: wufi_xml.H_Device) -> PhxDeviceLightingGarage:
    phx_obj = PhxDeviceLightingGarage()
    phx_obj.frac_high_efficiency = _data.FractionHightEfficiency
    return phx_obj


def _PhxDeviceCustomLighting(_data: wufi_xml.H_Device) -> PhxDeviceCustomLighting:
    phx_obj = PhxDeviceCustomLighting()

    return phx_obj


def _PhxDeviceCustomMEL(_data: wufi_xml.H_Device) -> PhxDeviceCustomMEL:
    phx_obj = PhxDeviceCustomMEL()

    return phx_obj
