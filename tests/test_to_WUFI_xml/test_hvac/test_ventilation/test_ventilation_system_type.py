from PHX.model.hvac.ventilation import PhxDeviceVentilatorParams
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def test_ventilator_ph_params_omit_sys_type_when_balanced(reset_class_counters):
    params = PhxDeviceVentilatorParams()  # default sys_type == 1 (balanced)

    result = generate_WUFI_XML_from_object(params, _header="", _schema_name="_DeviceVentilatorPhParams")

    assert "SystemTypeVentilation" not in result


def test_ventilator_ph_params_write_sys_type_when_not_balanced(reset_class_counters):
    params = PhxDeviceVentilatorParams()
    params.sys_type = 2  # Extract-air

    result = generate_WUFI_XML_from_object(params, _header="", _schema_name="_DeviceVentilatorPhParams")

    assert "<SystemTypeVentilation>2</SystemTypeVentilation>" in result
