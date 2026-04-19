# WUFI-Passive XML Schema Reference

WUFI-Passive XML files are the primary data exchange format for Passive House energy models. They can be 30,000–100,000+ lines and contain the complete building model: geometry, constructions, windows, HVAC, DHW, renewables, and certification parameters.

<div class="ph-meta-strip">
  <div class="ph-meta-item">
    <span class="ph-meta-k">Schema version</span>
    <span class="ph-meta-v">WUFI-Passive 3.3.x</span>
  </div>
  <div class="ph-meta-item">
    <span class="ph-meta-k">Data version</span>
    <span class="ph-meta-v">48+</span>
  </div>
  <div class="ph-meta-item">
    <span class="ph-meta-k">Maintainer</span>
    <span class="ph-meta-v">bldgtyp</span>
  </div>
  <div class="ph-meta-item">
    <span class="ph-meta-k">Source</span>
    <span class="ph-meta-v">PHX / docs</span>
  </div>
</div>

<div class="ph-fetch-callout">
  <div class="ph-fetch-callout__inner">
    <div>
      <div class="ph-fetch-callout__head">
        <span class="ph-bullet"></span>
        LLM-ready · Fetch this doc
      </div>
      <p class="ph-fetch-callout__body">
        This page is available at a stable URL for programmatic retrieval. Point your LLM tool at the URL below to receive the current canonical schema in plain Markdown.
      </p>
      <div class="ph-fetch-callout__url">
        <span class="ph-method">GET</span>
        <span>https://docs.passivehousetools.com/reference/wufi-xml-schema</span>
      </div>
    </div>
  </div>
</div>

---

## XML Structure Map

Format version 3.x, Data Version 48+. Section order is consistent across projects; line numbers vary by project size.

