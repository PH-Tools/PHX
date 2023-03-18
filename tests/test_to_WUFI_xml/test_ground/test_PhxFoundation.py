from PHX.model import ground
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object
from tests.test_to_WUFI_xml._utils import xml_string_to_list


def test_default_PhxFoundation(reset_class_counters):
    g1 = ground.PhxFoundation()
    result = generate_WUFI_XML_from_object(g1, _header="")
    assert xml_string_to_list(result) == [
        '<Name>__unnamed_foundation__</Name>',
        '<SettingFloorSlabType>6</SettingFloorSlabType>',
        '<FloorSlabType>5</FloorSlabType>'
    ]

def test_default_PhxHeatedBasement(reset_class_counters):
    g1 = ground.PhxHeatedBasement()
    result = generate_WUFI_XML_from_object(g1, _header="")
    assert xml_string_to_list(result) == [
        '<FloorSlabArea_Selection>6</FloorSlabArea_Selection>',
        '<FloorSlabArea>0.0</FloorSlabArea>',
        '<FloorSlabPerimeter_Selection>6</FloorSlabPerimeter_Selection>',
        '<FloorSlabPerimeter>0.0</FloorSlabPerimeter>',
        '<U_ValueBasementSlab_Selection>6</U_ValueBasementSlab_Selection>',
        '<U_ValueBasementSlab>1.0</U_ValueBasementSlab>',
        '<DepthBasementBelowGroundSurface_Selection>6</DepthBasementBelowGroundSurface_Selection>',
        '<DepthBasementBelowGroundSurface>2.5</DepthBasementBelowGroundSurface>',
        '<U_ValueBasementWall_Selection>6</U_ValueBasementWall_Selection>',
        '<U_ValueBasementWall>1.0</U_ValueBasementWall>',
    ]

def test_default_PhxUnHeatedBasement(reset_class_counters):
    g1 = ground.PhxUnHeatedBasement()
    result = generate_WUFI_XML_from_object(g1, _header="")
    assert xml_string_to_list(result) == [
        '<DepthBasementBelowGroundSurface_Selection>6</DepthBasementBelowGroundSurface_Selection>',
        '<DepthBasementBelowGroundSurface>0.0</DepthBasementBelowGroundSurface>',
        '<HeightBasementWallAboveGrade_Selection>6</HeightBasementWallAboveGrade_Selection>',
        '<HeightBasementWallAboveGrade>0.0</HeightBasementWallAboveGrade>',
        '<FloorSlabArea_Selection>6</FloorSlabArea_Selection>',
        '<FloorSlabArea>0.0</FloorSlabArea>',
        '<U_ValueBasementSlab_Selection>6</U_ValueBasementSlab_Selection>',
        '<U_ValueBasementSlab>0.0</U_ValueBasementSlab>',
        '<FloorCeilingArea_Selection>6</FloorCeilingArea_Selection>',
        '<FloorCeilingArea>0.0</FloorCeilingArea>',
        '<U_ValueCeilingToUnheatedCellar_Selection>6</U_ValueCeilingToUnheatedCellar_Selection>',
        '<U_ValueCeilingToUnheatedCellar>0.0</U_ValueCeilingToUnheatedCellar>',
        '<U_ValueBasementWall_Selection>6</U_ValueBasementWall_Selection>',
        '<U_ValueBasementWall>0.0</U_ValueBasementWall>',
        '<U_ValueWallAboveGround_Selection>6</U_ValueWallAboveGround_Selection>',
        '<U_ValueWallAboveGround>0.0</U_ValueWallAboveGround>',
        '<FloorSlabPerimeter_Selection>6</FloorSlabPerimeter_Selection>',
        '<FloorSlabPerimeter>0.0</FloorSlabPerimeter>',
        '<BasementVolume_Selection>6</BasementVolume_Selection>',
        '<BasementVolume>0.0</BasementVolume>'
        ]

def test_default_PhxSlabOnGrade(reset_class_counters):
    g1 = ground.PhxSlabOnGrade()
    result = generate_WUFI_XML_from_object(g1, _header="")
    assert xml_string_to_list(result) == [
        '<FloorSlabArea_Selection>6</FloorSlabArea_Selection>',
        '<FloorSlabArea>0.0</FloorSlabArea>',
        '<U_ValueBasementSlab_Selection>6</U_ValueBasementSlab_Selection>',
        '<U_ValueBasementSlab>1.0</U_ValueBasementSlab>',
        '<FloorSlabPerimeter_Selection>6</FloorSlabPerimeter_Selection>',
        '<FloorSlabPerimeter>0.0</FloorSlabPerimeter>',
        '<PositionPerimeterInsulation>3</PositionPerimeterInsulation>',
        '<PerimeterInsulationWidthDepth>0.3</PerimeterInsulationWidthDepth>',
        '<ConductivityPerimeterInsulation>0.04</ConductivityPerimeterInsulation>',
        '<ThicknessPerimeterInsulation>0.05</ThicknessPerimeterInsulation>'
    ]

def test_default_PhxCrawlspace(reset_class_counters):
    g1 = ground.PhxVentedCrawlspace()
    result = generate_WUFI_XML_from_object(g1, _header="")
    assert xml_string_to_list(result) == [
        '<FloorCeilingArea_Selection>6</FloorCeilingArea_Selection>',
        '<FloorCeilingArea>0.0</FloorCeilingArea>',
        '<U_ValueCeilingToUnheatedCellar_Selection>6</U_ValueCeilingToUnheatedCellar_Selection>',
        '<U_ValueCeilingToUnheatedCellar>1.0</U_ValueCeilingToUnheatedCellar>',
        '<FloorSlabPerimeter_Selection>6</FloorSlabPerimeter_Selection>',
        '<FloorSlabPerimeter>0.0</FloorSlabPerimeter>',
        '<HeightBasementWallAboveGrade_Selection>6</HeightBasementWallAboveGrade_Selection>',
        '<HeightBasementWallAboveGrade>0.0</HeightBasementWallAboveGrade>',
        '<U_ValueCrawlspaceFloor_Selection>6</U_ValueCrawlspaceFloor_Selection>',
        '<U_ValueCrawlspaceFloor>1.0</U_ValueCrawlspaceFloor>',
        '<CrawlspaceVentOpenings_Selection>6</CrawlspaceVentOpenings_Selection>',
        '<CrawlspaceVentOpenings>0.0</CrawlspaceVentOpenings>',
        '<U_ValueWallAboveGround_Selection>6</U_ValueWallAboveGround_Selection>',
        '<U_ValueWallAboveGround>1.0</U_ValueWallAboveGround>'
    ]