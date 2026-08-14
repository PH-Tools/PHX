from PHX.model.components import (
    PhxComponentAperture,
    PhxComponentBase,
    PhxComponentOpaque,
    PhxComponentThermalBridge,
)
from PHX.model.geometry import PhxPolygon, PhxVector, PhxVertix, PhxVertix2D
from PHX.model.identity import identity_scope


def _scoped_geometry_ids() -> tuple[tuple[int, ...], tuple[int, ...], int]:
    with identity_scope():
        opaque = PhxComponentOpaque()
        component_ids = (
            opaque.id_num,
            PhxComponentAperture(opaque).id_num,
            PhxComponentThermalBridge().id_num,
        )
        vertex_ids = (PhxVertix2D(0, 0).id_num, PhxVertix().id_num)
        polygon_id = PhxPolygon(
            _display_name="",
            _area=None,
            _center=None,
            normal_vector=PhxVector(0, 0, 1),
            plane=None,
        ).id_num
    return component_ids, vertex_ids, polygon_id


def test_scoped_envelope_and_geometry_ids_ignore_dirty_globals(reset_class_counters):
    PhxComponentBase._count = 100
    PhxVertix._count = 100
    PhxPolygon._count = 100

    first = _scoped_geometry_ids()
    second = _scoped_geometry_ids()

    assert second == first
    assert first == ((1, 2, 3), (1, 2), 1)
