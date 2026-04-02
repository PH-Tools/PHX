# -*- Python Version: 3.10 -*-

"""Conversion schemas for writing PHX objects to METr JSON format.

Each function is named `_ClassName` matching the PHX class and returns a dict (or list).
The converter discovers these by class name: PhxProject → _PhxProject(), etc.
"""

import operator
from datetime import datetime
from functools import reduce
from typing import Any

from PHX.model import (
    building,
    certification,
    components,
    constructions,
    elec_equip,
    geometry,
    ground,
    phx_site,
    project,
    shades,
    spaces,
)
from PHX.model.enums.hvac import DeviceType, PhxHotWaterPipingInchDiameterType
from PHX.model.hvac import collection as hvac_collection
from PHX.model.hvac import heat_pumps, heating, renewable_devices, water
from PHX.model.hvac import ventilation as hvac_ventilation
from PHX.model.schedules import occupancy, ventilation

TOL_LEV1 = 2  # Rounding tolerance: 9.843181919194 -> 9.84
TOL_LEV2 = 10  # Rounding tolerance: 9.843181919194 -> 9.8431819192


# -- Utility -------------------------------------------------------------------


NaN = "NaN"  # METR uses the literal string "NaN" for undefined numeric values


def _color_array(c: constructions.PhxColor) -> list[int]:
    """Convert a PhxColor to METR [A, R, G, B] array."""
    return [c.alpha, c.red, c.green, c.blue]


def _date_array(d: project.PhxProjectDate) -> list[int]:
    """Convert a PhxProjectDate to METR [year, month, day, hour, minute, second] array."""
    return [d.year, d.month, d.day, d.hour, d.minutes, 0]


# -- PROJECT -------------------------------------------------------------------


def _PhxProject(_p: project.PhxProject) -> dict:
    # -- Collect all unique materials across all assemblies into a global list.
    # -- METR-JSON stores materials separately from assemblies, referenced by ID.
    # -- Deduplicate by id_num (mixed-material layers can cause duplicates).
    all_materials: dict[int, constructions.PhxMaterial] = {}
    for assembly in _p.assembly_types.values():
        for layer in assembly.layers:
            for mat in layer.materials:
                if mat.id_num not in all_materials:
                    all_materials[mat.id_num] = mat

    return {
        "progVers": "3.5.0.1",
        "SIIP": 2,
        "calcScope": 4,
        "dimVisGeom": _p.visualized_geometry,
        "projD": _PhxProjectData(_p.project_data),
        "lMaterial": [_PhxMaterial(m) for m in all_materials.values()],
        "lAssembly": [_PhxConstructionOpaque(a) for a in _p.assembly_types.values()],
        "lWindow": [_PhxConstructionWindow(w) for w in _p.window_types.values()],
        "lSolProt": [_PhxWindowShade(s) for s in _p.shade_types.values()],
        "lOverhang": [],  # TODO: Phase 3 — overhangs
        "lUtilNResPH": [_UtilizationPattern(pat) for pat in _p.utilization_patterns_occupancy],
        "lUtilVentPH": [_UtilizationPatternVent(pat) for pat in _p.utilization_patterns_ventilation],
        "lFile": [],
        "timeProf": _build_time_profiles(_p),
        "lVariant": [_PhxVariant(v) for v in _p.variants],
    }


# -- PROJECT DATA --------------------------------------------------------------


def _PhxProjectData(_pd: project.PhxProjectData) -> dict:
    return {
        "cN": _pd.customer.name or "",
        "cLoc": _pd.customer.city or "",
        "cPostC": _pd.customer.post_code or "",
        "cStr": _pd.customer.street or "",
        "cTel": _pd.customer.telephone or "",
        "cEmail": _pd.customer.email or "",
        "bN": _pd.building.name or "",
        "bYCon": str(_pd.year_constructed),
        "bLoc": _pd.building.city or "",
        "bPostC": _pd.building.post_code or "",
        "bStr": _pd.building.street or "",
        "oIsC": _pd.owner_is_client,
        "oN": _pd.owner.name or "",
        "oLoc": _pd.owner.city or "",
        "oPostC": _pd.owner.post_code or "",
        "oStreet": _pd.owner.street or "",
        "rN": _pd.designer.name or "",
        "rLoc": _pd.designer.city or "",
        "rPostC": _pd.designer.post_code or "",
        "rStr": _pd.designer.street or "",
        "rTel": _pd.designer.telephone or "",
        "rLic": _pd.designer.license_number or "",
        "rEmail": _pd.designer.email or "",
        "date": _date_array(_pd.project_date),
        "wBkg": bool(_pd.image),
    }


# -- MATERIALS -----------------------------------------------------------------


def _PhxMaterial(_m: constructions.PhxMaterial) -> dict:
    return {
        "id": _m.id_num,
        "idDB": 0,
        "n": _m.display_name,
        "tConD": _m.conductivity,
        "densB": _m.density,
        "poros": _m.porosity,
        "hCapS": _m.heat_capacity,
        "difRes": _m.water_vapor_resistance,
        "refWC": _m.reference_water,
        "freeWSat": "NaN",
        "wACoef": "NaN",
        "tConSupM": "NaN",
        "tConSupT": "NaN",
        "typMC": "NaN",
        "typeSA": 1,
        "color": _color_array(_m.argb_color),
        # -- Hygric property curves (defaults)
        "lRHWC": [[0.0, 0.0]],
        "lnWCSuc": [[0.0, 0.0]],
        "lnWCRed": [[0.0, 0.0]],
        "lnWCTCond": [[0.0, _m.conductivity]],
        "lRHDiffRes": [[0.0, _m.water_vapor_resistance]],
        "lTEnth": [],
        "lTtCond": [],
        "RHWCGen": False,
        "nWCSucGen": False,
        "nWCRedGen": False,
        "nWCtCondGen": False,
        "TtCondGen": False,
    }


# -- ASSEMBLIES ----------------------------------------------------------------


def _PhxConstructionOpaque(_a: constructions.PhxConstructionOpaque) -> dict:
    return {
        "id": _a.id_num,
        "idDB": 0,
        "n": _a.display_name,
        "orderL": _a.layer_order,
        "typeGr": _a.grid_kind,
        "tRes": _a.r_value,
        "tRes6946": _a.r_value,
        "lLayer": [
            {
                "thick": layer.thickness_m,
                "idMat": layer.material.id_num,
            }
            for layer in _a.layers
        ],
    }


# -- WINDOW TYPES --------------------------------------------------------------


def _PhxConstructionWindow(
    _wt: constructions.PhxConstructionWindow,
) -> dict:
    return {
        "id": _wt.id_num,
        "idDB": 0,
        "n": _wt.display_name,
        "detU": _wt.use_detailed_uw,
        "detGd": False,  # Always use simplified glazing mode — PHX doesn't have detailed layer data
        "Uw": _wt.u_value_window,
        "frF": _wt.frame_factor,
        "trHem": _wt.glass_g_value,
        "secDispH": 0.0,
        "lwEmis": _wt.glass_mean_emissivity,
        "glazU": _wt.u_value_glass,
        "Ufr": _wt.u_value_frame,
        "trHemShade": 0.0,
        "frSWAbs": 0.0,
        "frEmisE": 0.8,
        "frEmisI": 0.8,
        "gtr": _wt.glass_g_value,
        "lAngleTr": [[0.0, 0.0, 0.0]],
        "lWLayer": [
            {
                "typeWl": 1,
                "thick": NaN,
                "color": [224, 255, 255, 255],
                "tCond": NaN,
                "emisE": NaN,
                "emisI": NaN,
                "absHem": NaN,
                "absSwI": NaN,
                "absHemShade": NaN,
                "absIShade": NaN,
                "lAngleAbs": [[0.0, 0.0, 0.0]],
            }
        ],
        "lrtbFrW": [
            _wt.frame_top.width,
            _wt.frame_right.width,
            _wt.frame_bottom.width,
            _wt.frame_left.width,
        ],
        "lrtbFrU": [
            _wt.frame_top.u_value,
            _wt.frame_right.u_value,
            _wt.frame_bottom.u_value,
            _wt.frame_left.u_value,
        ],
        "lrtbGlPsi": [
            _wt.frame_top.psi_glazing,
            _wt.frame_right.psi_glazing,
            _wt.frame_bottom.psi_glazing,
            _wt.frame_left.psi_glazing,
        ],
        "lrtbFrPsi": [
            _wt.frame_top.psi_install,
            _wt.frame_right.psi_install,
            _wt.frame_bottom.psi_install,
            _wt.frame_left.psi_install,
        ],
    }


# -- SOLAR PROTECTION / SHADING DEVICES ----------------------------------------


def _PhxWindowShade(_s: shades.PhxWindowShade) -> dict:
    return {
        "id": _s.id_num,
        "n": _s.display_name,
        "opModeSolP": _s.operation_mode,
        "maxRedSolP": _s.reduction_factor,
        "eEmisSolP": _s.external_emissivity,
        "eAbsSolP": _s.absorptivity,
        "tResSolP": _s.thermal_resistance_supplement,
        "tResCavSolP": _s.thermal_resistance_cavity,
        "limRadsolP": _s.radiation_limit,
        "exclWendSolP": _s.exclude_weekends,
        "limDINSolP": True,
    }


# -- UTILIZATION PATTERNS (VENTILATION) ----------------------------------------


def _UtilizationPatternVent(
    _vs: ventilation.PhxScheduleVentilation,
) -> dict:
    op = _vs.operating_periods
    return {
        "n": _vs.name,
        "id": _vs.id_num,
        "OperDw": _vs.operating_days,
        "OperWy": _vs.operating_weeks,
        "MSBMdf": [
            [round(op.high.period_operating_hours, TOL_LEV1), round(op.high.period_operation_speed, TOL_LEV1)],
            [round(op.standard.period_operating_hours, TOL_LEV1), round(op.standard.period_operation_speed, TOL_LEV1)],
            [round(op.basic.period_operating_hours, TOL_LEV1), round(op.basic.period_operation_speed, TOL_LEV1)],
            [round(op.minimum.period_operating_hours, TOL_LEV1), round(op.minimum.period_operation_speed, TOL_LEV1)],
        ],
    }


