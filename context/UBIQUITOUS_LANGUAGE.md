# Ubiquitous Language

Domain vocabulary for PHX. Terms are the words we use when *talking* about the domain;
class names appear only where the class *is* the domain concept. Where the code's name and
the domain's name disagree, the "Aliases to avoid" column names the loser and the
[Flagged ambiguities](#flagged-ambiguities) section says why.

---

## Translation pipeline

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **PHX Model** | The transient, in-memory object graph that sits between a source format and a target format, rooted at a **Project**. | model, energy model, PHX file, intermediate model |
| **Source Format** | A file or live object graph a **PHX Model** is built *from* (HBJSON, live Honeybee model, WUFI XML). | input format, upstream model |
| **Target Format** | A file a **PHX Model** is written *to* (WUFI XML, PHPP workbook, PPP, METr JSON). | output format, destination |
| **Importer** | A `from_*` package that builds a **PHX Model** from a **Source Format**. | parser, loader, converter |
| **Exporter** | A `to_*` package (or the PHPP write path) that writes a **PHX Model** to a **Target Format**. | writer, serializer, dumper |
| **Reader** | A `from_*` package that extracts data from a source *without* building a **PHX Model** (today: `from_PHPP`, which yields a `ResultsRecord`). | importer, scraper |
| **Conversion** | One end-to-end **Source Format** → **PHX Model** transformation. | import, translation, parse |
| **Refusal** | A typed, explanatory "I will not read this" returned by a **Reader** instead of a partial or guessed result. | error, exception, failure |

---

## Project structure

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **Project** | The top-level container for one building job: type libraries, utilization patterns, project data, and one or more **Variants**. | model, file, job |
| **Variant** | One certifiable building entity within a **Project**, derived from a Honeybee `ph_bldg_segment`, owning its own building, site, certification data, and mechanical systems. | design option, scheme, alternative, scenario |
| **Building** | The geometry container inside a **Variant**: the flat list of **Components** plus the list of **Zones**. | envelope, massing |
| **Zone** | A thermal zone: the boundary at which loads, thermal bridges, and electrical equipment are aggregated. | room, space, segment, thermal block |
| **Space** | A conditioned room or sub-room inside a **Zone**, carrying its own ventilation, occupancy, and lighting **Programs**. | room, zone, subzone |
| **Dwelling** | A residential unit; a grouping of Honeybee Rooms whose occupancy is normalized as a whole. | unit, apartment, `Room.zone` |
| **Site** | A **Variant's** location, climate, ground, and energy-factor data. | location, weather |

---

## Envelope

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **Component** | An opaque envelope surface (wall, floor, roof) carrying geometry, an **Assembly** reference, and its **Apertures**. | face, surface, element, certified component |
| **Aperture** | A window or door opening hosted by a **Component** and typed by a **Window Type**. | window, glazing, opening |
| **Aperture Element** | One individually-framed sash or lite within an **Aperture**, carrying its own polygon and resolved per-edge **Psi-Install** values. | pane, unit, sub-window |
| **Assembly** | A reusable opaque construction (ordered **Layers** yielding a U-value) held in the **Project** library and referenced by **Components**. | construction, buildup, type |
| **Layer** | One thickness of an **Assembly**, holding a single **Material** or a **Division Grid** of them. | course, ply |
| **Declared-U Assembly** | An **Assembly** stated as a U-value and a thickness rather than as real **Layers**, as designPH's user-defined library and PHI-certified construction systems do. Sources encode one as a no-mass **Material** between two thin conductive shells; PHX collapses that back to a single **Layer** when the source marks it. | declared assembly, SD construction, U-value assembly |
| **Division Grid** | The cell matrix that makes a **Layer** heterogeneous (e.g. studs plus insulation). | mixed layer, composite |
| **Material** | A named conductivity/density/capacity record used by a **Layer**. | product, substance |
| **Heat Flow Pathway** | One parallel path through a composite **Assembly**, per ISO 6946, used to compute an area-weighted R-value. | flow path, thermal path |
| **Thermal Bridge** | A named linear or point heat-loss element with a psi/chi value, owned by a **Zone**. | TB, junction, detail |
| **Window Type** | A reusable glazing-plus-frame construction in the **Project** library, referenced by **Apertures**. | window construction, glazing type |
| **Psi-Install** | The linear installation heat loss at one edge of an **Aperture Element**, resolved from the aperture's Install Type over the **Window Type** default. | install psi, frame psi, Ψ |
| **Shade Type** | A reusable window-shading device definition in the **Project** library. | shading, blind |

---

## Loads and operation

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **Program** | The pairing of one **Load** with one **Utilization Pattern** for a **Space**, in ventilation, occupancy, or lighting. | profile, setting, schedule |
| **Load** | The numeric magnitude half of a **Program** (airflow, people per area, watts). Per-instance and never shared between **Programs**. | rate, value, demand |
| **Utilization Pattern** | The time half of a **Program**: operating periods and hours, registered on the **Project** and referenced by number. | schedule, profile, pattern |
| **EFLH** | Equivalent full-load hours: annual operating-window hours scaled by relative utilization, clamped 0-8760. Used for lighting; not the operating window itself. | operating hours, run hours |
| **Occupancy Channel** | One of the two mutually exclusive routes occupancy reaches a **Target Format**: explicit Passive House occupancy on the **Zone**, or derived Honeybee People load on the **Space**. | occupancy source, people count |
| **Ventilation Room** | The aspect of a **Space** that carries supply/extract airflow and resolves to a **Ventilator**. | space, room, zone |
| **Utilization Zone** | The aspect of a **Space** that carries person and lighting loads; may exist with zero airflow. | space, load zone |

---

## Mechanical systems

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **Mechanical System Collection** | A **Variant's** grouping of **Devices**, ducting, and piping that together serve some share of the building. | system, HVAC, plant |
| **Device** | One piece of modeled equipment (ventilator, heater, heat pump, tank, PV array, elevator). | unit, equipment, machine |
| **Ventilator** | A balanced mechanical ventilation **Device** with heat or energy recovery. | ERV, HRV, vent unit, air handler |
| **Ventilation Assignment** | The resolved link from a **Space** to exactly one **Ventilator** in its **Variant**; absent (`None`) when unassigned. | vent unit ID, ERV ID, hookup |
| **Usage Profile** | The share of each end use (heating, cooling, DHW, ventilation) a **Device** covers. | coverage, allocation |
| **Zone Coverage** | The share of each **Zone** a **Mechanical System Collection** serves. | coverage, distribution |
| **Trunk / Branch / Fixture** | The three levels of DHW distribution piping, fixture being the leaf that owns **Pipe Segments**. | main / riser / run-out |
| **Recirculation Piping** | DHW loop piping stored flat, outside the trunk/branch/fixture hierarchy. | recirc loop, return line |
| **Supportive Device** | An auxiliary consumer (pump, fan, control) attached to a **Mechanical System Collection**. | accessory, aux |

---

## Identity and merging

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **Identifier** | The UUID-or-string key used for lookup and deduplication within a **Project** library. | ID, key, name |
| **ID Number** | The integer a **Target Format** uses to cross-reference an object in the written file. | ID, index, number |
| **Identity Scope** | The **Project**-owned context that allocates **ID Numbers** in per-domain namespaces, making concurrent conversions independent. | counter, ID space |
| **Claim** | A reservation of a specific **ID Number** imported from a source file, so later allocation cannot collide with it. | reserved ID, fixed ID |
| **Unique Key** | The value two objects must share to be eligible for **Merging**. | hash, group key, signature |
| **Merge** | Combining two objects that share a **Unique Key** into one, summing or area/length-weighting their quantities. | add, consolidate, collapse, join |
| **Dangling Reference** | An **ID Number** written to a **Target Format** that resolves to nothing in that file. | broken link, orphan |

---

## External formats and standards

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **PHPP** | PHI's Excel workbook, and the only accepted tool for PHI certification. | the spreadsheet, Excel |
| **WUFI-Passive** | The Phius desktop calculation tool whose XML PHX reads and writes. | WUFI, the XML |
| **METr** | Phius's browser-based successor to WUFI-Passive; its model file is JSON. | Cinch, the JSON |
| **PPP** | The designPH project file PHX writes for hand-off into **PHPP**. | designPH file |
| **HBJSON** | The serialized Honeybee model, carrying honeybee-ph extensions, that PHX usually reads. | JSON, the Honeybee file |
| **PHI** | The Passive House Institute standard family, certified through **PHPP**. | Passive House, international PH |
| **Phius** | The North American standard family, certified through **WUFI-Passive** or **METr**. | PHIUS+, US Passive House |

---

## Verification vocabulary

| Term | Definition | Aliases to avoid |
| ---- | ---------- | ---------------- |
| **Reference Case** | A stored HBJSON-plus-expected-output pair asserted byte-for-byte by the export tests. | fixture, sample, golden file |
| **Golden State** | The recorded set of exact PHPP cell writes the Excel write path must reproduce. | snapshot, baseline |
| **Legacy Counter** | The pre-**Identity Scope** class-level `_count` fallback used only by standalone constructors. | class counter, global ID |

---

## Relationships

- A **Project** owns one or more **Variants**, and exactly one library each of **Assemblies**, **Window Types**, **Shade Types**, and **Utilization Patterns**.
- A **Variant** owns one **Building**, one **Site**, its certification data, and zero or more **Mechanical System Collections**.
- A **Building** holds a flat list of **Components** and a list of **Zones**; a **Component** is not owned by a **Zone**.
- A **Component** references exactly one **Assembly** by **Identifier** and hosts zero or more **Apertures**.
- An **Aperture** references exactly one **Window Type** and holds one or more **Aperture Elements**; each element resolves four **Psi-Install** values.
- A **Zone** holds one or more **Spaces**, its **Thermal Bridges**, and its electrical equipment.
- A **Space** holds exactly one ventilation, one occupancy, and one lighting **Program**, and has at most one **Ventilation Assignment**.
- A **Program** owns its **Load** outright and *shares* its **Utilization Pattern** with the **Project**.
- Two **Spaces** merge only when their **Unique Key** matches, which for a **Space** means the same WUFI type and the same **Ventilation Assignment**.
- A **Mechanical System Collection** serves **Zones** through **Zone Coverage** and end uses through each **Device's Usage Profile**.

---

## Example dialogue

> **Dev:** "The export doubles the airflow when I run it twice. Isn't the **Space** merge supposed to produce a new object?"

> **Domain expert:** "It does produce a new **Space**. The bug was one level down: the merged **Space** took a *reference* to the first source **Space's** ventilation **Program**, then wrote the summed **Load** through it. That write landed back in the source graph."

> **Dev:** "So the fix is to deep-copy the **Program**?"

> **Domain expert:** "No. A **Program** is a **Load** plus a **Utilization Pattern**, and the two halves need opposite treatment. The **Load** must be fresh, because it is per-instance. The **Utilization Pattern** must stay the *same object*, because it is registered on the **Project** and the **Exporters** reference it by **ID Number**. Copy it and you write a **Dangling Reference**."

> **Dev:** "And the merge only fires for **Spaces** on the same **Ventilator**?"

> **Domain expert:** "Same **Unique Key**, which for a **Space** is the WUFI type plus the **Ventilation Assignment**. Say 'same **Ventilation Assignment**', not 'same ERV' — the flag is named for ERVs but the model just has a **Ventilator**, and an unassigned **Space** has no assignment at all rather than a zero."

---

## Flagged ambiguities

- **"Room", "Zone", and "Space" are three words for two-and-a-half concepts.** A Honeybee `Room` becomes a **Zone** when Rooms are grouped by building segment, *and* becomes one or more **Spaces** inside it. Use **Room** only for the Honeybee-side object, **Zone** for the thermal aggregation boundary, **Space** for the PHX room. Never say "room" about a `PhxSpace`.

- **"Space" itself is overloaded, and this is a known open defect.** `PhxSpace` conflates a **Ventilation Room** (has airflow, resolves to a **Ventilator**) with a **Utilization Zone** (has person/lighting loads, may have zero airflow). A WUFI file can contain the second without the first, which is why the importer's pairing is a heuristic. Name which aspect you mean when the distinction matters.

- **"Assembly" vs "Construction".** The class is `PhxConstructionOpaque`, the **Project** dict is `assembly_types`, and the **Component** field is `.assembly`. Canonical domain term is **Assembly**; "construction" is a class-name artifact. Do not introduce a third word ("buildup", "type").

- **"Variant" does not mean design option.** It is one building segment within a **Project**, not an alternative scheme. When comparing schemes, say "scheme" or "option" and expect them to live in *separate* **Projects**.

- **"Component" collides with the industry meaning.** In PHI/Phius usage a "certified component" is a window or ventilator product. In PHX a **Component** is an opaque envelope surface. `PhxComponentThermalBridge` is the exception that muddies this: a **Thermal Bridge** is not a surface, so call it a **Thermal Bridge**, never "a component".

- **"ERV", "HRV", "vent unit", and "ventilator" all point at one object.** The CLI flag is `merge_spaces_by_erv`, the field is `vent_unit_id_num`, the class is `PhxDeviceVentilator`. Use **Ventilator** for the device and **Ventilation Assignment** for the link. Reserve "ERV"/"HRV" for the recovery type when that specifically matters.

- **"Model" is the single most overloaded word here.** It means the Honeybee model, the **PHX Model**, the WUFI-Passive file, the PHPP workbook, or the practitioner's whole energy model depending on the sentence. Always qualify it, and prefer **Project** when you mean the PHX object graph.

- **"Importer" vs "Reader".** `from_PHPP` reads a closed workbook and returns a results record; it builds no **PHX Model**, so it is a **Reader**, not an **Importer**. Calling it an importer implies a round-trip that does not exist.

- **"Schedule" vs "utilization pattern".** The classes say `PhxSchedule*`, WUFI and the **Project** collections say utilization pattern. Prefer **Utilization Pattern** in prose, because the project-registered, referenced-by-**ID Number** nature is exactly what "schedule" hides.

- **"ID" is three different things.** **Identifier** (UUID/string, for lookup and dedup), **ID Number** (integer, for file cross-reference), and **Unique Key** (merge eligibility). Bare "ID" in a comment or a commit message is always ambiguous.

- **"Merge" vs "add" vs "consolidate".** The mechanism is `__add__`, the cleanup step is called consolidation, the effect is a merge. Use **Merge** as the domain verb and keep `__add__` as an implementation detail.
