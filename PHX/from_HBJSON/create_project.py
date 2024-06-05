# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions used to convert a standard HBJSON Model over to WUFI Objects"""

import logging
from collections import defaultdict
from typing import List, Tuple, Union

from honeybee import model, room
from honeybee.aperture import Aperture
from honeybee_ph.properties.room import RoomPhProperties
from honeybee_ph.team import ProjectTeam, ProjectTeamMember

from PHX.from_HBJSON import cleanup, create_assemblies, create_schedules, create_shades, create_variant
from PHX.model.project import PhxProject, PhxProjectData, ProjectData_Agent

logger = logging.getLogger()


class MissingPropertiesError(Exception):
    def __init__(self, _lbt_obj):
        self.message = (
            f'Error: LBT Object "{_lbt_obj}" does not have a .properties attribute?\n'
            "Can not add the .ph to missing .properties attribute."
        )
        super().__init__(self.message)


def sort_hb_rooms_by_bldg_segment(_hb_rooms: Tuple[room.Room]) -> List[List[room.Room]]:
    """Returns Groups of Honeybee-Rooms broken up by properties.ph.ph_bldg_segment.identifier.

    Arguments:
    ----------
        * _hb_rooms (List[room.Room]): The list of Honeybee Rooms to sort into bins.

    Returns:
    --------
        * (List[List[room.Room]]): A list of the groups of Honeybee Rooms.
    """

    rooms_by_segment = defaultdict(list)
    for room in _hb_rooms:
        hb_room_prop_ph: RoomPhProperties = room.properties.ph  # type: ignore
        rooms_by_segment[hb_room_prop_ph.ph_bldg_segment.identifier].append(room)
    return list(rooms_by_segment.values())


def hb_team_member_to_phx_agent(
    _hb_team_member: ProjectTeamMember,
) -> ProjectData_Agent:
    """Return a new PHX ProjectData_Agent with data based on a HB ProjectTeamMember."""
    return ProjectData_Agent(
        _hb_team_member.name,
        _hb_team_member.street,
        _hb_team_member.city,
        _hb_team_member.post_code,
        _hb_team_member.telephone,
        _hb_team_member.email,
    )


def get_project_data_from_hb_model(_hb_model: model.Model) -> PhxProjectData:
    """Return a new PhxProjectData with all team-member info based on an HB Model."""
    hb_proj_team = _hb_model.properties.ph.team  # type: ProjectTeam # type: ignore
    new_project_data = PhxProjectData()
    new_project_data.customer = hb_team_member_to_phx_agent(hb_proj_team.customer)
    new_project_data.owner = hb_team_member_to_phx_agent(hb_proj_team.owner)
    new_project_data.building = hb_team_member_to_phx_agent(hb_proj_team.building)
    new_project_data.designer = hb_team_member_to_phx_agent(hb_proj_team.designer)
    return new_project_data


def get_hb_apertures(_hb_model: model.Model) -> List[Aperture]:
    """Return a list of all the HB Apertures in the Model."""
    return [aperture for room in _hb_model.rooms for face in room.faces for aperture in face.apertures]


def convert_hb_model_to_PhxProject(
    _hb_model: model.Model,
    _group_components: bool = True,
    _merge_faces: Union[bool, float] = False,
    _merge_spaces_by_erv: bool = False,
) -> PhxProject:
    """Return a complete WUFI Project object with values based on the HB Model

    Arguments:
    ----------
        * _hb_model (model.Model): The Honeybee Model to base the WUFI Project on

        * _group_components (bool): default=True. Set to true to have the converter
            group the components by assembly-type.

        * _merge_faces (bool | float): default=False. Set to true to have the converter try and
            group together co-planar faces in the output room using the HB model tolerance.
            If a number is given, it will be used as the tolerance for merging faces.

        * _merge_spaces_by_erv (bool): default=False. Set to true to have the converter
            merge all the spaces by ERV zones. This is sometimes required by Phius for
            large buildings with multiple ERV zones.

    Returns:
    --------
        * (PhxProject): The new WUFI Project object.
    """

    phx_project = PhxProject()
    phx_project.project_data = get_project_data_from_hb_model(_hb_model)
    create_assemblies.build_opaque_assemblies_from_HB_model(phx_project, _hb_model)
    create_assemblies.build_transparent_assembly_types_from_HB_Model(phx_project, get_hb_apertures(_hb_model))
    create_schedules.add_all_HB_schedules_to_PHX_Project(phx_project, _hb_model)

    # -- TODO: Make all these operations if..else... with flags in the func arguments.

    # -- Merge the rooms together by their Building Segment, Add to the Project
    # -- then create a new variant from the merged room.
    # -- try and weld the vertices too in order to reduce load-time.
    for room_group in sort_hb_rooms_by_bldg_segment(_hb_model.rooms):  # type: ignore
        # -- Configure the merge_faces and merge_face_tolerance
        if isinstance(_merge_faces, bool):
            merge_faces: bool = _merge_faces
            merge_face_tolerance: float = _hb_model.tolerance
        else:
            merge_faces: bool = True
            merge_face_tolerance: float = _merge_faces

        merged_hb_room = cleanup.merge_rooms(room_group, merge_face_tolerance, _hb_model.angle_tolerance, merge_faces)

        new_variant = create_variant.from_hb_room(
            _hb_room=merged_hb_room,
            _assembly_dict=phx_project.assembly_types,
            _window_type_dict=phx_project.window_types,
            _vent_sched_collection=phx_project.utilization_patterns_ventilation,
            _occ_sched_collection=phx_project.utilization_patterns_occupancy,
            _lighting_sched_collection=phx_project.utilization_patterns_lighting,
            _group_components=_group_components,
            _merge_spaces_by_erv=_merge_spaces_by_erv,
            _tolerance=_hb_model.tolerance,
        )

        new_variant = cleanup.weld_vertices(new_variant)

        create_shades.add_hb_model_shades_to_variant(
            new_variant,
            _hb_model,
            _merge_faces=merge_faces,
            _tolerance=_hb_model.tolerance,
            _angle_tolerance_degrees=_hb_model.angle_tolerance,
        )

        phx_project.add_new_variant(new_variant)

    return phx_project