# -- UTILIZATION PATTERNS (OCCUPANCY / NON-RES PH) ----------------------------


def _UtilizationPattern(_p: occupancy.PhxScheduleOccupancy) -> dict:
    return {
        "id": _p.id_num,
        "n": _p.display_name,
        "hUtilL": 1,
        "beginU": _p.start_hour,
        "endU": _p.end_hour,
        "aUtil": round(_p.annual_utilization_days, TOL_LEV1),
        "illumLev": 300.0,
        "relAbs": _p.relative_utilization_factor,
        "pUfLight": 1.0,
        "aOccup": NaN,
        "rSetpT": NaN,
        "hRedT": NaN,
        "dUtilH": NaN,
        "aUtilH": NaN,
        "aUtHDt": NaN,
        "aUtHNt": NaN,
        "dHOpH": NaN,
        "dVentOpH": NaN,
        "maxTabD": NaN,
    }


# -- TIME PROFILES (mostly static defaults) -----------------------------------


def _build_time_profiles(_p: project.PhxProject) -> dict:
    """Build the timeProf section. Mostly static defaults for PH modeling."""
    now = datetime.now()

    # -- Standard 14 value profiles (zone boundary conditions)
    value_profiles = [
        {"id": 1, "n": "Value profile: 1", "u": 14, "k": "zT", "lV": [20.0]},
        {"id": 2, "n": "Value profile: 2", "u": 14, "k": "zTm", "lV": [27.0]},
        {"id": 3, "n": "Value profile: 3", "u": 22, "k": "zRH", "lV": [40.0]},
        {"id": 4, "n": "Value profile: 4", "u": 22, "k": "zRHm", "lV": [70.0]},
        {"id": 5, "n": "Value profile: 5", "u": 48, "k": "zCO2c", "lV": [3000.0]},
        {"id": 6, "n": "Value profile: 6", "u": 29, "k": "zV", "lV": [0.5]},
        {"id": 7, "n": "Value profile: 7", "u": 29, "k": "zMV", "lV": [0.0]},
        {"id": 8, "n": "Value profile: 8", "u": 56, "k": "zlM", "lV": [0.0]},
        {"id": 9, "n": "Value profile: 9", "u": 53, "k": "zlHC", "lV": [0.0]},
        {"id": 10, "n": "Value profile: 10", "u": 53, "k": "zlHR", "lV": [0.0]},
        {"id": 11, "n": "Value profile: 11", "u": 56, "k": "zlCO2", "lV": [0.0]},
        {"id": 12, "n": "Value profile: 12", "u": 60, "k": "zlHA", "lV": [0.0]},
        {"id": 13, "n": "Value profile: 13", "u": 61, "k": "zlClo", "lV": [0.7]},
        {"id": 14, "n": "Value profile: 14", "u": 62, "k": "zlAV", "lV": [0.1]},
    ]

    # -- Add HVAC capacity profiles if any variant has devices
    has_devices = any(len(mc.devices) > 0 for v in _p.variants for mc in v.mech_collections)
    if has_devices:
        value_profiles.extend(
            [
                {"id": 15, "n": "Value profile: 15", "u": 54, "k": "cH", "lV": [50.0]},
                {"id": 16, "n": "Value profile: 16", "u": 54, "k": "cC", "lV": [50.0]},
                {"id": 17, "n": "Value profile: 17", "u": 51, "k": "cV", "lV": [1000.0]},
            ]
        )

    return {
        "lTimeP": [
            {"id": 1, "n": "Time profile: 1", "lT": [0.0]},
        ],
        "lValP": value_profiles,
        "lProfile": [
            {
                "id": -1,
                "n": "Periode: 1",
                "begin": [now.year, 1, 1, 0, 0, 0],
                "end": [now.year + 1, 1, 1, 0, 0, 0],
                "dayMS": [True, True, True, True, True, True, True],
            },
        ],
    }


# -- VARIANTS ------------------------------------------------------------------


def _PhxVariant(_v: project.PhxVariant) -> dict:
    foundations = _v.phius_cert.ph_building_data.foundations
    return {
        "id": _v.id_num,
        "n": _v.name,
        "remarks": _v.remarks or "",
        "geom": _PhxGraphics3D(_v.graphics3D),
        "calcScope": -1,
        "HaMT": _build_default_HaMT(),
        "PHIUS": _PhxPhiusCertification(_v.phius_cert),
        "DIN4108": {"selC4108": 1, "reg4108": 2},
        "cliLoc": _PhxSite(_v.site, _v.phius_cert.phius_certification_criteria),
        "building": _PhxBuilding(_v.building, foundations),
        "HVAC": _Systems(_v._mech_collections),
        "res": {
            "cCurv": 0,
            "indexMC": -1,
            "posResF": 0.0,
            "lResF": 0.0,
        },
    }


def _build_default_HaMT() -> dict:
    """Default hygrothermal simulation parameters. Static for PH modeling."""
    now = datetime.now()
    return {
        "calcStart": [now.year, 1, 1, 0, 0, 0],
        "calcEnd": [now.year + 1, 1, 1, 0, 0, 0],
        "resTStep": 1.0,
        "interpCli": True,
        "prelCTime": 0.0,
        "cpyDesC": 4,
        "selCTH": 1,
        "cAccur": 2,
        "tIniPer": 2,
        "dayWeek": 4,
        "numB": {
            "shadeNB": True,
            "airFNB": False,
            "explRadEs": False,
            "htWDepNB": False,
            "rainNB": False,
            "enLRadIs": False,
            "mBalTNB": True,
            "selShadeNB": 1,
        },
        "plugIn": {
            "uPlugIn": False,
            "filePI": "",
            "strPI": "",
            "lParPI": [],
            "lResPI": [],
        },
    }


# -- GEOMETRY ------------------------------------------------------------------


def _PhxGraphics3D(_g3d: geometry.PhxGraphics3D) -> dict:
    return {
        "lIDXYZ": [[v.id_num, v.x, v.y, v.z] for v in _g3d.vertices],
        "lPoly": [_PhxPolygon(p) for p in _g3d.polygons],
    }


def _PhxPolygon(_p: geometry.PhxPolygon) -> dict:
    # -- Derive height above ground from vertex z-coordinates
    z_coords = [v.z for v in _p.vertices]
    min_z = min(z_coords) if z_coords else 0.0
    max_z = max(z_coords) if z_coords else 0.0
    h_above_ground = (min_z + max_z) / 2.0

    # -- Derive horizontal width and vertical height
    if isinstance(_p, geometry.PhxPolygonRectangular):
        hor_width = _p.width
        vert_height = _p.height
    else:
        # Estimate from bounding box for non-rectangular polygons
        x_coords = [v.x for v in _p.vertices]
        y_coords = [v.y for v in _p.vertices]
        dx = max(x_coords) - min(x_coords) if x_coords else 0.0
        dy = max(y_coords) - min(y_coords) if y_coords else 0.0
        dz = max_z - min_z
        if _p.is_horizontal:
            hor_width = max(dx, dy)
            vert_height = min(dx, dy)
        else:
            hor_width = max(dx, dy)
            vert_height = dz

    return {
        "id": _p.id_num,
        "areaP": round(_p.area, 6),
        "incl": round(_p.angle_from_horizontal, 6),
        "azimY": round(_p.cardinal_orientation_angle, 6),
        "horW": round(hor_width, 6),
        "perim": round(_p.perimeter_length(), 6),
        "hAGr": round(h_above_ground, 6),
        "vertH": round(vert_height, 6),
        "nVec": [_p.normal_vector.x, _p.normal_vector.y, _p.normal_vector.z],
        "idVert": _p.vertices_id_numbers,
        "idPolyI": _p.child_polygon_ids,
    }


# -- BUILDING ------------------------------------------------------------------


def _PhxBuilding(_b: building.PhxBuilding, _foundations: list[ground.PhxFoundation] | None = None) -> dict:
    # -- Collect all components: opaque (incl. shades) first, then apertures.
    # -- _b._components has all opaque; _b.aperture_components has all apertures.
    all_components: list[dict] = []
    for c in _b._components:
        all_components.append(_PhxComponentOpaque(c, len(all_components)))
    for c in _b.aperture_components:
        all_components.append(_PhxComponentAperture(c, len(all_components)))

    return {
        "OrAzim": 1,
        "orient": 1,
        "azimN": 180.0,
        "setAF": 1,
        "heightB": {"sel": 2, "val": [None, None], "iV": 0},
        "facWwe": {"sel": 6, "val": [None, None], "iV": 1},
        "facWns": {"sel": 6, "val": [None, None], "iV": 1},
        "bLocCat": 3,
        "uWBLThic": NaN,
        "uExpWindP": NaN,
        "distrComp": 1,
        "infilB50": NaN,
        "infilExpB": NaN,
        "coefLeakB": 0.7,
        "expLeakB": NaN,
        "efLeakAB": NaN,
        "presDifB": NaN,
        "refDisCB": NaN,
        "refFExpB": NaN,
        "opCompB": 0.7,
        "trCompB": 0.15,
        "ceilRoofB": 0.15,
        "fanZoneB": -1,
        "closeEWB": 1,
        "closeEOB": 1,
        "openInDB": 1,
        "openInOB": 1,
        "dPresB": 50.0,
        "overwrPB": False,
        "lComponent": all_components,
        "lZone": [_PhxZone(z, _foundations or []) for z in _b.zones],
        "lObj3D": [],
        "generB": _build_default_generB(),
        "countGenB": 0,
        "wasGenB": False,
        "chdSLGB": False,
    }


