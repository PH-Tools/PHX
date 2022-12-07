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


class Areas(BaseModel):
    name: str
    surface_rows: AreasSurfaceRows
    tfa_input: AreasDataInput
    thermal_bridge_rows: AreasThermalBridgeRows


# -----------------------------------------------------------------------------


class ColGround(BaseModel):
    ...


class Ground(BaseModel):
    name: str
    columns: ColGround


# -----------------------------------------------------------------------------


class ComponentsGlazingsInputs(BaseModel):
    description: InputItem
    g_value: InputItem
    u_value: InputItem


class ComponentsFramesInputs(BaseModel):
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
    width: InputItem
    height: InputItem
    host: InputItem
    glazing_id: InputItem
    frame_id: InputItem
    psi_i_left: InputItem
    psi_i_right: InputItem
    psi_i_bottom: InputItem
    psi_i_top: InputItem
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


class ColElecNonRes(BaseModel):
    ...


class ElecNonRes(BaseModel):
    name: str
    columns: ColElecNonRes


class ColAuxElec(BaseModel):
    ...


class AuxElec(BaseModel):
    name: str
    columns: ColAuxElec


class ColIhgNonRes(BaseModel):
    ...


class IhgNonRes(BaseModel):
    name: str
    columns: ColIhgNonRes


class ColPer(BaseModel):
    ...


class Per(BaseModel):
    name: str
    columns: ColPer


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
