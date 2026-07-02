from PHX.from_WUFI_XML import phx_schemas
from PHX.from_WUFI_XML import wufi_file_schema as wufi_xml


def test_wufi_ventilator_reads_subsoil_heat_exchange_fields(reset_class_counters):
    wufi_device = wufi_xml.WufiDevice.model_validate(
        {
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
            "PH_Parameters": {
                "Quantity": 1,
                "SubsoilHeatExchangeEfficiency": 0.3,
                "PreheatedIntakeTemperature": 8.0,
            },
        }
    )

    phx_ventilator = phx_schemas._PhxDevice_Ventilation(wufi_device)

    assert phx_ventilator.params.subsoil_heat_exchange_efficiency == 0.3
    assert phx_ventilator.params.preheated_intake_temperature_c == 8.0
