# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Data model of the PHPP 'Shape' (worksheet names and input column names)."""

from typing import Dict, Optional
from pydantic import BaseModel


# -----------------------------------------------------------------------------


class InputItem(BaseModel):
    column: Optional[str]
    row: Optional[int]
    unit: Optional[str]


# -----------------------------------------------------------------------------


class VerificationInputItem(BaseModel):
    locator_col: str
    locator_string: str
    input_column: str
    input_row_offset: int
    options: Optional[Dict]
    unit: Optional[str]


class Verification(BaseModel):
    name: str
    phi_building_category_type: VerificationInputItem
    phi_building_use_type: VerificationInputItem
    phi_building_ihg_type: VerificationInputItem
    phi_building_occupancy_type: VerificationInputItem

    phi_certification_type: VerificationInputItem
    phi_certification_class: VerificationInputItem
    phi_pe_type: VerificationInputItem
    phi_enerphit_type: VerificationInputItem
    phi_retrofit_type: VerificationInputItem

    num_of_units: VerificationInputItem
    setpoint_winter: VerificationInputItem
    setpoint_summer: VerificationInputItem
    mechanical_cooling: VerificationInputItem


# -----------------------------------------------------------------------------


class VariantWindows(BaseModel):
    locator_col_header: str
    locator_string_header: str
    input_col: str


class VariantAssemblies(BaseModel):
    locator_col_header: str
    locator_string_header: str
    input_col: str


class VariantVentilationInputItemNames(BaseModel):
    vent_type: str
    air_change_rate: str
    design_flow_rate: str
    install_location: str
    ventilator_unit: str


class VariantVentilation(BaseModel):
    locator_col_header: str
    locator_string_header: str
    input_col: str
    input_item_names: VariantVentilationInputItemNames


class VariantInputHeader(BaseModel):
    locator_col_header: str
    locator_string_header: str


class Variants(BaseModel):
    name: str
    active_value_column: str
    input_header: VariantInputHeader
    assemblies: VariantAssemblies
    radiation_balance: None
    thermal_bridges: None
    windows: VariantWindows
    ventilation: VariantVentilation
    summer_ventilation: None
    heating: None
    cooling: None
    user_defined: None


# -----------------------------------------------------------------------------


class ClimateNamedRanges(BaseModel):
    country: str
    region: str
    data_set: str


class ClimateDefinedRanges(BaseModel):
    climate_zone: str
    weather_station_altitude: str
    site_altitude: str
    latitude: str
    longitude: str


class ClimateActiveDatasetCol(BaseModel):
    country: str
    region: str
    dataset: str
    elevation_override: str


class ClimateActiveDataset(BaseModel):
    locator_col_header: str
    locator_string_header: str
    input_columns: ClimateActiveDatasetCol


class ClimateUDBlockCol(BaseModel):
    jan: str
    feb: str
    mar: str
    apr: str
    may: str
    jun: str
    jul: str
    aug: str
    sep: str
    oct: str
    nov: str
    dec: str
    peak_heating_1: str
    peak_heating_2: str
    peak_cooling_1: str
    peak_cooling_2: str
    PER: str
    latitude: str
    longitude: str
    elevation: str
    elevation_unit: str
    display_name: str
    summer_delta_t: str
    summer_delta_t_unit: str
    source: str


class ClimateUDBlockRows(BaseModel):
    temperature_air: InputItem
    radiation_north: InputItem
    radiation_east: InputItem
    radiation_south: InputItem
    radiation_west: InputItem
    radiation_global: InputItem
    temperature_dewpoint: InputItem
    temperature_sky: InputItem


class ClimateUDBlock(BaseModel):
    start_row: int
    locator_col_header: str
    locator_string_header: str
    input_columns: ClimateUDBlockCol
    input_rows: ClimateUDBlockRows


class Climate(BaseModel):
    name: str
    active_dataset: ClimateActiveDataset
    ud_block: ClimateUDBlock
    named_ranges: Optional[ClimateNamedRanges]
    defined_ranges: Optional[ClimateDefinedRanges]


# -----------------------------------------------------------------------------


