# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions used to create Project elements from the Honeybee-Model"""

from typing import Union, Optional

from honeybee import model
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass
from honeybee_energy.construction import window, windowshade

from honeybee_energy_ph.properties.construction.window import (
    WindowConstructionPhProperties,
)
from honeybee_ph_utils import iso_10077_1

from PHX.model import constructions, project, shades


def _conductivity_from_r_value(_r_value: float, _thickness: float) -> float:
    """Returns a material conductivity value (W/mk), given a known r-value (M2K/W) and thickness (M).

    Arguments:
    ----------
        * _r_value (float): The total R-Value of the layer.
        * _thickness (float): The total thickness of the layer.

    Returns:
    --------
        * float: The Conductivity value of the layer.
    """
    conductivity = _thickness / _r_value
    return conductivity


def build_phx_material_from_hb_EnergyMaterial(
    _hb_material: EnergyMaterial,
) -> constructions.PhxMaterial:
    """Returns a new PhxMaterial, with attributes based on a Honeybee-Energy EnergyMaterial.

    Arguments:
    ----------
        * _hb_material (EnergyMaterialNoMass): The Honeybee-Energy EnergyMaterialNoMass
        * _thickness (float): The thickness of the material layer.

    Returns:
    --------
        * (constructions.PhxMaterial): The new PhxMaterial with attributes based on the
            Honeybee-Energy EnergyMaterial.
    """
    new_mat = constructions.PhxMaterial()
    new_mat.display_name = _hb_material.display_name
    new_mat.conductivity = _hb_material.conductivity
    new_mat.density = _hb_material.density
    new_mat.heat_capacity = _hb_material.specific_heat
    new_mat.percentage_of_assembly = _hb_material.properties.ph.percentage_of_assembly  # type: ignore

    # -- Defaults
    new_mat.porosity = 0.95
    new_mat.water_vapor_resistance = 1.0
    new_mat.reference_water = 0.0

    return new_mat


def build_phx_material_from_hb_EnergyMaterialNoMass(
    _hb_material: EnergyMaterialNoMass, _thickness: float
) -> constructions.PhxMaterial:
    """Returns a new PhxMaterial, with attributes based on a Honeybee-Energy EnergyMaterialNoMass.
    Note that a thickness is required in order to determine the material conductivity.

    Arguments:
    ----------
        * _hb_material (EnergyMaterialNoMass): The Honeybee-Energy EnergyMaterialNoMass
        * _thickness (float): The thickness of the material layer.

    Returns:
    --------
        * (constructions.PhxMaterial): The new PhxMaterial with attributes based on the
            Honeybee-Energy EnergyMaterialNoMass.
    """
    new_mat = constructions.PhxMaterial()
    new_mat.display_name = _hb_material.display_name
    new_mat.conductivity = _conductivity_from_r_value(_hb_material.r_value, _thickness)
    new_mat.density = _hb_material.mass_area_density
    new_mat.heat_capacity = _hb_material.area_heat_capacity

    # -- Defaults
    new_mat.water_vapor_resistance = 1.0
    new_mat.porosity = 0.95
    new_mat.reference_water = 0.0

    return new_mat


def build_layer_from_hb_material(
    _hb_material: Union[EnergyMaterial, EnergyMaterialNoMass]
) -> constructions.PhxLayer:
    """Returns a new PHX-Layer with attributes based on a Honeybee-Material.

    Arguments:
    ----------
        *_hb_material (EnergyMaterial | EnergyMaterialNoMass): The Honeybee Material.

    Returns:
    --------
        * constructions.Layer: The new PHX-Layer object.
    """
    new_layer = constructions.PhxLayer()

    if isinstance(_hb_material, EnergyMaterial):
        new_layer.thickness_m = _hb_material.thickness

        if _hb_material.properties.ph.base_materials:  # type: ignore
            ## -- Layer is a heterogeneous material layer (ie: stud + insulation)
            for hb_sub_material in _hb_material.properties.ph.base_materials:  # type: ignore
                new_layer.add_material(
                    build_phx_material_from_hb_EnergyMaterial(hb_sub_material)
                )
        else:
            # -- Layer is homogeneous, use the base HB Material
            new_layer.add_material(
                build_phx_material_from_hb_EnergyMaterial(_hb_material)
            )

    elif isinstance(_hb_material, EnergyMaterialNoMass):
        # -- NoMass layers cannot be heterogeneous (yet....)
        new_layer.thickness_m = (
            0.1  # 0.1m = 4". Use as default since No-Mass has no thickness
        )
        new_layer.add_material(
            build_phx_material_from_hb_EnergyMaterialNoMass(
                _hb_material, new_layer.thickness_m
            )
        )

    else:
        raise TypeError(f"Error: Unsupported Material type: '{type(_hb_material)}'.")

    return new_layer