def _build_default_generB() -> dict:
    """Default building geometry generator parameters."""
    return {
        "mainSec": 1,
        "tRoof": 1,
        "tBottom": 1,
        "d1Rect": 12.0,
        "d2Rect": 9.0,
        "d1LS": 7.0,
        "d2LS": 7.0,
        "d3LS": 5.0,
        "d4LS": 7.0,
        "d1TS": 7.0,
        "d2TS": 6.0,
        "d3TS": 5.0,
        "d4TS": 4.0,
        "d5TS": 7.0,
        "h1Roof": 0.5,
        "h2Roof": 1.0,
        "h3Roof": 2.65,
        "inclR": 40.0,
        "gableEnd": False,
        "offsetR": 0.8,
        "h1Cel": 1.5,
        "h2Cel": 2.5,
        "hFirstS": 2.8,
        "hStor": 2.8,
        "cStor": 1,
        "groupCg": True,
    }


# -- COMPONENTS ----------------------------------------------------------------


def _component_surface_defaults(
    _face_type_value: int,
    _exposure_ext_value: int,
) -> dict:
    """Return default surface physics values based on component orientation.

    These are hygrothermal defaults not relevant to static PH modeling.
    """
    # Rsi/Rse depend on component type and exposure
    is_floor = _face_type_value == 2  # ComponentFaceType.FLOOR
    is_roof = _face_type_value == 3  # ComponentFaceType.ROOF_CEILING
    is_ground = _exposure_ext_value == -2  # ComponentExposureExterior.GROUND

    if is_ground and is_floor:
        rse = 0.0
        rsi = 0.17
        alfa_ci = 2.5
        alfa_ri = 3.382353
        alfa_ce = 99999.0
        alfa_re = 0.0
    elif is_ground:
        # Ground-contact walls: wall-type interior coefficients, ground exterior
        rse = 0.0
        rsi = 0.13
        alfa_ci = 3.192308
        alfa_ri = 4.5
        alfa_ce = 99999.0
        alfa_re = 0.0
    elif is_roof:
        rse = 0.04
        rsi = 0.1
        alfa_ci = 5.5
        alfa_ri = 4.5
        alfa_ce = 18.5
        alfa_re = 6.5
    else:
        # Wall or exterior floor
        rse = 0.04
        rsi = 0.13
        alfa_ci = 3.192308
        alfa_ri = 4.5
        alfa_ce = 18.5
        alfa_re = 6.5

    return {
        "selRsC": 1,
        "Rse": rse,
        "Rsi": rsi,
        "alfaCiC": alfa_ci,
        "alfaRiC": alfa_ri,
        "alfaCeC": alfa_ce,
        "alfaReC": alfa_re,
        "eCliC": 1,
        "idOptCliC": -1,
        "partSolIC": NaN,
        "solIPaC": NaN,
        "emisEC": 0.9,
        "emisIC": 0.9,
        "airFmC": False,
        "alfaWindBC": 4.5,
        "alfaWinwardC": 1.6,
        "alfaLeewardC": 0.33,
        "shadeC": 1.0,
        "idIsurfC": -1,
        "partSolEC": NaN,
        "solEPaC": NaN,
        "tAbsC": -2,
        "absEC": 0.4,
        "selSdeC": -1,
        "sdeC": 0.0 if is_ground else None,
        "selSdiC": -1,
        "sdiC": 0.0 if is_ground else None,
        "selIniMC": 1,
        "iniRHC": 0.8,
        "iniTC": 20.0,
        "lIniWcC": [],
        "tRainLC": -1,
        "tRainAC": -1,
        "rainR1C": 0.0,
        "rainR2C": 0.0,
        "rainAC": 0.0,
        "numC": {
            "cHeatC": True,
            "cMoistC": True,
            "exclCapilC": False,
            "exclEvC": False,
            "exclFusC": False,
            "incrAccurC": True,
            "adConvC": True,
        },
        "lMonPos": [],
        "synchrPFC": True,
        "lrtbFrPsi": [NaN, NaN, NaN, NaN],
        "depthWRevC": NaN,
        "distGlasC": 0.05,
        "widthWC": NaN,
        "hAGrC": {"sel": 6, "val": [None, None], "iV": 1},
        "retainResC": False,
        "obstrHC": 0.0,
        "obstrDC": 0.0,
        "otherShadeC": 1.0,
        "shadeSumC": 1.0,
        "eDoorC": False,
        "coolLTdifC": NaN,
        "multHTrC": NaN,
        "multShadeLC": NaN,
        "dCorShadeMC": 1.0,
        "corShadeMC": [NaN] * 12,
        "typeLAf": 2,
        "fDistrAf": NaN,
        "expAf": 0.65,
        "cFlowAf": NaN,
        "exFAf": NaN,
        "cFlowCAf": NaN,
        "addContrAf": 1,
    }


def _PhxComponentOpaque(_c: components.PhxComponentOpaque, _index: int) -> dict:
    """Convert a PhxComponentOpaque to a METR JSON component dict."""
    total_area = _c.get_total_net_component_area()

    # -- Get U-value from assembly
    try:
        u_value = _c.assembly.u_value
    except ZeroDivisionError:
        u_value = 0.0

    result = {
        "id": _c.id_num,
        "idSKP": -1,
        "itv": _index,
        "n": _c.display_name,
        "visC": True,
        "idIC": _c.exposure_interior,
        "idEC": _c.exposure_exterior.value,
        "typeC": _c.face_opacity.value,
        "areaC": round(total_area, 6),
        "Uph": round(u_value, 6),
        "Uhom": round(u_value, 6),
        "inclC": 90.0,
        "orient": 1,
        "azimN": 180.0,
        "retRes": False,
        "idAssC": _c.assembly_type_id_num,
        "idWtC": -1,
        "idSolPC": -1,
        "idOverhC": -1,
        "countC": 1,
        "OrAzim": 1,
        "idCompInC": _c.interior_attachment_id,
        "calculAC": {"res": "----", "OK": False, "lExpr": []},
    }

    # -- Add surface physics defaults
    result.update(
        _component_surface_defaults(
            _c.face_type.value,
            _c.exposure_exterior.value,
        )
    )

    # -- Colors and polygon references
    result.update(
        {
            "idColorIC": _c.color_interior.value,
            "idColorEC": _c.color_exterior.value,
            "colorEC": [255, 255, 255, 255],
            "colorIC": [255, 255, 255, 255],
            "idPolyC": sorted(_c.polygon_ids),
            "lPartOr": [],
        }
    )

    return result


def _PhxComponentAperture(_c: components.PhxComponentAperture, _index: int) -> dict:
    """Convert a PhxComponentAperture to a METR JSON component dict."""
    total_area = _c.get_total_aperture_area()

    result = {
        "id": _c.id_num,
        "idSKP": -1,
        "itv": _index,
        "n": _c.display_name,
        "visC": True,
        "idIC": _c.exposure_interior,
        "idEC": _c.exposure_exterior.value,
        "typeC": _c.face_opacity.value,
        "areaC": round(total_area, 6),
        "Uph": round(_c.window_type.u_value_window, 6) if _c.window_type else 0.0,
        "Uhom": round(_c.window_type.u_value_window, 6) if _c.window_type else 0.0,
        "inclC": 90.0,
        "orient": 1,
        "azimN": 180.0,
        "retRes": False,
        "idAssC": -1,
        "idWtC": _c.window_type.id_num if _c.window_type else -1,
        "idSolPC": _c.shade_type_id_num if hasattr(_c, "shade_type_id_num") else -1,
        "idOverhC": -1,
        "countC": 1,
        "OrAzim": 1,
        "idCompInC": _c.interior_attachment_id,
        "calculAC": {"res": "----", "OK": False, "lExpr": []},
    }

    # -- Add surface physics defaults (use wall defaults for windows)
    result.update(_component_surface_defaults(1, _c.exposure_exterior.value))

    # -- Aperture-specific overrides
    result["depthWRevC"] = _c.install_depth
    result["distGlasC"] = _c.average_shading_d_reveal or (_c.window_type.frame_top.width if _c.window_type else 0.05)
    result["dCorShadeMC"] = _c.default_monthly_shading_correction_factor
    # -- shadeC/shadeSumC stay at 1.0 (from surface defaults). When monthly shading
    # -- is enabled (wShade=True), METR uses dCorShadeMC instead of these simple factors.
    # -- Setting them to non-1.0 would cause double-counting.

    # -- Colors and polygon references
    result.update(
        {
            "idColorIC": _c.color_interior.value,
            "idColorEC": _c.color_exterior.value,
            "colorEC": [255, 255, 255, 255],
            "colorIC": [255, 255, 255, 255],
            "idPolyC": sorted(_c.polygon_ids),
            "lPartOr": [],
        }
    )

    return result


# -- ZONES ---------------------------------------------------------------------


def _zone_design_conditions() -> dict:
    """Default zone design conditions, referencing value profiles by ID."""
    return {
        "minTZ": {"PF": 1, "PTVid": [[-1, 1, 1]], "FCid": [-1, -1]},
        "maxTZ": {"PF": 1, "PTVid": [[-1, 1, 2]], "FCid": [-1, -1]},
        "minRHZ": {"PF": 1, "PTVid": [[-1, 1, 3]], "FCid": [-1, -1]},
        "maxRHZ": {"PF": 1, "PTVid": [[-1, 1, 4]], "FCid": [-1, -1]},
        "maxCO2Z": {"PF": 1, "PTVid": [[-1, 1, 5]], "FCid": [-1, -1]},
        "ventZ": {"PF": 1, "PTVid": [[-1, 1, 6]], "FCid": [-1, -1]},
        "mVentZ": {"PF": 1, "PTVid": [[-1, 1, 7]], "FCid": [-1, -1]},
        "lIZVentZ": [],
        "infiltrZ": 0.1,
        "mVCZ": 1,
        "minTDifZ": 3.0,
        "minTeZ": 0.0,
        "minRHdifZ": 0.5,
        "minCO2difZ": 0.1,
        "nABZ": 2,
        "sumVentDay": 0.0,
        "sumMVentNight": NaN,
        "addMVendEA": NaN,
        "sumVentNight": 0.0,
        "lSumVentD": [],
        "lSumVentN": [],
        "TRedUD": 1.0,
    }