class UValuesConstructorInputs(BaseModel):
    display_name: InputItem
    r_si: InputItem
    r_se: InputItem
    interior_insulation: InputItem
    sec_1_description: InputItem
    sec_1_conductivity: InputItem
    sec_2_description: InputItem
    sec_2_conductivity: InputItem
    sec_3_description: InputItem
    sec_3_conductivity: InputItem
    thickness: InputItem
    u_val_supplement: InputItem
    variants_layer_name: str
    variants_conductivity: str
    variants_thickness: str
    sec_2_percentage: InputItem
    sec_3_percentage: InputItem
    phpp_id_num_col_offset: int
    name_row_offset: int
    rse_row_offset: int
    rsi_row_offset: int
    first_layer_row_offset: int
    last_layer_row_offset: int


class UValuesConstructor(BaseModel):
    locator_col_header: str
    locator_string_header: str
    inputs: UValuesConstructorInputs


class UValues(BaseModel):
    name: str
    constructor: UValuesConstructor


# -----------------------------------------------------------------------------


class AreasDataInput(BaseModel):
    locator_col: str
    locator_string: str
    input_column: str
    input_row_offset: int
    unit: str


class AreasSurfaceInputs(BaseModel):
    description: InputItem
    group_number: InputItem
    quantity: InputItem
    area: InputItem
    assembly_id: InputItem
    orientation: InputItem
    angle: InputItem
    shading: InputItem
    absorptivity: InputItem
    emissivity: InputItem


class AreasThermalBridgeInputs(BaseModel):
    description: InputItem
    group_number: InputItem
    quantity: InputItem
    length: InputItem
    psi_value: InputItem
    fRsi_value: InputItem


