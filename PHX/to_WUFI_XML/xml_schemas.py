# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Conversion Schemas for how to write PH/HB objects to WUFI XML"""

from typing import List, Optional
import sys

from PHX.model import (
    building,
    certification,
    components,
    constructions,
    elec_equip,
    geometry,
    ground,
    hvac,
    loads,
    phx_site,
    project,
    schedules,
    spaces, shades,
)
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from PHX.to_WUFI_XML.xml_writables import XML_Node, XML_List, XML_Object, xml_writable
from PHX.model.enums.foundations import FoundationType

TOL_LEV1 = 2  # Value tolerance for rounding. ie; 9.843181919194 -> 9.84
TOL_LEV2 = 10  # Value tolerance for rounding. ie; 9.843181919194 -> 9.8431819192


# -- PROJECT ------------------------------------------------------------------


def _PhxProject(_wufi_project: project.PhxProject) -> List[xml_writable]:
    return [
        XML_Node("DataVersion", _wufi_project.data_version),
        XML_Node("UnitSystem", _wufi_project.data_version),
        XML_Node("ProgramVersion", _wufi_project.program_version),
        XML_Node("Scope", _wufi_project.scope),
        XML_Node("DimensionsVisualizedGeometry", _wufi_project.visualized_geometry),
        XML_Object("ProjectData", _wufi_project.project_data),
        XML_List(
            "UtilisationPatternsVentilation",
            [
                XML_Object(
                    _node_name="UtilizationPatternVent",
                    _node_object=vent_pat,
                    _attr_name="index",
                    _attr_value=i,
                    _schema_name="_UtilizationPatternVent",
                )
                for i, vent_pat in enumerate(
                    _wufi_project.utilization_patterns_ventilation
                )
            ],
        ),
        XML_List(
            "UtilizationPatternsPH",
            [
                XML_Object(
                    _node_name="UtilizationPattern",
                    _node_object=util_pat,
                    _attr_name="index",
                    _attr_value=i,
                    _schema_name="_UtilizationPattern",
                )
                for i, util_pat in enumerate(_wufi_project.utilization_patterns_occupancy)
            ],
        ),
        XML_List(
            "Variants",
            [
                XML_Object("Variant", var, "index", i)
                for i, var in enumerate(_wufi_project.variants)
            ],
        ),
        XML_List(
            "Assemblies",
            [
                XML_Object("Assembly", at_id, "index", i)
                for i, at_id in enumerate(_wufi_project.assembly_types.values())
            ],
        ),
        XML_List(
            "WindowTypes",
            [
                XML_Object("WindowType", wt_id, "index", i)
                for i, wt_id in enumerate(_wufi_project.window_types.values())
            ],
        ),
        XML_List(
            "SolarProtectionTypes",
            [
                XML_Object("SolarProtectionType", type_id, "index", i, _schema_name="_PhxWindowShade")
                for i, type_id in enumerate(_wufi_project.shade_types.values())
            ],
        ),
    ]


def _PhxVariant(_variant: project.PhxVariant) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _variant.id_num),
        XML_Node("Name", _variant.name),
        XML_Node("Remarks", _variant.remarks),
        XML_Node("PlugIn", _variant.plugin),
        XML_Object("Graphics_3D", _variant.graphics3D),
        XML_Object("Building", _variant.building),
        XML_Object("ClimateLocation", _variant.site),
        XML_Object("PassivehouseData", _variant.phius_cert),
        XML_Object(
            "HVAC", _variant.mech_systems, _schema_name="_PhxMechanicalSystemCollection"
        ),
    ]


def _PhxProjectData(_project_data: project.PhxProjectData) -> List[xml_writable]:
    return [
        XML_Node("Year_Construction", _project_data.year_constructed),
        XML_Node("OwnerIsClient", _project_data.owner_is_client),
        XML_Node("Date_Project", _project_data.project_date),
        XML_Node("WhiteBackgroundPictureBuilding", _project_data.image),
        XML_Node("Customer_Name", _project_data.customer.name),
        XML_Node("Customer_Street", _project_data.customer.street),
        XML_Node("Customer_Locality", _project_data.customer.city),
        XML_Node("Customer_PostalCode", _project_data.customer.post_code),
        XML_Node("Customer_Tel", _project_data.customer.telephone),
        XML_Node("Customer_Email", _project_data.customer.email),
        XML_Node("Building_Name", _project_data.building.name),
        XML_Node("Building_Street", _project_data.building.street),
        XML_Node("Building_Locality", _project_data.building.city),
        XML_Node("Building_PostalCode", _project_data.building.post_code),
        XML_Node("Owner_Name", _project_data.owner.name),
        XML_Node("Owner_Street", _project_data.owner.street),
        XML_Node("Owner_Locality", _project_data.owner.city),
        XML_Node("Owner_PostalCode", _project_data.owner.post_code),
        XML_Node("Responsible_Name", _project_data.responsible.name),
        XML_Node("Responsible_Street", _project_data.responsible.street),
        XML_Node("Responsible_Locality", _project_data.responsible.city),
        XML_Node("Responsible_PostalCode", _project_data.responsible.post_code),
        XML_Node("Responsible_Tel", _project_data.responsible.telephone),
        XML_Node("Responsible_LicenseNr", _project_data.responsible.license_number),
        XML_Node("Responsible_Email", _project_data.responsible.email),
    ]


# -- BUILDING -----------------------------------------------------------------


def _PhxBuilding(_b: building.PhxBuilding) -> List[xml_writable]:
    return [
        XML_List(
            "Components",
            [
                XML_Object("Component", c, "index", i)
                for i, c in enumerate(_b.all_components)
            ],
        ),
        XML_List(
            "Zones", [XML_Object("Zone", z, "index", i) for i, z in enumerate(_b.zones)]
        ),
    ]


def _PhxZone(_z: building.PhxZone) -> List[xml_writable]:
    _spec_cap_WH_m2k = {
        1: 60,
        2: 132,
        3: 204,
    }
    
    return [
        XML_Node("Name", _z.display_name),
        XML_Node("KindZone", 1, "choice", "Simulated zone"),
        XML_Node("IdentNr", _z.id_num),
        XML_List(
            "RoomsVentilation",
            [
                XML_Object("Room", sp, "index", i, _schema_name="_PhxSpace")
                for i, sp in enumerate(_z.spaces)
            ],
        ),
        XML_List(
            "LoadsPersonsPH",
            [
                XML_Object("LoadPerson", sp, "index", i, _schema_name="_LoadPerson")
                for i, sp in enumerate(_z.spaces)
            ],
        ),
        XML_Node("GrossVolume_Selection", 6),
        XML_Node("GrossVolume", _z.volume_gross),
        XML_Node("NetVolume_Selection", 6),
        XML_Node("NetVolume", _z.volume_net),
        XML_Node("FloorArea_Selection", 6),
        XML_Node("FloorArea", _z.weighted_net_floor_area),
        XML_Node("ClearanceHeight_Selection", 1),
        XML_Node("ClearanceHeight", _z.clearance_height),
        XML_Node("SpecificHeatCapacity_Selection", _z.specific_heat_capacity.value),
        XML_Node("SpecificHeatCapacity", _spec_cap_WH_m2k[_z.specific_heat_capacity.value]),
        XML_Node("IdentNrPH_Building", 1),
        XML_Node("OccupantQuantityUserDef", int(_z.res_occupant_quantity), "unit", "-"),
        XML_Node("NumberBedrooms", int(_z.res_number_bedrooms), "unit", "-"),
        XML_List(
            "HomeDevice",
            [
                XML_Object("Device", d, "index", i, _schema_name="_PhxElectricalDevice")
                for i, d in enumerate(_z.elec_equipment_collection.devices)
            ],
        ),
        XML_List(
            "ExhaustVents",
            [
                XML_Object(
                    "ExhaustVent", v, "index", i, _schema_name="_PhxExhaustVentilator"
                )
                for i, v in enumerate(_z.exhaust_ventilator_collection.devices)
            ],
        ),
        XML_List(
            "ThermalBridges",
            [
                XML_Object(
                    "ThermalBridge", tb, "index", i, _schema_name="_PhxThermalBridge"
                )
                for i, tb in enumerate(_z.thermal_bridges)
            ],
        ),
        XML_Node("SummerNaturalVentilationDay", 0, "unit", "1/hr"),
        XML_Node("SummerNaturalVentilationNight", 0, "unit", "1/hr"),
    ]


def _PhxThermalBridge(_tb: components.PhxComponentThermalBridge) -> List[xml_writable]:
    return [
        XML_Node("Name", _tb.display_name),
        XML_Node("Type", int(_tb.group_number.value) * -1),
        XML_Node("Length", _tb.length),
        XML_Node("PsiValue", _tb.psi_value),
        XML_Node("IdentNrOptionalClimate", -1),
    ]


def _PhxComponentOpaque(_c: components.PhxComponentOpaque) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _c.id_num),
        XML_Node("Name", _c.display_name),
        XML_Node("Visual", True),
        XML_Node("Type", _c.face_opacity.value),
        XML_Node("IdentNrColorI", _c.color_interior.value),
        XML_Node("IdentNrColorE", _c.color_exterior.value),
        XML_Node("InnerAttachment", _c.exposure_interior),
        XML_Node("OuterAttachment", _c.exposure_exterior.value),
        XML_Node("IdentNr_ComponentInnerSurface", _c.interior_attachment_id),
        XML_Node("IdentNrAssembly", _c.assembly_type_id_num),
        XML_Node("IdentNrWindowType", -1),
        XML_List(
            "IdentNrPolygons",
            [XML_Node("IdentNr", n, "index", i) for i, n in enumerate(_c.polygon_ids)],
        ),
    ]


