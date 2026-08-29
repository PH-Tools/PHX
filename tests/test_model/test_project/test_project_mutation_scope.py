# -*- Python Version: 3.10 -*-

"""Tests for PhxProject.identity_scope() on a project built without an allocator.

Projects built by the public converters are covered by
'tests/test_from_HBJSON/test_project_identity_isolation.py' and
'tests/test_from_WUFI/test_project/test_explicit_identity_claims.py'. What is left
is the other kind: a project hand-assembled from bare constructors, whose objects
are numbered by the legacy class counters. The scope must leave that regime alone
rather than starting a second, empty one alongside it.
"""

from PHX.model.building import PhxZone
from PHX.model.hvac.collection import PhxMechanicalSystemCollection
from PHX.model.project import PhxProject, PhxVariant


def test_scope_does_not_attach_an_allocator_to_a_standalone_project() -> None:
    """Entering the scope must not decide, as a side effect, that a hand-assembled
    project is now allocator-owned. Any later `_identity_allocator is not None`
    check would then be reading a flag the scope itself set."""
    phx_project = PhxProject()
    assert phx_project._identity_allocator is None

    with phx_project.identity_scope(owner=1):
        pass

    assert phx_project._identity_allocator is None


def test_scope_preserves_legacy_numbering_on_a_standalone_project(reset_class_counters) -> None:
    """A hand-assembled project's identity regime *is* the legacy counters, and they
    are already unique within it. The scope must not restart numbering at 1."""
    phx_project = PhxProject()
    phx_variant = PhxVariant()
    phx_variant.building.add_zone(PhxZone())
    phx_project.add_new_variant(phx_variant)
    existing_id = phx_variant.default_mech_collection.id_num

    with phx_project.identity_scope(owner=phx_variant.id_num):
        new_collection = PhxMechanicalSystemCollection()

    assert new_collection.id_num == existing_id + 1
