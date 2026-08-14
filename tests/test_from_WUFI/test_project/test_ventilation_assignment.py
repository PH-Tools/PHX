import pytest
from lxml import etree

from PHX.from_WUFI_XML import phx_schemas
from PHX.from_WUFI_XML.read_WUFI_XML_file import xml_to_dict
from PHX.from_WUFI_XML.wufi_file_schema import WufiRoom
from PHX.model.project import PhxProject
from PHX.model.schedules.ventilation import PhxScheduleVentilation


def _room_data(_vent_unit_xml):
    root = etree.fromstring("""<Room>
            <Name>Office</Name>
            <Type>1</Type>
            <IdentNrUtilizationPatternVent>1</IdentNrUtilizationPatternVent>
            {}
            <Quantity>1</Quantity>
            <AreaRoom>10.0</AreaRoom>
            <ClearRoomHeight>2.5</ClearRoomHeight>
            <DesignVolumeFlowRateSupply>25.0</DesignVolumeFlowRateSupply>
            <DesignVolumeFlowRateExhaust>25.0</DesignVolumeFlowRateExhaust>
        </Room>""".format(_vent_unit_xml))
    return WufiRoom.model_validate(xml_to_dict(root))


@pytest.mark.parametrize(
    ("source_xml", "expected"),
    [
        ("", None),
        ("<IdentNrVentilationUnit></IdentNrVentilationUnit>", None),
        ("<IdentNrVentilationUnit>0</IdentNrVentilationUnit>", None),
        ("<IdentNrVentilationUnit>7</IdentNrVentilationUnit>", 7),
    ],
)
def test_wufi_room_normalizes_absence_and_preserves_real_device_ids(source_xml, expected):
    project = PhxProject()
    schedule = PhxScheduleVentilation()
    schedule.id_num = 1
    project.utilization_patterns_ventilation["1"] = schedule

    space = phx_schemas._PhxSpace(_room_data(source_xml), project)

    assert space.vent_unit_id_num == expected
