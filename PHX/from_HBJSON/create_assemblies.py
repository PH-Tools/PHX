# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions used to create Project elements from the Honeybee-Model"""

from typing import Union, Optional, Any, Tuple, List

from honeybee import model
from honeybee.aperture import Aperture
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass
from honeybee_energy.construction import window, windowshade

from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy_ph.properties.construction.window import (
    WindowConstructionPhProperties,
)
from honeybee_energy_ph.construction.window import PhWindowGlazing, PhWindowFrame
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
                _project.add_assembly_type(new_assembly, hb_const.identifier)

            # -- Keep the ID numbers in sync
            _phx_assembly = _project.assembly_types[hb_const.identifier]
            hb_const.properties.ph.id_num = _phx_assembly.id_num

    return None


def _set_phx_window_type_glazing(
    _phx_window_type: constructions.PhxConstructionWindow,
    _hbph_glazing: Optional[PhWindowGlazing],
) -> constructions.PhxConstructionWindow:
    if _hbph_glazing:
        # -- Use Detailed PH-Params
        _phx_window_type.glazing_type_display_name = _hbph_glazing.display_name
        _phx_window_type.u_value_glass = _hbph_glazing.u_factor
        _phx_window_type.glass_g_value = _hbph_glazing.g_value
    return _phx_window_type


def _set_phx_window_type_frames(
    _phx_window_type: constructions.PhxConstructionWindow,
    _hbph_frame: Optional[PhWindowFrame],
) -> constructions.PhxConstructionWindow:
    """Sets the Frame properties of a PhxConstructionWindow based on a Honeybee-Ph WindowFrame."""
    if _hbph_frame:
        # -- Use Detailed PH-Params
        _phx_window_type.frame_type_display_name = _hbph_frame.display_name
        _phx_window_type.frame_top.u_value = _hbph_frame.top.u_factor
        _phx_window_type.frame_top.width = _hbph_frame.top.width
        _phx_window_type.frame_top.psi_glazing = _hbph_frame.top.psi_glazing
        _phx_window_type.frame_top.psi_install = _hbph_frame.top.psi_install

        _phx_window_type.frame_right.u_value = _hbph_frame.right.u_factor
        _phx_window_type.frame_right.width = _hbph_frame.right.width
        _phx_window_type.frame_right.psi_glazing = _hbph_frame.right.psi_glazing
        _phx_window_type.frame_right.psi_install = _hbph_frame.right.psi_install

        _phx_window_type.frame_bottom.u_value = _hbph_frame.bottom.u_factor
        _phx_window_type.frame_bottom.width = _hbph_frame.bottom.width
        _phx_window_type.frame_bottom.psi_glazing = _hbph_frame.bottom.psi_glazing
        _phx_window_type.frame_bottom.psi_install = _hbph_frame.bottom.psi_install

        _phx_window_type.frame_left.u_value = _hbph_frame.left.u_factor
        _phx_window_type.frame_left.width = _hbph_frame.left.width
        _phx_window_type.frame_left.psi_glazing = _hbph_frame.left.psi_glazing
        _phx_window_type.frame_left.psi_install = _hbph_frame.left.psi_install
    return _phx_window_type


def _set_phx_window_type_u_w_value(
    _phx_window_type: constructions.PhxConstructionWindow,
    _hbph_frame: Optional[PhWindowFrame],
    _hbph_glazing: Optional[PhWindowGlazing],
) -> constructions.PhxConstructionWindow:
    """Set the U-Value and Frame-Factor of a PhxConstructionWindow based on the given HBPH-Params."""
    if _hbph_frame and _hbph_glazing:
        _phx_window_type.frame_factor = iso_10077_1.calculate_window_frame_factor(
            _hbph_frame, _hbph_glazing
        )
        _phx_window_type.u_value_window = iso_10077_1.calculate_window_uw(
            _hbph_frame, _hbph_glazing
        )
    return _phx_window_type


