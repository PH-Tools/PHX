from PHX.from_WUFI_XML.phx_schemas import _PhxConstructionWindow
from PHX.from_WUFI_XML.wufi_file_schema import WufiWindowType
from PHX.model.project import PhxProject


def test_window_type_reads_distinct_frame_sides() -> None:
    wufi_window_type = WufiWindowType(
        IdentNr=1,
        Name="Asymmetric frame",
        Uw_Detailed=True,
        GlazingFrameDetailed=True,
        FrameFactor=0.3,
        U_Value=0.8,
        U_Value_Glazing=0.7,
        MeanEmissivity=0.04,
        g_Value=0.5,
        SHGC_Hemispherical=0.45,
        U_Value_Frame=1.0,
        Frame_Width_Left=0.11,
        Frame_U_Left=1.1,
        Glazing_Psi_Left=0.011,
        Frame_Psi_Left=0.021,
        Frame_Width_Right=0.12,
        Frame_U_Right=1.2,
        Glazing_Psi_Right=0.012,
        Frame_Psi_Right=0.022,
        Frame_Width_Top=0.13,
        Frame_U_Top=1.3,
        Glazing_Psi_Top=0.013,
        Frame_Psi_Top=0.023,
        Frame_Width_Bottom=0.14,
        Frame_U_Bottom=1.4,
        Glazing_Psi_Bottom=0.014,
        Frame_Psi_Bottom=0.024,
    )

    phx_window_type = _PhxConstructionWindow(wufi_window_type)

    assert (
        phx_window_type.frame_left.width,
        phx_window_type.frame_left.u_value,
        phx_window_type.frame_left.psi_glazing,
        phx_window_type.frame_left.psi_install,
    ) == (0.11, 1.1, 0.011, 0.021)
    assert (
        phx_window_type.frame_right.width,
        phx_window_type.frame_right.u_value,
        phx_window_type.frame_right.psi_glazing,
        phx_window_type.frame_right.psi_install,
    ) == (0.12, 1.2, 0.012, 0.022)
    assert (
        phx_window_type.frame_top.width,
        phx_window_type.frame_top.u_value,
        phx_window_type.frame_top.psi_glazing,
        phx_window_type.frame_top.psi_install,
    ) == (0.13, 1.3, 0.013, 0.023)
    assert (
        phx_window_type.frame_bottom.width,
        phx_window_type.frame_bottom.u_value,
        phx_window_type.frame_bottom.psi_glazing,
        phx_window_type.frame_bottom.psi_install,
    ) == (0.14, 1.4, 0.014, 0.024)


# -- Check the number of window types
def test_window_types_loaded_LA_MORA(
    phx_project_from_wufi_xml_LA_MORA: PhxProject,
) -> None:
    win_types = phx_project_from_wufi_xml_LA_MORA.window_types
    assert len(win_types) == 5


def test_window_types_loaded_RIDGEWAY(
    phx_project_from_wufi_xml_RIDGEWAY: PhxProject,
) -> None:
    win_types = phx_project_from_wufi_xml_RIDGEWAY.window_types
    assert len(win_types) == 77


def test_window_types_loaded_ARVERNE_D_NO_WIN(
    phx_project_from_wufi_xml_ARVERNE_D_NO_WIN: PhxProject,
) -> None:
    win_types = phx_project_from_wufi_xml_ARVERNE_D_NO_WIN.window_types
    assert len(win_types) == 0


# --- Check the actual window types
def test_got_all_win_types_LA_MORA(phx_project_from_wufi_xml_LA_MORA: PhxProject) -> None:
    assert len(phx_project_from_wufi_xml_LA_MORA.window_types) == 5

    type_1 = phx_project_from_wufi_xml_LA_MORA.get_window_types_by_name("LaMora_YKK_YES 45 XT")
    assert len(type_1) == 1

    type_2 = phx_project_from_wufi_xml_LA_MORA.get_window_types_by_name("LaMora_YKK_YES 45 XT_spandrel")
    assert len(type_2) == 1

    type_3 = phx_project_from_wufi_xml_LA_MORA.get_window_types_by_name("LaMora_YKK_YES 35 XT_medium entrance")
    assert len(type_3) == 1

    type_4 = phx_project_from_wufi_xml_LA_MORA.get_window_types_by_name("Wythe_76 MD_Triple pane_SHGC .34_Fixed")
    assert len(type_4) == 1

    type_5 = phx_project_from_wufi_xml_LA_MORA.get_window_types_by_name("Wythe_76 MD_Triple pane_SHGC .34_Awning")
    assert len(type_5) == 1
