from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_relative_absenteeism_is_the_complement_of_utilization(reset_class_counters):
    """WUFI 'RelativeAbsenteeism' is absence (DIN V 18599-10); PHX stores utilization."""
    pattern = PhxScheduleOccupancy(relative_utilization_factor=0.75)
    result = generate_WUFI_XML_from_object(pattern, _header="", _schema_name="_UtilizationPattern")

    assert '<RelativeAbsenteeism unit="-">0.25</RelativeAbsenteeism>' in xml_string_to_list(result)