```
WUFIplusProject
├── DataVersion
├── UnitSystem (0=SI, 1=IP)
├── DaylightSavingTime
├── ProjectData (project name, dates, agents)
├── Graphics3D (3D viewport state — skip)
├── ClimateLocation (weather file, site data)
├── UtilizationPatterns_NonRes (schedule collections)
├── UtilizationPatterns_Ventilation (ventilation schedule collections)
├── Zones
│   └── Zone
│       ├── Name, Volume, FloorArea
│       ├── Components (opaque + aperture surfaces)
│       │   └── Component
│       │       ├── IdentNr, Name, Type (1=opaque, 2=aperture)
│       │       ├── IdentNrAssembly (links to Assembly)
│       │       ├── IdentNrWindowType (links to WindowType, apertures only)
│       │       ├── DepthWindowReveal (apertures only)
│       │       └── DefaultCorrectionShadingMonth (apertures only)
│       ├── Rooms (ventilation spaces)
│       │   └── Room
│       │       ├── Name (matches ventilation device name)
│       │       ├── DesignVolumeFlowRateSupply [m³/h]
│       │       └── DesignVolumeFlowRateExhaust [m³/h]
│       ├── ThermalBridges
│       │   └── ThermalBridge
│       │       ├── Name, PsiValue [W/mK], Length [m]
│       │       └── Type
│       ├── InternalGainsData
│       └── GroundFloor / Foundation data
├── PassivehouseData
│   ├── PH_CertificateCriteria
│   ├── AnnualHeatingDemand [kWh/m²a]
│   ├── AnnualCoolingDemand [kWh/m²a]
│   ├── PeakHeatingLoad [W/m²]
│   ├── PeakCoolingLoad [W/m²]
│   ├── PH_Buildings
│   │   └── PH_Building (building data, airtightness, occupancy)
│   └── UseWUFIMeanMonthShading (true/false)
├── HVAC
│   └── Systems
│       └── System
│           ├── Name, Type, IdentNr
│           ├── ZonesCoverage
│           ├── Devices
│           │   └── Device
│           │       ├── Name, IdentNr
│           │       ├── SystemType (1=ventilation, 2=heating, 5=HP, 10=PV)
│           │       ├── TypeDevice
│           │       ├── UsedFor_Heating/DHW/Cooling/Ventilation
│           │       ├── HeatRecovery (ventilation devices)
│           │       ├── MoistureRecovery (ventilation devices)
│           │       └── PH_Parameters
│           │           ├── ElectricEfficiency [Wh/m³] (ventilation)
│           │           ├── HumidityRecoveryEfficiency (ventilation)
│           │           ├── Quantity (ventilation)
│           │           ├── RatedCOP1, RatedCOP2 (heat pumps)
│           │           ├── AnnualCOP (DHW heat pumps)
│           │           ├── HPWH_EF (DHW heat pumps)
│           │           ├── ArraySizePV [kW] (PV)
│           │           └── PhotovoltaicRenewableEnergy [kWh/yr] (PV)
│           └── PHDistribution
│               ├── DistributionDHW
│               │   └── Truncs > Trunc > Branches > Branch > Twigs
│               │       (piping lengths, materials, diameters)
│               └── DistributionVentilation
│                   └── Ducts
│                       └── Duct
│                           ├── Name
│                           ├── DuctLength [m]
│                           ├── InsulationThickness [mm]
│                           ├── ThermalConductivity [W/mK]
│                           ├── DuctType (1=supply, 2=extract)
│                           ├── DuctShape (1=round, 2=rectangular)
│                           └── AssignedVentUnits
├── Assemblies
│   └── Assembly
│       ├── Name, IdentNr
│       ├── Order_Layers (2=outside-to-inside)
│       └── Layers
│           └── Layer
│               ├── Thickness [m]
│               └── Material
│                   ├── Name, ThermalConductivity [W/mK]
│                   ├── BulkDensity [kg/m³]
│                   └── HeatCapacity [J/kgK]
└── WindowTypes
    └── WindowType
        ├── Name, IdentNr
        ├── FrameFactor (glass fraction, 0-1)
        ├── U_Value [W/m²K] (overall)
        ├── U_Value_Glazing [W/m²K]
        ├── g_Value / SHGC_Hemispherical
        ├── Frame_Width_{Left,Right,Top,Bottom} [m]
        ├── Frame_U_{Left,Right,Top,Bottom} [W/m²K]
        ├── Frame_Psi_{Left,Right,Top,Bottom} [W/mK]
        └── Glazing_Psi_{Left,Right,Top,Bottom} [W/mK]
```

### Device Type Identification

| SystemType | TypeDevice | What it is |
|---|---|---|
| 1 | 1 | Mechanical ventilation (ERV/HRV/NERV) |
| 2 | 2 | Direct electric or fossil heater |
| 5 | 5 | Heat pump (heating, cooling, or DHW) |
| 10 | 10 | Photovoltaic / renewable |

The `UsedFor_*` boolean fields further distinguish purpose (heating, DHW, cooling, ventilation).

### Section Size Estimates (typical large multifamily, ~78,000 lines)

| Section | Typical line range | Typical size |
|---|---|---|
| Zone Components (geometry) | 1,000–55,000 | 50,000+ lines |
| Zone Rooms (ventilation spaces) | 55,000–58,000 | 2,000–5,000 lines |
| Thermal Bridges | 72,000–73,000 | ~200 lines |
| PassivehouseData | 73,000–73,130 | ~130 lines |
| HVAC Devices | 73,130–73,950 | ~800 lines |
| DHW Piping | 73,950–74,450 | ~500 lines |
| Ducts | 74,450–75,300 | ~900 lines |
| Assemblies | 75,600–76,400 | ~800 lines |
| WindowTypes | 76,400–78,200 | ~1,800 lines |

---

## Quick Lookup Table