def _PhxComponentAperture(_c: components.PhxComponentAperture) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _c.id_num),
        XML_Node("Name", _c.display_name),
        XML_Node("Visual", True),
        XML_Node("Type", _c.face_opacity.value),
        XML_Node("IdentNrColorI", _c.color_interior.value),
        XML_Node("IdentNrColorE", _c.color_exterior.value),
        XML_Node("InnerAttachment", _c.exposure_interior),
        XML_Node("OuterAttachment", _c.exposure_exterior.value),
        XML_Node("IdentNr_ComponentInnerSurface", _c.interior_attachment_id),
        XML_Node("IdentNrAssembly", -1),
        XML_Node("IdentNrWindowType", _c.window_type_id_num),
        XML_List(
            "IdentNrPolygons",
            [XML_Node("IdentNr", n, "index", i) for i, n in enumerate(_c.polygon_ids)],
        ),
        XML_Node("DepthWindowReveal", _c.install_depth, "unit", "m"),
        XML_Node("IdentNrSolarProtection", _c.id_num_shade),
        XML_Node("IdentNrOverhang", -1),
    ]


# -- CERTIFICATION ------------------------------------------------------------


def _PhxPhBuildingData(
    _phius_cert: certification.PhxPhiusCertification,
) -> List[xml_writable]:    
    return [
        XML_Node("IdentNr", _phius_cert.ph_building_data._count),
        XML_Node(
            "BuildingCategory",
            _phius_cert.phius_certification_settings.phius_building_category_type.value,
        ),
        XML_Node(
            "OccupancyTypeResidential",
            _phius_cert.phius_certification_settings.phius_building_use_type.value,
        ),
        XML_Node(
            "BuildingStatus",
            _phius_cert.phius_certification_settings.phius_building_status.value,
        ),
        XML_Node(
            "BuildingType",
            _phius_cert.phius_certification_settings.phius_building_type.value,
        ),
        XML_Node(
            "OccupancySettingMethod",
            _phius_cert.ph_building_data.occupancy_setting_method,
        ),
        XML_Node("NumberUnits", _phius_cert.ph_building_data.num_of_units),
        XML_Node("CountStories", _phius_cert.ph_building_data.num_of_floors),
        XML_Node(
            "EnvelopeAirtightnessCoefficient",
            _phius_cert.ph_building_data.airtightness_q50,
        ),
        XML_Node("SummerHRVHumidityRecovery", 4, "choice", "Always"),
        XML_List(
            "FoundationInterfaces",
            [
                XML_Object("FoundationInterface", f, "index", i, _schema_name="_PhxFoundation")
                for i, f in enumerate(_phius_cert.ph_building_data.foundations)
            ],
        ),
        XML_Object(
            "InternalGainsAdditionalData",
            None,
            _schema_name="_InternalGainsAdditionalData",
        ),
        XML_Node("MechanicalRoomTemperature", _phius_cert.ph_building_data.mech_room_temp),
        XML_Node("IndoorTemperature", _phius_cert.ph_building_data.setpoints.winter),
        XML_Node("OverheatingTemperatureThreshold", _phius_cert.ph_building_data.setpoints.summer),
    ]


def _InternalGainsAdditionalData(*args, **kwargs) -> List[xml_writable]:
    return [
        XML_Node("EvaporationHeatPerPerson", 15, "unit", "W"),
        XML_Node("HeatLossFluschingWC", True),
        XML_Node("QuantityWCs", 1),
        XML_Node("RoomCategory", 1),
        XML_Node("UseDefaultValuesSchool", False),
        XML_Node("MarginalPerformanceRatioDHW", None),
    ]


def _PhxPhiusCertification(
    _phius_cert: certification.PhxPhiusCertification,
) -> List[xml_writable]:
    # No idea why this is a list in Wufi? When would there ever be more than 1? whatever...
    _temp_bldg_data_list = [_phius_cert]

    return [
        XML_Node(
            "PH_CertificateCriteria",
            _phius_cert.phius_certification_settings.phius_building_certification_program.value,
        ),
        XML_Node(
            "PH_SelectionTargetData",
            _phius_cert.phius_certification_criteria.ph_selection_target_data,
        ),
        XML_Node(
            "AnnualHeatingDemand",
            _phius_cert.phius_certification_criteria.phius_annual_heating_demand,
        ),
        XML_Node(
            "AnnualCoolingDemand",
            _phius_cert.phius_certification_criteria.phius_annual_cooling_demand,
        ),
        XML_Node(
            "PeakHeatingLoad",
            _phius_cert.phius_certification_criteria.phius_peak_heating_load,
        ),
        XML_Node(
            "PeakCoolingLoad",
            _phius_cert.phius_certification_criteria.phius_peak_cooling_load,
        ),
        XML_List(
            "PH_Buildings",
            [
                XML_Object(
                    "PH_Building", obj, "index", i, _schema_name="_PhxPhBuildingData"
                )
                for i, obj in enumerate(_temp_bldg_data_list)
            ],
        ),
    ]


# -- FOUNDATIONS --------------------------------------------------------------

def _PhxHeatedBasement(_f: ground.PhxHeatedBasement):
    return [
        XML_Node("FloorSlabArea_Selection", 6), # 6=User defined
        XML_Node("FloorSlabArea", _f.floor_slab_area_m2),
        XML_Node("FloorSlabPerimeter_Selection", 6), # 6=User defined
        XML_Node("FloorSlabPerimeter", _f.floor_slab_exposed_perimeter_m),
        XML_Node("U_ValueBasementSlab_Selection", 6), # 6=User defined
        XML_Node("U_ValueBasementSlab", _f.floor_slab_u_value),

        XML_Node("DepthBasementBelowGroundSurface_Selection", 6), # 6=user-defined
        XML_Node("DepthBasementBelowGroundSurface", _f.slab_depth_below_grade_m),
        
        # XML_Node("HeightBasementWallAboveGrade_Selection", 6), #6=user-defined
        # XML_Node("HeightBasementWallAboveGrade", _f.ab),

        XML_Node("U_ValueBasementWall_Selection", 6), #6=user-defined
        XML_Node("U_ValueBasementWall", _f.basement_wall_u_value),
    ]


def _PhxUnHeatedBasement(_f: ground.PhxUnHeatedBasement):
    return [
        XML_Node("DepthBasementBelowGroundSurface_Selection", 6), # 6=User defined
        XML_Node("DepthBasementBelowGroundSurface", _f.slab_depth_below_grade_m),
        XML_Node("HeightBasementWallAboveGrade_Selection", 6), # 6=User defined
        XML_Node("HeightBasementWallAboveGrade", _f.basement_wall_height_above_grade_m),    
        XML_Node("FloorSlabArea_Selection", 6), # 6=User defined
        XML_Node("FloorSlabArea", _f.floor_ceiling_area_m2),
        XML_Node("U_ValueBasementSlab_Selection", 6), # 6=User defined
        XML_Node("U_ValueBasementSlab", _f.floor_slab_u_value),
        XML_Node("FloorCeilingArea_Selection", 6), # 6=User defined
        XML_Node("FloorCeilingArea", _f.floor_ceiling_area_m2),
        XML_Node("U_ValueCeilingToUnheatedCellar_Selection", 6), # 6=User defined
        XML_Node("U_ValueCeilingToUnheatedCellar", _f.ceiling_u_value),
        XML_Node("U_ValueBasementWall_Selection", 6), # 6=User defined
        XML_Node("U_ValueBasementWall", _f.basement_wall_uValue_below_grade),
        XML_Node("U_ValueWallAboveGround_Selection", 6), # 6=User defined
        XML_Node("U_ValueWallAboveGround", _f.basement_wall_uValue_above_grade),
        XML_Node("FloorSlabPerimeter_Selection", 6), # 6=User defined
        XML_Node("FloorSlabPerimeter", _f.floor_slab_exposed_perimeter_m),
        XML_Node("BasementVolume_Selection", 6), # 6=User defined
        XML_Node("BasementVolume", _f.basement_volume_m3),
    ]


def _PhxSlabOnGrade(_f: ground.PhxSlabOnGrade):
    return [
        XML_Node("FloorSlabArea_Selection", 6), # 6=User defined
        XML_Node("FloorSlabArea", _f.floor_slab_area_m2),
        XML_Node("U_ValueBasementSlab_Selection", 6), # 6=User defined
        XML_Node("U_ValueBasementSlab", _f.floor_slab_u_value),
        XML_Node("FloorSlabPerimeter_Selection", 6), # 6=User defined
        XML_Node("FloorSlabPerimeter", _f.floor_slab_exposed_perimeter_m),
        XML_Node("PositionPerimeterInsulation", _f._perim_insulation_position.value),
        XML_Node("PerimeterInsulationWidthDepth", _f.perim_insulation_width_or_depth_m),
        XML_Node("ConductivityPerimeterInsulation", _f.perim_insulation_conductivity),
        XML_Node("ThicknessPerimeterInsulation", _f.perim_insulation_thickness_m),
    ]