def build_phx_window_type_from_HB_WindowConstruction(
    _project: project.PhxProject,
    _hb_win_const: window.WindowConstruction,
    _shade_const: Optional[windowshade.WindowConstructionShade],
) -> constructions.PhxConstructionWindow:
    """Create a new PhxConstructionWindow based on a HBPH-WindowConstruction.

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

    # -------------------------------------------------------------------------
    # -- Set the basic data first ---------------------------------------------
    # -- Glass ----------------------------------------------------------------
    phx_window_type.u_value_glass = _hb_win_const.u_factor
    phx_window_type.glass_g_value = _hb_win_const.shgc
    phx_window_type.u_value_window = _hb_win_const.u_factor
    phx_window_type.frame_factor = 0.75

    # -- Frames ---------------------------------------------------------------
    phx_window_type.set_all_frames_u_value(_hb_win_const.u_factor)
    phx_window_type.set_all_frames_width(0.1)
    phx_window_type.set_all_frames_psi_glazing(0.0)
    phx_window_type.set_all_frames_psi_install(0.0)

    # -------------------------------------------------------------------------
    # -- Then set detailed PH data, if any  -----------------------------------
    ph_frame = ph_params.ph_frame
    ph_glazing = ph_params.ph_glazing
    phx_window_type = _set_phx_window_type_glazing(phx_window_type, ph_glazing)
    phx_window_type = _set_phx_window_type_frames(phx_window_type, ph_frame)

    # -- Window Params as per ISO-10077-1 -------------------------------------
    phx_window_type = _set_phx_window_type_u_w_value(
        phx_window_type, ph_frame, ph_glazing
    )

    # -- Add Shading to the Window, if any -------------------------------------
    if _shade_const:
        phx_shade = _project.shade_types[_shade_const.shade_material.identifier]
        phx_window_type._id_num_shade = phx_shade.id_num

    return phx_window_type


def build_phx_shade_type_from_HB_WindowConstructionShade(
    _hb_const: windowshade.WindowConstructionShade,
) -> shades.PhxWindowShade:
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
    # TODO: Phius Shade Method?
    phx_shade.reduction_factor = _hb_shade_material.solar_transmittance

    # -- Keep the IDs aligned
    _hb_const.properties.ph.id_num = phx_shade.id_num  # type: ignore

    return phx_shade


def _get_hbph_window_constructions(
    _ap_ep_const,
) -> Tuple[WindowConstruction, Optional[WindowConstructionShade]]:
    """Get the WindowConstruction and WindowConstructionShade from an HB-Aperture Construction."""
    try:
        # -- It is a WindowConstructionShade if it has a 'window_construction' attribute
        hb_win_const = _ap_ep_const.window_construction
        hb_shade_const = _ap_ep_const
    except AttributeError:
        # -- otherwise, its a normal window construction
        hb_win_const = _ap_ep_const
        hb_shade_const = None

    return hb_win_const, hb_shade_const


def _new_shade_type(
    _project: project.PhxProject, hb_shade_const: WindowConstructionShade
) -> bool:
    """Check if a new shade type needs to be created for the given HB-WindowConstructionShade."""
    if hb_shade_const.shade_material.identifier in _project.shade_types:
        return False
    else:
        return True


def build_transparent_assembly_types_from_HB_Model(
    _project: project.PhxProject, _hb_apertures: List[Aperture]
) -> None:
    """Create PHX-WindowTypes (constructions) from an HB Model and add to the PHX-Project

    Will also align the id_nums of the Aperture Construction's with the WindowType in the Project dict.

    Arguments:
    ----------
        * _project (_project: project.PhxProject): The PhxProject to store the new window-type on.
        * _hb_apertures (List[Aperture]): The Honeybee Apertures to use as the source

    Returns:
    --------
        * None
    """

    for aperture in _hb_apertures:
        # ---------------------------------------------------------------------
        ap_ep_const = aperture.properties.energy.construction  # type: ignore
        hb_win_const, hb_shade_const = _get_hbph_window_constructions(ap_ep_const)

        # ---------------------------------------------------------------------
        # --- Build all the PHX Shades first since the window needs to know their ID num
        if hb_shade_const and _new_shade_type(_project, hb_shade_const):
            phx_shade_type = build_phx_shade_type_from_HB_WindowConstructionShade(
                hb_shade_const
            )
            _project.add_new_shade_type(phx_shade_type)

        # ---------------------------------------------------------------------
        # --- Build the PHX Windows
        if hb_win_const.identifier not in _project.window_types:
            phx_aperture_constr = build_phx_window_type_from_HB_WindowConstruction(
                _project, hb_win_const, hb_shade_const
            )
            _project.add_new_window_type(phx_aperture_constr)

        # ---------------------------------------------------------------------
        # -- Keep all the IDs aligned
        phx_win_type = _project.window_types[hb_win_const.identifier]
        hb_win_const.properties.ph.id_num = phx_win_type.id_num  # type: ignore

    return None
