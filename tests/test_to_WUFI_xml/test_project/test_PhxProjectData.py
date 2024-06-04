from PHX.model import project
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxProjectData(reset_class_counters):
    d1 = project.PhxProjectData()
    d1.project_date.year = 0
    d1.project_date.month = 0
    d1.project_date.day = 0
    d1.project_date.hour = 0
    d1.project_date.minutes = 0
    result = generate_WUFI_XML_from_object(d1, _header="")
    assert xml_string_to_list(result) == [
        "<Year_Construction>0</Year_Construction>",
        "<OwnerIsClient>false</OwnerIsClient>",
        "<Date_Project>",
        "<Year>0</Year>",
        "<Month>0</Month>",
        "<Day>0</Day>",
        "<Hour>0</Hour>",
        "<Minutes>0</Minutes>",
        "</Date_Project>",
        "<WhiteBackgroundPictureBuilding/>",
        "<Customer_Name/>",
        "<Customer_Street/>",
        "<Customer_Locality/>",
        "<Customer_PostalCode/>",
        "<Customer_Tel/>",
        "<Customer_Email/>",
        "<Building_Name/>",
        "<Building_Street/>",
        "<Building_Locality/>",
        "<Building_PostalCode/>",
        "<Owner_Name/>",
        "<Owner_Street/>",
        "<Owner_Locality/>",
        "<Owner_PostalCode/>",
        "<Responsible_Name/>",
        "<Responsible_Street/>",
        "<Responsible_Locality/>",
        "<Responsible_PostalCode/>",
        "<Responsible_Tel/>",
        "<Responsible_LicenseNr/>",
        "<Responsible_Email/>",
    ]
