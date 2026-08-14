# -*- Python Version: 3.10 -*-

"""Project-scoped numeric identity allocation for PHX conversions."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol, TypeAlias, TypeVar

IdentityNamespace: TypeAlias = Hashable


class IdentityNamespaceKey(str):
    """A named namespace carrying explicit project- or variant-ownership metadata."""

    variant_owned: bool

    def __new__(cls, value: str, *, variant_owned: bool = False):
        instance = super().__new__(cls, value)
        instance.variant_owned = variant_owned
        return instance


class IdentityNamespaces:
    """Stable namespace keys grouped by target/reference ownership."""

    VARIANTS = IdentityNamespaceKey("project.variants")
    MATERIALS = IdentityNamespaceKey("project.materials")
    ASSEMBLIES = IdentityNamespaceKey("project.assemblies")
    WINDOWS = IdentityNamespaceKey("project.windows")
    SHADES = IdentityNamespaceKey("project.shades")
    VENTILATION_PATTERNS = IdentityNamespaceKey("project.patterns.ventilation")
    OCCUPANCY_PATTERNS = IdentityNamespaceKey("project.patterns.occupancy")
    LIGHTING_PATTERNS = IdentityNamespaceKey("project.patterns.lighting")
    PH_BUILDING_DATA = IdentityNamespaceKey("variant.ph_building_data", variant_owned=True)
    COMPONENTS = IdentityNamespaceKey("variant.components", variant_owned=True)
    VERTICES = IdentityNamespaceKey("variant.geometry.vertices", variant_owned=True)
    POLYGONS = IdentityNamespaceKey("variant.geometry.polygons", variant_owned=True)
    ZONES = IdentityNamespaceKey("variant.zones", variant_owned=True)
    SPACES = IdentityNamespaceKey("variant.spaces", variant_owned=True)
    MECHANICAL_SYSTEMS = IdentityNamespaceKey("variant.mechanical.systems", variant_owned=True)
    RENEWABLE_COLLECTIONS = IdentityNamespaceKey("variant.mechanical.renewable_collections", variant_owned=True)
    SUPPORTIVE_COLLECTIONS = IdentityNamespaceKey("variant.mechanical.supportive_collections", variant_owned=True)
    EXHAUST_COLLECTIONS = IdentityNamespaceKey("variant.mechanical.exhaust_collections", variant_owned=True)
    SUPPORTIVE_DEVICES = IdentityNamespaceKey("variant.mechanical.supportive_devices", variant_owned=True)
    EXHAUST_DEVICES = IdentityNamespaceKey("variant.mechanical.exhaust_devices", variant_owned=True)
    DUCTS = IdentityNamespaceKey("variant.mechanical.ducts", variant_owned=True)
    PIPE_ELEMENTS = IdentityNamespaceKey("variant.mechanical.pipe_elements", variant_owned=True)
    PIPE_BRANCHES = IdentityNamespaceKey("variant.mechanical.pipe_branches", variant_owned=True)
    PIPE_TRUNKS = IdentityNamespaceKey("variant.mechanical.pipe_trunks", variant_owned=True)

    @staticmethod
    def mechanical_devices(owner: type[LegacyCounterOwner]) -> IdentityNamespaceKey:
        """Return the compatibility namespace for one mechanical leaf type."""
        return IdentityNamespaceKey(f"variant.mechanical.devices.{owner.__name__}", variant_owned=True)

    @staticmethod
    def electrical_devices(owner: type[LegacyCounterOwner]) -> IdentityNamespaceKey:
        """Return the compatibility namespace for one electrical leaf type."""
        return IdentityNamespaceKey(f"variant.electrical.devices.{owner.__name__}", variant_owned=True)


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

    def next_id(self, namespace: IdentityNamespace) -> int:
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
_CURRENT_OWNER: ContextVar[Hashable | None] = ContextVar("phx_identity_owner", default=None)


def current_identity_allocator() -> IdentityAllocator | None:
    """Return the allocator active in the current execution context, if any."""
    return _CURRENT_ALLOCATOR.get()


def _owned_namespace(namespace: IdentityNamespace) -> IdentityNamespace:
    """Qualify variant-local namespaces with the active deterministic owner."""
    owner = _CURRENT_OWNER.get()
    if owner is not None and isinstance(namespace, IdentityNamespaceKey) and namespace.variant_owned:
        return owner, namespace
    return namespace


@contextmanager
def identity_scope(allocator: IdentityAllocator | None = None) -> Iterator[IdentityAllocator]:
    """Activate a fresh or supplied allocator and always restore the prior context."""
    active_allocator = allocator or IdentityAllocator()
    token = _CURRENT_ALLOCATOR.set(active_allocator)
    try:
        yield active_allocator
    finally:
        _CURRENT_ALLOCATOR.reset(token)


@contextmanager
def identity_owner_scope(owner: Hashable) -> Iterator[None]:
    """Qualify variant-owned namespaces for one deterministic project subgraph."""
    token = _CURRENT_OWNER.set(owner)
    try:
        yield
    finally:
        _CURRENT_OWNER.reset(token)


def allocate_identity(namespace: IdentityNamespace, legacy_counter_owner: type[LegacyCounterOwner]) -> int:
    """Allocate from the active project or preserve legacy class-counter behavior."""
    allocator = current_identity_allocator()
    if allocator is not None:
        return allocator.next_id(_owned_namespace(namespace))
    legacy_counter_owner._count += 1
    return legacy_counter_owner._count


def claim_identity(namespace: IdentityNamespace, value: int, source: str) -> int:
    """Claim an explicit identity in the active project scope."""
    allocator = current_identity_allocator()
    if allocator is None:
        return value
    return allocator.claim_id(_owned_namespace(namespace), value, source)


class IdentityOwningProject(Protocol):
    """Structural contract for projects that retain their construction allocator."""

    def _attach_identity_allocator(self, allocator: IdentityAllocator) -> None: ...


ProjectT = TypeVar("ProjectT", bound=IdentityOwningProject)


def build_project_with_identities(builder: Callable[[], ProjectT]) -> ProjectT:
    """Build a project in a fresh scope and retain its allocator on success."""
    with identity_scope() as allocator:
        project = builder()
        project._attach_identity_allocator(allocator)
        return project
