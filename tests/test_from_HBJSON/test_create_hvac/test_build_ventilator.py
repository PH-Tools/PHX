from honeybee_phhvac.ventilation import PhVentilationSystem, Ventilator

from PHX.from_HBJSON.create_hvac import build_phx_ventilator


def test_build_phx_ventilator_maps_subsoil_heat_exchange_fields(reset_class_counters):
    hb_ventilator = Ventilator()
    hb_ventilator.subsoil_heat_exchange_efficiency = 0.3
    hb_ventilator.preheated_intake_temperature_c = 8.0

    hb_vent_system = PhVentilationSystem()
    hb_vent_system.ventilation_unit = hb_ventilator

    phx_ventilator = build_phx_ventilator(hb_vent_system)

    assert phx_ventilator.params.subsoil_heat_exchange_efficiency == 0.3
    assert phx_ventilator.params.preheated_intake_temperature_c == 8.0