def _PhxVentedCrawlspace(_f: ground.PhxVentedCrawlspace):
    return [
        XML_Node("FloorCeilingArea_Selection", 6), # 6=user-defined
        XML_Node("FloorCeilingArea", _f.crawlspace_floor_slab_area_m2),
        XML_Node("U_ValueCeilingToUnheatedCellar_Selection", 6), # 6=User defined
        XML_Node("U_ValueCeilingToUnheatedCellar", _f.ceiling_above_crawlspace_u_value),
        XML_Node("FloorSlabPerimeter_Selection", 6), # 6=User defined
        XML_Node("FloorSlabPerimeter", _f.crawlspace_floor_exposed_perimeter_m),
        XML_Node("HeightBasementWallAboveGrade_Selection", 6), # 6=User defined
        XML_Node("HeightBasementWallAboveGrade", _f.crawlspace_wall_height_above_grade_m),
        XML_Node("U_ValueCrawlspaceFloor_Selection", 6), # 6=user-defined
        XML_Node("U_ValueCrawlspaceFloor", _f.crawlspace_floor_u_value),
        XML_Node("CrawlspaceVentOpenings_Selection", 6), # 6=user-defined
        XML_Node("CrawlspaceVentOpenings", _f.crawlspace_vent_opening_are_m2),
        XML_Node("U_ValueWallAboveGround_Selection", 6), # 6=user-defined
        XML_Node("U_ValueWallAboveGround", _f.crawlspace_wall_u_value),
    ]


def _PhxFoundation(_f: ground.PhxFoundation) -> List[xml_writable]:
    common_attributes = [
        XML_Node("Name", _f.display_name),
        XML_Node("SettingFloorSlabType", _f.foundation_setting_num.value),
        XML_Node("FloorSlabType", _f.foundation_type_num.value),
    ]

    if _f.foundation_type_num == FoundationType.NONE:
        foundation_specific_attributes: List[xml_writable] = []
    else:
        foundation_schema = getattr(sys.modules[__name__], f"_{_f.__class__.__name__}")
        foundation_specific_attributes = foundation_schema(_f)

    return common_attributes + foundation_specific_attributes

    # -- Settings: Others
    # XML_Node("BasementVentilationACH", 1),


    # XML_Node("CrawlspaceVentOpenings_Selection", 1),
    # XML_Node("CrawlspaceVentOpenings", 1),
    # XML_Node("FloorCeilingArea_Selection", 1),
    # XML_Node("FloorCeilingArea", 1),
    # XML_Node("U_ValueCeilingToUnheatedCellar_Selection", 1),
    # XML_Node("U_ValueCeilingToUnheatedCellar", 1),

    # XML_Node("U_ValueWallAboveGround_Selection", 1),
    # XML_Node("U_ValueWallAboveGround", 1),
    # XML_Node("BasementVolume_Selection", 1),
    # XML_Node("BasementVolume", 1),
    # XML_Node("U_ValueCrawlspaceFloor_Selection", 1),
    # XML_Node("U_ValueCrawlspaceFloor", 1),


# -- CLIMATE ------------------------------------------------------------------


def _PH_ClimateLocation(_phx_site: phx_site.PhxSite) -> List[xml_writable]:
    def _in_wufi_order(_factor_dict: dict) -> List[phx_site.PhxEnergyFactorAlias]:
        """Returns the PE /CO2 conversion factors in WUFI-specific order."""
        fuel_order = [
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
        return [_factor_dict[fuel_name] for fuel_name in fuel_order]

    return [
        XML_Node("Selection", _phx_site.climate.selection.value),
        XML_Node("DailyTemperatureSwingSummer", _phx_site.climate.daily_temp_swing),
        XML_Node("AverageWindSpeed", _phx_site.climate.avg_wind_speed),
        # -- Location
        XML_Node("Latitude", _phx_site.location.latitude),
        XML_Node("Longitude", _phx_site.location.longitude),
        XML_Node("HeightNNWeatherStation", _phx_site.climate.station_elevation),
        XML_Node("dUTC", _phx_site.location.hours_from_UTC),
        XML_Node("HeightNNBuilding", _phx_site.location.site_elevation),
        XML_Node("ClimateZone", _phx_site.location.climate_zone),
        # -- Ground
        XML_Node(
            "GroundThermalConductivity", _phx_site.ground.ground_thermal_conductivity
        ),
        XML_Node("GroundHeatCapacitiy", _phx_site.ground.ground_heat_capacity),
        XML_Node("GroundDensity", _phx_site.ground.ground_density),
        XML_Node("DepthGroundwater", _phx_site.ground.depth_groundwater),
        XML_Node("FlowRateGroundwater", _phx_site.ground.flow_rate_groundwater),
        # -- Monthly
        XML_List(
            "TemperatureMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.temperature_air)
            ],
        ),
        XML_List(
            "DewPointTemperatureMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.temperature_dewpoint)
            ],
        ),
        XML_List(
            "SkyTemperatureMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.temperature_sky)
            ],
        ),
        XML_List(
            "NorthSolarRadiationMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.radiation_north)
            ],
        ),
        XML_List(
            "EastSolarRadiationMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.radiation_east)
            ],
        ),
        XML_List(
            "SouthSolarRadiationMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.radiation_south)
            ],
        ),
        XML_List(
            "WestSolarRadiationMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.radiation_west)
            ],
        ),
        XML_List(
            "GlobalSolarRadiationMonthly",
            [
                XML_Node("Item", val, "index", i)
                for i, val in enumerate(_phx_site.climate.radiation_global)
            ],
        ),
        # -- Peak Load Values
        XML_Node("TemperatureHeating1", _phx_site.climate.peak_heating_1.temperature_air),
        XML_Node(
            "NorthSolarRadiationHeating1",
            _phx_site.climate.peak_heating_1.radiation_north,
        ),
        XML_Node(
            "EastSolarRadiationHeating1", _phx_site.climate.peak_heating_1.radiation_east
        ),
        XML_Node(
            "SouthSolarRadiationHeating1",
            _phx_site.climate.peak_heating_1.radiation_south,
        ),
        XML_Node(
            "WestSolarRadiationHeating1", _phx_site.climate.peak_heating_1.radiation_west
        ),
        XML_Node(
            "GlobalSolarRadiationHeating1",
            _phx_site.climate.peak_heating_1.radiation_global,
        ),
        XML_Node("TemperatureHeating2", _phx_site.climate.peak_heating_2.temperature_air),
        XML_Node(
            "NorthSolarRadiationHeating2",
            _phx_site.climate.peak_heating_2.radiation_north,
        ),
        XML_Node(
            "EastSolarRadiationHeating2", _phx_site.climate.peak_heating_2.radiation_east
        ),
        XML_Node(
            "SouthSolarRadiationHeating2",
            _phx_site.climate.peak_heating_2.radiation_south,
        ),
        XML_Node(
            "WestSolarRadiationHeating2", _phx_site.climate.peak_heating_2.radiation_west
        ),
        XML_Node(
            "GlobalSolarRadiationHeating2",
            _phx_site.climate.peak_heating_2.radiation_global,
        ),
        XML_Node("TemperatureCooling", _phx_site.climate.peak_cooling_1.temperature_air),
        XML_Node(
            "NorthSolarRadiationCooling", _phx_site.climate.peak_cooling_1.radiation_north
        ),
        XML_Node(
            "EastSolarRadiationCooling", _phx_site.climate.peak_cooling_1.radiation_east
        ),
        XML_Node(
            "SouthSolarRadiationCooling", _phx_site.climate.peak_cooling_1.radiation_south
        ),
        XML_Node(
            "WestSolarRadiationCooling", _phx_site.climate.peak_cooling_1.radiation_west
        ),
        XML_Node(
            "GlobalSolarRadiationCooling",
            _phx_site.climate.peak_cooling_1.radiation_global,
        ),
        XML_Node("TemperatureCooling2", _phx_site.climate.peak_cooling_2.temperature_air),
        XML_Node(
            "NorthSolarRadiationCooling2",
            _phx_site.climate.peak_cooling_2.radiation_north,
        ),
        XML_Node(
            "EastSolarRadiationCooling2", _phx_site.climate.peak_cooling_2.radiation_east
        ),
        XML_Node(
            "SouthSolarRadiationCooling2",
            _phx_site.climate.peak_cooling_2.radiation_south,
        ),
        XML_Node(
            "WestSolarRadiationCooling2", _phx_site.climate.peak_cooling_2.radiation_west
        ),
        XML_Node(
            "GlobalSolarRadiationCooling2",
            _phx_site.climate.peak_cooling_2.radiation_global,
        ),
        XML_Node(
            "SelectionPECO2Factor", _phx_site.energy_factors.selection_pe_co2_factor.value
        ),
        XML_List(
            "PEFactorsUserDef",
            [
                XML_Node(f"PEF{i}", factor.value, "unit", factor.unit)
                for i, factor in enumerate(
                    _in_wufi_order(_phx_site.energy_factors.pe_factors)
                )
            ],
        ),
        XML_List(
            "CO2FactorsUserDef",
            [
                XML_Node(f"CO2F{i}", factor.value, "unit", factor.unit)
                for i, factor in enumerate(
                    _in_wufi_order(_phx_site.energy_factors.co2_factors)
                )
            ],
        ),
    ]


