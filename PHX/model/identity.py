# -*- Python Version: 3.10 -*-

"""Project-scoped numeric identity allocation for PHX conversions."""

from __future__ import annotations

from collections.abc import Hashable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol, TypeAlias

IdentityNamespace: TypeAlias = Hashable


class IdentityNamespaces:
    """Stable namespace keys grouped by target/reference ownership."""

    VARIANTS = "project.variants"
    MATERIALS = "project.materials"
    ASSEMBLIES = "project.assemblies"
    WINDOWS = "project.windows"
    SHADES = "project.shades"
    VENTILATION_PATTERNS = "project.patterns.ventilation"
    OCCUPANCY_PATTERNS = "project.patterns.occupancy"
    LIGHTING_PATTERNS = "project.patterns.lighting"
    PH_BUILDING_DATA = "variant.ph_building_data"
    COMPONENTS = "variant.components"
    VERTICES = "variant.geometry.vertices"
    POLYGONS = "variant.geometry.polygons"


class LegacyCounterOwner(Protocol):
    """Structural type for classes that retain the legacy counter fallback."""

    __name__: str
    _count: int


class IdentityAllocationError(ValueError):
    """Base error for invalid project identity allocation."""


class DuplicateIdentityError(IdentityAllocationError):
    """Raised when one identity is claimed twice in the same namespace."""

    def __init__(self, namespace: IdentityNamespace, value: int, existing_source: str, source: str):
        self.namespace = namespace
        self.value = value
        self.existing_source = existing_source
        self.source = source
        super().__init__(
            f"Duplicate identity in namespace {namespace!r}: {value}; "
            f"already claimed by {existing_source}; conflicting source {source}."
        )


class IdentityAllocator:
    """Allocate deterministic positive integers within independent namespaces."""

    def __init__(self) -> None:
        # Automatic claims below each next-candidate are represented by the
        # high-water mark; only sparse explicit claims retain source strings.
        self._claims: dict[IdentityNamespace, dict[int, str]] = {}
        self._next_candidates: dict[IdentityNamespace, int] = {}

    def next_id(self, namespace: IdentityNamespace, source: str = "automatic allocation") -> int:
        """Claim and return the next available positive integer in a namespace."""
        claims = self._claims.setdefault(namespace, {})
        candidate = self._next_candidates.get(namespace, 1)
        while candidate in claims:
            candidate += 1
        self._next_candidates[namespace] = candidate + 1
        return candidate

    def claim_id(self, namespace: IdentityNamespace, value: int, source: str = "explicit claim") -> int:
        """Claim an explicit positive integer, raising on a namespace conflict."""
        if value < 1:
            raise IdentityAllocationError(
                f"Identity in namespace {namespace!r} must be positive; received {value} from {source}."
            )
        claims = self._claims.setdefault(namespace, {})
        if value < self._next_candidates.get(namespace, 1):
            raise DuplicateIdentityError(namespace, value, "automatic allocation", source)
        if existing_source := claims.get(value):
            raise DuplicateIdentityError(namespace, value, existing_source, source)
        claims[value] = source
        self._next_candidates.setdefault(namespace, 1)
        return value

    def is_claimed(self, namespace: IdentityNamespace, value: int) -> bool:
        """Return whether a value is already claimed in a namespace."""
        return value < self._next_candidates.get(namespace, 1) or value in self._claims.get(namespace, {})

    def snapshot(self) -> dict[IdentityNamespace, tuple[int, ...]]:
        """Return a deterministic diagnostic view of allocated identities."""
        namespaces = self._claims.keys() | self._next_candidates.keys()
        return {
            namespace: tuple(
                sorted(set(range(1, self._next_candidates.get(namespace, 1))) | self._claims.get(namespace, {}).keys())
            )
            for namespace in sorted(namespaces, key=str)
        }


_CURRENT_ALLOCATOR: ContextVar[IdentityAllocator | None] = ContextVar("phx_identity_allocator", default=None)


def current_identity_allocator() -> IdentityAllocator | None:
    """Return the allocator active in the current execution context, if any."""
    return _CURRENT_ALLOCATOR.get()


@contextmanager
def identity_scope(allocator: IdentityAllocator | None = None) -> Iterator[IdentityAllocator]:
    """Activate a fresh or supplied allocator and always restore the prior context."""
    active_allocator = allocator or IdentityAllocator()
    token = _CURRENT_ALLOCATOR.set(active_allocator)
    try:
        yield active_allocator
    finally:
        _CURRENT_ALLOCATOR.reset(token)


def allocate_identity(namespace: IdentityNamespace, legacy_counter_owner: type[LegacyCounterOwner]) -> int:
    """Allocate from the active project or preserve legacy class-counter behavior."""
    allocator = current_identity_allocator()
    if allocator is not None:
        return allocator.next_id(namespace, source=legacy_counter_owner.__name__)
    legacy_counter_owner._count += 1
    return legacy_counter_owner._count


def claim_identity(namespace: IdentityNamespace, value: int, source: str) -> int:
    """Claim an explicit identity in the active project scope."""
    allocator = current_identity_allocator()
    if allocator is None:
        return value
    return allocator.claim_id(namespace, value, source)