def _zone_loads(_z: building.PhxZone) -> dict:
    """Zone loads including appliances and lighting."""
    return {
        "mLz": {"PF": 1, "PTVid": [[-1, 1, 8]], "FCid": [-1, -1]},
        "hcLz": {"PF": 1, "PTVid": [[-1, 1, 9]], "FCid": [-1, -1]},
        "hrLz": {"PF": 1, "PTVid": [[-1, 1, 10]], "FCid": [-1, -1]},
        "CO2Lz": {"PF": 1, "PTVid": [[-1, 1, 11]], "FCid": [-1, -1]},
        "haLz": {"PF": 1, "PTVid": [[-1, 1, 12]], "FCid": [-1, -1]},
        "cloLz": {"PF": 1, "PTVid": [[-1, 1, 13]], "FCid": [-1, -1]},
        "avLz": {"PF": 1, "PTVid": [[-1, 1, 14]], "FCid": [-1, -1]},
        "nOcc": int(_z.res_occupant_quantity),
        "humSour": 2.0,
        "lPersZ": [_LoadsOccupancy(sp) for sp in _z.spaces],
        "lOffEq": [],
        "lAuxEl": [],
        "lLight": [_LoadsLighting(sp) for sp in _z.spaces],
        "lProces": [],
        "lHomeDev": [_PhxElectricalDevice(d) for d in _z.elec_equipment_collection.devices],
    }


def _zone_calc_params() -> dict:
    """Default zone calculation parameters."""
    return {
        "iniTz": 20.0,
        "iniRHz": 55.0,
        "iniCO2z": 400.0,
        "uCO2z": 48,
        "absSolAirZ": 0.1,
        "solDistrZ": 1,
        "hContrZ": 1,
        "hContrParZ": 1,
        "idZthZ": -1,
        "LRadIs": False,
        "redMVHumHz": False,
        "aLTHHz": False,
        "minTHumHz": 7.0,
    }


def _sel_val(_value: float | None, _sel: int = 6) -> dict:
    """Build a standard selection/value object for foundation fields."""
    return {"sel": _sel, "val": [_value, None], "iV": 0}


def _PhxFoundation(_f: ground.PhxFoundation, _zone_id: int = -1) -> dict:
    """Convert a PhxFoundation to a METR JSON foundation dict.

    METR uses a 'super-foundation' pattern: all fields are present regardless of
    foundation type. The `typFound` field determines which fields are active.
    `idZrel` links the foundation to a zone for automatic U-value detection.
    """
    # -- Common fields
    d: dict[str, Any] = {
        "n": _f.display_name,
        "posPerIns": 1,
        "perInsWD": 0.0,
        "thickPer": 0.0,
        "condPer": 0.04,
        "flSlabTs": _f.foundation_setting_num.value,
        "typFound": _f.foundation_type_num.value,
        "phShiftMG": NaN,
        "harmFrac": NaN,
        "bmentACH": 0.0,
        "bmentDepth": _sel_val(0.0),
        "hbmentWAG": _sel_val(0.0),
        "hcsWAG": _sel_val(0.0),
        "crowlSVentO": _sel_val(0.0),
        "flSArea": {"sel": 6, "val": [None], "iV": 0},
        "bmentFlU": _sel_val(0.0),
        "slabFlU": _sel_val(0.0),
        "ceilCelA": {"sel": 6, "val": [None], "iV": 0},
        "ceToUCU": _sel_val(0.0),
        "bmentWU": _sel_val(0.0),
        "wallUAG": _sel_val(0.0),
        "wallUcsAG": _sel_val(0.0),
        "flPer": _sel_val(0.0),
        "bmentVol": _sel_val(0.0),
        "crawlFlU": _sel_val(0.0),
    }

    # -- Type-specific overrides
    if isinstance(_f, ground.PhxHeatedBasement):
        d["flSArea"] = {"sel": 6, "val": [_f.floor_slab_area_m2], "iV": 0}
        d["flPer"] = _sel_val(_f.floor_slab_exposed_perimeter_m)
        d["bmentFlU"] = _sel_val(_f.floor_slab_u_value)
        d["slabFlU"] = _sel_val(_f.floor_slab_u_value)
        d["bmentDepth"] = _sel_val(_f.slab_depth_below_grade_m)
        d["bmentWU"] = _sel_val(_f.basement_wall_u_value)

    elif isinstance(_f, ground.PhxUnHeatedBasement):
        d["bmentDepth"] = _sel_val(_f.slab_depth_below_grade_m)
        d["hbmentWAG"] = _sel_val(_f.basement_wall_height_above_grade_m)
        d["flSArea"] = {"sel": 6, "val": [_f.floor_ceiling_area_m2], "iV": 0}
        d["bmentFlU"] = _sel_val(_f.floor_slab_u_value)
        d["ceilCelA"] = {"sel": 6, "val": [_f.floor_ceiling_area_m2], "iV": 0}
        d["ceToUCU"] = _sel_val(_f.ceiling_u_value)
        d["bmentWU"] = _sel_val(_f.basement_wall_uValue_below_grade)
        d["wallUAG"] = _sel_val(_f.basement_wall_uValue_above_grade)
        d["flPer"] = _sel_val(_f.floor_slab_exposed_perimeter_m)
        d["bmentVol"] = _sel_val(_f.basement_volume_m3)
        d["bmentACH"] = _f.basement_ventilation_ach or 0.0

    elif isinstance(_f, ground.PhxSlabOnGrade):
        # -- If no user-defined U-value, use sel=2 ("Detect Automatically")
        if _f.floor_slab_u_value is None:
            slab_u_sel = 2
        else:
            slab_u_sel = 6
        d["flSArea"] = {"sel": 6, "val": [_f.floor_slab_area_m2], "iV": 0}
        d["slabFlU"] = _sel_val(_f.floor_slab_u_value, _sel=slab_u_sel)
        d["bmentFlU"] = _sel_val(_f.floor_slab_u_value, _sel=slab_u_sel)
        d["flPer"] = _sel_val(_f.floor_slab_exposed_perimeter_m)
        d["posPerIns"] = _f.perim_insulation_position.value
        d["perInsWD"] = _f.perim_insulation_width_or_depth_m or 0.0
        d["thickPer"] = _f.perim_insulation_thickness_m or 0.0
        d["condPer"] = _f.perim_insulation_conductivity or 0.04

    elif isinstance(_f, ground.PhxVentedCrawlspace):
        d["ceilCelA"] = {"sel": 6, "val": [_f.crawlspace_floor_slab_area_m2], "iV": 0}
        d["flSArea"] = {"sel": 6, "val": [_f.crawlspace_floor_slab_area_m2], "iV": 0}
        d["ceToUCU"] = _sel_val(_f.ceiling_above_crawlspace_u_value)
        d["flPer"] = _sel_val(_f.crawlspace_floor_exposed_perimeter_m)
        d["hcsWAG"] = _sel_val(_f.crawlspace_wall_height_above_grade_m)
        d["crawlFlU"] = _sel_val(_f.crawlspace_floor_u_value)
        d["crowlSVentO"] = _sel_val(_f.crawlspace_vent_opening_are_m2)
        d["wallUcsAG"] = _sel_val(_f.crawlspace_wall_u_value)

    d["idZrel"] = _zone_id
    return d


def _metr_spaces(_z: building.PhxZone) -> list[spaces.PhxSpace]:
    """Return the list of spaces for a zone, merging by ERV if the flag is set."""
    if not _z.merge_spaces_by_erv:
        return _z.ventilated_spaces

    merged_spaces: list[spaces.PhxSpace] = []
    for space_group in _z.ventilated_spaces_grouped_by_erv:
        if len(space_group) > 1:
            new_space = reduce(operator.add, space_group)
        else:
            new_space = space_group[0]
            new_space.display_name = new_space.vent_unit_display_name
        merged_spaces.append(new_space)
    return sorted(merged_spaces, key=lambda x: x.vent_unit_display_name)


def _PhxZone(_z: building.PhxZone, _foundations: list[ground.PhxFoundation] | None = None) -> dict:
    """Convert a PhxZone to a METR JSON zone dict."""
    room_list = [_PhxSpace(sp) for sp in _metr_spaces(_z)]

    return {
        "n": _z.display_name,
        "typeZ": _z.zone_type.value,
        "id": _z.id_num,
        "visVolZ": {"sel": 2, "val": [_z.volume_gross, None], "iV": 0},
        "grossVolZ": {"sel": 7, "val": [_z.volume_gross, None], "iV": 0},
        "netVolZ": {"sel": 6, "val": [_z.volume_net, _z.volume_net, _z.volume_net, _z.volume_net], "iV": 3},
        "flAreaZ": {
            "sel": 6,
            "val": [
                _z.icfa_override or _z.weighted_net_floor_area,
                _z.weighted_net_floor_area,
                _z.weighted_net_floor_area,
            ],
            "iV": 2,
        },
        "hFlaGZ": {"sel": 6, "val": [None, None], "iV": 1},
        "calculGVolZ": {"res": "----", "OK": False, "lExpr": []},
        "calculNVolZ": {"res": "----", "OK": False, "lExpr": []},
        "calculFlAZ": {"res": "----", "OK": False, "lExpr": []},
        "iCliZ": 1,
        "indexCurvZ": -1,
        "idOptCliZ": -1,
        "desCondZ": _zone_design_conditions(),
        "loadsZ": _zone_loads(_z),
        "calcParZ": _zone_calc_params(),
        "boundCondZ": {
            "tResH": 0.13,
            "tResU": 0.17,
            "tResD": 0.1,
            "color": [255, 255, 0, 255],
        },
        "idPHcase": 1,
        "tRoomH": {"sel": 1, "val": [_z.clearance_height, None], "iV": 0},
        "shCapZ": {"sel": _z.specific_heat_capacity.value, "val": [60.0, 132.0, 204.0, None], "iV": 0},
        "humCapZ": 700.0,
        "nHeavyStr": NaN,
        "lTbZ": [_PhxComponentThermalBridge(tb) for tb in _z.thermal_bridges],
        "lRoom": room_list,
        "vsAm": NaN,
        "vsD": 0.0,
        "vsN": 0.0,
        "vsaA": NaN,
        "vsSPc": NaN,
        "vsAmex": NaN,
        "vsSp": NaN,
        "nBedR": _z.res_number_bedrooms,
        "lExhVent": [_PhxExhaustVentilator(v) for v in _z.exhaust_ventilator_collection.devices],
        "lFoundPH": [_PhxFoundation(f, _z.id_num) for f in (_foundations or [])],
        "trn4108": 1,
        "dVent4108": 1,
        "nVent4108": 1,
        "nMVent4108": 1,
        "tAttZ": 0,
        "iCliAZ": 1,
        "idOptCliAZ": -1,
    }


