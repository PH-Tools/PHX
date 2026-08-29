import pytest

from PHX.model.building import PhxZone
from PHX.model.hvac.heat_pumps import PhxHeatPumpAnnual, PhxHeatPumpDevice
from PHX.model.identity import build_project_with_identities, identity_owner_scope
from PHX.model.identity_validation import IdentityValidationTarget, validate_project_identities
from PHX.model.project import PhxProject, PhxVariant
from PHX.to_WUFI_XML._bug_fixes import split_cooling_into_multiple_systems

# -- Variants that must all come through the split with their total capacity intact.
# -- One device is the case the transform was originally written for; two or more is
# -- where dividing by the collection count used to inflate the installed capacity.
_SPLIT_CASES = [
    (300.0,),
    (1628.5,),
    (150.0, 150.0),
    (250.0, 250.0, 250.0),
    (100.0, 100.0, 100.0, 100.0),
]


def _add_cooling_device(_phx_variant: PhxVariant, _capacity: float) -> None:
    """Add one cooling heat-pump of the given recirculation capacity to the variant."""
    new_heat_pump = PhxHeatPumpAnnual()
    new_heat_pump.usage_profile.cooling = True
    new_heat_pump.params_cooling.recirculation.used = True
    new_heat_pump.params_cooling.recirculation.capacity = _capacity
    _phx_variant.default_mech_collection.add_new_mech_device(new_heat_pump.identifier, new_heat_pump)


def _standalone_project(*_capacities: float) -> PhxProject:
    """A hand-assembled project, numbered by the legacy class counters."""
    phx_project = PhxProject()
    phx_variant = PhxVariant()
    phx_variant.building.add_zone(PhxZone())
    phx_project.add_new_variant(phx_variant)
    for capacity in _capacities:
        _add_cooling_device(phx_variant, capacity)
    return phx_project


def _allocator_built_project(*_capacities: float) -> PhxProject:
    """A project built the way the public converters build it, with its own allocator."""

    def _build() -> PhxProject:
        phx_project = PhxProject()
        with identity_owner_scope(1):
            phx_variant = PhxVariant()
            phx_variant.building.add_zone(PhxZone())
            for capacity in _capacities:
                _add_cooling_device(phx_variant, capacity)
        phx_project.add_new_variant(phx_variant)
        return phx_project

    return build_project_with_identities(_build)


def _cooling_devices(_phx_variant: PhxVariant) -> list[PhxHeatPumpDevice]:
    """Every cooling device in the variant, across all of its collections."""
    return [device for collection in _phx_variant.mech_collections for device in collection.cooling_devices]


def _total_cooling_capacity(_phx_variant: PhxVariant) -> float:
    """The total installed recirculation cooling capacity across every collection."""
    return sum(d.params_cooling.recirculation.capacity for d in _cooling_devices(_phx_variant))


def test_cooling_capacity_fix_below_200KW() -> None:
    phx_project = split_cooling_into_multiple_systems(_standalone_project(100.0))

    # -- Check if the cooling capacity is not split
    assert len(phx_project.variants[0].mech_collections[0].heat_pump_devices) == 1


def test_cooling_capacity_fix_300KW_makes_2_systems() -> None:
    phx_project = split_cooling_into_multiple_systems(_standalone_project(300.0))

    # -- Check if the cooling capacity is split
    assert len(phx_project.variants[0].mech_collections) == 2
    for collection in phx_project.variants[0].mech_collections:
        assert len(collection.heat_pump_devices) == 1
        assert collection.heat_pump_devices[0].params_cooling.recirculation.capacity == 150.0


def test_cooling_capacity_fix_540KW_makes_3_systems() -> None:
    phx_project = split_cooling_into_multiple_systems(_standalone_project(540.0))

    # -- Check if the cooling capacity is split
    assert len(phx_project.variants[0].mech_collections) == 3
    for collection in phx_project.variants[0].mech_collections:
        assert len(collection.heat_pump_devices) == 1
        assert collection.heat_pump_devices[0].params_cooling.recirculation.capacity == 180.0


def test_cooling_capacity_fix_300KW_with_2_mech_systems() -> None:
    phx_project = split_cooling_into_multiple_systems(_standalone_project(150.0, 150.0))

    # -- 2 existing devices + 1 new system, and the 300 KW is spread over all three
    assert len(phx_project.variants[0].mech_collections) == 2
    assert len(phx_project.variants[0].mech_collections[0].heat_pump_devices) == 2
    assert len(phx_project.variants[0].mech_collections[1].heat_pump_devices) == 1
    for device in _cooling_devices(phx_project.variants[0]):
        assert device.params_cooling.recirculation.capacity == 100.0


# -----------------------------------------------------------------------------
# -- The split builds new model objects after the conversion scope has closed.
# -- Both project kinds must come out of it with a valid identity graph.
# --
# -- These use 'reset_class_counters' deliberately: they are *about* the
# -- boundary between the project allocator and the legacy-counter fallback, and
# -- a stale counter left over from another test would hide a real collision the
# -- same way a long-lived process hides it in the field.


def test_split_keeps_identities_unique_for_an_allocator_built_project(reset_class_counters) -> None:
    phx_project = _allocator_built_project(1628.5)

    phx_project = split_cooling_into_multiple_systems(phx_project)

    validate_project_identities(phx_project, IdentityValidationTarget.WUFI)


def test_split_allocates_from_the_project_not_the_legacy_counter(reset_class_counters) -> None:
    phx_project = _allocator_built_project(1628.5)
    counter_before = PhxHeatPumpAnnual._count

    split_cooling_into_multiple_systems(phx_project)

    assert PhxHeatPumpAnnual._count == counter_before


def test_split_keeps_identities_unique_for_a_standalone_project(reset_class_counters) -> None:
    phx_project = _standalone_project(1628.5)

    phx_project = split_cooling_into_multiple_systems(phx_project)

    validate_project_identities(phx_project, IdentityValidationTarget.WUFI)


# -----------------------------------------------------------------------------
# -- The split re-sizes the existing devices as well as adding new ones, so the
# -- total installed capacity has to come out the same as it went in.


@pytest.mark.parametrize("capacities", _SPLIT_CASES)
def test_split_conserves_total_cooling_capacity(capacities: tuple[float, ...]) -> None:
    phx_project = _standalone_project(*capacities)
    phx_variant = phx_project.variants[0]
    capacity_before = _total_cooling_capacity(phx_variant)

    split_cooling_into_multiple_systems(phx_project)

    assert _total_cooling_capacity(phx_variant) == pytest.approx(capacity_before)


@pytest.mark.parametrize("capacities", _SPLIT_CASES)
def test_split_leaves_every_device_below_the_wufi_limit(capacities: tuple[float, ...]) -> None:
    """The whole point of the split: WUFI-Passive v3.x rejects a system over 200 KW."""
    phx_project = _standalone_project(*capacities)

    split_cooling_into_multiple_systems(phx_project)

    for device in _cooling_devices(phx_project.variants[0]):
        assert device.params_cooling.recirculation.capacity <= 200.0


@pytest.mark.parametrize("capacities", _SPLIT_CASES)
def test_split_covers_exactly_all_of_the_cooling_load(capacities: tuple[float, ...]) -> None:
    phx_project = _standalone_project(*capacities)

    split_cooling_into_multiple_systems(phx_project)

    coverage = sum(d.usage_profile.cooling_percent for d in _cooling_devices(phx_project.variants[0]))
    assert coverage == pytest.approx(1.0)