class AreasThermalBridgeRows(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: AreasThermalBridgeInputs


class AreasSurfaceRows(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: AreasSurfaceInputs


class AreasDefinedRanges(BaseModel):
    treated_floor_area: str
    window_area_north: str
    window_area_east: str
    window_area_south: str
    window_area_west: str
    window_area_horizontal: str
    door_area: str
    exposed_wall_area: str
    ground_wall_area: str
    roof_ceiling_area: str
    floor_area: str


class Areas(BaseModel):
    name: str
    surface_rows: AreasSurfaceRows
    tfa_input: AreasDataInput
    thermal_bridge_rows: AreasThermalBridgeRows
    defined_ranges: AreasDefinedRanges


# -----------------------------------------------------------------------------


class ColGround(BaseModel):
    ...


class Ground(BaseModel):
    name: str
    columns: ColGround


# -----------------------------------------------------------------------------


class ComponentsGlazingsInputs(BaseModel):
    id: InputItem
    description: InputItem
    g_value: InputItem
    u_value: InputItem


class ComponentsFramesInputs(BaseModel):
    id: InputItem
    description: InputItem
    u_value_left: InputItem
    u_value_right: InputItem
    u_value_bottom: InputItem
    u_value_top: InputItem
    width_left: InputItem
    width_right: InputItem
    width_bottom: InputItem
    width_top: InputItem
    psi_g_left: InputItem
    psi_g_right: InputItem
    psi_g_bottom: InputItem
    psi_g_top: InputItem
    psi_i_left: InputItem
    psi_i_right: InputItem
    psi_i_bottom: InputItem
    psi_i_top: InputItem


class ComponentsVentilatorsInputs(BaseModel):
    id: InputItem
    display_name: InputItem
    sensible_heat_recovery: InputItem
    latent_heat_recovery: InputItem
    electric_efficiency: InputItem
    min_m3h: InputItem
    max_m3h: InputItem
    pa_per_section: InputItem
    pa_per_fittings: InputItem
    frost_protection_reqd: InputItem
    noise_35DBA: InputItem
    noise_supply_air: InputItem
    noise_extract_air: InputItem
    additional_info: InputItem


class ComponentsGlazings(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: ComponentsGlazingsInputs


class ComponentsFrames(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: ComponentsFramesInputs


class ComponentsVentilators(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: ComponentsVentilatorsInputs


class Components(BaseModel):
    name: str
    glazings: ComponentsGlazings
    frames: ComponentsFrames
    ventilators: ComponentsVentilators


# -----------------------------------------------------------------------------


class WindowWindowRowsColumns(BaseModel):
    quantity: InputItem
    description: InputItem
    orientation_angle: InputItem
    vertical_angle: InputItem
    orientation_label: InputItem
    width: InputItem
    height: InputItem
    host: InputItem
    glazing_id: InputItem
    frame_id: InputItem
    psi_i_left: InputItem
    psi_i_right: InputItem
    psi_i_bottom: InputItem
    psi_i_top: InputItem
    window_area: InputItem
    glazing_area: InputItem
    glazing_fraction: InputItem
    u_w: InputItem
    u_w_installed: InputItem
    comfort_exempt: InputItem
    comfort_temp: InputItem
    variant_input: InputItem


class WindowWindowRows(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: WindowWindowRowsColumns


class WindowWindowRowsEnd(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str


class Windows(BaseModel):
    name: str
    window_rows: WindowWindowRows
    window_rows_end: WindowWindowRowsEnd


# -----------------------------------------------------------------------------


class ShadingRowInputs(BaseModel):
    h_hori: InputItem
    d_hori: InputItem
    o_reveal: InputItem
    d_reveal: InputItem
    o_over: InputItem
    d_over: InputItem
    r_other_winter: InputItem
    r_other_summer: InputItem
    temp_z: InputItem
    regulated: InputItem


class ShadingRows(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: ShadingRowInputs


class ShadingRowsEnd(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str


class Shading(BaseModel):
    name: str
    shading_rows: ShadingRows
    shading_rows_end: ShadingRowsEnd


# -----------------------------------------------------------------------------


class VentilationInputItem(BaseModel):
    locator_col: str
    locator_string: str
    input_column: str
    unit: Optional[str]


class Ventilation(BaseModel):
    name: str
    vent_type: VentilationInputItem
    wind_coeff_e: VentilationInputItem
    wind_coeff_f: VentilationInputItem
    airtightness_n50: VentilationInputItem
    airtightness_Vn50: VentilationInputItem
    multi_unit_on: VentilationInputItem
    variants_col: str


# -----------------------------------------------------------------------------


class AddnlVentInputsRooms(BaseModel):
    quantity: InputItem
    display_name: InputItem
    vent_unit_assigned: InputItem
    weighted_floor_area: InputItem
    clear_height: InputItem
    V_sup: InputItem
    V_eta: InputItem
    V_trans: InputItem
    operating_hours: InputItem
    operating_days: InputItem
    holiday_days: InputItem
    period_high_speed: InputItem
    period_high_time: InputItem
    period_standard_speed: InputItem
    period_standard_time: InputItem
    period_minimum_speed: InputItem
    period_minimum_time: InputItem


class AddnlVentInputsUnits(BaseModel):
    quantity: InputItem
    display_name: InputItem
    unit_selected: InputItem
    oda_sup_pa: InputItem
    eta_eha_pa: InputItem
    addnl_pa: InputItem
    ext_location: InputItem
    subsoil_hr: InputItem
    frost_protection_type: InputItem
    temperature_below_defrost_used: InputItem


class AddnlVentInputsDucts(BaseModel):
    quantity: InputItem
    diameter: InputItem
    width: InputItem
    height: InputItem
    insul_thickness: InputItem
    insul_conductivity: InputItem
    insul_reflective: InputItem
    sup_air_duct_len: InputItem
    oda_air_duct_len: InputItem
    exh_air_duct_len: InputItem
    duct_assign_1: InputItem
    duct_assign_2: InputItem
    duct_assign_3: InputItem
    duct_assign_4: InputItem
    duct_assign_5: InputItem
    duct_assign_6: InputItem
    duct_assign_7: InputItem
    duct_assign_8: InputItem
    duct_assign_9: InputItem
    duct_assign_10: InputItem


class AddnlVentRoomsInputBlockRooms(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: AddnlVentInputsRooms


class AddnlVentRoomsInputBlockUnits(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: AddnlVentInputsUnits


class AddnlVentRoomsInputBlockDucts(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    locator_string_end: str
    inputs: AddnlVentInputsDucts


class AddnlVent(BaseModel):
    name: str
    rooms: AddnlVentRoomsInputBlockRooms
    units: AddnlVentRoomsInputBlockUnits
    ducts: AddnlVentRoomsInputBlockDucts


# -----------------------------------------------------------------------------


class HeatingDemand(BaseModel):
    name: str
    col_kWh_year: str
    col_kWh_m2_year: str
    row_total_losses_transmission: int
    row_total_losses_ventilation: int
    row_total_losses: int
    row_total_gains_solar: int
    row_total_gains_internal: int
    row_utilization_factor: int
    row_useful_gains: int
    row_annual_demand: int


class HeatingPeakLoad(BaseModel):
    name: str
    col_Watts1: str
    col_Watts2: str
    row_total_losses_transmission: int
    row_total_losses_ventilation: int
    row_total_losses: int
    row_total_gains_solar: int
    row_total_gains_internal: int
    row_total_gains: int
    row_total_load: int


# -----------------------------------------------------------------------------


class CoolingDemand(BaseModel):
    name: str
    col_kWh_year: str
    col_kWh_m2_year: str
    row_total_losses_transmission: int
    row_total_losses_ventilation: int
    row_total_losses: int
    row_utilization_factor: int
    row_useful_losses: int
    row_total_gains_solar: int
    row_total_gains_internal: int
    row_total_gains: int
    row_annual_sensible_demand: int
    row_annual_latent_demand: int
    address_specific_latent_cooling_demand: str
    address_tfa: str


class CoolingPeakLoad(BaseModel):
    name: str
    col_Watts1: str
    col_Watts2: str
    row_total_losses_transmission: int
    row_total_losses_ventilation: int
    row_total_gains_solar: int
    row_total_gains_internal: int
    row_total_sensible_load: int
    row_total_latent_load: int


# -----------------------------------------------------------------------------


class ColSummVent(BaseModel):
    ...


class SummVent(BaseModel):
    name: str
    columns: ColSummVent


class ColCoolingUnits(BaseModel):
    ...


class CoolingUnits(BaseModel):
    name: str
    columns: ColCoolingUnits


# -----------------------------------------------------------------------------


class DhwRecircPipingInputRows(BaseModel):
    total_length: InputItem
    diameter: InputItem
    insul_thickness: InputItem
    insul_reflective: InputItem
    insul_conductivity: InputItem


class DhwRecircPiping(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    input_rows_offset: DhwRecircPipingInputRows
    input_col_start: str


class DhwBranchPipingInputRows(BaseModel):
    diameter: InputItem
    total_length: InputItem
    num_taps: int


class DhwBranchPiping(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    input_rows_offset: DhwBranchPipingInputRows
    input_col_start: str


class DhwTankInputOptions(BaseModel):
    options: Dict


class DhwTankInputColumns(BaseModel):
    tank_1: str
    tank_2: str
    tank_buffer: str


class DhwTankInputRows(BaseModel):
    tank_type: InputItem
    standby_losses: InputItem
    storage_capacity: InputItem
    standby_fraction: InputItem
    tank_location: InputItem
    water_temp: InputItem


class DhwTanks(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    input_columns: DhwTankInputColumns
    tank_type: DhwTankInputOptions
    tank_location: DhwTankInputOptions
    input_rows: DhwTankInputRows


class Dhw(BaseModel):
    name: str
    recirc_piping: DhwRecircPiping
    branch_piping: DhwBranchPiping
    tanks: DhwTanks


# -----------------------------------------------------------------------------


class ColSolarDhw(BaseModel):
    ...


class SolarDhw(BaseModel):
    name: str
    columns: ColSolarDhw


class ColPv(BaseModel):
    ...


class Pv(BaseModel):
    name: str
    columns: ColPv


# -----------------------------------------------------------------------------


class ElectricityInputColumns(BaseModel):
    selection: str
    used: str
    in_conditioned_space: str
    energy_demand_per_use: str
    utilization_factor: str
    frequency: str
    reference_quantity: str


class ElectricityInputRow(BaseModel):
    data: int
    selection: int
    selection_options: Dict


class ElectricityInputRows(BaseModel):
    dishwasher: ElectricityInputRow
    clothes_washing: ElectricityInputRow
    clothes_drying: ElectricityInputRow
    refrigerator: ElectricityInputRow
    freezer: ElectricityInputRow
    fridge_freezer: ElectricityInputRow
    cooking: ElectricityInputRow
    lighting: ElectricityInputRow
    consumer_elec: ElectricityInputRow
    small_appliances: ElectricityInputRow


class Electricity(BaseModel):
    name: str
    input_columns: ElectricityInputColumns
    input_rows: ElectricityInputRows


# -----------------------------------------------------------------------------


class ColUseNonRes(BaseModel):
    ...


class UseNonRes(BaseModel):
    name: str
    columns: ColUseNonRes


# -----------------------------------------------------------------------------


class InputsLightingRowsElecNonRes(BaseModel):
    room_zone_name: str
    net_floor_area: str
    utilization_profile: str
    room_has_window: str
    room_angle_from_north: str
    room_orientation: str
    factor: str
    glazing_light_transmission: str
    room_depth: str
    room_width: str
    room_height: str
    lintel_height: str
    window_width: str
    daily_utilization: str
    nominal_illumination: str
    installed_power: str
    lighting_control: str
    motion_detector_used: str
    utilization_hours_year: str
    ud_annual_full_load_hours: str
    annual_full_load_hours: str
    daily_full_load_hours: str
    annual_energy_demand: str


class LightingRowsElecNonRes(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    locator_string_exit: str
    inputs: InputsLightingRowsElecNonRes


class ElecNonRes(BaseModel):
    name: str
    lighting_rows: LightingRowsElecNonRes


# -----------------------------------------------------------------------------


class ColIhgNonRes(BaseModel):
    ...


class IhgNonRes(BaseModel):
    name: str
    columns: ColIhgNonRes


# -----------------------------------------------------------------------------


class ColAuxElec(BaseModel):
    ...


class AuxElec(BaseModel):
    name: str
    columns: ColAuxElec


# -----------------------------------------------------------------------------


class PerColumns(BaseModel):
    final_energy: str
    per_energy: str
    pe_energy: str
    co2_emissions: str


class PerAddresses(BaseModel):
    tfa: str
    footprint: str


class PerDataBlock(BaseModel):
    locator_string_heading: str
    locator_string_start: str
    locator_string_end: Optional[str]


class Per(BaseModel):
    name: str
    locator_col: str
    columns: PerColumns
    addresses: PerAddresses
    heating: PerDataBlock
    cooling: PerDataBlock
    dhw: PerDataBlock
    household_electric: PerDataBlock
    additional_gas: PerDataBlock
    energy_generation: PerDataBlock


# -----------------------------------------------------------------------------


class ColHp(BaseModel):
    ...


class Hp(BaseModel):
    name: str
    columns: ColHp


class ColBoiler(BaseModel):
    ...


class Boiler(BaseModel):
    name: str
    columns: ColBoiler


class DataVersion(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    input_column: Dict


class Data(BaseModel):
    name: str
    version: DataVersion


# -----------------------------------------------------------------------------


class OverviewBasicData(BaseModel):
    address_number_dwellings_res: str
    address_number_dwellings_nonres: str
    address_number_occupants_res: str
    address_number_occupants_nonres: str
    address_project_name: str


class OverviewBuildingEnvelope(BaseModel):
    address_area_envelope: str
    address_area_tfa: str


class OverviewVentilation(BaseModel):
    address_vn50: str


class Overview(BaseModel):
    name: str
    basic_data: OverviewBasicData
    building_envelope: OverviewBuildingEnvelope
    ventilation: OverviewVentilation


# -----------------------------------------------------------------------------


class PhppShape(BaseModel):
    VERIFICATION: Verification
    VARIANTS: Variants
    CLIMATE: Climate
    UVALUES: UValues
    AREAS: Areas
    GROUND: Ground
    COMPONENTS: Components
    WINDOWS: Windows
    SHADING: Shading
    VENTILATION: Ventilation
    ADDNL_VENT: AddnlVent
    HEATING_DEMAND: HeatingDemand
    HEATING_PEAK_LOAD: HeatingPeakLoad
    COOLING_DEMAND: CoolingDemand
    COOLING_PEAK_LOAD: CoolingPeakLoad
    SUMM_VENT: SummVent
    COOLING_UNITS: CoolingUnits
    DHW: Dhw
    SOLAR_DHW: SolarDhw
    PV: Pv
    ELECTRICITY: Electricity
    USE_NON_RES: UseNonRes
    ELEC_NON_RES: ElecNonRes
    AUX_ELEC: AuxElec
    IHG_NON_RES: IhgNonRes
    PER: Per
    HP: Hp
    BOILER: Boiler
    DATA: Data
    OVERVIEW: Overview
