from PHX.from_WUFI_XML import phx_schemas
from PHX.from_WUFI_XML import wufi_file_schema as wufi_xml


def _make_tb_data(**overrides):
    data = {
        "Name": "A000_INT_DRAIN_PIPES",
        "Type": -15,
        "Length": 51.85,
        "PsiValue": 0.043461,
        "IdentNrOptionalClimate": -1,
    }
    data.update(overrides)
    return wufi_xml.WufiThermalBridge.model_validate(data)


def test_wufi_thermal_bridge_defaults_to_not_interior_pipe(reset_class_counters):
    phx_tb = phx_schemas._PhxComponentThermalBridge(_make_tb_data())
    assert phx_tb.is_interior_pipe is False


def test_wufi_thermal_bridge_reads_interior_pipe_flag(reset_class_counters):
    phx_tb = phx_schemas._PhxComponentThermalBridge(_make_tb_data(IsInteriorPipe=True))
    assert phx_tb.is_interior_pipe is True
