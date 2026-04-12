from PHX.model.certification import PhxPhBuildingData, PhxSummerVentilation
from PHX.model.enums.hvac import PhxNighttimeVentilationControl, PhxSummerBypassMode


class TestPhxSummerVentilationDefaults:
    def test_ventilation_system_ach_is_none(self):
        sv = PhxSummerVentilation()
        assert sv.ventilation_system_ach is None

    def test_summer_bypass_mode_default(self):
        sv = PhxSummerVentilation()
        assert sv.summer_bypass_mode == PhxSummerBypassMode.ALWAYS

    def test_daytime_extract_system_ach_default(self):
        sv = PhxSummerVentilation()
        assert sv.daytime_extract_system_ach == 0.0

    def test_daytime_extract_system_fan_power_default(self):
        sv = PhxSummerVentilation()
        assert sv.daytime_extract_system_fan_power_wh_m3 == 0.0

    def test_daytime_window_ach_default(self):
        sv = PhxSummerVentilation()
        assert sv.daytime_window_ach == 0.0

    def test_nighttime_extract_system_ach_default(self):
        sv = PhxSummerVentilation()
        assert sv.nighttime_extract_system_ach == 0.0

    def test_nighttime_extract_system_fan_power_default(self):
        sv = PhxSummerVentilation()
        assert sv.nighttime_extract_system_fan_power_wh_m3 == 0.0

    def test_nighttime_extract_system_heat_fraction_default(self):
        sv = PhxSummerVentilation()
        assert sv.nighttime_extract_system_heat_fraction == 0.0

    def test_nighttime_extract_system_control_default(self):
        sv = PhxSummerVentilation()
        assert sv.nighttime_extract_system_control == PhxNighttimeVentilationControl.TEMPERATURE_CONTROLLED

    def test_nighttime_window_ach_default(self):
        sv = PhxSummerVentilation()
        assert sv.nighttime_window_ach == 0.0

    def test_nighttime_minimum_indoor_temp_default(self):
        sv = PhxSummerVentilation()
        assert sv.nighttime_minimum_indoor_temp_C == 0.0


class TestPhxSummerVentilationCustomValues:
    def test_custom_construction(self):
        sv = PhxSummerVentilation(
            ventilation_system_ach=1.5,
            summer_bypass_mode=PhxSummerBypassMode.TEMP_CONTROLLED,
            daytime_extract_system_ach=0.3,
            daytime_extract_system_fan_power_wh_m3=0.45,
            daytime_window_ach=0.2,
            nighttime_extract_system_ach=0.6,
            nighttime_extract_system_fan_power_wh_m3=0.55,
            nighttime_extract_system_heat_fraction=0.8,
            nighttime_extract_system_control=PhxNighttimeVentilationControl.HUMIDITY_CONTROLLED,
            nighttime_window_ach=0.4,
            nighttime_minimum_indoor_temp_C=18.0,
        )
        assert sv.ventilation_system_ach == 1.5
        assert sv.summer_bypass_mode == PhxSummerBypassMode.TEMP_CONTROLLED
        assert sv.daytime_extract_system_ach == 0.3
        assert sv.daytime_extract_system_fan_power_wh_m3 == 0.45
        assert sv.daytime_window_ach == 0.2
        assert sv.nighttime_extract_system_ach == 0.6
        assert sv.nighttime_extract_system_fan_power_wh_m3 == 0.55
        assert sv.nighttime_extract_system_heat_fraction == 0.8
        assert sv.nighttime_extract_system_control == PhxNighttimeVentilationControl.HUMIDITY_CONTROLLED
        assert sv.nighttime_window_ach == 0.4
        assert sv.nighttime_minimum_indoor_temp_C == 18.0


class TestPhxSummerVentilationEquality:
    def test_default_instances_are_equal(self):
        sv1 = PhxSummerVentilation()
        sv2 = PhxSummerVentilation()
        assert sv1 == sv2

    def test_different_bypass_mode_not_equal(self):
        sv1 = PhxSummerVentilation()
        sv2 = PhxSummerVentilation(summer_bypass_mode=PhxSummerBypassMode.TEMP_CONTROLLED)
        assert sv1 != sv2

    def test_different_ach_not_equal(self):
        sv1 = PhxSummerVentilation()
        sv2 = PhxSummerVentilation(ventilation_system_ach=1.0)
        assert sv1 != sv2

    def test_different_nighttime_control_not_equal(self):
        sv1 = PhxSummerVentilation()
        sv2 = PhxSummerVentilation(nighttime_extract_system_control=PhxNighttimeVentilationControl.HUMIDITY_CONTROLLED)
        assert sv1 != sv2

    def test_float_tolerance(self):
        sv1 = PhxSummerVentilation(daytime_window_ach=1.0)
        sv2 = PhxSummerVentilation(daytime_window_ach=1.0000001)
        assert sv1 == sv2

    def test_float_beyond_tolerance_not_equal(self):
        sv1 = PhxSummerVentilation(daytime_window_ach=1.0)
        sv2 = PhxSummerVentilation(daytime_window_ach=1.01)
        assert sv1 != sv2


class TestPhxPhBuildingDataSummerVentilation:
    def test_building_data_has_summer_ventilation(self, reset_class_counters):
        bd = PhxPhBuildingData()
        assert isinstance(bd.summer_ventilation, PhxSummerVentilation)

    def test_building_data_summer_ventilation_defaults(self, reset_class_counters):
        bd = PhxPhBuildingData()
        assert bd.summer_ventilation.summer_bypass_mode == PhxSummerBypassMode.ALWAYS
        assert bd.summer_ventilation.ventilation_system_ach is None

    def test_building_data_equality_with_same_summer_ventilation(self, reset_class_counters):
        bd1 = PhxPhBuildingData()
        bd2 = PhxPhBuildingData()
        assert bd1 == bd2

    def test_building_data_inequality_with_different_summer_ventilation(self, reset_class_counters):
        bd1 = PhxPhBuildingData()
        bd2 = PhxPhBuildingData()
        bd2.summer_ventilation.summer_bypass_mode = PhxSummerBypassMode.TEMP_CONTROLLED
        assert bd1 != bd2
