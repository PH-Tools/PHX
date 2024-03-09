from PHX.from_WUFI_XML.read_WUFI_XML_file import string_to_xml_dict
from PHX.from_WUFI_XML.wufi_file_schema import HomeDevice
from PHX.model.elec_equip import *
from PHX.from_WUFI_XML.phx_schemas import _PhxHomeDevice, _PhxDeviceClothesDryer

XML_STRING = """
<Device index="3">
    <Comment>default</Comment>
    <ReferenceQuantity>1</ReferenceQuantity>
    <Quantity>2</Quantity>
    <InConditionedSpace>true</InConditionedSpace>
    <ReferenceEnergyDemandNorm>2</ReferenceEnergyDemandNorm>
    <EnergyDemandNorm>0.0</EnergyDemandNorm>
    <EnergyDemandNormUse>3.5</EnergyDemandNormUse>
    <CEF_CombinedEnergyFactor>3.93</CEF_CombinedEnergyFactor>
    <Type>3</Type>
    <Dryer_Choice>4</Dryer_Choice>
    <GasConsumption>0</GasConsumption>
    <EfficiencyFactorGas>2.67</EfficiencyFactorGas>
    <FieldUtilizationFactorPreselection>1</FieldUtilizationFactorPreselection>
    <FieldUtilizationFactor>1.18</FieldUtilizationFactor>
</Device>
"""


def test_create_xml_object_from_string() -> None:
    xml_dict = string_to_xml_dict(XML_STRING)
    new_wufi_xml_obj = HomeDevice(**xml_dict)

    assert new_wufi_xml_obj.Comment == "default"
    assert new_wufi_xml_obj.ReferenceQuantity == 1
    assert new_wufi_xml_obj.Quantity == 2
    assert new_wufi_xml_obj.InConditionedSpace == True
    assert new_wufi_xml_obj.ReferenceEnergyDemandNorm == 2
    assert new_wufi_xml_obj.EnergyDemandNorm == 0.0
    assert new_wufi_xml_obj.EnergyDemandNormUse == 3.5
    assert new_wufi_xml_obj.CEF_CombinedEnergyFactor == 3.93
    assert new_wufi_xml_obj.Type == 3

    assert new_wufi_xml_obj.Dryer_Choice == 4
    assert new_wufi_xml_obj.GasConsumption == 0
    assert new_wufi_xml_obj.EfficiencyFactorGas == 2.67
    assert new_wufi_xml_obj.FieldUtilizationFactorPreselection == 1
    assert new_wufi_xml_obj.FieldUtilizationFactor == 1.18


def test_create_phx_object_from_xml_string() -> None:
    xml_dict = string_to_xml_dict(XML_STRING)
    new_wufi_xml_obj = HomeDevice(**xml_dict)

    # -- Test using the device factory which transfers *all* attributes
    new_phx_obj: PhxDeviceClothesDryer = _PhxHomeDevice(new_wufi_xml_obj)  # type: ignore
    assert new_phx_obj.comment == "default"
    assert new_phx_obj.quantity == 2
    assert new_phx_obj.in_conditioned_space == True
    assert new_phx_obj.reference_energy_norm == 2
    assert new_phx_obj.energy_demand_per_use == 3.5
    assert new_phx_obj.combined_energy_factor == 3.93

    # -- Individual items *only* have the custom attributes
    new_phx_dishwasher = _PhxDeviceClothesDryer(new_wufi_xml_obj)
    assert new_phx_dishwasher.dryer_type == 4
    assert new_phx_dishwasher.gas_consumption == 0
    assert new_phx_dishwasher.gas_efficiency_factor == 2.67
    assert new_phx_dishwasher.field_utilization_factor_type == 1
    assert new_phx_dishwasher.field_utilization_factor == 1.18