def _PhxSite(_phx_site: phx_site.PhxSite) -> List[xml_writable]:
    return [
        XML_Node("Selection", _phx_site.selection.value),
        # XML_Node('IDNr_DB', _climate.),
        # XML_Node('Name_DB', _climate.),
        # XML_Node('Comment_DB', _climate.),
        XML_Node("Latitude_DB", _phx_site.location.latitude, "unit", "°"),
        XML_Node("Longitude_DB", _phx_site.location.longitude, "unit", "°"),
        XML_Node("HeightNN_DB", _phx_site.location.site_elevation, "unit", "m"),
        XML_Node("dUTC_DB", _phx_site.location.hours_from_UTC),
        # XML_Node('FileName_DB', _climate.),
        # XML_Node('Type_DB', _climate.),
        # XML_Node('CatalogueNr_DB', _climate.),
        # XML_Node('MapNr_DB', _climate.),
        XML_Node("Albedo", -2, "choice", "User defined"),
        XML_Node("GroundReflShort", 0.2, "unit", "-"),
        XML_Node("GroundReflLong", 0.1, "unit", "-"),
        XML_Node("GroundEmission", 0.9, "unit", "-"),
        XML_Node("CloudIndex", 0.66, "unit", "-"),
        XML_Node("CO2concenration", 350, "unit", "mg/m³"),
        XML_Node("Unit_CO2concentration", 48, "choice", "ppmv"),
        XML_Object("PH_ClimateLocation", _phx_site, _schema_name="_PH_ClimateLocation"),
    ]


# -- GEOMETRY -----------------------------------------------------------------


def _PhxGraphics3D(_graphics3D: geometry.PhxGraphics3D) -> List[xml_writable]:
    return [
        XML_List(
            "Vertices",
            [
                XML_Object("Vertix", var, "index", i)
                for i, var in enumerate(_graphics3D.vertices)
            ],
        ),
        XML_List(
            "Polygons",
            [
                XML_Object("Polygon", var, "index", i, _schema_name="_PhxPolygon")
                for i, var in enumerate(_graphics3D.polygons)
            ],
        ),
    ]


def _PhxPolygon(_p: geometry.PhxPolygon) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _p.id_num),
        XML_Node("NormalVectorX", round(_p.normal_vector.x, TOL_LEV2)),
        XML_Node("NormalVectorY", round(_p.normal_vector.y, TOL_LEV2)),
        XML_Node("NormalVectorZ", round(_p.normal_vector.z, TOL_LEV2)),
        XML_List(
            "IdentNrPoints",
            [
                XML_Node("IdentNr", v_id, "index", i)
                for i, v_id in enumerate(_p.vertices_id_numbers)
            ],
        ),
        XML_List(
            "IdentNrPolygonsInside",
            [
                XML_Node("IdentNr", v_id, "index", i)
                for i, v_id in enumerate(_p.child_polygon_ids)
            ],
        ),
    ]


def _PhxVertix(_v: geometry.PhxVertix) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _v.id_num),
        XML_Node("X", round(_v.x, TOL_LEV2)),
        XML_Node("Y", round(_v.y, TOL_LEV2)),
        XML_Node("Z", round(_v.z, TOL_LEV2)),
    ]


# -- CONSTRUCTIONS ------------------------------------------------------------


def _PhxConstructionOpaque(_a: constructions.PhxConstructionOpaque) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _a.id_num),
        XML_Node("Name", _a.display_name),
        XML_Node("Order_Layers", _a.layer_order),
        XML_Node("Grid_Kind", _a.grid_kind),
        XML_List(
            "Layers",
            [XML_Object("Layer", n, "index", i) for i, n in enumerate(_a.layers)],
        ),
    ]


def _PhxLayer(_l: constructions.PhxLayer) -> List[xml_writable]:
    return [
        XML_Node("Thickness", _l.thickness_m),
        XML_Object("Material", _l.material),
    ]


def _PhxMaterial(_m: constructions.PhxMaterial) -> List[xml_writable]:
    return [
        XML_Node("Name", _m.display_name),
        XML_Node("ThermalConductivity", _m.conductivity),
        XML_Node("BulkDensity", _m.density),
        XML_Node("Porosity", _m.porosity),
        XML_Node("HeatCapacity", _m.heat_capacity),
        XML_Node("WaterVaporResistance", _m.water_vapor_resistance),
        XML_Node("ReferenceW", _m.reference_water),
    ]


def _PhxConstructionWindow(
    _wt: constructions.PhxConstructionWindow,
) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", _wt.id_num),
        XML_Node("Name", _wt.display_name),
        XML_Node("Uw_Detailed", _wt.use_detailed_uw),
        XML_Node("GlazingFrameDetailed", _wt.use_detailed_frame),
        XML_Node("FrameFactor", _wt.frame_factor),
        XML_Node("U_Value", _wt.u_value_window),
        XML_Node("U_Value_Glazing", _wt.u_value_glass),
        XML_Node("MeanEmissivity", _wt.glass_mean_emissivity),
        XML_Node("g_Value", _wt.glass_g_value),
        XML_Node("SHGC_Hemispherical", _wt.glass_g_value),
        # --
        XML_Node("U_Value_Frame", _wt.u_value_frame),
        # --
        XML_Node("Frame_Width_Left", _wt.frame_left.width),
        XML_Node("Frame_Psi_Left", _wt.frame_left.psi_install),
        XML_Node("Frame_U_Left", _wt.frame_left.u_value),
        XML_Node("Glazing_Psi_Left", _wt.frame_left.psi_glazing),
        # --
        XML_Node("Frame_Width_Right", _wt.frame_right.width),
        XML_Node("Frame_Psi_Right", _wt.frame_right.psi_install),
        XML_Node("Frame_U_Right", _wt.frame_right.u_value),
        XML_Node("Glazing_Psi_Right", _wt.frame_right.psi_glazing),
        # --
        XML_Node("Frame_Width_Top", _wt.frame_top.width),
        XML_Node("Frame_Psi_Top", _wt.frame_top.psi_install),
        XML_Node("Frame_U_Top", _wt.frame_top.u_value),
        XML_Node("Glazing_Psi_Top", _wt.frame_top.psi_glazing),
        # --
        XML_Node("Frame_Width_Bottom", _wt.frame_bottom.width),
        XML_Node("Frame_Psi_Bottom", _wt.frame_bottom.psi_install),
        XML_Node("Frame_U_Bottom", _wt.frame_bottom.u_value),
        XML_Node("Glazing_Psi_Bottom", _wt.frame_bottom.psi_glazing),
    ]


def _PhxWindowShade(_s: shades.PhxWindowShade) -> List[xml_writable]:
    return [
      XML_Node("IdentNr", _s.id_num),
      XML_Node("Name", _s.display_name),
      XML_Node("OperationMode", _s.operation_mode),
      XML_Node("MaxRedFactorRadiation", _s.reduction_factor),
      XML_Node("ExternalEmissivity", _s.external_emissivity),
      XML_Node("EquivalentAbsorptivity", _s.absorptivity),
      XML_Node("ThermalResistanceSupplement", _s.thermal_resistance_supplement),
      XML_Node("ThermalResistanceCavity", _s.thermal_resistance_cavity),
      XML_Node("RadiationLimitValue", _s.radiation_limit),
      XML_Node("ExcludeWeekends", _s.exclude_weekends),
    ]


# -- VENTILATION --------------------------------------------------------------


def _PhxSpace(_r: spaces.PhxSpace) -> List[xml_writable]:
    return [
        XML_Node("Name", _r.display_name),
        XML_Node("Type", _r.wufi_type),
        XML_Node("IdentNrUtilizationPatternVent", _r.ventilation.schedule.id_num),
        XML_Node("IdentNrVentilationUnit", _r.vent_unit_id_num),
        XML_Node("Quantity", _r.quantity),
        XML_Node("AreaRoom", _r.weighted_floor_area, "unit", "m²"),
        XML_Node("ClearRoomHeight", _r.clear_height, "unit", "m"),
        XML_Node(
            "DesignVolumeFlowRateSupply",
            round(_r.ventilation.load.flow_supply, TOL_LEV1),
            "unit",
            "m³/h",
        ),
        XML_Node(
            "DesignVolumeFlowRateExhaust",
            round(_r.ventilation.load.flow_extract, TOL_LEV1),
            "unit",
            "m³/h",
        ),
        # XML_Node('SupplyFlowRateUserDef', 'Test', "unit", "m³/h"),
        # XML_Node('ExhaustFlowRateUserDef', 'Test', "unit", "m³/h"),
        # XML_Node('DesignFlowInterzonalUserDef', 'Test', "unit", "m³/h"),
    ]