def build_opaque_assemblies_from_HB_model(
    _project: project.PhxProject, _hb_model: model.Model
) -> None:
    """Build Opaque Constructions from Honeybee Faces and add to the PHX-Project.

    Will also align the id_nums of the face's Construction with the Assembly in the Project dict.

    Arguments:
    ----------
        * _hb_model (model.Model): The Honeybee Model to use as the source.

    Returns:
    --------
        * None
    """

    for room in _hb_model.rooms:
        for face in room.faces:
            hb_const = face.properties.energy.construction

            if not hb_const.identifier in _project.assembly_types:
                # -- Create a new Assembly with Layers from the Honeybee-Construction
                new_assembly = constructions.PhxConstructionOpaque()
                new_assembly.id_num = constructions.PhxConstructionOpaque._count
                new_assembly.display_name = hb_const.display_name
                new_assembly.layers = [
                    build_layer_from_hb_material(layer) for layer in hb_const.materials
                ]

                # -- Add the assembly to the Project
                _project.assembly_types[hb_const.identifier] = new_assembly

            hb_const.properties.ph.id_num = _project.assembly_types[
                hb_const.identifier
            ].id_num

    return None


def build_phx_window_type_from_HB_WindowConstruction(
    _project: project.PhxProject, 
    _hb_win_const: window.WindowConstruction,
    _shade_const: Optional[windowshade.WindowConstructionShade]
) -> constructions.PhxConstructionWindow:
    """Create a new PHX-WindowType based on a HB-Window-Construction.

    If any detailed PH-Params exist for the frame or glass on the HB-Window-Construction's
    .properties.ph.* then those will be used. Otherwise, the basic HB-Window-Construction
    attributes will be used.

    Arguments:
    ----------
        * _hb_win_const (window.WindowConstruction): The Honeybee Window Construction to
            base the new PHX-WindowType on.

    Returns:
    --------
        * (constructions.WindowType): The new PHX-WindowType.
    """

    phx_window_type = constructions.PhxConstructionWindow()
    phx_window_type.id_num = constructions.PhxConstructionWindow._count
    phx_window_type.display_name = _hb_win_const.display_name
    phx_window_type.identifier = _hb_win_const.identifier

    ph_params: WindowConstructionPhProperties = _hb_win_const.properties.ph  # type: ignore

    # -- Glass ----------------------------------------------------------------
    if ph_params.ph_glazing:
        # -- Use Detailed PH-Params
        phx_window_type.glazing_type_display_name = ph_params.ph_glazing.display_name
        phx_window_type.u_value_glass = ph_params.ph_glazing.u_factor
        phx_window_type.glass_g_value = ph_params.ph_glazing.g_value
    else:
        # -- Use the basic Honeybee Params
        phx_window_type.u_value_glass = _hb_win_const.u_factor
        phx_window_type.glass_g_value = _hb_win_const.shgc

    # -- Frames ---------------------------------------------------------------
    if ph_params.ph_frame:
        # -- Use Detailed PH-Params
        phx_window_type.frame_type_display_name = ph_params.ph_frame.display_name
        phx_window_type.frame_top.u_value = ph_params.ph_frame.top.u_factor
        phx_window_type.frame_top.width = ph_params.ph_frame.top.width
        phx_window_type.frame_top.psi_glazing = ph_params.ph_frame.top.psi_glazing
        phx_window_type.frame_top.psi_install = ph_params.ph_frame.top.psi_install

        phx_window_type.frame_right.u_value = ph_params.ph_frame.right.u_factor
        phx_window_type.frame_right.width = ph_params.ph_frame.right.width
        phx_window_type.frame_right.psi_glazing = ph_params.ph_frame.right.psi_glazing
        phx_window_type.frame_right.psi_install = ph_params.ph_frame.right.psi_install

        phx_window_type.frame_bottom.u_value = ph_params.ph_frame.bottom.u_factor
        phx_window_type.frame_bottom.width = ph_params.ph_frame.bottom.width
        phx_window_type.frame_bottom.psi_glazing = ph_params.ph_frame.bottom.psi_glazing
        phx_window_type.frame_bottom.psi_install = ph_params.ph_frame.bottom.psi_install

        phx_window_type.frame_left.u_value = ph_params.ph_frame.left.u_factor
        phx_window_type.frame_left.width = ph_params.ph_frame.left.width
        phx_window_type.frame_left.psi_glazing = ph_params.ph_frame.left.psi_glazing
        phx_window_type.frame_left.psi_install = ph_params.ph_frame.left.psi_install
    else:
        # -- Use the basic Honeybee Params
        phx_window_type.frame_top.u_value = _hb_win_const.u_factor
        phx_window_type.frame_top.width = 0.1
        phx_window_type.frame_top.psi_glazing = 0.0
        phx_window_type.frame_top.psi_install = 0.0

        phx_window_type.frame_right.u_value = _hb_win_const.u_factor
        phx_window_type.frame_right.width = 0.1
        phx_window_type.frame_right.psi_glazing = 0.0
        phx_window_type.frame_right.psi_install = 0.0

        phx_window_type.frame_bottom.u_value = _hb_win_const.u_factor
        phx_window_type.frame_bottom.width = 0.1
        phx_window_type.frame_bottom.psi_glazing = 0.0
        phx_window_type.frame_bottom.psi_install = 0.0

        phx_window_type.frame_left.u_value = _hb_win_const.u_factor
        phx_window_type.frame_left.width = 0.1
        phx_window_type.frame_left.psi_glazing = 0.0
        phx_window_type.frame_left.psi_install = 0.0

    # -- Window Params as per ISO-10077-1 -------------------------------------
    if ph_params.ph_frame and ph_params.ph_glazing:
        phx_window_type.frame_factor = iso_10077_1.calculate_window_frame_factor(
            ph_params.ph_frame, ph_params.ph_glazing
        )
        phx_window_type.u_value_window = iso_10077_1.calculate_window_uw(
            ph_params.ph_frame, ph_params.ph_glazing
        )
    else:
        phx_window_type.frame_factor = 0.75
        phx_window_type.u_value_window = _hb_win_const.u_factor

    # -- Add Shading, if any --------------------------------------------------
    if _shade_const:
        phx_shade = _project.shade_types[_shade_const.shade_material.identifier]
        phx_window_type.id_num_shade = phx_shade.id_num

    return phx_window_type


