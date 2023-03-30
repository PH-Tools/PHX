# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions used to convert a standard HBJSON Model over to WUFI Objects"""

from collections import defaultdict
from typing import Tuple, List

from honeybee import model
from honeybee import room

from honeybee_ph.properties.room import RoomPhProperties

from PHX.model.project import PhxProject
from PHX.from_HBJSON import cleanup, create_assemblies, create_variant, create_shades
from PHX.from_HBJSON import create_schedules


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


def convert_hb_model_to_PhxProject(
    _hb_model: model.Model, group_components: bool = False
) -> PhxProject:
    """Return a complete WUFI Project object with values based on the HB Model

    Arguments:
    ----------
        * _hb_model (model.Model): The Honeybee Model to base the WUFI Project on
        * group_components (bool): default=False. Set to true to have the converter
            group the components by assembly-type.

    Returns:
    --------
        * (PhxProject): The new WUFI Project object.
    """

    phx_project = PhxProject()
    create_assemblies.build_opaque_assemblies_from_HB_model(phx_project, _hb_model)
    create_assemblies.build_transparent_assembly_types_from_HB_Model(phx_project, _hb_model)
    create_schedules.add_all_HB_schedules_to_PHX_Project(phx_project, _hb_model)

    # -- TODO: Make all these operations if..else... with flags in the func arguments.

    # -- Merge the rooms together by their Building Segment, Add to the Project
    # -- then create a new variant from the merged room.
    # -- try and weld the vertices too in order to reduce load-time.
    for room_group in sort_hb_rooms_by_bldg_segment(_hb_model.rooms):
        merged_hb_room = cleanup.merge_rooms(room_group)

        new_variant = create_variant.from_hb_room(
            merged_hb_room,
            phx_project.assembly_types,
            phx_project.window_types,
            phx_project.utilization_patterns_ventilation,
            group_components,
        )

        new_variant = cleanup.weld_vertices(new_variant)

        create_shades.add_hb_model_shades_to_variant(new_variant, _hb_model)

        phx_project.add_new_variant(new_variant)

    return phx_project