# -- SPACES (ROOMS) -----------------------------------------------------------


def _PhxSpace(_sp: spaces.PhxSpace) -> dict:
    """Convert a PhxSpace to a METR JSON room dict."""
    return {
        "n": _sp.display_name,
        "tRoom": _sp.wufi_type,
        "quantity": _sp.quantity,
        "area": round(_sp.weighted_floor_area, 6),
        "clearH": round(_sp.clear_height, 6),
        "dVFrSup": round(_sp.ventilation.load.flow_supply, TOL_LEV1),
        "dVFrEx": round(_sp.ventilation.load.flow_extract, TOL_LEV1),
        "dVFiz": 0.0,
        "idUPatV": _sp.ventilation.schedule.id_num,
        "idVUnit": _sp.vent_unit_id_num,
    }


# -- THERMAL BRIDGES ----------------------------------------------------------


def _PhxComponentThermalBridge(_tb: components.PhxComponentThermalBridge) -> dict:
    """Convert a PhxComponentThermalBridge to a METR JSON thermal bridge dict."""
    return {
        "n": _tb.display_name,
        "typeTbZ": _tb.group_number * -1,
        "lengthTbZ": _tb.length,
        "psiTbZ": _tb.psi_value,
        "idOptCli": -1,
        "CalculL": {"res": "----", "OK": False, "lExpr": []},
    }


# -- EXHAUST VENTILATION -------------------------------------------------------


def _PhxExhaustVentilator(_v) -> dict:
    """Convert a PhxExhaustVentilator to a METR JSON exhaust vent dict."""
    return {
        "n": _v.display_name,
        "typeExhV": _v.params.exhaust_type.value,
        "ExhVfR": _v.params.exhaust_flow_rate_m3h,
        "runTU": _v.params.annual_runtime_minutes,
    }


# -- ELECTRICAL EQUIPMENT (HOME DEVICES / APPLIANCES) -------------------------


def _PhxElectricalDevice(_d: elec_equip.PhxElectricalDevice) -> dict:
    """Convert a PhxElectricalDevice to a METR JSON home device dict.

    METR uses a flat 'super-appliance' structure (like HVAC devices): every appliance
    has ALL keys regardless of type. Device-specific values override the defaults.
    """
    energy = _d.get_energy_demand()
    dev = {
        "tHdev": _d.device_type.value,
        "Com": _d.comment or "default",
        "refQ": _d.reference_quantity,
        "quantity": _d.get_quantity(),
        "inCondSp": _d.in_conditioned_space,
        "refUY": _d.reference_energy_norm,
        "refUY1": _d.reference_energy_norm,
        "refDY": _d.reference_energy_norm,
        "refUC": _d.reference_energy_norm,
        "enDrY": energy,
        "enDrD": energy,
        "enDY": energy,
        "enDrU": _d.energy_demand_per_use,
        "enDrU1": _d.energy_demand_per_use,
        "CEFef": _d.combined_energy_factor,
        # -- Device-specific defaults (overridden below as needed)
        "wCon": 1,
        "dWCapSel": 1,
        "dWCapPl": 12.0,
        "utilFact": NaN,
        "capCW": 0.081383,
        "MEF": 2.38,
        "tDryer": -1,
        "GasCon": NaN,
        "CEFGas": 2.67,
        "fUtilFsel": 1,
        "fUtilF": 1.18,
        "tCook": 1,
        "highEffic": NaN,
        "freq": NaN,
        "rDamp": NaN,
        "fHEff": NaN,
    }

    # -- Device-specific overlays
    if isinstance(_d, elec_equip.PhxDeviceDishwasher):
        dev["wCon"] = _d.water_connection
        dev["dWCapSel"] = _d.capacity_type
        dev["dWCapPl"] = _d.capacity
        dev["refED"] = 7  # kWh/year
        dev["enDrU2"] = energy
    elif isinstance(_d, elec_equip.PhxDeviceClothesWasher):
        dev["wCon"] = _d.water_connection
        dev["utilFact"] = _d.utilization_factor or NaN
        dev["capCW"] = _d.capacity
        dev["MEF"] = _d.modified_energy_factor
        dev["refED"] = 6  # MEF/year
    elif isinstance(_d, elec_equip.PhxDeviceClothesDryer):
        dev["tDryer"] = _d.dryer_type
        dev["GasCon"] = _d.gas_consumption or NaN
        dev["CEFGas"] = _d.gas_efficiency_factor
        dev["fUtilFsel"] = _d.field_utilization_factor_type
        dev["fUtilF"] = _d.field_utilization_factor
        dev["refED"] = 4  # CEF
    elif isinstance(_d, elec_equip.PhxDeviceCooktop):
        dev["tCook"] = _d.cooktop_type
        dev["enDrU1"] = energy
    elif isinstance(
        _d, (elec_equip.PhxDeviceFridgeFreezer, elec_equip.PhxDeviceRefrigerator, elec_equip.PhxDeviceFreezer)
    ):
        dev["refED"] = 3  # kWh/year
        dev["fSize"] = 2
    elif isinstance(_d, elec_equip.PhxDeviceLightingGarage):
        dev["fHEff"] = _d.frac_high_efficiency or NaN
        dev["refQ"] = 8  # METr "n.a." for garage lighting
    elif isinstance(_d, (elec_equip.PhxDeviceLightingInterior, elec_equip.PhxDeviceLightingExterior)):
        dev["fHEff"] = _d.frac_high_efficiency or NaN
    elif isinstance(_d, (elec_equip.PhxDeviceCustomLighting, elec_equip.PhxDeviceCustomMEL)):
        dev["refQ"] = 5  # METR "User defined" reference quantity
        dev["quantity"] = 1
        dev["enDrU1"] = energy
        dev["enDrY"] = 0
        dev["enDrD"] = 0
        dev["enDY"] = 0

    return dev


def _LoadsLighting(_sp: spaces.PhxSpace) -> dict:
    """Convert a PhxSpace's lighting data to a METR JSON lighting load dict."""
    return {
        "n": _sp.display_name,
        "idUPat": _sp.occupancy.schedule.id_num,
        "lightTr": 1,
        "cLight": 1,
        "inTE": True,
        "mDet": False,
        "facInclW": False,
        "frFloorA": 1.0,
        "devNorth": 0.0,
        "roomD": 1.0,
        "roomW": 1.0,
        "roomH": 1.0,
        "lintelH": 1.0,
        "widthW": 1.0,
        "instLP": _sp.lighting.load.installed_w_per_m2,
        "lFLoadH": round(_sp.lighting.schedule.full_load_lighting_hours, 1),
        "lightTrU": NaN,
    }


def _LoadsOccupancy(_sp: spaces.PhxSpace) -> dict:
    """Convert a PhxSpace's occupancy data to a METR JSON persons load dict."""
    return {
        "n": _sp.display_name,
        "idUPat": _sp.occupancy.schedule.id_num,
        "actPers": 3,
        "nOcc": _sp.peak_occupancy,
        "flAUZone": round(_sp.weighted_floor_area, 6),
    }


# -- CLIMATE / LOCATION -------------------------------------------------------


def _pad_monthly(values: list[float], pad_to: int = 16, pad_value: Any = 0.0) -> list:
    """Pad a monthly array to `pad_to` elements.

    Arguments:
    ----------
        * values: The source monthly values (typically 12 elements).
        * pad_to: Target array length (16 for METR).
        * pad_value: Value to use for padding (0.0 or "NaN").
    """
    result = list(values[:12]) if values else [0.0] * 12
    while len(result) < 12:
        result.append(0.0)
    while len(result) < pad_to:
        result.append(pad_value)
    return result


def _monthly_with_peak_loads(
    monthly_12: list[float],
    peak_loads: list[phx_site.PhxClimatePeakLoad],
    attr: str,
    pad_value: Any = 0.0,
) -> list:
    """Build a 16-element monthly array: 12 monthly values + 4 peak load values.

    Positions 12-15 = [peak_heating_1, peak_heating_2, peak_cooling_1, peak_cooling_2].

    Arguments:
    ----------
        * monthly_12: The 12 monthly values.
        * peak_loads: List of 4 PhxClimatePeakLoad objects [htg1, htg2, clg1, clg2].
        * attr: Attribute name to read from each peak load (e.g., "temperature_air").
        * pad_value: Fallback value if the attribute is None.
    """
    result = list(monthly_12[:12]) if monthly_12 else [0.0] * 12
    while len(result) < 12:
        result.append(0.0)
    for pl in peak_loads:
        val = getattr(pl, attr, None)
        result.append(val if val is not None else pad_value)
    return result


def _pe_co2_in_wufi_order(factor_dict: dict) -> list[float]:
    """Return PE or CO2 factor values in WUFI-specific order (16 items)."""
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
    return [factor_dict[name].value for name in fuel_order if name in factor_dict]


