from PHX.model.enums.hvac import PhxHotWaterPipingInchDiameterType


def test_PhxHotWaterPipingInchDiameterType_nearest_key_from_inch():
    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.30)
    assert t == PhxHotWaterPipingInchDiameterType._0_3_8_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.35)
    assert t == PhxHotWaterPipingInchDiameterType._0_3_8_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.40)
    assert t == PhxHotWaterPipingInchDiameterType._0_3_8_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.45)
    assert t == PhxHotWaterPipingInchDiameterType._0_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.5)
    assert t == PhxHotWaterPipingInchDiameterType._0_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.55)
    assert t == PhxHotWaterPipingInchDiameterType._0_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.65)
    assert t == PhxHotWaterPipingInchDiameterType._0_5_8_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.75)
    assert t == PhxHotWaterPipingInchDiameterType._0_3_4_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.85)
    assert t == PhxHotWaterPipingInchDiameterType._0_3_4_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(0.95)
    assert t == PhxHotWaterPipingInchDiameterType._1_0_0_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.05)
    assert t == PhxHotWaterPipingInchDiameterType._1_0_0_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.15)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_4_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.25)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_4_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.35)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_4_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.45)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.55)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.65)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.75)
    assert t == PhxHotWaterPipingInchDiameterType._1_1_2_IN

    t = PhxHotWaterPipingInchDiameterType.nearest_key(1.85)
    assert t == PhxHotWaterPipingInchDiameterType._2_0_0_IN