| You want to find... | Look in... |
|---|---|
| Ventilation units (ERV/HRV/NERV) | `HVAC > Systems > System > Devices` (TypeDevice=1) |
| Heat pumps, heaters | `HVAC > Systems > System > Devices` (TypeDevice=2 or 5) |
| DHW water heaters | `HVAC > Systems > System > Devices` (UsedFor_DHW=true) |
| PV / renewables | `HVAC > Systems > System > Devices` (SystemType=10) |
| Ducts | `HVAC > Systems > System > PHDistribution > DistributionVentilation > Ducts` |
| DHW piping | `HVAC > Systems > System > PHDistribution > DistributionDHW > Truncs` |
| Thermal bridges | `Zones > Zone > ThermalBridges` |
| Window types (thermal properties) | `WindowTypes > WindowType` (near end of file) |
| Window components (shading, reveals) | `Zones > Zone > Components > Component` (Type=2) |
| Opaque assemblies | `Assemblies > Assembly` (near end of file) |
| Certification targets | `PassivehouseData > AnnualHeatingDemand`, etc. |
| Space ventilation airflows | `Zones > Zone > Rooms > Room` |
| Climate / location | `ClimateLocation` or `ProjectData` section |

---

## Field Dictionary

Maps WUFI-Passive UI labels to their XML element names.

### Ventilation Devices

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Heat recovery efficiency / SRE | `<HeatRecovery>` | Device | fraction (0–1) |
| Moisture recovery efficiency | `<MoistureRecovery>` | Device | fraction (0–1) |
| Humidity recovery efficiency | `<HumidityRecoveryEfficiency>` | Device > PH_Parameters | fraction (0–1) |
| Electric efficiency | `<ElectricEfficiency>` | Device > PH_Parameters | Wh/m³ |
| Quantity | `<Quantity>` | Device > PH_Parameters | count |
| Frost protection required | `<DefrostRequired>` | Device > PH_Parameters | boolean |
| Temperature below which defrost is used | `<TemperatureBelowDefrostUsed>` | Device > PH_Parameters | °C |
| No summer bypass | `<NoSummerBypass>` | Device > PH_Parameters | boolean |
| In conditioned space | `<InConditionedSpace>` | Device > PH_Parameters | boolean |

### Heat Pumps

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| COP at test point 1 | `<RatedCOP1>` | Device > PH_Parameters | dimensionless |
| COP at test point 2 | `<RatedCOP2>` | Device > PH_Parameters | dimensionless |
| Ambient temp at test point 1 | `<AmbientTemperature1>` | Device > PH_Parameters | °C |
| Ambient temp at test point 2 | `<AmbientTemperature2>` | Device > PH_Parameters | °C |
| Annual COP (DHW) | `<AnnualCOP>` | Device > PH_Parameters | dimensionless |
| HPWH Energy Factor | `<HPWH_EF>` | Device > PH_Parameters | dimensionless |

### PV / Renewables

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Array size | `<ArraySizePV>` | Device > PH_Parameters | kW |
| Annual PV energy | `<PhotovoltaicRenewableEnergy>` | Device > PH_Parameters | kWh/yr |
| On-site utilization | `<OnsiteUtilization>` | Device > PH_Parameters | fraction (0–1) |

### Ducts

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Duct length | `<DuctLength>` | Duct | m |
| Insulation thickness | `<InsulationThickness>` | Duct | mm |
| Thermal conductivity of insulation | `<ThermalConductivity>` | Duct | W/mK |
| Duct diameter | `<DuctDiameter>` | Duct | mm |
| Duct shape (round/rectangular) | `<DuctShape>` | Duct | 1=round, 2=rect |
| Duct type (supply/extract) | `<DuctType>` | Duct | 1=supply, 2=extract |
| Reflective insulation | `<IsReflective>` | Duct | boolean |
| Rectangular height | `<DuctShapeHeight>` | Duct | mm |
| Rectangular width | `<DuctShapeWidth>` | Duct | mm |

### Windows — WindowType Definition

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Frame factor (glass fraction) | `<FrameFactor>` | WindowType | fraction (0–1) |
| Window U-value (overall) | `<U_Value>` | WindowType | W/m²K |
| Glazing U-value | `<U_Value_Glazing>` | WindowType | W/m²K |
| g-value / SHGC | `<g_Value>` or `<SHGC_Hemispherical>` | WindowType | fraction (0–1) |
| Frame width (per edge) | `<Frame_Width_{Left,Right,Top,Bottom}>` | WindowType | m |
| Frame U-value (per edge) | `<Frame_U_{Left,Right,Top,Bottom}>` | WindowType | W/m²K |
| Frame psi-install (per edge) | `<Frame_Psi_{Left,Right,Top,Bottom}>` | WindowType | W/mK |
| Glazing psi-spacer (per edge) | `<Glazing_Psi_{Left,Right,Top,Bottom}>` | WindowType | W/mK |

