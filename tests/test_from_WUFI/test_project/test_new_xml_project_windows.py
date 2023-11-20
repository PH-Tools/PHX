from typing import ValuesView
from PHX.model.project import PhxProject
from PHX.model.constructions import PhxConstructionWindow


def test_project_data(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Project Data
    hbjson_windows = phx_project_from_hbjson.window_types
    xml_windows = phx_project_from_wufi_xml.window_types

    # -- Check the two
    assert len(hbjson_windows) == len(xml_windows)


def _find_matching_window(
    hbjson_type: PhxConstructionWindow, xml_types: ValuesView[PhxConstructionWindow]
) -> PhxConstructionWindow:
    for xml_type in xml_types:
        if hbjson_type.display_name == xml_type.display_name:
            return xml_type
    raise Exception(
        f"Window Type {hbjson_type.display_name} not found in XML set?"\
        f"XML window display-name include only: '{[_.display_name for _ in xml_types]}'"
    )


def test_window_type_attributes_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Project Data
    hbjson_windows = phx_project_from_hbjson.window_types
    xml_windows = phx_project_from_wufi_xml.window_types

    assert len(hbjson_windows) == len(xml_windows)

    for hbjson_type in hbjson_windows.values():
        xml_type = _find_matching_window(hbjson_type, xml_windows.values())

        assert hbjson_type.display_name == xml_type.display_name
        assert hbjson_type.u_value_window == xml_type.u_value_window
        assert hbjson_type.u_value_glass == xml_type.u_value_glass
        assert hbjson_type.u_value_frame == xml_type.u_value_frame
        assert hbjson_type.glass_mean_emissivity == xml_type.glass_mean_emissivity
        assert hbjson_type.glass_g_value == xml_type.glass_g_value
        # assert hbjson_type.id_num_shade == xml_type.id_num_shade


def test_window_FrameElement_attributes_match(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Project Data
    hbjson_windows = phx_project_from_hbjson.window_types
    xml_windows = phx_project_from_wufi_xml.window_types

    for hbjson_type in hbjson_windows.values():
        xml_type = _find_matching_window(hbjson_type, xml_windows.values())

        assert hbjson_type.frame_top.width == xml_type.frame_top.width
        assert hbjson_type.frame_top.u_value == xml_type.frame_top.u_value
        assert hbjson_type.frame_top.psi_glazing == xml_type.frame_top.psi_glazing
        assert hbjson_type.frame_top.psi_install == xml_type.frame_top.psi_install

        assert hbjson_type.frame_right.width == xml_type.frame_right.width
        assert hbjson_type.frame_right.u_value == xml_type.frame_right.u_value
        assert hbjson_type.frame_right.psi_glazing == xml_type.frame_right.psi_glazing
        assert hbjson_type.frame_right.psi_install == xml_type.frame_right.psi_install

        assert hbjson_type.frame_bottom.width == xml_type.frame_bottom.width
        assert hbjson_type.frame_bottom.u_value == xml_type.frame_bottom.u_value
        assert hbjson_type.frame_bottom.psi_glazing == xml_type.frame_bottom.psi_glazing
        assert hbjson_type.frame_bottom.psi_install == xml_type.frame_bottom.psi_install

        assert hbjson_type.frame_left.width == xml_type.frame_left.width
        assert hbjson_type.frame_left.u_value == xml_type.frame_left.u_value
        assert hbjson_type.frame_left.psi_glazing == xml_type.frame_left.psi_glazing
        assert hbjson_type.frame_left.psi_install == xml_type.frame_left.psi_install
