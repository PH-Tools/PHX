from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
from honeybee_energy.material.shade import EnergyWindowMaterialShade
from honeybee_energy_ph.construction.window import PhWindowFrame, PhWindowFrameElement, PhWindowGlazing

from PHX.from_HBJSON.create_assemblies import build_phx_window_type_from_HB_WindowConstruction
from PHX.model.project import PhxProject


def test_create_phx_window_from_hb_window_default():
    phx_proj = PhxProject()

    hb_const = WindowConstruction(
        identifier="test_window_construction",
        materials=[
            EnergyWindowMaterialSimpleGlazSys(
                identifier="test_glazing_mat",
                u_factor=1.0,
                shgc=0.5,
            )
        ],
    )

    phx_window_type = build_phx_window_type_from_HB_WindowConstruction(phx_proj, hb_const, None)

    # -- Basic Values
    assert phx_window_type.display_name == "test_window_construction"
    assert phx_window_type.u_value_glass == 1.0097620191408223
    assert phx_window_type.glass_g_value == 0.5

    # -- Defaulty Values
    assert phx_window_type.frame_top.u_value == 1.0097620191408223
    assert phx_window_type.frame_top.width == 0.1
    assert phx_window_type.frame_top.psi_glazing == 0.0
    assert phx_window_type.frame_top.psi_install == 0.0

    # -- Defaulty Values
    assert phx_window_type.frame_factor == 0.75
    assert phx_window_type.u_value_window == hb_const.u_factor

    # -- No Shades Added
    assert len(phx_proj.shade_types) == 0


def test_create_phx_window_from_hb_window_with_ph_glazing():
    # -- Build the Inputs
    phx_proj = PhxProject()
    hb_const = WindowConstruction(
        identifier="test_window_construction",
        materials=[
            EnergyWindowMaterialSimpleGlazSys(
                identifier="test_glazing_mat",
                u_factor=1.0,
                shgc=0.5,
            )
        ],
    )

    ph_glazing = PhWindowGlazing("id_glazing")
    ph_glazing.u_factor = 0.25
    ph_glazing.g_value = 0.56

    hb_const.properties.ph.ph_glazing = ph_glazing  # type: ignore

    # -- build the PHX Window Type
    phx_window_type = build_phx_window_type_from_HB_WindowConstruction(phx_proj, hb_const, None)

    # -- Basic Values
    assert phx_window_type.display_name == "test_window_construction"
    assert phx_window_type.u_value_glass == 0.25
    assert phx_window_type.glass_g_value == 0.56

    # -- Frame Values
    assert phx_window_type.frame_top.u_value == 1.0097620191408223
    assert phx_window_type.frame_top.width == 0.1
    assert phx_window_type.frame_top.psi_glazing == 0.0
    assert phx_window_type.frame_top.psi_install == 0.0

    # -- Defaulty Values
    assert phx_window_type.frame_factor == 0.75
    assert phx_window_type.u_value_window == 1.0097620191408223

    # -- No Shades Added
    assert len(phx_proj.shade_types) == 0


def test_create_phx_window_from_hb_window_with_ph_frame():
    # -- Build the Inputs
    phx_proj = PhxProject()
    hb_const = WindowConstruction(
        identifier="test_window_construction",
        materials=[
            EnergyWindowMaterialSimpleGlazSys(
                identifier="test_glazing_mat",
                u_factor=1.0,
                shgc=0.5,
            )
        ],
    )
    hb_frame = PhWindowFrame("id_frame")
    hb_frame.top = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.top.u_factor = 0.123
    hb_frame.top.width = 0.205
    hb_frame.top.psi_glazing = 0.5
    hb_frame.top.psi_install = 0.6
    hb_frame.right = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.right.u_factor = 0.345
    hb_frame.right.width = 0.205
    hb_frame.right.psi_glazing = 0.5
    hb_frame.right.psi_install = 0.6
    hb_frame.bottom = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.bottom.u_factor = 0.567
    hb_frame.bottom.width = 0.205
    hb_frame.bottom.psi_glazing = 0.5
    hb_frame.bottom.psi_install = 0.6
    hb_frame.left = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.left.u_factor = 0.789
    hb_frame.left.width = 0.205
    hb_frame.left.psi_glazing = 0.5
    hb_frame.left.psi_install = 0.6

    hb_const.properties.ph.ph_frame = hb_frame  # type: ignore

    # -- build the PHX Window Type
    phx_window_type = build_phx_window_type_from_HB_WindowConstruction(phx_proj, hb_const, None)

    # -- Basic Values
    assert phx_window_type.display_name == "test_window_construction"

    # # -- Frame Values
    assert phx_window_type.frame_top.u_value == 0.123
    assert phx_window_type.frame_top.width == 0.205
    assert phx_window_type.frame_top.psi_glazing == 0.5
    assert phx_window_type.frame_top.psi_install == 0.6

    assert phx_window_type.frame_right.u_value == 0.345
    assert phx_window_type.frame_right.width == 0.205
    assert phx_window_type.frame_right.psi_glazing == 0.5
    assert phx_window_type.frame_right.psi_install == 0.6

    assert phx_window_type.frame_bottom.u_value == 0.567
    assert phx_window_type.frame_bottom.width == 0.205
    assert phx_window_type.frame_bottom.psi_glazing == 0.5
    assert phx_window_type.frame_bottom.psi_install == 0.6

    assert phx_window_type.frame_left.u_value == 0.789
    assert phx_window_type.frame_left.width == 0.205
    assert phx_window_type.frame_left.psi_glazing == 0.5
    assert phx_window_type.frame_left.psi_install == 0.6

    # -- Glazing Values
    assert phx_window_type.glass_g_value == 0.5
    assert phx_window_type.u_value_glass == 1.0097620191408223

    # # -- Defaulty Values
    assert phx_window_type.frame_factor == 0.75
    assert phx_window_type.u_value_window == 1.0097620191408223

    # -- No Shades Added
    assert len(phx_proj.shade_types) == 0


