from PHX.model.constructions import PhxLayer, PhxMaterial


# --- Normal Layers --------


def test_default_PhxLayer() -> None:
    layer = PhxLayer()
    assert layer is not None


def test_layer_set_basic_attributes() -> None:
    layer = PhxLayer()
    layer.thickness_m = 0.106
    layer.add_material(
        PhxMaterial()
    )

    assert layer.thickness_mm == 106
    assert layer.material.display_name == ''
    assert layer.layer_resistance == 0.0
    assert layer.layer_conductance == 0.0


def test_layer_from_u_value() -> None:
    layer = PhxLayer.from_total_u_value(0.1)
    assert layer is not None
    assert layer.material is not None
    assert layer.material.display_name == 'Material'
    assert layer.thickness_m == 1
    assert layer.thickness_mm == 1_000
    assert layer.layer_resistance == 10.0
    assert layer.layer_conductance == 0.1