def _PhxSite(_s: phx_site.PhxSite, _criteria: certification.PhxPhiusCertificationCriteria | None = None) -> dict:
    """Convert a PhxSite to METR JSON cliLoc dict."""
    # -- Peak loads in METR order: [heating_1, heating_2, cooling_1, cooling_2]
    _peaks = [
        _s.climate.peak_heating_1,
        _s.climate.peak_heating_2,
        _s.climate.peak_cooling_1,
        _s.climate.peak_cooling_2,
    ]
    return {
        "selCli": _s.selection.value,
        "lat": _s.location.latitude if _s.location.latitude else NaN,
        "long": _s.location.longitude if _s.location.longitude else NaN,
        "latB": _s.location.latitude if _s.location.latitude else NaN,
        "longB": _s.location.longitude if _s.location.longitude else NaN,
        "hNN": _s.climate.station_elevation if _s.climate.station_elevation is not None else NaN,
        "hNNB": _s.location.site_elevation if _s.location.site_elevation is not None else NaN,
        "dUTCB": _s.location.hours_from_UTC if _s.location.hours_from_UTC else NaN,
        "file": "",
        "nCli": "Not defined",
        "Com": "",
        "albedo": -2,
        "gRefShort": 0.2,
        "gRefLong": 0.1,
        "gEmis": 0.9,
        "cloudI": 0.66,
        "CO2c": 350.0,
        "uCO2c": 48,
        "pECO2": _s.energy_factors.selection_pe_co2_factor.value,
        "selSpCtD": 2,
        "hDegDays65": NaN,
        "cDegDays50": NaN,
        "aGlobRad": 1150.0,
        "hDesDryT": 0.0,
        "cDesDryT": 24.0,
        "dehumDHR": 1050.0,
        "elPrice": NaN,
        "aHDem": _criteria.phius_annual_heating_demand if _criteria else 15.0,
        "aCDem": _criteria.phius_annual_cooling_demand if _criteria else 15.0,
        "pHLoad": _criteria.phius_peak_heating_load if _criteria else 10.0,
        "pCLoad": _criteria.phius_peak_cooling_load if _criteria else 10.0,
        "lOptCli": [],
        "boundCond": {
            "tResH": 0.04,
            "tResU": 0.04,
            "tResD": 0.04,
            "color": [0, 255, 255, 255],
        },
        "selCliPH": _s.climate.selection.value,
        "n": "User defined",
        "TSSummer": _s.climate.daily_temp_swing,
        "aWindSp": _s.climate.avg_wind_speed,
        "cliZUS": _s.location.climate_zone,
        "gtCond": _s.ground.ground_thermal_conductivity,
        "ghCap": _s.ground.ground_heat_capacity,
        "gdens": _s.ground.ground_density,
        "depthGW": _s.ground.depth_groundwater,
        "flowGW": _s.ground.flow_rate_groundwater,
        # -- Monthly arrays (12) + peak load values (4) = 16 elements
        # -- Positions 12-15: [peak_heating_1, peak_heating_2, peak_cooling_1, peak_cooling_2]
        "TMo": _monthly_with_peak_loads(_s.climate.temperature_air, _peaks, "temperature_air", 0.0),
        "dewPMo": _monthly_with_peak_loads(_s.climate.temperature_dewpoint, _peaks, "temperature_dewpoint", NaN),
        "skyTMo": _monthly_with_peak_loads(_s.climate.temperature_sky, _peaks, "temperature_sky", NaN),
        "gTMo": [NaN] * 16,
        "nRadMo": _monthly_with_peak_loads(_s.climate.radiation_north, _peaks, "radiation_north", 0.0),
        "eRadMo": _monthly_with_peak_loads(_s.climate.radiation_east, _peaks, "radiation_east", 0.0),
        "sRadMo": _monthly_with_peak_loads(_s.climate.radiation_south, _peaks, "radiation_south", 0.0),
        "wRadMo": _monthly_with_peak_loads(_s.climate.radiation_west, _peaks, "radiation_west", 0.0),
        "gRadMo": _monthly_with_peak_loads(_s.climate.radiation_global, _peaks, "radiation_global", 0.0),
        "pEud": _pe_co2_in_wufi_order(_s.energy_factors.pe_factors),
        "CO2ud": _pe_co2_in_wufi_order(_s.energy_factors.co2_factors),
    }


# -- PHIUS CERTIFICATION -------------------------------------------------------


def _PhxPhiusCertification(_cert: certification.PhxPhiusCertification) -> dict:
    """Convert PhxPhiusCertification to METR JSON PHIUS dict."""
    settings = _cert.phius_certification_settings
    criteria = _cert.phius_certification_criteria
    bd = _cert.ph_building_data

    return {
        "certCri": settings.phius_building_certification_program.value,
        "wShade": _cert.use_monthly_shading,
        "ShadeTrTot": 3,
        "lCase": [
            {
                "id": bd.id_num,
                "certCri": settings.phius_building_certification_program.value,
                "n": "",
                "bCatResnR": settings.phius_building_category_type.value,
                "typeOccR": settings.phius_building_use_type.value,
                "tOccNRes": 4,
                "bStatus": settings.phius_building_status.value,
                "tBState": settings.phius_building_type.value,
                "iBGains": 2,
                "tOccMet": bd.occupancy_setting_method,
                "nUnits": bd.num_of_units or 1,
                "nFloor": bd.num_of_floors or 1,
                "tVentSys": 1,
                "indoorT": bd.setpoints.winter,
                "minTnVent": bd.setpoints.winter,
                "airPerson": 30.582194,
                "bmentVent": 0.5,
                "tInfiltr": 2,
                "nCombMat": bd.non_combustible_materials,
                "n50": NaN,
                "tightEnv50": bd.airtightness_q50,
                "volPresTest": NaN,
                "iHeatGains": NaN,
                "maxRDehum": 12.0,
                "overhTLim": bd.setpoints.summer,
                "mechRT": bd.mech_room_temp,
                "tapOPersDay": 3.0,
                "tapOUtilDay": 365.0,
                "consDHW60": NaN,
                "cWaterT": NaN,
                "aContrSys": 1,
                "sumHRec": bd.summer_hrv_bypass_mode.value,
                "bWindExp": bd.building_exposure_type.value,
                "windSCoef": NaN,
                "windExp": NaN,
                "windSF": NaN,
                "evapHP": 15.0,
                "hLflushWC": True,
                "nWC": 1,
                "idWCutilP": 1,
                "uDefSchool": False,
                "margPRDHW": NaN,
                "calculAirPt": {"res": "----", "OK": False, "lExpr": []},
            }
        ],
    }


# -- HVAC SYSTEMS --------------------------------------------------------------


def _Systems(_collections: list[hvac_collection.PhxMechanicalSystemCollection]) -> dict:
    """Convert mechanical system collections to METR JSON HVAC dict."""
    return {
        "lSystem": [_PhxMechanicalSystemCollection(c) for c in _collections],
    }


def _PhxMechanicalSystemCollection(_c: hvac_collection.PhxMechanicalSystemCollection) -> dict:
    """Convert a single PhxMechanicalSystemCollection to METR JSON system dict."""
    zc = _c.zone_coverage
    # -- Combine mechanical devices + renewable devices (PV, etc.)
    all_devices = list(_c.devices) + list(_c.renewable_devices.devices)
    num_ventilators = sum(1 for d in all_devices if isinstance(d, hvac_ventilation.PhxDeviceVentilator))
    return {
        "n": _c.display_name,
        "typeSys": _c.sys_type_num,
        "id": _c.id_num,
        "lZoneCover": [
            {
                "idZone": zc.zone_num,
                "czHCVHD": [
                    zc.heating,
                    zc.cooling,
                    zc.ventilation,
                    zc.humidification,
                    zc.dehumidification,
                ],
            }
        ],
        "lDevice": [_PhxMechanicalDevice(d, num_ventilators) for d in all_devices],
        "distrib": _build_default_distribution(_c),
        "suppDev": {
            "uVal": False,
            "devCondSp": True,
            "lSuppDev": [_PhxSupportiveDevice(d) for d in _c.supportive_devices.devices],
        },
    }


def _build_device_defaults() -> dict:
    """Build the ~131-key base device dict with NaN/default values.

    METR uses a flat 'super-device' structure where every device has ALL keys
    regardless of device type. Device-specific overlays set the relevant values.
    """
    return {
        # -- Identity
        "info": "",
        "n": "",
        "id": 0,
        "typeDev": 1,
        "typeDevDB": 1,
        # -- Ventilation (V suffix)
        "hRec": 0.0,
        "hRecE": 0.0,
        "mRec": 0.0,
        "mRecE": 0.0,
        "mRecV": 0.0,
        "elEffV": NaN,
        "frostPV": False,
        "quantV": 1,
        "sHXeffV": 0.0,
        "defrTV": NaN,
        "defrAV": False,
        "inCondSpV": True,
        "noSByP": False,
        "calcEMV": {},
        # -- Climate reference
        "uOptCli": False,
        "idOptCli": -1,
        # -- Usage / coverage
        "uHWCVHD": [False, False, False, False, False, False],
        "cHWCVHD": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        # -- Boiler (B suffix)
        "enSB": 1,
        "mPowB": 10.0,
        "solFrB": NaN,
        "condB": False,
        "eff30B": NaN,
        "effNOB": NaN,
        "rTm30B": NaN,
        "t7055B": NaN,
        "t5545B": NaN,
        "t3528B": NaN,
        "hl70B": NaN,
        "effbB": NaN,
        "effcB": NaN,
        "hrelcB": NaN,
        "tOnOfB": NaN,
        "uHbcB": NaN,
        "avPowB": NaN,
        "demCycB": NaN,
        "psRunB": NaN,
        "nTrPB": False,
        "ccB": False,
        "areaMRB": NaN,
        # -- Heat pump (HP suffix)
        "tHP": 3,
        "hLscHP": NaN,
        "tStdHP": NaN,
        "fAdExHP": NaN,
        "eHRHP": NaN,
        "elEfHP": NaN,
        "efSHXHP": NaN,
        "pHP": 1,
        "frostPHP": False,
        "solFCHP": NaN,
        "solFcHP": NaN,
        "aCOP": NaN,
        "tSysPHP": NaN,
        "acCOPHP": NaN,
        "athHP": [NaN, NaN, NaN, NaN],
        "powhHP": [NaN, NaN, NaN, NaN],
        "cophHP": [NaN, NaN, NaN, NaN],
        "aatWHP": [NaN, NaN, NaN, NaN],
        "powWHP": [NaN, NaN, NaN, NaN],
        "powrWHP": [NaN, NaN, NaN, NaN],
        "copsWHP": [NaN, NaN, NaN, NaN],
        "copsrWHP": [NaN, NaN, NaN, NaN],
        "atsHP": [NaN, NaN, NaN, NaN],
        "powsHP": [NaN, NaN, NaN, NaN],
        "copsHP": [NaN, NaN, NaN, NaN],
        "rCOP1HP": NaN,
        "rCOP2HP": NaN,
        "aT1HP": NaN,
        "aT2HP": NaN,
        "aCOPHP": NaN,
        "pHGHP": NaN,
        "hpWHHP": NaN,
        # -- Solar collector (SC suffix)
        "typeSC": 1,
        "tEffSC": NaN,
        "k1SC": NaN,
        "k2SC": NaN,
        "tCapSC": NaN,
        "kdirSC": NaN,
        "kdfuSC": NaN,
        "tYieldSC": NaN,
        "areaASC": NaN,
        "auxEnSC": NaN,
        "areaSC": NaN,
        "devNSC": 180.0,
        "inclSC": 30.0,
        "hccfSC": NaN,
        "hsoSC": 0.0,
        "hdsoSC": NaN,
        "arfSC": 1.0,
        "priorSC": True,
        "idsSC": -1,
        # -- Water storage (WS suffix)
        "volWS": 1000.0,
        "lStWS": NaN,
        "totLWS": NaN,
        "inOptWS": 1,
        "aHreWS": NaN,
        "ambTWS": NaN,
        "tTWS": NaN,
        "qauntWS": 1,
        "inTEnvWS": True,
        # -- District heat (DH suffix)
        "eCarrDH": 3,
        "solFrDH": 0.0,
        "uFTrSDH": NaN,
        "perfHG": NaN,
        "pEF": NaN,
        "eCO2": NaN,
        "inTEnvUD": True,
        "acCOPu": NaN,
        # -- Photovoltaic (PV suffix)
        "sitePV": 1,
        "suPV": 1,
        "ouPV": 1,
        "aSizePV": NaN,
        "renEnPV": NaN,
        "sUtilPV": 1.0,
        "sUtilPVro": 1.0,
        # -- DHW distribution (DW suffix)
        "tDW": 36.1111,
        "efDW": 0.45,
        "plDW": 22.86,
        "pWFDW": 1,
        "locDW": 1,
        "pfDW": 1.0,
        "fFDW": 1.0,
        # -- Shared
        "auxEn": NaN,
        "auxEnDHW": NaN,
        "inCondSp": True,
        "auxEncsSC": True,
    }


