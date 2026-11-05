from PHX.from_WUFI_XML import phx_schemas
from PHX.from_WUFI_XML.wufi_file_schema import WufiProcessLoad
from PHX.model.loads.process import PhxProcessLoad
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_process_load_writes_wufi_process_loads_row(reset_class_counters):
    """A PhxProcessLoad becomes one WUFI 'ProcessLoads' row (annual energy in kWh/a)."""
    load = PhxProcessLoad(display_name="Lab: Kiln", annual_energy_kwh=4380.0, comment="from HB")
    result = generate_WUFI_XML_from_object(load, _header="", _schema_name="_PhxProcessLoad")

    assert xml_string_to_list(result) == [
        "<Name>Lab: Kiln</Name>",
        '<TotalEnergyUse unit="kWh/a">4380.0</TotalEnergyUse>',
        "<Quantity>1</Quantity>",
        "<IncludeInSourceEnergyTotal>true</IncludeInSourceEnergyTotal>",
        "<IncreaseSourceEnergyAllowance>false</IncreaseSourceEnergyAllowance>",
        "<InsideThermalEnvelope>true</InsideThermalEnvelope>",
        '<PowerRatingOpt unit="W">0.0</PowerRatingOpt>',
        '<AnnualUseHoursOpt unit="h">0.0</AnnualUseHoursOpt>',
        "<Comment>from HB</Comment>",
    ]


def test_wufi_process_loads_row_reads_back_to_a_phx_process_load():
    """A WUFI-authored 'ProcessLoads' row (School.xml shape) reads into a PhxProcessLoad."""
    wufi_row = WufiProcessLoad(
        Name="Table Top AC Unit",
        TotalEnergyUse={"value": "1800", "unit_type": "kWh/a"},
        Quantity=4,
        IncludeInSourceEnergyTotal=True,
        IncreaseSourceEnergyAllowance=False,
        InsideThermalEnvelope=False,
        PowerRatingOpt={"value": "1800", "unit_type": "W"},
        AnnualUseHoursOpt={"value": "1000", "unit_type": "h"},
    )

    assert phx_schemas._PhxProcessLoad(wufi_row) == PhxProcessLoad(
        display_name="Table Top AC Unit",
        annual_energy_kwh=1800.0,
        quantity=4,
        inside_thermal_envelope=False,
        power_rating_w=1800.0,
        annual_use_hours=1000.0,
    )
