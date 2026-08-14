from PHX.model.certification import PhxPhBuildingData, PhxPhiusCertification
from PHX.model.constructions import PhxConstructionOpaque, PhxConstructionWindow, PhxMaterial
from PHX.model.identity import identity_scope
from PHX.model.project import PhxVariant
from PHX.model.schedules.lighting import PhxScheduleLighting
from PHX.model.schedules.occupancy import PhxScheduleOccupancy
from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.model.shades import PhxWindowShade
from PHX.to_WUFI_XML.xml_builder import generate_WUFI_XML_from_object


def _scoped_library_ids() -> tuple[int, ...]:
    with identity_scope():
        return (
            PhxVariant().id_num,
            PhxMaterial().id_num,
            PhxConstructionOpaque().id_num,
            PhxConstructionWindow().id_num,
            PhxWindowShade().id_num,
            PhxScheduleVentilation().id_num,
            PhxScheduleOccupancy().id_num,
            PhxScheduleLighting().id_num,
            PhxPhBuildingData().id_num,
        )


def test_scoped_library_ids_ignore_dirty_legacy_counters(reset_class_counters):
    counter_owners = (
        PhxVariant,
        PhxMaterial,
        PhxConstructionOpaque,
        PhxConstructionWindow,
        PhxWindowShade,
        PhxScheduleVentilation,
        PhxScheduleOccupancy,
        PhxScheduleLighting,
        PhxPhBuildingData,
    )
    for owner in counter_owners:
        owner._count = 100

    assert _scoped_library_ids() == _scoped_library_ids()


def test_ph_building_export_uses_instance_identity(reset_class_counters):
    first = PhxPhiusCertification()
    building_data = first.ph_building_data
    before = generate_WUFI_XML_from_object(first, _schema_name="_PhxPhBuildingData")

    PhxPhiusCertification()
    after = generate_WUFI_XML_from_object(first, _schema_name="_PhxPhBuildingData")

    assert after == before
    assert f"<IdentNr>{building_data.id_num}</IdentNr>" in after