# -- Device-type-specific info labels -----------------------------------------

_DEVICE_INFO_LABELS = {
    DeviceType.VENTILATION: "Mechanical ventilation",
    DeviceType.ELECTRIC: "Electric",
    DeviceType.BOILER: "Boiler",
    DeviceType.DISTRICT_HEAT: "District heating",
    DeviceType.HEAT_PUMP: "Heat pump",
    DeviceType.WATER_STORAGE: "Water storage",
    DeviceType.PHOTOVOLTAIC: "Photovoltaic / RES",
}


def _set_device_coverage(_d, dev: dict) -> None:
    """Set uHWCVHD (usage booleans) and cHWCVHD (coverage fractions) from usage_profile."""
    up = getattr(_d, "usage_profile", None)
    if up is None:
        return
    dev["uHWCVHD"] = [
        up.space_heating,
        up.dhw_heating,
        up.cooling,
        up.ventilation,
        up.humidification,
        up.dehumidification,
    ]
    dev["cHWCVHD"] = [
        up.space_heating_percent,
        up.dhw_heating_percent,
        up.cooling_percent,
        up.ventilation_percent,
        up.humidification_percent,
        up.dehumidification_percent,
    ]


def _overlay_ventilation(_d: hvac_ventilation.PhxDeviceVentilator, dev: dict) -> None:
    """Overlay ventilation-specific fields from a PhxDeviceVentilator."""
    _set_device_coverage(_d, dev)
    p = _d.params
    dev["hRec"] = p.sensible_heat_recovery
    dev["hRecE"] = p.sensible_heat_recovery
    dev["mRec"] = p.latent_heat_recovery
    dev["mRecE"] = p.latent_heat_recovery
    dev["mRecV"] = p.latent_heat_recovery
    dev["elEffV"] = p.electric_efficiency
    dev["frostPV"] = p.frost_protection_reqd
    dev["quantV"] = p.quantity
    dev["defrTV"] = p.temperature_below_defrost_used
    dev["defrAV"] = p.frost_protection_reqd
    dev["inCondSpV"] = p.in_conditioned_space
    dev["elEfHP"] = p.electric_efficiency
    dev["noSByP"] = False
    dev["capV"] = {"PF": 1, "PTVid": [[-1, 1, 17]], "FCid": [-1, -1]}


def _overlay_heat_pump(_d, dev: dict) -> None:
    """Overlay heat-pump-specific fields."""
    _set_device_coverage(_d, dev)
    p = _d.params
    dev["inCondSp"] = getattr(p, "in_conditioned_space", True)

    if isinstance(_d, heat_pumps.PhxHeatPumpAnnual):
        dev["tHP"] = 3
        dev["aCOP"] = p.annual_COP or NaN
    elif isinstance(_d, heat_pumps.PhxHeatPumpMonthly):
        dev["tHP"] = 4
        dev["rCOP1HP"] = p.COP_1 or NaN
        dev["rCOP2HP"] = p.COP_2 or NaN
        dev["aT1HP"] = p.ambient_temp_1 or NaN
        dev["aT2HP"] = p.ambient_temp_2 or NaN
    elif isinstance(_d, heat_pumps.PhxHeatPumpHotWater):
        dev["tHP"] = 5
        dev["aCOP"] = p.annual_COP or NaN
        dev["aCOPHP"] = p.annual_COP or NaN
        dev["tSysPHP"] = p.total_system_perf_ratio or NaN
        dev["pHGHP"] = p.total_system_perf_ratio or NaN
        dev["hpWHHP"] = p.annual_energy_factor or NaN
    elif isinstance(_d, heat_pumps.PhxHeatPumpCombined):
        dev["tHP"] = 2

    # -- Cooling params
    if hasattr(_d, "params_cooling"):
        pc = _d.params_cooling
        if pc.recirculation.used or pc.ventilation.used:
            dev["capC"] = {"PF": 1, "PTVid": [[-1, 1, 16]], "FCid": [-1, -1]}


def _overlay_water_storage(_d: water.PhxHotWaterTank, dev: dict) -> None:
    """Overlay water-storage-specific fields."""
    _set_device_coverage(_d, dev)
    p = _d.params
    dev["volWS"] = p.storage_capacity
    dev["lStWS"] = p.standby_losses if p.standby_losses is not None else NaN
    dev["totLWS"] = p.standby_losses if p.standby_losses is not None else NaN
    dev["inOptWS"] = p.input_option.value if hasattr(p.input_option, "value") else 1
    dev["aHreWS"] = p.storage_loss_rate if p.storage_loss_rate is not None else NaN
    dev["ambTWS"] = p.room_temp if p.room_temp is not None else NaN
    dev["tTWS"] = p.water_temp if p.water_temp is not None else NaN
    dev["qauntWS"] = _d.quantity or 1
    dev["inTEnvWS"] = p.in_conditioned_space
    dev["inCondSp"] = p.in_conditioned_space


def _overlay_photovoltaic(_d: renewable_devices.PhxDevicePhotovoltaic, dev: dict) -> None:
    """Overlay photovoltaic-specific fields."""
    _set_device_coverage(_d, dev)
    p = _d.params
    dev["sitePV"] = p.location_type
    dev["suPV"] = p.utilization_type
    dev["ouPV"] = p.onsite_utilization_type
    dev["aSizePV"] = p.array_size or NaN
    dev["renEnPV"] = p.photovoltaic_renewable_energy or NaN
    dev["sUtilPV"] = p.onsite_utilization_factor
    dev["sUtilPVro"] = p.onsite_utilization_factor
    dev["auxEn"] = p.auxiliary_energy or NaN
    dev["auxEnDHW"] = p.auxiliary_energy_DHW or NaN
    dev["inCondSp"] = p.in_conditioned_space


def _overlay_boiler_fossil(_d: heating.PhxHeaterBoilerFossil, dev: dict) -> None:
    """Overlay fossil boiler-specific fields."""
    _set_device_coverage(_d, dev)
    p = _d.params
    dev["enSB"] = p.fuel.value if hasattr(p.fuel, "value") else 1
    dev["condB"] = p.condensing
    dev["eff30B"] = p.effic_at_30_percent_load
    dev["effNOB"] = p.effic_at_nominal_load
    dev["rTm30B"] = p.avg_rtrn_temp_at_30_percent_load
    dev["t7055B"] = p.avg_temp_at_70C_55C
    dev["t5545B"] = p.avg_temp_at_55C_45C
    dev["t3528B"] = p.avg_temp_at_32C_28C
    dev["hl70B"] = p.standby_loss_at_70C or NaN
    dev["mPowB"] = p.rated_capacity
    dev["inCondSp"] = p.in_conditioned_space


def _overlay_boiler_wood(_d: heating.PhxHeaterBoilerWood, dev: dict) -> None:
    """Overlay wood boiler-specific fields."""
    _set_device_coverage(_d, dev)
    p = _d.params
    dev["enSB"] = p.fuel.value if hasattr(p.fuel, "value") else 1
    dev["effbB"] = p.effic_in_basic_cycle
    dev["effcB"] = p.effic_in_const_operation
    dev["hrelcB"] = p.avg_frac_heat_output
    dev["tOnOfB"] = p.temp_diff_on_off
    dev["mPowB"] = p.rated_capacity
    dev["demCycB"] = p.demand_basic_cycle
    dev["psRunB"] = p.power_stationary_run
    dev["uHbcB"] = p.power_standard_run or NaN
    dev["nTrPB"] = p.no_transport_pellets or False
    dev["ccB"] = p.only_control or False
    dev["areaMRB"] = p.area_mech_room or NaN


