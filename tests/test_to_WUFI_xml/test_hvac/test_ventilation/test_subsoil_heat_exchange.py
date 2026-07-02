from PHX.model.hvac.ventilation import PhxDeviceVentilatorParams
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def test_ventilator_ph_params_omit_subsoil_heat_exchange_when_unset(reset_class_counters):
    params = PhxDeviceVentilatorParams()

    result = generate_WUFI_XML_from_object(params, _header="", _schema_name="_DeviceVentilatorPhParams")

    assert "SubsoilHeatExchangeEfficiency" not in result
    assert "PreheatedIntakeTemperature" not in result


def test_ventilator_ph_params_write_subsoil_heat_exchange_when_set(reset_class_counters):
    params = PhxDeviceVentilatorParams()
    params.subsoil_heat_exchange_efficiency = 0.3
    params.preheated_intake_temperature_c = 8.0

    result = generate_WUFI_XML_from_object(params, _header="", _schema_name="_DeviceVentilatorPhParams")

    assert '<SubsoilHeatExchangeEfficiency unit="-">0.3</SubsoilHeatExchangeEfficiency>' in result
    assert '<PreheatedIntakeTemperature unit="C">8.0</PreheatedIntakeTemperature>' in result
