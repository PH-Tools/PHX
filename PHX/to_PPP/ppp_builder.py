# -*- Python Version: 3.10 -*-

"""Orchestrator: builds a complete PppFile from a PhxProject."""

from __future__ import annotations

from PHX.model.project import PhxProject
from PHX.to_PPP.ppp_schemas import (
    ASSEMBLY_ID_OFFSET,
    AssemblyMap,
    FrameMap,
    GlazingMap,
    SurfaceIndexMap,
    _frame_dedup_key,
    _glazing_dedup_key,
    ebf_sections,
    meta_sections,
    overbuilt_sections,
    shading_sections,
    surface_sections,
    thermal_bridge_sections,
    u_value_sections,
    user_component_sections,
    ventilation_sections,
    window_sections,
)
from PHX.to_PPP.ppp_sections import PppFile


def _build_assembly_map(project: PhxProject) -> AssemblyMap:
    """Build {assembly.identifier: (ppp_id, "NNud-Name")} for all project assemblies."""
    result: AssemblyMap = {}
    for i, (asm_id, asm) in enumerate(project.assembly_types.items()):
        ppp_id = ASSEMBLY_ID_OFFSET + i
        ref = f"{ppp_id:02d}ud-{asm.display_name}"
        result[asm_id] = (ppp_id, ref)
    return result


def _build_glazing_map(project: PhxProject) -> GlazingMap:
    """Build {dedup_key: (idx, "NNud-GlazingName")} for unique glazing types."""
    result: GlazingMap = {}
    idx = 1
    for wt in project.window_types.values():
        key = _glazing_dedup_key(wt)
        if key not in result:
            ref = f"{idx:02d}ud-{wt.glazing_type_display_name}"
            result[key] = (idx, ref)
            idx += 1
    return result


def _build_frame_map(project: PhxProject) -> FrameMap:
    """Build {dedup_key: (idx, "NNud-FrameName")} for unique frame types."""
    result: FrameMap = {}
    idx = 1
    for wt in project.window_types.values():
        key = _frame_dedup_key(wt)
        if key not in result:
            ref = f"{idx:02d}ud-{wt.frame_type_display_name}"
            result[key] = (idx, ref)
            idx += 1
    return result


def _build_surface_index_map(variant) -> SurfaceIndexMap:
    """Build {id(component): (1-based row_num, display_name)} for opaque components."""
    result: SurfaceIndexMap = {}
    for i, comp in enumerate(variant.building.opaque_components):
        result[id(comp)] = (i + 1, comp.display_name)
    return result


def build_ppp_file(project: PhxProject) -> PppFile:
    """Build a complete PppFile from a PhxProject."""
    variant = project.variants[0]

    # Build cross-reference maps
    assembly_map = _build_assembly_map(project)
    glazing_map = _build_glazing_map(project)
    frame_map = _build_frame_map(project)
    surface_index_map = _build_surface_index_map(variant)

    sections = []
    sections += meta_sections(project, variant)
    sections += ebf_sections(variant)
    sections += surface_sections(variant, assembly_map)
    sections += thermal_bridge_sections(variant)
    sections += window_sections(variant, surface_index_map, glazing_map, frame_map)
    sections += shading_sections(variant)
    sections += ventilation_sections(variant)
    sections += u_value_sections(project, assembly_map)
    sections += user_component_sections(project, glazing_map, frame_map, assembly_map)
    sections += overbuilt_sections()

    return PppFile(sections=sections)