def _UtilizationPatternVent(_vent_sched: PhxScheduleVentilation) -> List[xml_writable]:
    op_periods = _vent_sched.operating_periods
    return [
        XML_Node("Name", _vent_sched.name),
        XML_Node("IdentNr", _vent_sched.id_num),
        XML_Node("OperatingDays", _vent_sched.operating_days),
        XML_Node("OperatingWeeks", _vent_sched.operating_weeks),
        XML_Node("Maximum_DOS", round(op_periods.high.period_operating_hours, TOL_LEV1)),
        XML_Node("Maximum_PDF", round(op_periods.high.period_operation_speed, TOL_LEV1)),
        XML_Node(
            "Standard_DOS", round(op_periods.standard.period_operating_hours, TOL_LEV1)
        ),
        XML_Node(
            "Standard_PDF", round(op_periods.standard.period_operation_speed, TOL_LEV1)
        ),
        XML_Node("Basic_DOS", round(op_periods.basic.period_operating_hours, TOL_LEV1)),
        XML_Node("Basic_PDF", round(op_periods.basic.period_operation_speed, TOL_LEV1)),
        XML_Node(
            "Minimum_DOS", round(op_periods.minimum.period_operating_hours, TOL_LEV1)
        ),
        XML_Node(
            "Minimum_PDF", round(op_periods.minimum.period_operation_speed, TOL_LEV1)
        ),
    ]


# -- MECHANICAL DEVICES -------------------------------------------------------


def _PhxDeviceVentilator(_d: hvac.PhxDeviceVentilator) -> List[xml_writable]:
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("SystemType", _d.system_type.value),
        XML_Node("TypeDevice", _d.device_type.value),
        XML_Node("UsedFor_Heating", _d.usage_profile.space_heating),
        XML_Node("UsedFor_DHW", _d.usage_profile.dhw_heating),
        XML_Node("UsedFor_Cooling", _d.usage_profile.cooling),
        XML_Node("UsedFor_Ventilation", _d.usage_profile.ventilation),
        XML_Node("UsedFor_Humidification", _d.usage_profile.humidification),
        XML_Node("UsedFor_Dehumidification", _d.usage_profile.dehumidification),
        XML_Node("UseOptionalClimate", False),
        XML_Node("IdentNr_OptionalClimate", -1),
        XML_Node("HeatRecovery", _d.params.sensible_heat_recovery),
        XML_Node("MoistureRecovery ", _d.params.latent_heat_recovery),
        XML_Object("PH_Parameters", _d.params, _schema_name="_DeviceVentilatorPhParams"),
    ]


def _DeviceVentilatorPhParams(_p: hvac.PhxDeviceVentilatorParams) -> List[xml_writable]:
    return [
        XML_Node("Quantity", _p.quantity),
        XML_Node("HumidityRecoveryEfficiency", _p.latent_heat_recovery),
        XML_Node("ElectricEfficiency", _p.electric_efficiency),
        XML_Node("DefrostRequired", _p.frost_protection_reqd),
        XML_Node("FrostProtection", _p.frost_protection_reqd),
        XML_Node("TemperatureBelowDefrostUsed", _p.temperature_below_defrost_used),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
        XML_Node("NoSummerBypass", False),
        # XML_Node("SubsoilHeatExchangeEfficiency", _p.),
        # XML_Node("VolumeFlowRateFrom", "unit","m³/h", _p.),
        # XML_Node("VolumeFlowRateTo", "unit","m³/h", _p.),
        # XML_Node("Maximum_VOS", _p.),
        # XML_Node("Maximum_PP", _p.),
        # XML_Node("Standard_VOS", _p.),
        # XML_Node("Standard_PP", _p.),
        # XML_Node("Basic_VOS", _p.),
        # XML_Node("Basic_PP", _p.),
        # XML_Node("Minimum_VOS", _p.),
        # XML_Node("Minimum_PP", _p.),
        # XML_Node("AuxiliaryEnergy", _p.),
        # XML_Node("AuxiliaryEnergyDHW", _p.),
    ]


def _PhxExhaustVentilator(_v: hvac.AnyPhxExhaustVent) -> List[xml_writable]:
    return [
        XML_Node("Name", _v.display_name),
        XML_Node("Type", _v.params.exhaust_type.value),
        XML_Node(
            "ExhaustVolumeFlowRate", _v.params.exhaust_flow_rate_m3h, "unit", "m³/h"
        ),
        XML_Node("RunTimePerYear", _v.params.annual_runtime_minutes),
    ]


# -- Elec Heating--------------------------------------------------------------


def _PhxDeviceHeaterElec(_d: hvac.PhxHeaterElectric) -> List[xml_writable]:
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("SystemType", _d.system_type.value),
        XML_Node("TypeDevice", _d.device_type.value),
        XML_Node("UsedFor_Heating", _d.usage_profile.space_heating),
        XML_Node("UsedFor_DHW", _d.usage_profile.dhw_heating),
        XML_Node("UsedFor_Cooling", _d.usage_profile.cooling),
        XML_Node("UsedFor_Ventilation", _d.usage_profile.ventilation),
        XML_Node("UsedFor_Humidification", _d.usage_profile.humidification),
        XML_Node("UsedFor_Dehumidification", _d.usage_profile.dehumidification),
        XML_Object("PH_Parameters", _d.params, _schema_name="_DeviceHeaterElecPhParams"),
        XML_Object("DHW_Parameters", _d, _schema_name="_DeviceHeaterElecDeviceParams"),
        XML_Object(
            "Heating_Parameters", _d, _schema_name="_DeviceHeaterElecDeviceParams"
        ),
    ]


def _DeviceHeaterElecPhParams(_p: hvac.PhxMechanicalDeviceParams) -> List[xml_writable]:
    return [
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
    ]


def _DeviceHeaterElecDeviceParams(_d: hvac.PhxHeaterElectric) -> List[xml_writable]:
    return [
        XML_Node("CoverageWithinSystem", _d.percent_coverage),
        XML_Node("Unit", _d.unit),
        XML_Node("Selection", 1),
    ]


# -- Boilers ------------------------------------------------------------------


def _PhxDeviceHeaterBoiler(_d: hvac.PhxHeaterBoiler) -> List[xml_writable]:
    ph_params = {
        "GAS": "_DeviceHeaterBoilerFossilPhParams",
        "OIL": "_DeviceHeaterBoilerFossilPhParams",
        "WOOD_LOG": "_DeviceHeaterBoilerWoodPhParams",
        "WOOD_PELLET": "_DeviceHeaterBoilerWoodPhParams",
    }
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("SystemType", _d.system_type.value),
        XML_Node("TypeDevice", _d.device_type.value),
        XML_Node("UsedFor_Heating", _d.usage_profile.space_heating),
        XML_Node("UsedFor_DHW", _d.usage_profile.dhw_heating),
        XML_Node("UsedFor_Cooling", _d.usage_profile.cooling),
        XML_Node("UsedFor_Ventilation", _d.usage_profile.ventilation),
        XML_Node("UsedFor_Humidification", _d.usage_profile.humidification),
        XML_Node("UsedFor_Dehumidification", _d.usage_profile.dehumidification),
        XML_Object(
            "PH_Parameters", _d.params, _schema_name=ph_params[_d.params.fuel.name]
        ),
        XML_Object("DHW_Parameters", _d, _schema_name="_DeviceHeaterBoilerDeviceParams"),
        XML_Object(
            "Heating_Parameters", _d, _schema_name="_DeviceHeaterBoilerDeviceParams"
        ),
    ]


def _DeviceHeaterBoilerWoodPhParams(
    _p: hvac.PhxHeaterBoilerWoodParams,
) -> List[xml_writable]:
    return [
        XML_Node("EnergySourceBoilerType", _p.fuel.value),
        XML_Node("MaximalBoilerPower", _p.rated_capacity),
        XML_Node("SolarFractionBoilerSpaceHeating", _p.solar_fraction),
        XML_Node("EfficiencyHeatGeneratorBasicCycle", _p.effic_in_basic_cycle),
        XML_Node("EfficiencyHeatGeneratorConstantOperation", _p.effic_in_const_operation),
        XML_Node(
            "AverageFractionHeatOutputReleasedHeatingCircuit", _p.avg_frac_heat_output
        ),
        XML_Node("TemperatureDifferencePowerOnPowerOff", _p.temp_diff_on_off),
        XML_Node("UsefulHeatOutputBasicCycl", _p.rated_capacity),
        XML_Node("AveragePowerOutputHeatGenerator", _p.rated_capacity),
        XML_Node("DemandBasicCycle", _p.demand_basic_cycle),
        XML_Node("PowerConsumptionStationarRun", _p.power_standard_run),
        XML_Node("NoTransportPellets", _p.no_transport_pellets),
        XML_Node("OnlyControl", _p.only_control),
        XML_Node("AreaMechanicalRoom", _p.area_mech_room),
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
    ]


def _DeviceHeaterBoilerFossilPhParams(
    _p: hvac.PhxHeaterBoilerFossilParams,
) -> List[xml_writable]:
    return [
        XML_Node("EnergySourceBoilerType", _p.fuel.value),
        XML_Node("CondensingBoiler", _p.condensing),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
        XML_Node("MaximalBoilerPower", _p.rated_capacity),
        XML_Node("BoilerEfficiency30", _p.effic_at_30_percent_load),
        XML_Node("BoilerEfficiencyNominalOutput", _p.effic_at_nominal_load),
        XML_Node(
            "AverageReturnTemperatureMeasured30Load", _p.avg_rtrn_temp_at_30_percent_load
        ),
        XML_Node("AverageBoilerTemperatureDesign70_55", _p.avg_temp_at_70C_55C),
        XML_Node("AverageBoilerTemperatureDesign55_45", _p.avg_temp_at_55C_45C),
        XML_Node("AverageBoilerTemperatureDesign35_28", _p.avg_temp_at_32C_28C),
        XML_Node("StandbyHeatLossBoiler70", _p.standby_loss_at_70C),
        XML_Node("SolarFractionBoilerSpaceHeating", _p.aux_energy),
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
    ]


