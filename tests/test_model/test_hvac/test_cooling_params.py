from PHX.model.enums import hvac
from PHX.model.hvac import cooling_params


# -- Ventilation Cooling ------------------------------------------------------


def test_default_PhxCoolingVentilationParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingVentilationParams()
    p2 = cooling_params.PhxCoolingVentilationParams()

    p3 = p1 + p2
    assert p3 == p2 == p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.single_speed == p1.single_speed
    assert p3.min_coil_temp == p1.min_coil_temp
    assert p3.capacity == p1.capacity
    assert p3.annual_COP == p1.annual_COP
    assert p3.total_system_perf_ratio == p1.total_system_perf_ratio


def test_add_PhxCoolingVentilationParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingVentilationParams(
        single_speed=True,
        min_coil_temp=20,
        capacity=20,
        annual_COP=6,
    )
    p2 = cooling_params.PhxCoolingVentilationParams(
        single_speed=False,
        min_coil_temp=10,
        capacity=10,
        annual_COP=4,
    )

    p3 = p1 + p2
    assert p3 != p2 != p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.single_speed == True
    assert p3.min_coil_temp == 15
    assert p3.capacity == 15
    assert p3.annual_COP == 5
    assert p3.total_system_perf_ratio == 0.2


# -- Recirculation Cooling ------------------------------------------------------


def test_default_PhxCoolingRecirculationParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingRecirculationParams()
    p2 = cooling_params.PhxCoolingRecirculationParams()

    p3 = p1 + p2
    assert p3 == p2 == p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.single_speed == p1.single_speed
    assert p3.min_coil_temp == p1.min_coil_temp
    assert p3.capacity == p1.capacity
    assert p3.annual_COP == p1.annual_COP
    assert p3.total_system_perf_ratio == p1.total_system_perf_ratio
    assert p3.flow_rate_m3_hr == p1.flow_rate_m3_hr
    assert p3.flow_rate_variable == p1.flow_rate_variable


def test_add_PhxCoolingRecirculationParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingRecirculationParams(
        single_speed=True,
        min_coil_temp=20,
        capacity=20,
        annual_COP=6,
        flow_rate_m3_hr=100,
        flow_rate_variable=True,
    )
    p2 = cooling_params.PhxCoolingRecirculationParams(
        single_speed=False,
        min_coil_temp=10,
        capacity=10,
        annual_COP=4,
        flow_rate_m3_hr=50,
        flow_rate_variable=False,
    )

    p3 = p1 + p2
    assert p3 != p2 != p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.single_speed == True
    assert p3.min_coil_temp == 15
    assert p3.capacity == 15
    assert p3.annual_COP == 5
    assert p3.total_system_perf_ratio == 0.2
    assert p3.flow_rate_m3_hr == 75
    assert p3.flow_rate_variable == True


# -- Dehumidification ---------------------------------------------------------


def test_default_PhxCoolingDehumidificationParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingDehumidificationParams()
    p2 = cooling_params.PhxCoolingDehumidificationParams()

    p3 = p1 + p2
    assert p3 == p2 == p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.annual_COP == p1.annual_COP
    assert p3.total_system_perf_ratio == p1.total_system_perf_ratio
    assert p3.useful_heat_loss == p1.useful_heat_loss


def test_add_PhxCoolingDehumidificationParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingDehumidificationParams(
        annual_COP=6, useful_heat_loss=False
    )
    p2 = cooling_params.PhxCoolingDehumidificationParams(
        annual_COP=4, useful_heat_loss=True
    )

    p3 = p1 + p2
    assert p3 != p2 != p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.annual_COP == 5
    assert p3.total_system_perf_ratio == 0.2
    assert p3.useful_heat_loss == True


# -- Panel Cooling ------------------------------------------------------------


def test_default_PhxCoolingPanelParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingPanelParams()
    p2 = cooling_params.PhxCoolingPanelParams()

    p3 = p1 + p2
    assert p3 == p2 == p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.annual_COP == p1.annual_COP
    assert p3.total_system_perf_ratio == p1.total_system_perf_ratio


def test_add_PhxCoolingPanelParams(reset_class_counters):
    p1 = cooling_params.PhxCoolingPanelParams(annual_COP=6)
    p2 = cooling_params.PhxCoolingPanelParams(annual_COP=4)

    p3 = p1 + p2
    assert p3 != p2 != p1

    # -- Base attrs
    assert p3.aux_energy == p1.aux_energy
    assert p3.aux_energy_dhw == p1.aux_energy_dhw
    assert p3.solar_fraction == p1.solar_fraction
    assert p3.in_conditioned_space == p1.in_conditioned_space

    # -- Class-specific attrs
    assert p3.annual_COP == 5
    assert p3.total_system_perf_ratio == 0.2
