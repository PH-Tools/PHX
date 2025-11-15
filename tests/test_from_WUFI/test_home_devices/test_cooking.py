from PHX.from_WUFI_XML.phx_schemas import _PhxDeviceCooktop, _PhxHomeDevice
from PHX.from_WUFI_XML.read_WUFI_XML_file import string_to_xml_dict
from PHX.from_WUFI_XML.wufi_file_schema import WufiHomeDevice
from PHX.model.elec_equip import *

XML_STRING = """
<Device index="0">
    <Comment>default</Comment>
    <ReferenceQuantity>1</ReferenceQuantity>
    <Quantity>2</Quantity>
    <InConditionedSpace>true</InConditionedSpace>
    <ReferenceEnergyDemandNorm>1</ReferenceEnergyDemandNorm>
    <EnergyDemandNorm>0.0</EnergyDemandNorm>
    <EnergyDemandNormUse>0.25</EnergyDemandNormUse>
    <CEF_CombinedEnergyFactor>0</CEF_CombinedEnergyFactor>
    <Type>7</Type>
    <CookingWith>1</CookingWith>
</Device>
"""


def test_create_xml_object_from_string() -> None:
    xml_dict = string_to_xml_dict(XML_STRING)
    new_home_device = WufiHomeDevice(**xml_dict)

    assert new_home_device.Comment == "default"
    assert new_home_device.ReferenceQuantity == 1
    assert new_home_device.Quantity == 2
    assert new_home_device.InConditionedSpace
    assert new_home_device.ReferenceEnergyDemandNorm == 1
    assert new_home_device.EnergyDemandNorm == 0.0
    assert new_home_device.EnergyDemandNormUse == 0.25
    assert new_home_device.CEF_CombinedEnergyFactor == 0
    assert new_home_device.Type == 7


def test_create_phx_object_from_xml_string() -> None:
    xml_dict = string_to_xml_dict(XML_STRING)
    new_wufi_xml_obj = WufiHomeDevice(**xml_dict)

    # -- Test using the device factory which transfers *all* attributes
    new_phx_obj: PhxDeviceCooktop = _PhxHomeDevice(new_wufi_xml_obj)  # type: ignore
    assert new_phx_obj.comment == "default"
    assert new_phx_obj.quantity == 2
    assert new_phx_obj.in_conditioned_space
    assert new_phx_obj.reference_energy_norm == 1
    assert new_phx_obj.energy_demand_per_use == 0.25
    assert new_phx_obj.cooktop_type == 1

    # -- Individual items *only* have the custom attributes
    new_phx_dishwasher = _PhxDeviceCooktop(new_wufi_xml_obj)
    assert new_phx_dishwasher.cooktop_type == 1
