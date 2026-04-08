# -*- Python Version: 3.10 -*-

"""Schema functions that convert PHX model objects into PppSection lists."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from PHX.model.enums.building import ComponentExposureExterior, ComponentFaceType
from PHX.to_PPP.ppp_sections import PppSection

if TYPE_CHECKING:
    from PHX.model.components import PhxApertureElement, PhxComponentOpaque, PhxComponentThermalBridge
    from PHX.model.constructions import PhxConstructionWindow
    from PHX.model.project import PhxProject, PhxVariant

# -- Slot limits
MAX_SURFACES = 100
MAX_WINDOWS = 152
MAX_THERMAL_BRIDGES = 100
MAX_U_VALUE_BLOCKS = 60
MAX_USER_GLAZING = 99
MAX_USER_FRAMES = 99
MAX_USER_ASSEMBLIES = 17
ASSEMBLY_ID_OFFSET = 83  # DesignPH convention: user assemblies start at 83


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pad_text(values: list[str], total: int, pad: str = "-") -> list[str]:
    """Pad a text list to `total` length with `pad`."""
    return values + [pad] * (total - len(values))


def _pad_num(values: list[str], total: int, pad: str = "") -> list[str]:
    """Pad a numeric list to `total` length with blank strings."""
    return values + [pad] * (total - len(values))


def _pad_num_offset(values: list[str], total: int, pad: str = "") -> list[str]:
    """Build a 101-row section: empty first row + values padded to total-1."""
    return [""] + _pad_num(values, total - 1, pad)


def _fmt(value: float | None) -> str:
    """Format a float as a string, or empty if None."""
    if value is None:
        return ""
    return f"{value:f}"


def _group_label(component: PhxComponentOpaque) -> str:
    """Return the PPP group label for an opaque component."""
    if component.exposure_exterior == ComponentExposureExterior.SURFACE:
        return "18-Partition Wall to Neighbour"
    elif component.face_type == ComponentFaceType.WALL:
        if component.exposure_exterior == ComponentExposureExterior.EXTERIOR:
            return "8-External Wall - Ambient"
        else:
            return "9-External Wall - Ground"
    elif component.face_type == ComponentFaceType.FLOOR:
        return "11-Floor slab / Basement ceiling"
    elif component.face_type == ComponentFaceType.ROOF_CEILING:
        return "10-Roof/Ceiling - Ambient"
    elif component.face_type == ComponentFaceType.AIR_BOUNDARY:
        return "12-Air Boundary"
    else:
        return "12-"


def _surface_tilt(component: PhxComponentOpaque) -> float:
    """Return the tilt angle for a component (from first polygon)."""
    if component.polygons:
        return component.polygons[0].angle_from_horizontal
    return 90.0


def _surface_orientation(component: PhxComponentOpaque) -> float:
    """Return the orientation angle for a component (from first polygon)."""
    if component.polygons:
        return component.polygons[0].cardinal_orientation_angle
    return 0.0


def _surface_dims(component: PhxComponentOpaque) -> tuple[str, str, str]:
    """Return (a, b, custom_area) strings for a surface.

    Strategy: try to get width/height from rectangular polygons.
    If the polygon isn't rectangular or has multiple polygons, use custom area.
    """
    if not component.polygons:
        return ("", "", "")

    total_area = sum(p.area for p in component.polygons)

    # Try the first polygon for rectangular dims
    poly = component.polygons[0]
    try:
        w = poly.width  # type: ignore
        h = poly.height  # type: ignore
        if len(component.polygons) == 1 and abs(w * h - total_area) < 0.001:
            return (f"{w:f}", f"{h:f}", "")
        else:
            return (f"{w:f}", "", f"{total_area:f}")
    except Exception:
        return ("", "", f"{total_area:f}")


# ---------------------------------------------------------------------------
# Cross-reference map types
# ---------------------------------------------------------------------------

AssemblyMap = dict[str, tuple[int, str]]  # {assembly.identifier: (ppp_id, "NNud-Name")}
GlazingMap = dict[str, tuple[int, str]]  # {dedup_key: (idx, "NNud-Name")}
FrameMap = dict[str, tuple[int, str]]  # {dedup_key: (idx, "NNud-Name")}
SurfaceIndexMap = dict[int, tuple[int, str]]  # {component id(): (row_num, display_name)}


# ---------------------------------------------------------------------------
# 1. Metadata sections
# ---------------------------------------------------------------------------


def meta_sections(_project: PhxProject, _variant: PhxVariant) -> list[PppSection]:
    """Build the header / metadata sections."""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # pppmeta_kopf
    kopf = PppSection(
        "pppmeta_kopf",
        5,
        1,
        [
            "1,4",
            "10,1",
            "PHX",
            "CodenameCell=A1",
            "",
        ],
    )

    # Nachweis
    building_data = getattr(_variant, "_phi_building_data", None)
    if building_data and hasattr(building_data, "num_of_units"):
        num_units = str(building_data.num_of_units or 1)
    else:
        num_units = "1"

    first_name = getattr(_project.project_data.owner, "first_name", "") or ""
    last_name = getattr(_project.project_data.owner, "last_name", "") or ""

    country_code = _variant.site.phpp_codes.country_code
    region = country_code.split("-")[0] if "-" in country_code else country_code

    return [
        kopf,
        PppSection("Nachweis_Zahl_WE", 1, 1, [num_units]),
        PppSection("Nachweis_Vorname", 1, 2, [first_name, ""]),
        PppSection("Nachweis_Nachname", 1, 2, [last_name, ""]),
        PppSection("Nachweis_Import_Aus_DesignPH", 1, 1, [f"Project data imported from PHX {timestamp}"]),
        PppSection("Nachweis_IWQ_Nutzung", 1, 1, ["10-Dwelling"]),
        PppSection("Klima_Region", 1, 1, [region]),
        PppSection("Klima_Standort", 1, 1, [_variant.site.phpp_codes.dataset_name or ""]),
    ]


# ---------------------------------------------------------------------------
# 2. Energy Reference Area (EBF)
# ---------------------------------------------------------------------------


def ebf_sections(_variant: PhxVariant) -> list[PppSection]:
    """Build the 5 EBF sections."""
    total_area = _variant.building.weighted_net_floor_area
    tfa = _variant.building.tfa_override
    ebf = tfa if tfa is not None else total_area

    return [
        PppSection("Flaechen_Flaecheneingabe_Anzahl_EBF", 1, 1, ["1"]),
        PppSection("Flaechen_Flaecheneingabe_a_EBF", 1, 1, [""]),
        PppSection("Flaechen_Flaecheneingabe_b_EBF", 1, 1, [""]),
        PppSection("Flaechen_Flaecheneingabe_Eigene_Ermittlung_EBF", 1, 1, [f"{ebf:f}"]),
        PppSection("Flaechen_Flaecheneingabe_eigener_Abzug_EBF", 1, 1, [""]),
    ]


# ---------------------------------------------------------------------------
# 3. Building Surfaces
# ---------------------------------------------------------------------------


def surface_sections(
    _variant: PhxVariant,
    _assembly_map: AssemblyMap,
) -> list[PppSection]:
    """Build all surface-related sections (names, dims, assemblies, tilt, orientation, groups)."""
    components = _variant.building.opaque_components[:MAX_SURFACES]
    n = len(components)

    # -- Names (100 rows, text padding)
    names = [c.display_name for c in components]

    # -- Counts (101 rows, offset)
    counts = ["1"] * n

    # -- Dimensions
    a_vals: list[str] = []
    b_vals: list[str] = []
    area_vals: list[str] = []
    for c in components:
        a, b, custom = _surface_dims(c)
        a_vals.append(a)
        b_vals.append(b)
        area_vals.append(custom)

    # -- Assembly references (keyed by display_name to match project.assembly_types)
    assembly_refs: list[str] = []
    assembly_names: list[str] = []
    for c in components:
        asm_name = c.assembly.display_name if c.assembly else ""
        if asm_name in _assembly_map:
            idx, ref = _assembly_map[asm_name]
            assembly_refs.append(ref)
            assembly_names.append(asm_name)
        else:
            assembly_refs.append("")
            assembly_names.append("")

    # -- Solar radiation: tilt, orientation, shading factor
    tilts = [f"{_surface_tilt(c)}" for c in components]
    orientations = [f"{_surface_orientation(c)}" for c in components]

    # -- Groups
    groups = [_group_label(c) for c in components]

    N = MAX_SURFACES
    N1 = MAX_SURFACES + 1
    empty_n = [""] * n

    return [
        PppSection(
            "Flaechen_Flaecheneingabe_Bauteil_Bezeichnung",
            N,
            1,
            _pad_text(names, N),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_Anzahl",
            N1,
            1,
            _pad_num_offset(counts, N1),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_a",
            N1,
            1,
            _pad_num_offset(a_vals, N1),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_b",
            N1,
            1,
            _pad_num_offset(b_vals, N1),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_Eigene_Ermittlung",
            N1,
            1,
            _pad_num_offset(area_vals, N1),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_eigener_Abzug",
            N1,
            1,
            _pad_num_offset(empty_n, N1),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_Bauteilaufbau",
            N,
            1,
            _pad_num(assembly_refs, N),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_Nr_Bausystem",
            N,
            1,
            _pad_num(assembly_names, N),
        ),
        PppSection(
            "Flaechen_Strahlungsbilanz_Neigung",
            N,
            1,
            _pad_num(tilts, N),
        ),
        PppSection(
            "Flaechen_Strahlungsbilanz_Orientierung",
            N,
            1,
            _pad_num(orientations, N),
        ),
        PppSection(
            "Flaechen_Strahlungsbilanz_Verschattungsfaktor",
            N,
            1,
            _pad_num(empty_n, N),
        ),
        PppSection(
            "Flaechen_Absorption",
            N,
            1,
            _pad_num(empty_n, N),
        ),
        PppSection(
            "Flaechen_Emission",
            N,
            1,
            _pad_num(empty_n, N),
        ),
        PppSection(
            "Flaechen_Flaecheneingabe_Zuordnung_zu_Gruppe",
            N,
            1,
            _pad_num(groups, N),
        ),
    ]


# ---------------------------------------------------------------------------
# 4. Thermal Bridges
# ---------------------------------------------------------------------------


def thermal_bridge_sections(_variant: PhxVariant) -> list[PppSection]:
    """Build all thermal bridge sections."""
    tbs: list[PhxComponentThermalBridge] = [tb for zone in _variant.building.zones for tb in zone.thermal_bridges][
        :MAX_THERMAL_BRIDGES
    ]
    n = len(tbs)

    names = [tb.display_name or "-" for tb in tbs]
    counts = [str(int(tb.quantity or 1)) for tb in tbs]
    lengths = [_fmt(tb.length) for tb in tbs]
    deductions = [""] * n
    psis = [_fmt(tb.psi_value) for tb in tbs]
    frsis = [_fmt(tb.fRsi_value) for tb in tbs]

    # Bausystem is 100x2 = 200 values (all empty)
    bausystem: list[str] = ["", ""] * MAX_THERMAL_BRIDGES

    group_nrs = [str(tb.group_number) for tb in tbs]

    TB = MAX_THERMAL_BRIDGES
    return [
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Bezeichnung",
            TB,
            1,
            _pad_text(names, TB),
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Anzahl",
            TB,
            1,
            _pad_num(counts, TB),
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Ermittlung_Laenge",
            TB,
            1,
            _pad_num(lengths, TB),
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Abzug_Laenge",
            TB,
            1,
            _pad_num(deductions, TB),
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Psi",
            TB,
            1,
            _pad_num(psis, TB),
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_fRsi",
            TB,
            1,
            _pad_num(frsis, TB),
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Bausystem",
            TB,
            2,
            bausystem,
        ),
        PppSection(
            "Flaechen_Waermebrueckeneingabe_Gruppen_Nr",
            TB,
            1,
            _pad_num(group_nrs, TB),
        ),
    ]


# ---------------------------------------------------------------------------
# 5. Windows
# ---------------------------------------------------------------------------


def _collect_window_elements(
    _variant: PhxVariant,
) -> list[tuple[PhxApertureElement, PhxComponentOpaque]]:
    """Collect all aperture elements with their host opaque component."""
    results: list[tuple[PhxApertureElement, PhxComponentOpaque]] = []
    for comp in _variant.building.opaque_components:
        for aperture in comp.apertures:
            for element in aperture.elements:
                results.append((element, comp))
    return sorted(results, key=lambda x: x[0].display_name)[:MAX_WINDOWS]


def window_sections(
    _variant: PhxVariant,
    _surface_index_map: SurfaceIndexMap,
    _glazing_map: GlazingMap,
    _frame_map: FrameMap,
) -> list[PppSection]:
    """Build all Fenster_* sections."""
    elements = _collect_window_elements(_variant)
    n = len(elements)

    pos_nrs: list[str] = []
    names: list[str] = []
    counts: list[str] = []
    hosts: list[str] = []
    frames: list[str] = []
    glazings: list[str] = []
    widths: list[str] = []
    heights: list[str] = []

    for i, (elem, host_comp) in enumerate(elements):
        pos_nrs.append(f"{i + 1:03d}")
        names.append(elem.display_name or f"Window_{i + 1:03d}")
        counts.append("1")

        # Host reference
        host_key = id(host_comp)
        if host_key in _surface_index_map:
            row_num, surf_name = _surface_index_map[host_key]
            hosts.append(f"{row_num}-{surf_name}")
        else:
            hosts.append("")

        # Frame and glazing references
        wt = elem.host.window_type
        glazing_key = _glazing_dedup_key(wt)
        frame_key = _frame_dedup_key(wt)

        if glazing_key in _glazing_map:
            glazings.append(_glazing_map[glazing_key][1])
        else:
            glazings.append("")

        if frame_key in _frame_map:
            frames.append(_frame_map[frame_key][1])
        else:
            frames.append("")

        widths.append(f"{elem.width:f}")
        heights.append(f"{elem.height:f}")

    # Fenster_Einbau: 152x4 = 608 values. Default all edges to 1 (normal install).
    einbau: list[str] = []
    for _ in range(n):
        einbau.extend(["1", "1", "1", "1"])
    einbau.extend([""] * (4 * (MAX_WINDOWS - n)))

    W = MAX_WINDOWS
    return [
        PppSection("Fenster_Bezeichnung_Pos_Nr", W, 1, _pad_num(pos_nrs, W)),
        PppSection("Fenster_Bezeichnung_Pos", W, 1, _pad_text(names, W)),
        PppSection("Fenster_Anzahl", W, 1, _pad_num(counts, W)),
        PppSection("Fenster_eingebaut", W, 1, _pad_num(hosts, W)),
        PppSection("Fenster_Rahmen", W, 1, _pad_num(frames, W)),
        PppSection("Fenster_Verglasung", W, 1, _pad_num(glazings, W)),
        PppSection("Fenster_Rohbaumasze_Breite", W, 1, _pad_num(widths, W)),
        PppSection("Fenster_Rohbaumasze_Hoehe", W, 1, _pad_num(heights, W)),
        PppSection("Fenster_Einbau", W, 4, einbau),
    ]


# ---------------------------------------------------------------------------
# 6. Window Shading
# ---------------------------------------------------------------------------


def shading_sections(_variant: PhxVariant) -> list[PppSection]:
    """Build all Verschattung_* sections."""
    elements = _collect_window_elements(_variant)
    n = len(elements)

    d_horis: list[str] = []
    h_horis: list[str] = []
    d_reveals: list[str] = []
    o_reveals: list[str] = []
    d_overs: list[str] = []
    o_overs: list[str] = []
    winter_factors: list[str] = []
    summer_factors: list[str] = []

    for elem, _ in elements:
        sd = elem.shading_dimensions
        d_horis.append(_fmt(sd.d_hori))
        h_horis.append(_fmt(sd.h_hori))
        d_reveals.append(_fmt(sd.d_reveal))
        o_reveals.append(_fmt(sd.o_reveal))
        d_overs.append(_fmt(sd.d_over))
        o_overs.append(_fmt(sd.o_over))
        winter_factors.append(_fmt(elem.winter_shading_factor))
        summer_factors.append(_fmt(elem.summer_shading_factor))

    W = MAX_WINDOWS
    return [
        PppSection("Verschattung_Entfernung_Hori", W, 1, _pad_num(d_horis, W)),
        PppSection("Verschattung_Hoehe_Hori", W, 1, _pad_num(h_horis, W)),
        PppSection("Verschattung_Tiefe_Laibung", W, 1, _pad_num(d_reveals, W)),
        PppSection("Verschattung_Abstand_Laibung", W, 1, _pad_num(o_reveals, W)),
        PppSection("Verschattung_Abstand_Ueberstand", W, 1, _pad_num(d_overs, W)),
        PppSection("Verschattung_Tiefe_Ueberstand", W, 1, _pad_num(o_overs, W)),
        PppSection("Verschattung_Zusaetzlicher_Faktor", W, 1, _pad_num(winter_factors, W)),
        PppSection("Verschattung_S_Zusaetzlicher_Faktor", W, 1, _pad_num(summer_factors, W)),
    ]


# ---------------------------------------------------------------------------
# 7. Ventilation
# ---------------------------------------------------------------------------


def ventilation_sections(_variant: PhxVariant) -> list[PppSection]:
    """Build the 6 ventilation sections."""
    bd = _variant.phi_cert
    building_data = getattr(bd, "building_data", None)
    n50 = ""
    room_height = ""
    net_volume = ""
    if building_data:
        n50 = _fmt(getattr(building_data, "airtightness_n50", None))
    # Compute average room height from spaces
    total_area = 0.0
    total_volume = 0.0
    for zone in _variant.building.zones:
        for space in zone.spaces:
            total_area += space.floor_area
            total_volume += space.net_volume
    if total_area > 0:
        room_height = f"{total_volume / total_area:f}"
        net_volume = f"{total_volume:f}"

    # Ventilation type - default to balanced PH ventilation with HR
    vent_type = "1-Balanced PH ventilation with HR"
    vent_device = ""
    wind_protection = "2-Moderate screening"

    # Try to get wind exposure from building_data
    if building_data:
        exp = getattr(building_data, "building_exposure_type", None)
        if exp is not None:
            wind_map = {
                1: "1-No screening",
                2: "2-Moderate screening",
                3: "3-High screening",
            }
            if hasattr(exp, "value"):
                wind_protection = wind_map.get(exp.value, "2-Moderate screening")

    return [
        PppSection(
            "Lueftung_Infiltrationsluftwechsel_Drucktestluftwechsel",
            1,
            1,
            [n50],
        ),
        PppSection("Lueftung_Raumhoehe", 1, 1, [room_height]),
        PppSection(
            "Lueftung_Infiltrationsluftwechsel_Netto_Volumenstrom",
            1,
            1,
            [net_volume],
        ),
        PppSection(
            "Lueftung_Art_Der_Lueftungsanlage",
            1,
            2,
            [vent_type, ""],
        ),
        PppSection(
            "Lueftung_Auswahl_Lueftungsgeraet",
            1,
            3,
            [vent_device, "", ""],
        ),
        PppSection(
            "Lueftung_Infiltration_Windschutzkoeffizient",
            1,
            2,
            [wind_protection, ""],
        ),
    ]


# ---------------------------------------------------------------------------
# 8. U-Value Blocks (60 blocks, all empty — simplified approach)
# ---------------------------------------------------------------------------


def u_value_sections(_project: PhxProject, _assembly_map: AssemblyMap) -> list[PppSection]:
    """Build 60 U-value blocks. All blocks are empty (simplified — assembly U-values
    are provided via Komponenten_user_Bauteilaufbauten instead)."""
    sections: list[PppSection] = []
    for block_num in range(1, MAX_U_VALUE_BLOCKS + 1):
        prefix = f"U_Werte_Bauteil_{block_num}"
        sections.append(PppSection(f"{prefix}_Bezeichnung", 1, 5, [""] * 5))
        sections.append(PppSection(f"{prefix}_Delta_U", 1, 1, [""]))
        sections.append(PppSection(f"{prefix}_Flaechenanteil_2", 1, 1, [""]))
        sections.append(PppSection(f"{prefix}_Flaechenanteil_3", 1, 1, [""]))
        sections.append(PppSection(f"{prefix}_Innendaemmung", 1, 1, [""]))
        sections.append(
            PppSection(
                f"{prefix}_Waermeuebergangswiderstand",
                2,
                1,
                ["", "0.0"],
            )
        )
        sections.append(
            PppSection(
                f"{prefix}_Summe_Breite_Dicke",
                8,
                1,
                [""] * 8,
            )
        )
        sections.append(PppSection(f"{prefix}_Teilflaechen", 8, 6, [""] * 48))
    return sections


# ---------------------------------------------------------------------------
# 9. User Components
# ---------------------------------------------------------------------------


def _glazing_dedup_key(wt: PhxConstructionWindow) -> str:
    """Return a dedup key for glazing type."""
    return f"{wt.glazing_type_display_name}|{wt.glass_g_value}|{wt.u_value_glass}"


def _frame_dedup_key(wt: PhxConstructionWindow) -> str:
    """Return a dedup key for frame type."""
    return (
        f"{wt.frame_type_display_name}"
        f"|{wt.frame_left.width}|{wt.frame_left.u_value}"
        f"|{wt.frame_right.width}|{wt.frame_right.u_value}"
        f"|{wt.frame_top.width}|{wt.frame_top.u_value}"
        f"|{wt.frame_bottom.width}|{wt.frame_bottom.u_value}"
    )


def _build_frame_row(wt: PhxConstructionWindow) -> list[str]:
    """Build a 44-element row for a frame type."""
    row: list[str] = [""] * 44
    row[0] = wt.frame_type_display_name

    # Col 2 (idx 1): empty
    # Col 3 (idx 2): psi-glazing average
    avg_psi_g = (
        wt.frame_left.psi_glazing + wt.frame_right.psi_glazing + wt.frame_top.psi_glazing + wt.frame_bottom.psi_glazing
    ) / 4.0
    row[2] = f"{avg_psi_g}"

    # Col 4 (idx 3): empty
    # Cols 5-12 (idx 4-11): width (mm) and Uf for each side
    sides = [wt.frame_left, wt.frame_right, wt.frame_top, wt.frame_bottom]
    for i, frame_el in enumerate(sides):
        row[4 + i * 2] = f"{frame_el.width * 1000:f}"
        row[5 + i * 2] = f"{frame_el.u_value:f}"

    # Cols 13-36 (idx 12-35): empty (installation psi situations)

    # Col 37 (idx 36): psi-glazing avg (same as col 3)
    row[36] = f"{avg_psi_g}"
    # Col 38 (idx 37): psi-glazing left
    row[37] = f"{wt.frame_left.psi_glazing:f}"
    # Col 39 (idx 38): psi-glazing right
    row[38] = f"{wt.frame_right.psi_glazing:f}"

    # Cols 40-43 (idx 39-42): empty

    # Col 44 (idx 43): psi-install average
    avg_psi_i = (
        wt.frame_left.psi_install + wt.frame_right.psi_install + wt.frame_top.psi_install + wt.frame_bottom.psi_install
    ) / 4.0
    row[43] = f"{avg_psi_i:f}"

    return row


def user_component_sections(
    _project: PhxProject,
    _glazing_map: GlazingMap,
    _frame_map: FrameMap,
    _assembly_map: AssemblyMap,
) -> list[PppSection]:
    """Build the 3 user component sections (glazing, frames, assemblies)."""

    # -- Glazing (99 x 3)
    glazing_values: list[str] = []
    glazing_wt_by_key: dict[str, PhxConstructionWindow] = {}
    for wt in _project.window_types.values():
        key = _glazing_dedup_key(wt)
        if key not in glazing_wt_by_key:
            glazing_wt_by_key[key] = wt

    def _glazing_sort_key(item):
        return _glazing_map.get(item[0], (999, ""))[0]

    for key, wt in sorted(glazing_wt_by_key.items(), key=_glazing_sort_key):
        glazing_values.extend(
            [
                wt.glazing_type_display_name,
                f"{wt.glass_g_value}",
                f"{wt.u_value_glass:f}",
            ]
        )
    # Pad remaining slots
    for _ in range(MAX_USER_GLAZING - len(glazing_wt_by_key)):
        glazing_values.extend(["", "0.0", "0.000000"])

    # -- Frames (99 x 44)
    frame_values: list[str] = []
    frame_wt_by_key: dict[str, PhxConstructionWindow] = {}
    for wt in _project.window_types.values():
        key = _frame_dedup_key(wt)
        if key not in frame_wt_by_key:
            frame_wt_by_key[key] = wt

    def _frame_sort_key(item):
        return _frame_map.get(item[0], (999, ""))[0]

    for key, wt in sorted(frame_wt_by_key.items(), key=_frame_sort_key):
        frame_values.extend(_build_frame_row(wt))
    # Pad remaining slots
    for _ in range(MAX_USER_FRAMES - len(frame_wt_by_key)):
        row = [""] * 44
        row[2] = "0.0"
        row[36] = "0.0"
        row[43] = "0.000000"
        frame_values.extend(row)

    # -- Assemblies (17 x 4)
    assembly_values: list[str] = []
    sorted_assemblies = sorted(_assembly_map.items(), key=lambda x: x[1][0])
    for asm_id, (idx, ref) in sorted_assemblies:
        asm = _project.assembly_types.get(asm_id)
        if asm:
            assembly_values.extend(
                [
                    asm.display_name,
                    f"{asm.u_value:f}" if hasattr(asm, "u_value") and asm.u_value else "0.000000",
                    "0.150000",  # thermal capacitance default
                    "0",
                ]
            )
        else:
            assembly_values.extend(["", "0.000000", "0.000000", "0"])
    # Pad remaining slots
    for _ in range(MAX_USER_ASSEMBLIES - len(sorted_assemblies)):
        assembly_values.extend(["", "0.000000", "0.000000", "0"])

    return [
        PppSection(
            "Komponenten_user_Verglasung",
            MAX_USER_GLAZING,
            3,
            glazing_values,
        ),
        PppSection(
            "Komponenten_user_Fensterrahmen",
            MAX_USER_FRAMES,
            44,
            frame_values,
        ),
        PppSection(
            "Komponenten_user_Bauteilaufbauten",
            MAX_USER_ASSEMBLIES,
            4,
            assembly_values,
        ),
    ]


# ---------------------------------------------------------------------------
# 10. Overbuilt Areas
# ---------------------------------------------------------------------------


def overbuilt_sections() -> list[PppSection]:
    """Build the 5 overbuilt area sections (all empty)."""
    return [
        PppSection("Flaechen_Flaecheneingabe_Anzahl_Ueberbaut", 1, 1, [""]),
        PppSection("Flaechen_Flaecheneingabe_a_Ueberbaut", 1, 1, [""]),
        PppSection("Flaechen_Flaecheneingabe_b_Ueberbaut", 1, 1, [""]),
        PppSection("Flaechen_Flaecheneingabe_Eigene_Ermittlung_Ueberbaut", 1, 1, ["0.000000"]),
        PppSection("Flaechen_Flaecheneingabe_eigener_Abzug_Ueberbaut", 1, 1, [""]),
    ]