def _DeviceHeaterBoilerDeviceParams(_d: hvac.PhxHeaterBoiler) -> List[xml_writable]:
    return [
        XML_Node("CoverageWithinSystem", _d.percent_coverage),
        XML_Node("Unit", _d.unit),
        XML_Node("Selection", 1),
    ]


# -- District Heat ------------------------------------------------------------


def _PhxDeviceHeaterDistrict(_d: hvac.PhxHeaterDistrictHeat) -> List[xml_writable]:
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("SystemType", _d.system_type.value),
        XML_Node("TypeDevice", _d.device_type.value),
        XML_Node("UsedFor_Heating", _d.usage_profile.space_heating),
        XML_Node("UsedFor_DHW", _d.usage_profile.dhw_heating),
        XML_Node("UsedFor_Cooling", _d.usage_profile.cooling),
        XML_Node("UsedFor_Ventilation", _d.usage_profile.ventilation),
        XML_Node("UsedFor_Humidification", _d.usage_profile.humidification),
        XML_Node("UsedFor_Dehumidification", _d.usage_profile.dehumidification),
        XML_Object(
            "DHW_Parameters", _d, _schema_name="_DeviceHeaterDistrictDeviceParams"
        ),
        XML_Object(
            "Heating_Parameters", _d, _schema_name="_DeviceHeaterDistrictDeviceParams"
        ),
    ]


def _DeviceHeaterDistrictDeviceParams(
    _d: hvac.PhxHeaterDistrictHeat,
) -> List[xml_writable]:
    return [
        XML_Node("CoverageWithinSystem", _d.percent_coverage),
        XML_Node("Unit", _d.unit),
        XML_Node("Selection", 1),
    ]


# -- Heat Pumps ---------------------------------------------------------------


def _PhxDeviceHeaterHeatPump(_d: hvac.PhxHeaterHeatPump) -> List[xml_writable]:
    param_schemas = {
        hvac.PhxHeaterHeatPumpAnnualParams.hp_type.value: "_DeviceHeaterHeatPumpPhParamsAnnual",
        hvac.PhxHeaterHeatPumpMonthlyParams.hp_type.value: "_DeviceHeaterHeatPumpPhParamsMonthly",
        hvac.PhxHeaterHeatPumpHotWaterParams.hp_type.value: "_DeviceHeaterHeatPumpPhParamsHotWater",
        hvac.PhxHeaterHeatPumpCombinedParams.hp_type.value: "_DeviceHeaterHeatPumpPhParamsCombined",
    }
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("SystemType", _d.system_type.value),
        XML_Node("TypeDevice", _d.device_type.value),
        XML_Node("UsedFor_Heating", _d.usage_profile.space_heating),
        XML_Node("UsedFor_DHW", _d.usage_profile.dhw_heating),
        XML_Node("UsedFor_Cooling", _d.usage_profile.cooling),
        XML_Node("UsedFor_Ventilation", _d.usage_profile.ventilation),
        XML_Node("UsedFor_Humidification", _d.usage_profile.humidification),
        XML_Node("UsedFor_Dehumidification", _d.usage_profile.dehumidification),
        XML_Object(
            "PH_Parameters",
            _d.params,
            _schema_name=param_schemas[_d.params.hp_type.value],
        ),
        XML_Object(
            "DHW_Parameters", _d, _schema_name="_DeviceHeaterHeatPumpDeviceParams"
        ),
        XML_Object(
            "Heating_Parameters", _d, _schema_name="_DeviceHeaterHeatPumpDeviceParams"
        ),
    ]


def _DeviceHeaterHeatPumpPhParamsAnnual(
    _p: hvac.PhxHeaterHeatPumpAnnualParams,
) -> List[xml_writable]:
    return [
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
        XML_Node("AnnualCOP", _p.annual_COP),
        XML_Node("TotalSystemPerformanceRatioHeatGenerator", _p.total_system_perf_ratio),
        XML_Node("HPType", _p.hp_type.value),
    ]


def _DeviceHeaterHeatPumpPhParamsMonthly(
    _p: hvac.PhxHeaterHeatPumpMonthlyParams,
) -> List[xml_writable]:
    return [
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
        XML_Node("RatedCOP1", _p.COP_1),
        XML_Node("RatedCOP2", _p.COP_2),
        XML_Node("AmbientTemperature1", _p.ambient_temp_1),
        XML_Node("AmbientTemperature2", _p.ambient_temp_2),
        XML_Node("HPType", _p.hp_type.value),
    ]


def _DeviceHeaterHeatPumpPhParamsHotWater(
    _p: hvac.PhxHeaterHeatPumpHotWaterParams,
) -> List[xml_writable]:
    return [
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
        XML_Node("AnnualCOP", _p.annual_COP),
        XML_Node("TotalSystemPerformanceRatioHeatGenerator", _p.annual_system_perf_ratio),
        XML_Node("HPWH_EF", _p.annual_energy_factor),
        XML_Node("HPType", _p.hp_type.value),
    ]


def _DeviceHeaterHeatPumpPhParamsCombined(
    _p: hvac.PhxHeaterHeatPumpCombinedParams,
) -> List[xml_writable]:
    return [
        XML_Node("AuxiliaryEnergy", _p.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _p.aux_energy_dhw),
        XML_Node("InConditionedSpace", _p.in_conditioned_space),
        XML_Node("HPType", _p.hp_type.value),
    ]


def _DeviceHeaterHeatPumpDeviceParams(_d: hvac.PhxHeaterHeatPump) -> List[xml_writable]:
    return [
        XML_Node("CoverageWithinSystem", _d.percent_coverage),
        XML_Node("Unit", _d.unit),
        XML_Node("Selection", 1),
    ]


def _PhxDeviceWaterStorage(_d: hvac.PhxHotWaterTank) -> List[xml_writable]:
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("SystemType", _d.system_type.value),
        XML_Node("TypeDevice", _d.device_type.value),
        XML_Node("UsedFor_Heating", _d.usage_profile.space_heating),
        XML_Node("UsedFor_DHW", _d.usage_profile.dhw_heating),
        XML_Node("UsedFor_Cooling", _d.usage_profile.cooling),
        XML_Node("UsedFor_Ventilation", _d.usage_profile.ventilation),
        XML_Node("UsedFor_Humidification", _d.usage_profile.humidification),
        XML_Node("UsedFor_Dehumidification", _d.usage_profile.dehumidification),
        XML_Object("PH_Parameters", _d, _schema_name="_DeviceWaterStoragePhParams"),
    ]


def _DeviceWaterStoragePhParams(_t: hvac.PhxHotWaterTank) -> List[xml_writable]:
    return [
        XML_Node("SolarThermalStorageCapacity", _t.params.storage_capacity),
        XML_Node("StorageLossesStandby", _t.params.standby_losses),
        XML_Node("TotalSolarThermalStorageLosses", _t.params.standby_losses),
        XML_Node("InputOption", _t.params.input_option.value),
        XML_Node("AverageHeatReleaseStorage", _t.params.storage_loss_rate),
        XML_Node("TankRoomTemp ", _t.params.room_temp),
        XML_Node("TypicalStorageWaterTemperature", _t.params.water_temp),
        XML_Node("QauntityWS", _t.quantity),
        XML_Node("AuxiliaryEnergy", _t.params.aux_energy),
        XML_Node("AuxiliaryEnergyDHW", _t.params.aux_energy_dhw),
        XML_Node("InConditionedSpace", _t.params.in_conditioned_space),
    ]


# -- MECHANICAL SYSTEMS / DISTRIBUTION ----------------------------------------


class DistributionDHW:
    """Manager class to organize the Hot-Water piping."""

    def __init__(self, _phx_mech_collection: hvac.PhxMechanicalSystemCollection):
        self.phx_mech_collection = _phx_mech_collection
        
        self.calc_method = 1 # Simplified individual pipes
        self.pipe_material = 1 # Copper M
        self.demand_recirc = True
        self.num_bathrooms = 1
        self.hot_water_fixtures = 1
        self.all_pipes_insulated = True
        self.units_or_floors = 1
        self.pipe_diameter_m = 1 # 3/8" Copper
        self.air_temp = 20 # Deg C
        self.water_temp = 60 # Deg C
        self.daily_recirc_hours = 24