### Windows — Component / Aperture Shading

These fields live on the aperture Component entries in the Zone, NOT on the WindowType.

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Depth of window reveal | `<DepthWindowReveal>` | Component (Type=2) | m |
| Distance from glazing edge to reveal | `<DistanceDaylightOpeningToReveal>` | Component (Type=2) | m |
| Default correction factor (mean month shading) | `<DefaultCorrectionShadingMonth>` | Component (Type=2) | fraction (0–1) |
| Solar protection device assignment | `<IdentNrSolarProtection>` | Component (Type=2) | ID ref (-1=none) |
| Overhang assignment | `<IdentNrOverhang>` | Component (Type=2) | ID ref (-1=none) |
| Window type assignment | `<IdentNrWindowType>` | Component (Type=2) | ID ref |

!!! warning "Shading factors are multiplicative"
    WUFI applies shading from reveal geometry, overhang, solar protection, and the Default correction factor as separate multiplicative factors. The `DefaultCorrectionShadingMonth` should contain only its intended correction — WUFI independently computes reveal-depth shading from `DepthWindowReveal`. What this field represents varies by project; always check the project's methodology documentation.

### Thermal Bridges

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Psi value | `<PsiValue>` | ThermalBridge | W/mK |
| Length | `<Length>` | ThermalBridge | m |
| Type | `<Type>` | ThermalBridge | enum |

### Assemblies

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Layer order | `<Order_Layers>` | Assembly | 2=outside-to-inside |
| Layer thickness | `<Thickness>` | Layer | m |
| Material thermal conductivity | `<ThermalConductivity>` | Material | W/mK |
| Material density | `<BulkDensity>` | Material | kg/m³ |
| Material heat capacity | `<HeatCapacity>` | Material | J/kgK |

### Certification / PassivehouseData

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Annual heating demand target | `<AnnualHeatingDemand>` | PassivehouseData | kWh/m²a |
| Annual cooling demand target | `<AnnualCoolingDemand>` | PassivehouseData | kWh/m²a |
| Peak heating load target | `<PeakHeatingLoad>` | PassivehouseData | W/m² |
| Peak cooling load target | `<PeakCoolingLoad>` | PassivehouseData | W/m² |
| Certification criteria selection | `<PH_CertificateCriteria>` | PassivehouseData | enum |
| Target data selection | `<PH_SelectionTargetData>` | PassivehouseData | enum (2=user) |
| Airtightness (n50 or ACH) | `<EnvelopeAirtightnessCoefficient>` | PH_Building | 1/h |
| Number of units | `<NumberUnits>` | PH_Building | count |
| Number of stories | `<CountStories>` | PH_Building | count |

### Ventilation Spaces (Rooms)

| WUFI UI Label | XML Element | XML Location | Units in XML |
|---|---|---|---|
| Room/space name | `<Name>` | Room | text |
| Floor area | `<AreaRoom>` | Room | m² |
| Clear height | `<ClearRoomHeight>` | Room | m |
| Design supply airflow | `<DesignVolumeFlowRateSupply>` | Room | m³/h |
| Design exhaust airflow | `<DesignVolumeFlowRateExhaust>` | Room | m³/h |
| Ventilation unit assignment | `<IdentNrVentilationUnit>` | Room | ID ref |

---

## Unit Conversions

WUFI-Passive XML stores all values in SI units regardless of the project's display unit system.

### Ventilation

| From (IP) | To (SI/XML) | Factor | Notes |
|---|---|---|---|
| CFM | m³/h | × 1.69901 | `CFM × 1.69901 = m³/h` |
| W/cfm | Wh/m³ | ÷ 1.69901 | `(W/cfm) / 1.69901 = Wh/m³` |

