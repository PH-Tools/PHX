import pytest

from PHX.model.identity import (
    DuplicateIdentityError,
    IdentityAllocator,
    allocate_identity,
    current_identity_allocator,
    identity_scope,
)


class LegacyCounter:
    _count = 40


def test_namespaces_allocate_independently():
    allocator = IdentityAllocator()

    assert allocator.next_id("materials") == 1
    assert allocator.next_id("materials") == 2
    assert allocator.next_id("variants") == 1


def test_explicit_claims_are_preserved_and_skipped():
    allocator = IdentityAllocator()

    assert allocator.claim_id("materials", 4, source="material[0]") == 4
    assert [allocator.next_id("materials") for _ in range(4)] == [1, 2, 3, 5]
    assert allocator.is_claimed("materials", 4)


def test_duplicate_claim_reports_namespace_value_and_sources():
    allocator = IdentityAllocator()
    allocator.claim_id("materials", 7, source="material[0]")

    with pytest.raises(DuplicateIdentityError, match=r"materials.*7.*material\[0\].*material\[1\]"):
        allocator.claim_id("materials", 7, source="material[1]")


def test_same_number_is_legal_in_independent_namespaces():
    allocator = IdentityAllocator()

    assert allocator.claim_id("materials", 7) == 7
    assert allocator.claim_id("variants", 7) == 7


def test_scope_restores_context_after_success_and_exception():
    assert current_identity_allocator() is None
    with identity_scope() as allocator:
        assert current_identity_allocator() is allocator
        assert allocate_identity("materials", LegacyCounter) == 1
    assert current_identity_allocator() is None

    with pytest.raises(RuntimeError, match="boom"), identity_scope():
        raise RuntimeError("boom")
    assert current_identity_allocator() is None


def test_nested_scope_is_fresh_unless_allocator_is_reused():
    with identity_scope() as parent:
        assert allocate_identity("materials", LegacyCounter) == 1
        with identity_scope() as child:
            assert child is not parent
            assert allocate_identity("materials", LegacyCounter) == 1
        with identity_scope(parent):
            assert allocate_identity("materials", LegacyCounter) == 2


def test_fallback_preserves_direct_constructor_counter_behavior():
    original = LegacyCounter._count
    try:
        assert allocate_identity("materials", LegacyCounter) == 41
        assert LegacyCounter._count == 41
    finally:
        LegacyCounter._count = original


def test_allocator_snapshot_is_sorted_and_diagnostic_only():
    allocator = IdentityAllocator()
    allocator.claim_id("z", 4, source="four")
    allocator.next_id("a")

    assert allocator.snapshot() == {"a": (1,), "z": (4,)}
