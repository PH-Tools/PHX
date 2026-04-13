"""Tests for ihg_utilization_factor round-trip through WUFI XML import."""

from PHX.from_WUFI_XML.phx_schemas import _PhxHomeDevice
from PHX.from_WUFI_XML.read_WUFI_XML_file import string_to_xml_dict
from PHX.from_WUFI_XML.wufi_file_schema import WufiHomeDevice
from PHX.model.elec_equip import PhxDeviceDishwasher

XML_WITH_IHG = """
<Device index="1">
    <Comment>test</Comment>
    <ReferenceQuantity>1</ReferenceQuantity>
    <Quantity>1</Quantity>
    <InConditionedSpace>true</InConditionedSpace>
    <ReferenceEnergyDemandNorm>2</ReferenceEnergyDemandNorm>
    <EnergyDemandNorm>100.0</EnergyDemandNorm>
    <EnergyDemandNormUse>100.0</EnergyDemandNormUse>
    <CEF_CombinedEnergyFactor>0</CEF_CombinedEnergyFactor>
    <IHG_UtilizationFactor>0.45</IHG_UtilizationFactor>
    <Type>1</Type>
    <Connection>1</Connection>
    <DishwasherCapacityPreselection>1</DishwasherCapacityPreselection>
    <DishwasherCapacityInPlace>1.0</DishwasherCapacityInPlace>
</Device>
"""

XML_WITHOUT_IHG = """
<Device index="1">
    <Comment>legacy</Comment>
    <ReferenceQuantity>1</ReferenceQuantity>
    <Quantity>1</Quantity>
    <InConditionedSpace>true</InConditionedSpace>
    <ReferenceEnergyDemandNorm>2</ReferenceEnergyDemandNorm>
    <EnergyDemandNorm>100.0</EnergyDemandNorm>
    <EnergyDemandNormUse>100.0</EnergyDemandNormUse>
    <CEF_CombinedEnergyFactor>0</CEF_CombinedEnergyFactor>
    <Type>1</Type>
    <Connection>1</Connection>
    <DishwasherCapacityPreselection>1</DishwasherCapacityPreselection>
    <DishwasherCapacityInPlace>1.0</DishwasherCapacityInPlace>
</Device>
"""


def test_wufi_xml_schema_parses_ihg_utilization_factor() -> None:
    xml_dict = string_to_xml_dict(XML_WITH_IHG)
    wufi_obj = WufiHomeDevice(**xml_dict)
    assert wufi_obj.IHG_UtilizationFactor == 0.45


def test_wufi_xml_schema_missing_ihg_defaults_to_none() -> None:
    xml_dict = string_to_xml_dict(XML_WITHOUT_IHG)
    wufi_obj = WufiHomeDevice(**xml_dict)
    assert wufi_obj.IHG_UtilizationFactor is None


def test_phx_device_gets_ihg_from_xml() -> None:
    xml_dict = string_to_xml_dict(XML_WITH_IHG)
    wufi_obj = WufiHomeDevice(**xml_dict)
    phx_obj: PhxDeviceDishwasher = _PhxHomeDevice(wufi_obj)  # type: ignore
    assert phx_obj.ihg_utilization_factor == 0.45


def test_phx_device_keeps_default_ihg_when_xml_missing() -> None:
    """Backwards compat: legacy XML without IHG_UtilizationFactor keeps device default."""
    xml_dict = string_to_xml_dict(XML_WITHOUT_IHG)
    wufi_obj = WufiHomeDevice(**xml_dict)
    phx_obj: PhxDeviceDishwasher = _PhxHomeDevice(wufi_obj)  # type: ignore
    # Dishwasher default is 0.30
    assert phx_obj.ihg_utilization_factor == 0.30
