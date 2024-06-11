# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Data model of the PHPP 'Shape' (worksheet names and input column names)."""

from typing import Dict, Optional

from pydantic import BaseModel

# -----------------------------------------------------------------------------


class InputItem(BaseModel):
    column: Optional[str] = None
    row: Optional[int] = None
    unit: Optional[str] = None

    @property
    def xl_range(self) -> str:
        return f"{self.column}{self.row}"


# -----------------------------------------------------------------------------


class VerificationInputItem(BaseModel):
    locator_col: str
    locator_string: str
    input_column: str
    input_row_offset: int
    options: Optional[Dict] = None
    unit: Optional[str] = None


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
    named_ranges: Optional[ClimateNamedRanges] = None
    defined_ranges: Optional[ClimateDefinedRanges] = None


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
    result_val_col: str
    result_val_row_offset: int
    result_val_unit: str


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


class AreasSummaryRows(BaseModel):
    temp_zones: str
    area_type: str
    group_number: str
    area: str
    average_u_value: str


class AreasSurfaceRows(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    inputs: AreasSurfaceInputs


class AreasDefinedRanges(BaseModel):
    treated_floor_area: InputItem
    window_area_north: InputItem
    window_area_east: InputItem
    window_area_south: InputItem
    window_area_west: InputItem
    window_area_horizontal: InputItem
    door_area: InputItem
    exposed_wall_area: InputItem
    ground_wall_area: InputItem
    roof_ceiling_area: InputItem
    floor_area: InputItem


class Areas(BaseModel):
    name: str
    summary_rows: AreasSummaryRows
    surface_rows: AreasSurfaceRows
    tfa_input: AreasDataInput
    thermal_bridge_rows: AreasThermalBridgeRows
    defined_ranges: AreasDefinedRanges


# -----------------------------------------------------------------------------


class ColGround(BaseModel): ...


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
    """
    Note: this is done differently for glazing than everywhere else because
    in PHPP10, there is a potential Excel formula error in cell IH9 where it
    references the climate data. If the climate is NOT already set, this will
    Error. Then because of a bug in MacOS AppleScript:
    (https://github.com/xlwings/xlwings/issues/1924) XL-Wings will silently pass
    by this cell, which then throws off the row count. Therefor to avoid,
    just hard-coding the start row in this case.
    """

    entry_column: str
    entry_start_row: int
    header_start_row: int
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
    unit: Optional[str] = None


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
    unit: str
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
    unit: str
    col_weather_1: str
    col_weather_2: str
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
    unit: str
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
    unit: str
    col_weather_1: str
    col_weather_2: str
    row_total_losses_transmission: int
    row_total_losses_ventilation: int
    row_total_gains_solar: int
    row_total_gains_internal: int
    row_total_sensible_load: int
    row_total_latent_load: int


# -----------------------------------------------------------------------------


class ColSummVent(BaseModel): ...


class SummVent(BaseModel):
    name: str
    columns: ColSummVent


# -----------------------------------------------------------------------------


class SupplyAirCoolingUnits(BaseModel):
    used: str
    num_units: str
    device_type_name: str
    SEER: str


class RecirculationAirCoolingUnits(BaseModel):
    used: str
    num_units: str
    device_type_name: str
    SEER: str


class DehumidificationCoolingUnits(BaseModel):
    used: str
    waste_heat_to_room: str
    SEER: str


class PanelCoolingUnits(BaseModel):
    used: str
    device_type_name: str
    SEER: str


class CoolingUnits(BaseModel):
    name: str
    SEER_unit: str
    supply_air: SupplyAirCoolingUnits
    recirculation_air: RecirculationAirCoolingUnits
    dehumidification: DehumidificationCoolingUnits
    panel: PanelCoolingUnits


# -----------------------------------------------------------------------------


class DhwRecircPipingInputRows(BaseModel):
    total_length: InputItem
    diameter: InputItem
    insul_thickness: InputItem
    insul_reflective: InputItem
    insul_conductivity: InputItem
    daily_period: InputItem
    water_temp: InputItem


class DhwRecircPiping(BaseModel):
    locator_col_header: str
    locator_string_header: str
    locator_col_entry: str
    locator_string_entry: str
    input_rows_offset: DhwRecircPipingInputRows
    input_col_start: str


class DhwBranchPipingInputRows(BaseModel):
    water_temp: InputItem
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
    entry_row_start: int
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


class RangesSolarDhw(BaseModel):
    footprint: str
    annual_dhw_contribution: str
    annual_dhw_energy: str
    annual_heating_contribution: str
    annual_heating_energy: str


class SolarDhw(BaseModel):
    name: str
    footprint_unit: str
    energy_unit: str
    ranges: RangesSolarDhw


# -----------------------------------------------------------------------------


class ColsSolarPV(BaseModel):
    systems_start: str
    systems_end: str


class RowsSolarPV(BaseModel):
    systems_start: int
    current: int
    voltage: int
    num_panels: int
    name: int
    footprint: int
    annual_energy: int
    systems_end: int


class SolarPv(BaseModel):
    name: str
    footprint_unit: str
    energy_unit: str
    columns: ColsSolarPV
    rows: RowsSolarPV


# -----------------------------------------------------------------------------


class ElectricityInputColumns(BaseModel):
    selection: str
    used: str
    in_conditioned_space: str
    energy_demand_per_use: str
    utilization_factor: str
    frequency: str
    reference_quantity: str
    annual_energy_demand: str


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
    lighting_interior: ElectricityInputRow
    lighting_exterior: ElectricityInputRow
    consumer_elec: ElectricityInputRow
    small_appliances: ElectricityInputRow


class Electricity(BaseModel):
    name: str
    input_columns: ElectricityInputColumns
    input_rows: ElectricityInputRows


# -----------------------------------------------------------------------------


class ColUseNonRes(BaseModel): ...


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
    installed_power: InputItem
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


class ColIhgNonRes(BaseModel): ...


class IhgNonRes(BaseModel):
    name: str
    columns: ColIhgNonRes


# -----------------------------------------------------------------------------


class ColAuxElec(BaseModel): ...


class AuxElec(BaseModel):
    name: str
    columns: ColAuxElec


# -----------------------------------------------------------------------------


class PerColumns(BaseModel):
    calculated_efficiency: str
    user_determined_efficiency: str
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
    locator_string_end: Optional[str] = None


class PerNamedRanges(BaseModel):
    heating_type_1: str
    heating_type_2: str


class PerHeatingTypesBlock(BaseModel):
    range_start: str
    range_end: str


class Per(BaseModel):
    name: str
    locator_col: str
    unit: str
    named_ranges: PerNamedRanges
    columns: PerColumns
    addresses: PerAddresses
    heating_types: PerHeatingTypesBlock
    heating: PerDataBlock
    cooling: PerDataBlock
    dhw: PerDataBlock
    household_electric: PerDataBlock
    additional_gas: PerDataBlock
    energy_generation: PerDataBlock


# -----------------------------------------------------------------------------


class ColHp(BaseModel): ...


class Hp(BaseModel):
    name: str
    columns: ColHp


class ColBoiler(BaseModel): ...


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
    address_area_envelope: InputItem
    address_area_tfa: InputItem


class OverviewVentilation(BaseModel):
    vn50: InputItem


class Overview(BaseModel):
    name: str
    basic_data: OverviewBasicData
    building_envelope: OverviewBuildingEnvelope
    ventilation: OverviewVentilation


class EasyPh(BaseModel):
    name: str


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
    SOLAR_PV: SolarPv
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
    EASY_PH: EasyPh
