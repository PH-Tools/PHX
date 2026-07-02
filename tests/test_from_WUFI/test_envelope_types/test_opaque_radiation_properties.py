from PHX.from_WUFI_XML import phx_schemas
from PHX.from_WUFI_XML import wufi_file_schema as wufi_xml
from PHX.model.constructions import PhxConstructionOpaque


def test_wufi_component_reads_assembly_radiation_properties(reset_class_counters):
    assembly = PhxConstructionOpaque()
    assembly.id_num = 1
    component = wufi_xml.WufiComponent.model_validate(
        {
            "IdentNr": 1,
            "Name": "Wall",
            "Visual": True,
            "Type": 1,
            "IdentNrColorI": 1,
            "IdentNrColorE": 1,
            "InnerAttachment": 1,
            "OuterAttachment": -1,
            "IdentNr_ComponentInnerSurface": -1,
            "IdentNrAssembly": 1,
            "IdentNrWindowType": -1,
            "IdentNrPolygons": [],
            "EmissionExtern": 0.82,
            "KindAbsorption": -2,
            "Absorption": 0.35,
        }
    )

    phx_component = phx_schemas._PhxComponentOpaque(component, {}, {"1": assembly}, {})

    assert phx_component.assembly.exterior_solar_absorptance == 0.35
    assert phx_component.assembly.exterior_thermal_emissivity == 0.82