def _PhxMechanicalDevice(_d, _num_ventilators: int = 1) -> dict:
    """Convert a mechanical device to a METR JSON device dict.

    METR uses a flat ~131-key 'super-device' structure. Every device has ALL keys
    regardless of type. We build defaults, then overlay device-specific values.
    """
    dev = _build_device_defaults()

    # -- Identity fields
    dev["n"] = getattr(_d, "display_name", "") or ""
    dev["id"] = getattr(_d, "id_num", 0)

    device_type = getattr(_d, "device_type", None)
    if hasattr(device_type, "value"):
        dev["typeDev"] = device_type.value
        dev["typeDevDB"] = device_type.value
        dev["info"] = _DEVICE_INFO_LABELS.get(device_type, "")
    else:
        dev["typeDev"] = 1
        dev["typeDevDB"] = 1

    # -- Shared params
    params = getattr(_d, "params", None)
    if params is not None:
        dev["auxEn"] = getattr(params, "aux_energy", None) or NaN
        dev["auxEnDHW"] = getattr(params, "aux_energy_dhw", None) or NaN
        dev["inCondSp"] = getattr(params, "in_conditioned_space", True)

    # -- Usage profile / coverage (applies to all device types)
    _set_device_coverage(_d, dev)

    # -- For ventilators, split ventilation coverage evenly across all units
    if isinstance(_d, hvac_ventilation.PhxDeviceVentilator) and _num_ventilators > 1:
        dev["cHWCVHD"][3] = 1.0 / _num_ventilators

    # -- Device-type-specific overlays
    if isinstance(_d, hvac_ventilation.PhxDeviceVentilator):
        _overlay_ventilation(_d, dev)
    elif isinstance(
        _d,
        (
            heat_pumps.PhxHeatPumpAnnual,
            heat_pumps.PhxHeatPumpMonthly,
            heat_pumps.PhxHeatPumpHotWater,
            heat_pumps.PhxHeatPumpCombined,
        ),
    ):
        _overlay_heat_pump(_d, dev)
    elif isinstance(_d, water.PhxHotWaterTank):
        _overlay_water_storage(_d, dev)
    elif isinstance(_d, renewable_devices.PhxDevicePhotovoltaic):
        _overlay_photovoltaic(_d, dev)
    elif isinstance(_d, heating.PhxHeaterBoilerFossil):
        _overlay_boiler_fossil(_d, dev)
    elif isinstance(_d, heating.PhxHeaterBoilerWood):
        _overlay_boiler_wood(_d, dev)

    # -- Non-ventilator devices: set noSByP=True and add capacity profile refs
    if not isinstance(_d, hvac_ventilation.PhxDeviceVentilator):
        dev["noSByP"] = True
        # -- If device provides space heating, reference the heating capacity profile
        if dev["uHWCVHD"][0]:  # space_heating = True
            dev["capH"] = {"PF": 1, "PTVid": [[-1, 1, 15]], "FCid": [-1, -1]}

    return dev


def _PhxSupportiveDevice(_d) -> dict:
    """Convert a supportive device to a METR JSON dict."""
    device_type = getattr(_d, "device_type", None)
    params = getattr(_d, "params", None)
    return {
        "n": getattr(_d, "display_name", ""),
        "tsDev": device_type.value if hasattr(device_type, "value") else 10,
        "quantity": getattr(_d, "quantity", 1),
        "inCondSp": getattr(params, "in_conditioned_space", True) if params else True,
        "nEdem": getattr(params, "norm_energy_demand_W", NaN) if params else NaN,
        "contr": False,
        "poOper": getattr(params, "annual_period_operation_khrs", 8.76) if params else 8.76,
    }


def _diameter_enum_value(_diameter_mm: float) -> int:
    """Convert a pipe diameter in mm to the METR/WUFI inch-diameter enum value."""
    diameter_inches = (_diameter_mm / 25.4) if _diameter_mm else 0.0
    return PhxHotWaterPipingInchDiameterType.nearest_key(diameter_inches).value


def _DistributionDHWTwig(_twg) -> dict:
    """Convert a PhxPipeElement (twig/fixture) to a METR JSON dict."""
    return {
        "n": _twg.display_name,
        "id": _twg.id_num,
        "plW": _twg.length_m,
        "pmW": _twg.material.value,
        "pdW": _diameter_enum_value(_twg.weighted_diameter_mm),
    }


def _DistributionDHWBranch(_br) -> dict:
    """Convert a PhxPipeBranch to a METR JSON dict."""
    return {
        "n": _br.display_name,
        "id": _br.id_num,
        "plW": _br.pipe_element.length_m,
        "pmW": _br.pipe_element.material.value,
        "pdW": _diameter_enum_value(_br.pipe_element.weighted_diameter_mm),
        "lTwigW": [_DistributionDHWTwig(tw) for tw in _br.fixtures],
    }


def _DistributionDHWTrunc(_t) -> dict:
    """Convert a PhxPipeTrunk to a METR JSON dict."""
    return {
        "n": _t.display_name,
        "id": _t.id_num,
        "plW": _t.pipe_element.length_m,
        "pmW": _t.pipe_element.material.value,
        "pdW": _diameter_enum_value(_t.pipe_element.weighted_diameter_mm),
        "cUoF": _t.multiplier,
        "drecW": _t.demand_recirculation,
        "lBranchW": [_DistributionDHWBranch(br) for br in _t.branches],
    }


def _PhxDuctElement(_d) -> dict:
    """Convert a PhxDuctElement to a METR JSON duct dict."""
    return {
        "n": _d.display_name,
        "id": _d.id_num,
        "dDuct": _d.diameter_mm,
        "wDuct": _d.width_mm,
        "hDuct": _d.height_mm,
        "lDuct": _d.length_m,
        "tIns": _d.insulation_thickness_mm,
        "tCond": _d.insulation_conductivity_wmk,
        "quantity": _d.quantity,
        "tDuct": _d.duct_type.value,
        "ductS": _d.duct_shape,
        "isRefl": _d.is_reflective,
        "lassVU": list(_d.assigned_vent_unit_ids),
    }


def _build_cooling_distribution(_c: hvac_collection.PhxMechanicalSystemCollection) -> dict:
    """Build cooling distribution fields from heat pump cooling params."""
    cooling_devices = [d for d in _c.heat_pump_devices if d.usage_profile.cooling]

    # -- Defaults
    d: dict[str, Any] = {
        "ventC": False,
        "sassC": False,
        "recC": False,
        "rassC": False,
        "dehumC": False,
        "panelC": False,
        "crTC": NaN,
        "cTC": NaN,
        "recfC": 0.0,
        "mcpC": NaN,
        "copAC": NaN,
        "crdC": False,
        "mrcpC": NaN,
        "rcopC": NaN,
        "udhlC": False,
        "dcopC": NaN,
        "pcopC": NaN,
        "delC": NaN,
        "seerC": NaN,
        "eerC": NaN,
    }

    if not cooling_devices:
        return d

    # -- Combine cooling params from all cooling-capable heat pumps
    for hp in cooling_devices:
        pc = hp.params_cooling

        if pc.ventilation.used:
            d["ventC"] = True
            d["sassC"] = pc.ventilation.single_speed
            d["mcpC"] = pc.ventilation.capacity
            d["cTC"] = pc.ventilation.min_coil_temp
            d["copAC"] = pc.ventilation.annual_COP

        if pc.recirculation.used:
            d["recC"] = True
            d["rassC"] = pc.recirculation.single_speed
            d["mrcpC"] = pc.recirculation.capacity
            d["crTC"] = pc.recirculation.min_coil_temp
            d["rcopC"] = pc.recirculation.annual_COP
            d["recfC"] = pc.recirculation.flow_rate_m3_hr
            d["crdC"] = pc.recirculation.flow_rate_variable

        if pc.dehumidification.used:
            d["dehumC"] = True
            d["udhlC"] = pc.dehumidification.useful_heat_loss
            d["dcopC"] = pc.dehumidification.annual_COP

        if pc.panel.used:
            d["panelC"] = True
            d["pcopC"] = pc.panel.annual_COP

    return d


def _build_default_distribution(_c: hvac_collection.PhxMechanicalSystemCollection) -> dict:
    """Distribution parameters for HVAC system, pulling DHW values from the collection."""
    hw_params = _c._distribution_hw_recirculation_params
    return {
        "lRadiator": [],
        "lTab": [],
        "lSplitDU": [],
        "desSupTTabs": 35.0,
        "spRetTlTabs": 35.0,
        "aTlTabs": -10.0,
        "spRetThTabs": 35.0,
        "aThTabs": 20.0,
        "pSurfCond": True,
        "limSurfHum": False,
        "limRHSurf": 65.0,
        "lPipesH": [NaN, NaN, NaN],
        "hLossH": [NaN, NaN, NaN],
        "roomTH": [20.0, NaN, NaN],
        "desFTH": [NaN, NaN, NaN],
        "desSHlH": [NaN, NaN, NaN],
        "flowTCH": [False, False, False],
        **_build_cooling_distribution(_c),
        "lVentDuct": [_PhxDuctElement(d) for d in _c.vent_ducting],
        "tapWT": 45.0,
        "cmpW": hw_params.calc_method.value,
        "pmW": hw_params.pipe_material.value,
        "pdW": _diameter_enum_value(hw_params.pipe_diameter) if hw_params.calc_method.value < 4 else 1,
        "hwfeW": hw_params.hot_water_fixtures,
        "drecW": hw_params.demand_recirc,
        "sfeW": 1,
        "nbrW": hw_params.num_bathrooms,
        "pinsW": hw_params.all_pipes_insulated,
        "ufW": hw_params.units_or_floors.value,
        "lTruncW": [_DistributionDHWTrunc(t) for t in _c.dhw_distribution_trunks],
        "lcpW": [_c.dhw_recirc_total_length_m, NaN, NaN],
        "hlcW": [_c.dhw_recirc_weighted_heat_loss_coeff, NaN, NaN],
        "trW": [hw_params.air_temp, NaN, NaN],
        "dftW": [hw_params.water_temp, NaN, NaN],
        "dhcW": [hw_params.daily_recirc_hours, NaN, NaN],
        "lpW": [_c.dhw_distribution_total_length_m, NaN, NaN],
        "dpW": [_c.dhw_distribution_weighted_diameter_mm, NaN, NaN],
        "hrsW": [NaN, NaN, NaN],
    }