def _DistributionDHW(_d: DistributionDHW):
    return [
        # -- Settings
        XML_Node("CalculationMethodIndividualPipes", _d.calc_method),
        XML_Node("DemandRecirculation", _d.demand_recirc),
        XML_Node("SelectionhotWaterFixtureEff", _d.hot_water_fixtures),
        XML_Node("NumberOfBathrooms", _d.num_bathrooms),
        XML_Node("AllPipesAreInsulated", _d.all_pipes_insulated),
        XML_Node("SelectionUnitsOrFloors", _d.units_or_floors),
        XML_Node("PipeMaterialSimplifiedMethod", _d.pipe_material),
        XML_Node("PipeDiameterSimplifiedMethod", _d.pipe_diameter_m),

        # -- Simplified Method
        XML_Node("TemperatureRoom_WR", _d.air_temp),
        XML_Node("DesignFlowTemperature_WR", _d.water_temp),
        XML_Node("DailyRunningHoursCirculation_WR", _d.daily_recirc_hours),
        XML_Node("LengthCirculationPipes_WR", _d.phx_mech_collection.dhw_recirc_total_length_m),
        XML_Node("HeatLossCoefficient_WR", _d.phx_mech_collection.dhw_recirc_weighted_heat_loss_coeff),
        XML_Node("LengthIndividualPipes_WR", _d.phx_mech_collection.dhw_branch_total_length_m),
        XML_Node("ExteriorPipeDiameter_WR", _d.phx_mech_collection.dhw_branch_weighted_diameter_mm),

    # -- Detailed Methods (Not Implemented Yet)
        # XML_Node("HeatReleaseStorage_WR", _d.),
        # XML_Node("HotWaterFixtureEffectiveness", _d.),
    #     XML_Node("LengthCirculationPipes_CR1", _d.),
    #     XML_Node("LengthCirculationPipes_CR2", _d.),
    #     XML_Node("HeatLossCoefficient_CR1", _d.),
    #     XML_Node("HeatLossCoefficient_CR2", _d.),
    #     XML_Node("TemperatureRoom_CR1", _d.),
    #     XML_Node("TemperatureRoom_CR2", _d.),
    #     XML_Node("DesignFlowTemperature_CR1", _d.),
    #     XML_Node("DesignFlowTemperature_CR2", _d.),
    #     XML_Node("DailyRunningHoursCirculation_CR1", _d.),
    #     XML_Node("DailyRunningHoursCirculation_CR2", _d.),
    #     XML_Node("LengthIndividualPipes_CR1", _d.),
    #     XML_Node("LengthIndividualPipes_CR2", _d.),
    #     XML_Node("ExteriorPipeDiameter_CR1", _d.),
    #     XML_Node("ExteriorPipeDiameter_CR2", _d.),
    #     XML_Node("HeatReleaseStorage_CR1", _d.),
    #     XML_Node("HeatReleaseStorage_CR2", _d.),
    ]


class DistributionHeating:
    def __init__(self):
        raise NotImplementedError


def _DistributionHeating(_d):
    raise NotImplementedError
    # return [
    #     XML_Node("LengthPipes_WR", _d.),
    #     XML_Node("LengthPipes_CR1", _d.),
    #     XML_Node("LengthPipes_CR2", _d.),
    #     XML_Node("HeatLossCoefficient_WR", _d.),
    #     XML_Node("HeatLossCoefficient_CR1", _d.),
    #     XML_Node("HeatLossCoefficient_CR2", _d.),
    #     XML_Node("TemperatureRoom_WR", _d.),
    #     XML_Node("TemperatureRoom_CR1", _d.),
    #     XML_Node("TemperatureRoom_CR2", _d.),
    #     XML_Node("DesignFlowTemperature_WR", _d.),
    #     XML_Node("DesignFlowTemperature_CR1", _d.),
    #     XML_Node("DesignFlowTemperature_CR2", _d.),
    #     XML_Node("DesignSystemHeatingLoad_WR", _d.),
    #     XML_Node("DesignSystemHeatingLoad_CR1", _d.),
    #     XML_Node("DesignSystemHeatingLoad_CR2", _d.),
    #     XML_Node("FlowTControl_WR", _d.),
    #     XML_Node("FlowTControl_CR1", _d.),
    #     XML_Node("FlowTControl_CR2", _d.),
    # ]


def _PhxDuctElement(_d: hvac.PhxDuctElement) -> List[xml_writable]:
    return [
        XML_Node("Name", _d.display_name),
        XML_Node("IdentNr", _d.id_num),
        XML_Node("DuctDiameter", _d.diameter, "unit", "mm"),
        XML_Node("DuctShapeHeight", _d.height, "unit", "mm"),
        XML_Node("DuctShapeWidth", _d.width, "unit", "mm"),
        XML_Node("DuctLength", _d.length, "unit", "m"),
        XML_Node("InsulationThickness", _d.insulation_thickness, "unit", "mm"),
        XML_Node("ThermalConductivity", _d.insulation_conductivity, "unit", "W/mK"),
        XML_Node("Quantity", _d.quantity, "unit", "-"),
        XML_Node("DuctType", _d.duct_type.value),
        XML_Node("DuctShape", _d.duct_shape),
        XML_Node("IsReflective", _d.is_reflective),
        XML_List("AssignedVentUnits", [XML_Node('IdentNrVentUnit', id, 'index', i)
                                             for i, id in enumerate(_d.assigned_vent_unit_ids)]),
    ]


"""DEV NOTE: I don't want to have the Cooling distribution as part of the PHX model.
It is stupid that things like COP are stored in there. So use a temp class for now."""


class TempDistributionCooling:
    """Temporary wrapper class for WUFI format Cooling Distribution data"""

    def __init__(self, _devices: List[hvac.AnyPhxCooling]):
        # -- have to sort and combine the systems together
        self.ventilation_device = self.sum_devices(_devices, hvac.CoolingType.VENTILATION)
        self.recirculation_device = self.sum_devices(
            _devices, hvac.CoolingType.RECIRCULATION
        )
        self.dehumidification_device = self.sum_devices(
            _devices, hvac.CoolingType.DEHUMIDIFICATION
        )
        self.panel_device = self.sum_devices(_devices, hvac.CoolingType.PANEL)

    def sum_devices(
        self, _cooling_devices: List[hvac.AnyPhxCooling], _device_type: hvac.CoolingType
    ) -> Optional[hvac.AnyPhxCooling]:
        """Returns a single HVAC Cooling device, made from a list of input devices, or None if no devices found.

        Arguments:
        ----------
            * _cooling_devices:
            * _device_type:

        Returns:
        --------
            * Optional[hvac.AnyPhxCooling]:
        """
        devices = [d for d in _cooling_devices if d.cooling_type == _device_type]
        if len(devices) == 0:
            return None
        else:
            return sum(devices)


def _DistributionCooling(_clg_distr: TempDistributionCooling) -> List[xml_writable]:
    base = []

    if _clg_distr.ventilation_device:
        vent_params: hvac.PhxCoolingVentilationParams = (
            _clg_distr.ventilation_device.params
        )
        base += [
            XML_Node("CoolingViaVentilationAir", True),
            XML_Node("SupplyAirCoolingOnOff", vent_params.single_speed),
            XML_Node("MaxSupplyAirCoolingPower", vent_params.capacity),
            XML_Node("MinTemperatureCoolingCoilSupplyAir", vent_params.min_coil_temp),
            XML_Node("SupplyAirCoolinCOP", vent_params.annual_COP),
        ]
    if _clg_distr.recirculation_device:
        recirc_params: hvac.PhxCoolingRecirculationParams = (
            _clg_distr.recirculation_device.params
        )
        base += [
            XML_Node("CoolingViaRecirculation", True),
            XML_Node("RecirculatingAirOnOff", recirc_params.single_speed),
            XML_Node("MaxRecirculationAirCoolingPower", recirc_params.capacity),
            XML_Node("MinTempCoolingCoilRecirculatingAir", recirc_params.min_coil_temp),
            XML_Node("RecirculationCoolingCOP", recirc_params.annual_COP),
            XML_Node("RecirculationAirVolume", recirc_params.flow_rate_m3_hr),
            XML_Node(
                "ControlledRecirculationVolumeFlow", recirc_params.flow_rate_variable
            ),
        ]
    if _clg_distr.dehumidification_device:
        dehumid_params: hvac.PhxCoolingDehumidificationParams = (
            _clg_distr.dehumidification_device.params
        )
        base += [
            XML_Node("Dehumidification", True),
            XML_Node("UsefullDehumidificationHeatLoss", dehumid_params.useful_heat_loss),
            XML_Node("DehumdificationCOP", dehumid_params.annual_COP),
            XML_Node("SEER", None),
            XML_Node("EER", None),
            XML_Node("DehumidificationElEnergy", None),
        ]
    if _clg_distr.panel_device:
        panel_params: hvac.PhxCoolingPanelParams = _clg_distr.panel_device.params
        base += [
            XML_Node("PanelCooling", True),
            XML_Node("DehumdificationCOP", panel_params.annual_COP),
        ]

    return base


def _PHDistribution(_c: hvac.PhxMechanicalSystemCollection):
    return [
        XML_Object('DistributionDHW', DistributionDHW(_c)),
        # XML_Object('DistributionHeating', DistributionHeating()),
        XML_Object(
            "DistributionCooling",
            TempDistributionCooling(_c.cooling_devices),
            _schema_name="_DistributionCooling",
        ),
        XML_List('DistributionVentilation', [XML_Object('Duct', d, 'index', i)
                                             for i, d in enumerate(_c.vent_ducting)]),
        XML_Node("UseDefaultValues", True),
        XML_Node("DeviceInConditionedSpace", True),
    ]


# -- MECHANICAL SYSTEMS / COLLECTIONS -----------------------------------------


def _PhxZoneCoverage(_zc: hvac.PhxZoneCoverage) -> List[xml_writable]:
    return [
        XML_Node("IdentNrZone", _zc.zone_num),
        XML_Node("CoverageHeating", _zc.zone_num),
        XML_Node("CoverageCooling", _zc.zone_num),
        XML_Node("CoverageVentilation", _zc.zone_num),
        XML_Node("CoverageHumidification", _zc.zone_num),
        XML_Node("CoverageDehumidification", _zc.zone_num),
    ]


