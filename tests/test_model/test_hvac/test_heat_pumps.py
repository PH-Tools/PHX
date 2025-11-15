from PHX.model.hvac import heat_pumps


def test_default_PhxHeatPumpAnnual(reset_class_counters):
    d1 = heat_pumps.PhxHeatPumpAnnual()
    d2 = heat_pumps.PhxHeatPumpAnnual()

    assert d1.id_num == 1
    assert d2.id_num == 2


def test_default_PhxHeatPumpMonthly(reset_class_counters):
    d1 = heat_pumps.PhxHeatPumpMonthly()
    d2 = heat_pumps.PhxHeatPumpMonthly()

    assert d1.id_num == 1
    assert d2.id_num == 2


def test_default_PhxHeatPumpMonthlyParams_set_monthly_COPs(reset_class_counters):
    p1 = heat_pumps.PhxHeatPumpMonthlyParams()
    p2 = heat_pumps.PhxHeatPumpMonthlyParams()

    p1.monthly_COPS = []
    assert p1.COP_1 is None
    assert p1.COP_2 is None
    assert p1.monthly_COPS is None
    assert p2.COP_1 is None
    assert p2.COP_2 is None
    assert p2.monthly_COPS is None

    p1.monthly_COPS = [1, 2]
    assert p1.COP_1 == 1
    assert p1.COP_2 == 2
    assert p1.monthly_COPS is None
    assert p2.COP_1 is None
    assert p2.COP_2 is None
    assert p2.monthly_COPS is None

    p2.monthly_COPS = [12]
    assert p1.COP_1 == 1
    assert p1.COP_2 == 2
    assert p1.monthly_COPS is None
    assert p2.COP_1 == 12
    assert p2.COP_2 == 12
    assert p2.monthly_COPS is None

    p1.monthly_COPS = [6, 5, 4]
    assert p1.COP_1 == 6
    assert p1.COP_2 == 5
    assert p1.monthly_COPS is None
    assert p2.COP_1 == 12
    assert p2.COP_2 == 12
    assert p2.monthly_COPS is None


def test_default_PhxHeatPumpMonthlyParams_set_monthly_temps(reset_class_counters):
    p1 = heat_pumps.PhxHeatPumpMonthlyParams()
    p2 = heat_pumps.PhxHeatPumpMonthlyParams()

    p1.monthly_temps = []
    assert p1.ambient_temp_1 is None
    assert p1.ambient_temp_2 is None
    assert p1.monthly_temps is None
    assert p2.ambient_temp_1 is None
    assert p2.ambient_temp_2 is None
    assert p2.monthly_temps is None

    p1.monthly_temps = [1, 2]
    assert p1.ambient_temp_1 == 1
    assert p1.ambient_temp_2 == 2
    assert p1.monthly_temps is None
    assert p2.ambient_temp_1 is None
    assert p2.ambient_temp_2 is None
    assert p2.monthly_temps is None

    p2.monthly_temps = [12]
    assert p1.ambient_temp_1 == 1
    assert p1.ambient_temp_2 == 2
    assert p1.monthly_temps is None
    assert p2.ambient_temp_1 == 12
    assert p2.ambient_temp_2 == 12
    assert p2.monthly_temps is None

    p1.monthly_temps = [6, 5, 4]
    assert p1.ambient_temp_1 == 6
    assert p1.ambient_temp_2 == 5
    assert p1.monthly_temps is None
    assert p2.ambient_temp_1 == 12
    assert p2.ambient_temp_2 == 12
    assert p2.monthly_temps is None


def test_default_PhxHeatPumpHotWater(reset_class_counters):
    d1 = heat_pumps.PhxHeatPumpHotWater()
    d2 = heat_pumps.PhxHeatPumpHotWater()

    assert d1.id_num == 1
    assert d2.id_num == 2


def test_default_PhxHeatPumpCombined(reset_class_counters):
    d1 = heat_pumps.PhxHeatPumpCombined()
    d2 = heat_pumps.PhxHeatPumpCombined()

    assert d1.id_num == 1
    assert d2.id_num == 2
