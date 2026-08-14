from types import SimpleNamespace

import pytest
from honeybee_ph import site

from PHX.from_HBJSON import create_variant
from PHX.from_HBJSON.create_variant import add_climate_from_hb_room
from PHX.model import project


def _hb_room_with_site(hb_site):
    return SimpleNamespace(
        display_name="Climate Test Room",
        properties=SimpleNamespace(
            ph=SimpleNamespace(
                ph_bldg_segment=SimpleNamespace(site=hb_site),
            )
        ),
    )


def _set_explicit_readiness(hb_site, monthly_issues, peak_issues):
    hb_site.climate.provenance = SimpleNamespace(source_type="test_explicit")
    hb_site.climate.monthly_demand_readiness_issues = lambda: list(monthly_issues)
    hb_site.climate.peak_load_readiness_issues = lambda: list(peak_issues)


def _blank_phpp_codes(hb_site):
    hb_site.phpp_library_codes.country_code = ""
    hb_site.phpp_library_codes.region_code = ""
    hb_site.phpp_library_codes.dataset_name = ""


def test_monthly_only_climate_raises_targeted_readiness_diagnostic_before_copy():
    hb_site = site.Site()
    _set_explicit_readiness(
        hb_site,
        monthly_issues=[],
        peak_issues=[
            "provenance.peak_load_data_available: approved or specialized peak-load climate data must be supplied separately."
        ],
    )
    hb_site.climate.peak_loads = None
    _blank_phpp_codes(hb_site)
    variant = project.PhxVariant()
    original_station_elevation = variant.site.climate.station_elevation

    with pytest.raises(ValueError) as error:
        add_climate_from_hb_room(variant, _hb_room_with_site(hb_site))

    message = str(error.value)
    assert "Climate Test Room" in message
    assert "climate is not ready for PHX conversion" in message
    assert "approved or specialized peak-load climate data must be supplied separately" in message
    assert variant.site.climate.station_elevation == original_station_elevation


def test_legacy_climate_with_populated_peak_sets_remains_supported():
    hb_site = site.Site()
    hb_site.climate.provenance = None
    hb_site.climate.peak_loads.heat_load_1.temp = -12.5
    variant = project.PhxVariant()

    add_climate_from_hb_room(variant, _hb_room_with_site(hb_site))

    assert variant.site.climate.peak_heating_1.temperature_air == -12.5


def test_explicit_complete_climate_remains_supported():
    hb_site = site.Site()
    _set_explicit_readiness(hb_site, monthly_issues=[], peak_issues=[])
    _blank_phpp_codes(hb_site)
    hb_site.climate.peak_loads.heat_load_1.temp = -15.0
    variant = project.PhxVariant()

    add_climate_from_hb_room(variant, _hb_room_with_site(hb_site))

    assert variant.site.climate.peak_heating_1.temperature_air == -15.0
    assert variant.site.phpp_codes.country_code == ""
    assert variant.site.phpp_codes.region_code == ""
    assert variant.site.phpp_codes.dataset_name == ""


def test_monthly_unavailable_climate_is_rejected_before_default_zeros_are_copied():
    hb_site = site.Site()
    _set_explicit_readiness(
        hb_site,
        monthly_issues=["provenance.monthly_data_available: monthly climate data is explicitly unavailable."],
        peak_issues=[],
    )
    variant = project.PhxVariant()
    original_air_temperatures = list(variant.site.climate.temperature_air)

    with pytest.raises(ValueError) as error:
        add_climate_from_hb_room(variant, _hb_room_with_site(hb_site))

    assert "monthly_data_available" in str(error.value)
    assert variant.site.climate.temperature_air == original_air_temperatures


def test_full_variant_pipeline_rejects_climate_before_other_builders(monkeypatch):
    hb_site = site.Site()
    _set_explicit_readiness(
        hb_site,
        monthly_issues=[],
        peak_issues=[
            "provenance.peak_load_data_available: approved or specialized peak-load climate data must be supplied separately."
        ],
    )
    hb_site.climate.peak_loads = None
    hb_room = _hb_room_with_site(hb_site)
    hb_room.properties.ph.id_num = 0

    def fail_if_called(*args, **kwargs):
        raise AssertionError("non-climate builder ran before readiness rejection")

    monkeypatch.setattr(create_variant, "add_ventilation_systems_from_hb_rooms", fail_if_called)

    with pytest.raises(ValueError, match="climate is not ready for PHX conversion"):
        create_variant.from_hb_room(
            hb_room,
            _assembly_dict={},
            _window_type_dict={},
            _vent_sched_collection=None,
            _occ_sched_collection=None,
            _lighting_sched_collection=None,
        )
