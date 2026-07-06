from PHX.from_WUFI_XML import phx_schemas
from PHX.from_WUFI_XML import wufi_file_schema as wufi_xml


def _wufi_ventilator_dict(ph_params: dict) -> dict:
    return {
        "Name": "Ventilator",
        "IdentNr": 1,
        "SystemType": 1,
        "TypeDevice": 1,
        "UsedFor_Heating": False,
        "UsedFor_DHW": False,
        "UsedFor_Cooling": False,
        "UsedFor_Ventilation": True,
        "UsedFor_Humidification": False,
        "UsedFor_Dehumidification": False,
        "HeatRecovery": 0.75,
        "MoistureRecovery": 0.0,
        "PH_Parameters": ph_params,
    }


def test_wufi_ventilator_reads_sys_type(reset_class_counters):
    wufi_device = wufi_xml.WufiDevice.model_validate(_wufi_ventilator_dict({"Quantity": 1, "SystemTypeVentilation": 2}))

    phx_ventilator = phx_schemas._PhxDevice_Ventilation(wufi_device)

    assert phx_ventilator.params.sys_type == 2


def test_wufi_ventilator_defaults_sys_type_when_node_absent(reset_class_counters):
    wufi_device = wufi_xml.WufiDevice.model_validate(_wufi_ventilator_dict({"Quantity": 1}))

    phx_ventilator = phx_schemas._PhxDevice_Ventilation(wufi_device)

    assert phx_ventilator.params.sys_type == 1