def test_creat_phx_window_from_hb_window_with_ph_frame_and_ph_glazing():
    # -- Build the Inputs
    phx_proj = PhxProject()
    hb_const = WindowConstruction(
        identifier="test_window_construction",
        materials=[
            EnergyWindowMaterialSimpleGlazSys(
                identifier="test_glazing_mat",
                u_factor=1.0,
                shgc=0.5,
            )
        ],
    )
    hb_frame = PhWindowFrame("id_frame")
    hb_frame.top = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.top.u_factor = 0.123
    hb_frame.top.width = 0.205
    hb_frame.top.psi_glazing = 0.5
    hb_frame.top.psi_install = 0.6
    hb_frame.right = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.right.u_factor = 0.345
    hb_frame.right.width = 0.205
    hb_frame.right.psi_glazing = 0.5
    hb_frame.right.psi_install = 0.6
    hb_frame.bottom = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.bottom.u_factor = 0.567
    hb_frame.bottom.width = 0.205
    hb_frame.bottom.psi_glazing = 0.5
    hb_frame.bottom.psi_install = 0.6
    hb_frame.left = PhWindowFrameElement("PhWindowFrameElement")
    hb_frame.left.u_factor = 0.789
    hb_frame.left.width = 0.205
    hb_frame.left.psi_glazing = 0.5
    hb_frame.left.psi_install = 0.6

    # -- Build the glazing
    ph_glazing = PhWindowGlazing("id_glazing")
    ph_glazing.u_factor = 0.25
    ph_glazing.g_value = 0.56

    hb_const.properties.ph.ph_glazing = ph_glazing  # type: ignore
    hb_const.properties.ph.ph_frame = hb_frame  # type: ignore

    # -- build the PHX Window Type
    phx_window_type = build_phx_window_type_from_HB_WindowConstruction(phx_proj, hb_const, None)

    # -- Basic Values
    assert phx_window_type.display_name == "test_window_construction"

    # -- Glass Values
    assert phx_window_type.u_value_glass == 0.25
    assert phx_window_type.glass_g_value == 0.56

    # # -- Frame Values
    assert phx_window_type.frame_top.u_value == 0.123
    assert phx_window_type.frame_top.width == 0.205
    assert phx_window_type.frame_top.psi_glazing == 0.5
    assert phx_window_type.frame_top.psi_install == 0.6

    assert phx_window_type.frame_right.u_value == 0.345
    assert phx_window_type.frame_right.width == 0.205
    assert phx_window_type.frame_right.psi_glazing == 0.5
    assert phx_window_type.frame_right.psi_install == 0.6

    assert phx_window_type.frame_bottom.u_value == 0.567
    assert phx_window_type.frame_bottom.width == 0.205
    assert phx_window_type.frame_bottom.psi_glazing == 0.5
    assert phx_window_type.frame_bottom.psi_install == 0.6

    assert phx_window_type.frame_left.u_value == 0.789
    assert phx_window_type.frame_left.width == 0.205
    assert phx_window_type.frame_left.psi_glazing == 0.5
    assert phx_window_type.frame_left.psi_install == 0.6
