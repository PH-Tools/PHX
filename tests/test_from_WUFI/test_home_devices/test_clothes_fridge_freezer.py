from PHX.from_WUFI_XML.read_WUFI_XML_file import string_to_xml_dict
from PHX.from_WUFI_XML.wufi_file_schema import HomeDevice
from PHX.model.elec_equip import *
from PHX.from_WUFI_XML.phx_schemas import _PhxHomeDevice, _PhxDeviceFridgeFreezer

XML_STRING = """
<Device index="2">
    <Comment>default</Comment>
    <ReferenceQuantity>4</ReferenceQuantity>
    <Quantity>2</Quantity>
    <InConditionedSpace>true</InConditionedSpace>
    <ReferenceEnergyDemandNorm>1</ReferenceEnergyDemandNorm>
    <EnergyDemandNorm>0.0</EnergyDemandNorm>
    <EnergyDemandNormUse>1.0</EnergyDemandNormUse>
    <CEF_CombinedEnergyFactor>0</CEF_CombinedEnergyFactor>
    <Type>6</Type>
</Device>
"""


def test_create_xml_object_from_string() -> None:
    xml_dict = string_to_xml_dict(XML_STRING)
    new_wufi_xml_obj = HomeDevice(**xml_dict)

    assert new_wufi_xml_obj.Comment == "default"
    assert new_wufi_xml_obj.ReferenceQuantity == 4
    assert new_wufi_xml_obj.Quantity == 2
    assert new_wufi_xml_obj.InConditionedSpace == True
    assert new_wufi_xml_obj.ReferenceEnergyDemandNorm == 1
    assert new_wufi_xml_obj.EnergyDemandNorm == 0
    assert new_wufi_xml_obj.EnergyDemandNormUse == 1
    assert new_wufi_xml_obj.CEF_CombinedEnergyFactor == 0
    assert new_wufi_xml_obj.Type == 6


def test_create_phx_object_from_xml_string() -> None:
    xml_dict = string_to_xml_dict(XML_STRING)
    new_wufi_xml_obj = HomeDevice(**xml_dict)

    # -- Test using the device factory which transfers *all* attributes
    new_phx_obj: PhxDeviceFridgeFreezer = _PhxHomeDevice(new_wufi_xml_obj)  # type: ignore
    assert new_phx_obj.comment == "default"
    assert new_phx_obj.quantity == 2
    assert new_phx_obj.in_conditioned_space == True
    assert new_phx_obj.reference_energy_norm == 1
    assert new_phx_obj.energy_demand_per_use == 1
    assert new_phx_obj.combined_energy_factor == 0

    # -- Individual items *only* have the custom attributes
    new_phx_dishwasher = _PhxDeviceFridgeFreezer(new_wufi_xml_obj)
    assert new_phx_dishwasher