def build_transparent_assembly_types_from_HB_Model(
    _project: project.PhxProject, _hb_model: model.Model
) -> None:
    """Create PHX-WindowTypes (constructions) from an HB Model and add to the PHX-Project

    Will also align the id_nums of the Aperture Construction's with the WindowType in the Project dict.

    Arguments:
    ----------
        * _project (_project: project.PhxProject): The PhxProject to store the new window-type on.
        * _hb_model (model.Model): The Honeybee Model to use as the source.

    Returns:
    --------
        * None
    """
    apertures = (aperture for room in _hb_model.rooms for face in room.faces for aperture in face.apertures)
    for aperture in apertures:
        # -- If it is a WindowConstructionShade, pull out the normal WindowConstruction
        if hasattr(aperture.properties.energy.construction, "window_construction"):
            # -- It is a WindowConstructionShade
            hb_win_construction = aperture.properties.energy.construction.window_construction
            hb_shade_construction = aperture.properties.energy.construction
        else:
            # -- It is a normal WindowConstruction
            hb_win_construction = aperture.properties.energy.construction
            hb_shade_construction = None

        # --- Build all the PHX Shades first since the window needs to know their ID num
        if hb_shade_construction and hb_shade_construction.shade_material.identifier not in _project.shade_types:
            phx_shade_type = build_phx_shade_type_from_HB_WindowConstructionShade(hb_shade_construction)
            _project.add_new_shade_type(phx_shade_type)

        # --- Build the PHX Windows
        if hb_win_construction.identifier not in _project.window_types:
            phx_aperture_constr = build_phx_window_type_from_HB_WindowConstruction(
                _project, hb_win_construction, hb_shade_construction)
            _project.add_new_window_type(phx_aperture_constr)

        # -- Keep all the IDs aligned
        phx_win_type = _project.window_types[hb_win_construction.identifier]
        hb_win_construction.properties.ph.id_num = phx_win_type.id_num

    return None


def build_phx_shade_type_from_HB_WindowConstructionShade(
        _hb_const: windowshade.WindowConstructionShade) -> shades.PhxWindowShade:
    """Create a new PhxWindowShade object with attributes based on an HBE-WindowConstructionShade.
    
    Arguments:
    ----------
        * _hb_const: (windowshade.WindowConstructionShade) The source HBE-WindowConstructionShade.
    
    Returns:
    --------
        * (shades.PhxWindowShade): The new PHX Window Shade type.
    """
    _hb_shade_material = _hb_const.shade_material
    
    phx_shade = shades.PhxWindowShade()
    phx_shade.display_name = _hb_shade_material.display_name
    phx_shade.identifier = _hb_shade_material.identifier
    phx_shade.reduction_factor = _hb_shade_material.solar_transmittance #TODO: Phius Shade Method?

    # -- Keep the IDs aligned
    _hb_const.properties.ph.id_num = phx_shade.id_num

    return phx_shade