def _PhxMechanicalDevices(
    _hvac_collection: hvac.PhxMechanicalSystemCollection,
) -> List[xml_writable]:
    devices = {
        hvac.DeviceType.VENTILATION: "_PhxDeviceVentilator",
        hvac.DeviceType.ELECTRIC: "_PhxDeviceHeaterElec",
        hvac.DeviceType.BOILER: "_PhxDeviceHeaterBoiler",
        hvac.DeviceType.DISTRICT_HEAT: "_PhxDeviceHeaterDistrict",
        hvac.DeviceType.HEAT_PUMP: "_PhxDeviceHeaterHeatPump",
        hvac.DeviceType.WATER_STORAGE: "_PhxDeviceWaterStorage",
    }

    return [
        XML_Node("Name", _hvac_collection.display_name),
        XML_Node(
            "Type", _hvac_collection.sys_type_num, "choice", _hvac_collection.sys_type_str
        ),
        XML_Node("IdentNr", _hvac_collection.id_num),
        XML_List(
            "ZonesCoverage",
            [
                XML_Object("ZoneCoverage", n, "index", i)
                for i, n in enumerate([_hvac_collection.zone_coverage])
            ],
        ),
        XML_List(
            "Devices",
            [
                XML_Object("Device", d, "index", i, _schema_name=devices[d.device_type])
                for i, d in enumerate(_hvac_collection.devices)
            ],
        ),
        XML_Object("PHDistribution", _hvac_collection, _schema_name="_PHDistribution"),
    ]


def _PhxMechanicalSystemCollection(
    _hvac: hvac.PhxMechanicalSystemCollection,
) -> List[xml_writable]:
    return [
        XML_List(
            "Systems",
            [
                XML_Object("System", n, "index", i, _schema_name="_PhxMechanicalDevices")
                for i, n in enumerate([_hvac])
            ],
        ),
    ]


# -- ELEC. EQUIPMENT DEVICES --------------------------------------------------


def _PhxDeviceDishwasher(_d: elec_equip.PhxDeviceDishwasher) -> List[xml_writable]:
    return [
        XML_Node("Type", 1),
        XML_Node("Connection", _d.water_connection),
        XML_Node("DishwasherCapacityPreselection", _d.capacity_type),
        XML_Node("DishwasherCapacityInPlace", _d.capacity),
    ]


def _PhxDeviceClothesWasher(_d: elec_equip.PhxDeviceClothesWasher) -> List[xml_writable]:
    return [
        XML_Node("Type", 2),
        XML_Node("Connection", _d.water_connection),
        XML_Node("UtilizationFactor", _d.utilization_factor),
        XML_Node("CapacityClothesWasher", _d.capacity),
        XML_Node("MEF_ModifiedEnergyFactor", _d.modified_energy_factor),
    ]


def _PhxDeviceClothesDryer(_d: elec_equip.PhxDeviceClothesDryer) -> List[xml_writable]:
    return [
        XML_Node("Type", 3),
        XML_Node("Dryer_Choice", _d.dryer_type),
        XML_Node("GasConsumption", _d.gas_consumption),
        XML_Node("EfficiencyFactorGas", _d.gas_efficiency_factor),
        XML_Node("FieldUtilizationFactorPreselection", _d.field_utilization_factor_type),
        XML_Node("FieldUtilizationFactor", _d.field_utilization_factor),
    ]


def _PhxDeviceRefrigerator(_d: elec_equip.PhxDeviceRefrigerator) -> List[xml_writable]:
    return [
        XML_Node("Type", 4),
    ]


def _PhxDeviceFreezer(_d: elec_equip.PhxDeviceFreezer) -> List[xml_writable]:
    return [
        XML_Node("Type", 5),
    ]


def _PhxDeviceFridgeFreezer(_d: elec_equip.PhxDeviceFridgeFreezer) -> List[xml_writable]:
    return [
        XML_Node("Type", 6),
    ]


def _PhxDeviceCooktop(_d: elec_equip.PhxDeviceCooktop) -> List[xml_writable]:
    return [
        XML_Node("Type", 7),
        XML_Node("CookingWith", _d.cooktop_type),
    ]


def _PhxDeviceMEL(_d: elec_equip.PhxDeviceMEL) -> List[xml_writable]:
    return [
        XML_Node("Type", 13),
    ]


def _PhxDeviceLightingInterior(
    _d: elec_equip.PhxDeviceLightingInterior,
) -> List[xml_writable]:
    return [
        XML_Node("Type", 14),
        XML_Node("FractionHightEfficiency", _d.frac_high_efficiency),
    ]


def _PhxDeviceLightingExterior(
    _d: elec_equip.PhxDeviceLightingExterior,
) -> List[xml_writable]:
    return [
        XML_Node("Type", 15),
        XML_Node("FractionHightEfficiency", _d.frac_high_efficiency),
    ]


def _PhxDeviceLightingGarage(
    _d: elec_equip.PhxDeviceLightingGarage,
) -> List[xml_writable]:
    return [
        XML_Node("Type", 16),
        XML_Node("FractionHightEfficiency", _d.frac_high_efficiency),
    ]


def _PhxDeviceCustomElec(_d: elec_equip.PhxDeviceCustomElec) -> List[xml_writable]:
    return [
        XML_Node("Type", 11),
    ]


def _PhxDeviceCustomLighting(
    _d: elec_equip.PhxDeviceCustomLighting,
) -> List[xml_writable]:
    return [
        XML_Node("Type", 17),
    ]


def _PhxDeviceCustomMEL(_d: elec_equip.PhxDeviceCustomMEL) -> List[xml_writable]:
    return [
        XML_Node("Type", 18),
    ]

def _PhxElevatorHydraulic(_d: elec_equip.PhxElevatorHydraulic) -> List[xml_writable]:
    return [
        XML_Node("Type", 11),
    ]

def _PhxElevatorGearedTraction(_d: elec_equip.PhxElevatorGearedTraction) -> List[xml_writable]:
    return [
        XML_Node("Type", 11),
    ]

def _PhxElevatorGearlessTraction(_d: elec_equip.PhxElevatorGearlessTraction) -> List[xml_writable]:
    return [
        XML_Node("Type", 11),
    ]


def _PhxElectricalDevice(_d: elec_equip.PhxElectricalDevice) -> List[xml_writable]:
    common_attributes = [
        XML_Node("Comment", _d.comment),
        XML_Node("ReferenceQuantity", _d.reference_quantity),
        XML_Node("Quantity", _d.get_quantity()),
        XML_Node("InConditionedSpace", _d.in_conditioned_space),
        XML_Node("ReferenceEnergyDemandNorm", _d.reference_energy_norm),
        XML_Node("EnergyDemandNorm", _d.get_energy_demand()),
        XML_Node("EnergyDemandNormUse", _d.energy_demand_per_use),
        XML_Node("CEF_CombinedEnergyFactor", _d.combined_energy_factor),
    ]

    device_schema = getattr(sys.modules[__name__], f"_{_d.__class__.__name__}")
    appliance_specific_attributes = device_schema(_d)
    return common_attributes + appliance_specific_attributes


# -- NON-RES PROGRAM DATA -----------------------------------------------------


def _UtilizationPattern(_p: PhxScheduleOccupancy) -> List[xml_writable]:
    return [
        XML_Node("IdentNr", ""),
        XML_Node("Name", _p.display_name),
        XML_Node("HeightUtilizationLevel", 0.5),
        XML_Node("BeginUtilization", _p.start_hour),
        XML_Node("EndUtilization", _p.end_hour),
        XML_Node("AnnualUtilizationDays", round(_p.annual_utilization_days, TOL_LEV1)),
        XML_Node("IlluminationLevel", 300, "unit", "lux"),
        XML_Node("RelativeAbsenteeism", _p.relative_utilization_factor, "unit", "-"),
        XML_Node("PartUseFactorPeriodForLighting", 1, "unit", "-"),
        # XML_Node("AverageOccupancy", "", "unit", "m²/Person"),
        # XML_Node("RoomSetpointTemperature", "", "unit", "°C"),
        # XML_Node("HeatingTemperatureReduction", "", "unit", "°C"),
        # XML_Node("DailyUtilizationHours", "", "unit", "hrs/d"),
        # XML_Node("AnnualUtilizationHours", "", "unit", "hrs/yr"),
        # XML_Node("AnnualUtilizationHoursDaytime", "", "unit", "hrs/yr"),
        # XML_Node("AnnualUtilizationHoursNighttime", "", "unit", "hrs/yr"),
        # XML_Node("DailyHeatingOperationHours", "", "unit", "hrs/d"),
        # XML_Node("DailyVentilationOperatingHours", "", "unit", "hrs/d"),
        # XML_Node("NumberOfMaxTabsPerDay", "", "unit", "-"),
    ]


def _LoadPerson(_sp: spaces.PhxSpace) -> List[xml_writable]:
    return [
        XML_Node("Name", _sp.display_name),
        XML_Node("IdentNrUtilizationPattern", 1),
        XML_Node("ChoiceActivityPersons", 3),
        XML_Node("NumberOccupants", 1),
        XML_Node("FloorAreaUtilizationZone", _sp.floor_area, "unit", "m²"),
    ]