### Thermal Performance

| From (IP) | To (SI/XML) | Factor |
|---|---|---|
| Btu/hr-ft²-F | W/m²K | × 5.6783 |
| W/m²K | Btu/hr-ft²-F | × 0.17611 |
| Btu/hr-ft-F | W/mK (linear, psi) | × 1.7307 |
| W/mK | Btu/hr-ft-F (linear, psi) | × 0.57782 |

### Energy Demand / Load

| From (IP) | To (SI/XML) | Factor |
|---|---|---|
| kBtu/ft²·yr | kWh/m²·yr | × 3.1546 |
| kWh/m²·yr | kBtu/ft²·yr | × 0.31700 |
| Btu/hr·ft² | W/m² | × 3.1546 |
| W/m² | Btu/hr·ft² | × 0.31700 |

### Length / Thickness

| From (IP) | To (SI/XML) | Factor |
|---|---|---|
| inches | meters | × 0.0254 |
| inches | millimeters | × 25.4 |
| feet | meters | × 0.3048 |

Common duct insulation thicknesses: 1" = 25.4 mm, 1.5" = 38.1 mm, 1.875" = 47.625 mm, 2" = 50.8 mm.

### R-value / Conductivity

| From (IP) | To (SI/XML) | Formula |
|---|---|---|
| R/inch (hr-ft²-F/Btu-in) | W/mK | `k = 0.14423 / (R_per_inch)` |
| W/mK | R/inch | `R_per_inch = 0.14423 / k` |

### Temperature

| From (IP) | To (SI/XML) | Formula |
|---|---|---|
| °F | °C | `(°F - 32) / 1.8` |
| ΔF | ΔC | `ΔF / 1.8` |

### Area / Volume

| From (IP) | To (SI/XML) | Factor |
|---|---|---|
| ft² | m² | × 0.09290 |
| ft³ | m³ | × 0.02832 |

### Common Verification Patterns

- **ERV heat recovery**: `<HeatRecovery>0.857</HeatRecovery>` — dimensionless fraction. Compare directly against datasheet SRE/ATRE.
- **ERV electric efficiency**: `<ElectricEfficiency>0.3337</ElectricEfficiency>` (Wh/m³) → `0.3337 × 1.69901 = 0.567 W/cfm`
- **Duct insulation**: `<InsulationThickness>47.625</InsulationThickness>` (mm) = 1.875". `<ThermalConductivity>0.02219</ThermalConductivity>` → R/inch = 0.14423/0.02219 = 6.5
- **Certification target**: `<AnnualHeatingDemand>11.357</AnnualHeatingDemand>` (kWh/m²) → `11.357 × 0.31700 = 3.60 kBtu/ft²`
- **Thermal bridge psi**: `<PsiValue>0.4344</PsiValue>` (W/mK) → `0.4344 / 1.7307 = 0.251 Btu/hr-ft-F`

---

## Key Gotchas

**FrameFactor vs DefaultCorrectionShadingMonth.** `FrameFactor` on the WindowType is the glass-to-total area ratio for thermal calculation. `DefaultCorrectionShadingMonth` on the aperture Component (Type=2) is a separate solar correction factor. Don't confuse them. On some projects, WindowType may have FrameFactor ≈ 1.0 with near-zero frame widths because the U-value was pre-calculated externally.

**ElectricEfficiency is in Wh/m³, not W/cfm.** Divide by 1.69901 to get W/cfm, or multiply W/cfm by 0.58856 to predict the XML value.

**Order_Layers on assemblies matters.** `Order_Layers=2` means layers are listed outside-to-inside. For floor assemblies over ground, "outside" = ground side.

**Airflows are in m³/h, not CFM.** Divide by 1.69901 to convert to CFM.

**Thermal conductivity for ducts is composite.** If duct insulation has multiple layers, the XML stores a single equivalent conductivity.

**PsiValue on thermal bridges is in W/mK.** Divide by 1.7307 to convert to Btu/hr-ft-F.
