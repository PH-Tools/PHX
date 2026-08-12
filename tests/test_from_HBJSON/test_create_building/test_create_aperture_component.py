from honeybee.room import Room
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
from honeybee_energy_ph.construction.window import PhApertureInstallType, PhWindowFrame, PhWindowGlazing

from PHX.from_HBJSON.create_building import create_component_from_hb_aperture
from PHX.model import components, constructions


def _build_hb_room_with_aperture(_with_ph_frame: bool = True):
    """Return (hb_room, hb_aperture, window_type_dict) for a simple room with one window."""
    glazing_material = EnergyWindowMaterialSimpleGlazSys("test_mat", u_factor=1.0, shgc=0.4)
    construction = WindowConstruction("test_construction", [glazing_material])

    if _with_ph_frame:
        ph_frame = PhWindowFrame("test_frame")
        for frame_element in ph_frame.elements:
            frame_element.psi_install = 0.04
        construction.properties.ph.ph_frame = ph_frame
        construction.properties.ph.ph_glazing = PhWindowGlazing("test_glazing")

    hb_room = Room.from_box("test_room", 5, 5, 3)
    wall_face = hb_room[1]
    wall_face.apertures_by_ratio(0.4)
    hb_aperture = wall_face.apertures[0]
    hb_aperture.properties.energy.construction = construction

    phx_window_type = constructions.PhxConstructionWindow()
    phx_window_type.identifier = construction.identifier
    if _with_ph_frame:
        phx_window_type.set_all_frames_psi_install(0.04)
    window_type_dict = {construction.identifier: phx_window_type}

    return hb_room, hb_aperture, window_type_dict


def _install_type(_name: str, _psi: float) -> PhApertureInstallType:
    install_type = PhApertureInstallType(_name)
    install_type.psi_install = _psi
    return install_type


def test_aperture_component_element_psi_matches_type_when_no_assignments(reset_class_counters) -> None:
    hb_room, hb_aperture, window_type_dict = _build_hb_room_with_aperture()
    host = components.PhxComponentOpaque()

    phx_ap = create_component_from_hb_aperture(host, hb_aperture, hb_room, window_type_dict)

    (element,) = phx_ap.elements
    assert element.install_psi is not None
    assert element.resolved_psi_install.values == (0.04, 0.04, 0.04, 0.04)
    # -- equal to the window-type's own values: no-op for grouping / variants
    assert element.resolved_psi_install.unique_key == "psi(0.0400,0.0400,0.0400,0.0400)"


def test_aperture_component_element_psi_carries_install_type_overrides(reset_class_counters) -> None:
    hb_room, hb_aperture, window_type_dict = _build_hb_room_with_aperture()
    hb_aperture.properties.ph.install_types.left = _install_type("Party Wall", 0.0)
    hb_aperture.properties.ph.install_types.top = _install_type("Buried Head", 0.085)
    host = components.PhxComponentOpaque()

    phx_ap = create_component_from_hb_aperture(host, hb_aperture, hb_room, window_type_dict)

    (element,) = phx_ap.elements
    assert element.install_psi is not None
    assert element.install_psi.top == 0.085
    assert element.install_psi.right == 0.04
    assert element.install_psi.bottom == 0.04
    assert element.install_psi.left == 0.0
    # -- the shared window type is never mutated
    assert phx_ap.window_type.frame_left.psi_install == 0.04


def test_aperture_component_without_ph_frame_falls_back_to_type_values(reset_class_counters) -> None:
    hb_room, hb_aperture, window_type_dict = _build_hb_room_with_aperture(_with_ph_frame=False)
    host = components.PhxComponentOpaque()

    phx_ap = create_component_from_hb_aperture(host, hb_aperture, hb_room, window_type_dict)

    (element,) = phx_ap.elements
    assert element.install_psi is None
    # -- resolved values fall back to the (default 0.0) window-type values
    assert element.resolved_psi_install.values == (0.0, 0.0, 0.0, 0.0)


def test_two_apertures_one_construction_different_conditions(reset_class_counters) -> None:
    """The headline invariant: per-instance conditions, one window type, distinct unique_keys."""
    hb_room, hb_aperture_1, window_type_dict = _build_hb_room_with_aperture()

    wall_face_2 = hb_room[2]
    wall_face_2.apertures_by_ratio(0.4)
    hb_aperture_2 = wall_face_2.apertures[0]
    hb_aperture_2.properties.energy.construction = hb_aperture_1.properties.energy.construction
    hb_aperture_2.properties.ph.install_types.left = _install_type("Party Wall", 0.0)

    host = components.PhxComponentOpaque()
    phx_ap_1 = create_component_from_hb_aperture(host, hb_aperture_1, hb_room, window_type_dict)
    phx_ap_2 = create_component_from_hb_aperture(host, hb_aperture_2, hb_room, window_type_dict)

    # -- one shared window type object; no extra types anywhere
    assert phx_ap_1.window_type is phx_ap_2.window_type
    assert len(window_type_dict) == 1

    # -- but the components must not merge (different resolved psi)
    assert phx_ap_1.unique_key != phx_ap_2.unique_key
    assert phx_ap_1.elements[0].resolved_psi_install.values == (0.04, 0.04, 0.04, 0.04)
    assert phx_ap_2.elements[0].resolved_psi_install.values == (0.04, 0.04, 0.04, 0.0)
