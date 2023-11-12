from PHX.model.project import PhxProject


# -- Check the number of window types
def test_window_types_loaded_LA_MORA(phx_project_from_wufi_xml_LA_MORA: PhxProject) -> None:
    win_types = phx_project_from_wufi_xml_LA_MORA.window_types
    assert len(win_types) == 5


def test_window_types_loaded_RIDGEWAY(phx_project_from_wufi_xml_RIDGEWAY: PhxProject) -> None:
    win_types = phx_project_from_wufi_xml_RIDGEWAY.window_types
    assert len(win_types) == 77


def test_window_types_loaded_ARVERNE_D_NO_WIN(phx_project_from_wufi_xml_ARVERNE_D_NO_WIN: PhxProject) -> None:
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
   
