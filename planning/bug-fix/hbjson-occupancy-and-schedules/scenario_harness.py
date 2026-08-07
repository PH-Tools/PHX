"""Confirm the Option-3 gate against every realistic room/dwelling configuration.

Loads the REAL GH component logic (set_number_of_people / set_people_per_m2) so the
people_per_area sync behaviour is the production one, not a re-implementation.
"""
import importlib.util, sys, types

# -- stub the Rhino-only IO shim (only used in type comments)
stub = types.ModuleType("ph_gh_component_io"); stub.gh_io = types.SimpleNamespace(IGH=object)
sys.modules["ph_gh_component_io"] = stub

_p = "/Users/em/Dropbox/bldgtyp-00/00_PH_Tools/honeybee_grasshopper_ph/honeybee_ph_rhino/gh_compo_io/program/set_res_occupancy.py"
_spec = importlib.util.spec_from_file_location("sro", _p)
sro = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sro)

from honeybee.room import Room
from honeybee_energy.lib.programtypes import program_type_by_identifier
from honeybee_energy_ph.properties.load.people import PhDwellings


class FakeIGH:
    def get_rhino_areas_unit_name(self): return "M2"
    def warning(self, m): print("   ! warn:", m)


def make_room(name, program="2019::SmallOffice::OpenOffice", w=10.0, d=10.0, origin_x=0.0):
    r = Room.from_box(name, w, d, 3.0, origin=__import__("ladybug_geometry.geometry3d.pointvector", fromlist=["Point3D"]).Point3D(origin_x, 0, 0))
    r.properties.energy.program_type = program_type_by_identifier(program)
    r.properties.energy.people = r.properties.energy.people.duplicate()
    return r


def tag_dwelling(rooms, num_dwellings=1):
    """Emulate 'HBPH - Set Dwelling': all rooms share ONE PhDwellings instance."""
    d = PhDwellings(_num_dwellings=num_dwellings)
    for r in rooms:
        r.properties.energy.people.properties.ph.dwellings = d


def gate(hbe_occ):
    """Option 3: explicit PH occupancy wins; otherwise derive from the HB load."""
    return not hbe_occ.properties.ph.number_people


def report(title, rooms, ran_component, num_people=None):
    print("\n" + "-" * 94)
    print(title)
    if ran_component:
        sro.set_number_of_people(rooms, num_people)
        sro.set_people_per_m2(rooms, FakeIGH())
    total_zone = sum(r.properties.energy.people.properties.ph.number_people for r in rooms)
    total_space = 0.0
    for r in rooms:
        ppl = r.properties.energy.people
        pph = ppl.properties.ph
        use = gate(ppl)
        peak = ppl.people_per_area * r.floor_area if use else 0.0
        total_space += peak
        print(f"   {r.display_name:14s} n_ppl={pph.number_people:<5} dwell_tag={'yes' if pph.number_dwelling_units else 'no ':3s} "
              f"ppl/m2={ppl.people_per_area:.5f}  gate={'HB-fallback' if use else 'skip(explicit)':14s} space_peak={peak:6.2f}")
    print(f"   => zone-level (Channel A) = {total_zone:.2f} people | per-space (Channel B) = {total_space:.2f} people")


# ---------------------------------------------------------------------------
# S1 - Non-residential. No dwelling tag, Set Occupancy never run.
report("S1  NON-RES office: no dwelling tag, Set Occupancy never run",
       [make_room("OFFICE_01"), make_room("OFFICE_02", origin_x=20)], ran_component=False)

# S2 - Residential, one room per apartment, occupancy set.
rooms = [make_room("APT_A"), make_room("APT_B", origin_x=20)]
tag_dwelling([rooms[0]]); tag_dwelling([rooms[1]])
report("S2  RES: 1 room per apartment, Set Dwelling then Set Occupancy [2, 3]",
       rooms, ran_component=True, num_people=[2.0, 3.0])

# S3 - Residential + hallway, hallway explicitly 0, hallway NOT in the dwelling.
rooms = [make_room("APT_A"), make_room("HALL", origin_x=20)]
tag_dwelling([rooms[0]])
report("S3  RES: apartment (dwelling) + untagged hallway, Set Occupancy [4, 0]",
       rooms, ran_component=True, num_people=[4.0, 0.0])

# S4 - THE LEAK: multi-room dwelling, people on one room only.
rooms = [make_room("APT_LIVING"), make_room("APT_BED", origin_x=20), make_room("APT_HALL", origin_x=40)]
tag_dwelling(rooms)  # all three share ONE dwelling
report("S4  RES: ONE apartment spanning 3 rooms, Set Occupancy [4, 0, 0]  <-- the leak",
       rooms, ran_component=True, num_people=[4.0, 0.0, 0.0])

# S5 - Same dwelling, but occupancy distributed across the rooms.
rooms = [make_room("APT_LIVING"), make_room("APT_BED", origin_x=20), make_room("APT_HALL", origin_x=40)]
tag_dwelling(rooms)
report("S5  RES: same 3-room apartment, Set Occupancy [2, 1, 1] (distributed)",
       rooms, ran_component=True, num_people=[2.0, 1.0, 1.0])

# S6 - Residential model, dwellings tagged but Set Occupancy NEVER run.
rooms = [make_room("APT_A"), make_room("APT_B", origin_x=20)]
tag_dwelling([rooms[0]]); tag_dwelling([rooms[1]])
report("S6  RES: dwellings tagged, Set Occupancy NEVER run",
       rooms, ran_component=False)

# S7 - Mixed-use: apartments + ground-floor retail on a stock HB program.
rooms = [make_room("APT_A"), make_room("RETAIL", origin_x=20)]
tag_dwelling([rooms[0]])
report("S7  MIXED: apartment (dwelling) + retail (stock HB program), Set Occupancy [4, 0]",
       rooms, ran_component=True, num_people=[4.0, 0.0])


# ===========================================================================
# GATE B: per DWELLING-GROUP instead of per ROOM.
# Skip the HB fallback if ANY room in the room's dwelling group has explicit people.
# ===========================================================================
print("\n\n" + "=" * 94)
print("GATE B  --  per dwelling-group")
print("=" * 94)


def _group_key(r):
    """Untagged rooms are their own group (PhDwellings.default() is a shared singleton)."""
    pph = r.properties.energy.people.properties.ph
    if pph.dwellings.identifier == PhDwellings.default().identifier:
        return ("untagged", r.identifier)
    return ("dwelling", pph.dwellings.identifier)


def build_group_totals(rooms):
    totals = {}
    for r in rooms:
        k = _group_key(r)
        totals[k] = totals.get(k, 0.0) + r.properties.energy.people.properties.ph.number_people
    return totals


def report_b(title, rooms, ran_component, num_people=None):
    print("\n" + "-" * 94)
    print(title)
    if ran_component:
        sro.set_number_of_people(rooms, num_people)
        sro.set_people_per_m2(rooms, FakeIGH())
    totals = build_group_totals(rooms)
    zone = sum(r.properties.energy.people.properties.ph.number_people for r in rooms)
    space = 0.0
    for r in rooms:
        ppl = r.properties.energy.people
        use = not totals[_group_key(r)]
        peak = ppl.people_per_area * r.floor_area if use else 0.0
        space += peak
        print(f"   {r.display_name:14s} n_ppl={ppl.properties.ph.number_people:<5} "
              f"grp_total={totals[_group_key(r)]:<5} ppl/m2={ppl.people_per_area:.5f}  "
              f"gate={'HB-fallback' if use else 'skip(explicit)':14s} space_peak={peak:6.2f}")
    print(f"   => zone (A) = {zone:.2f} | per-space (B) = {space:.2f}")


import io, contextlib
def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        fn(*a, **k)
    return buf.getvalue()

r = [make_room("OFFICE_01"), make_room("OFFICE_02", origin_x=20)]
report_b("S1  NON-RES office: no tag, never ran Set Occupancy", r, False)

r = [make_room("APT_A"), make_room("APT_B", origin_x=20)]
tag_dwelling([r[0]]); tag_dwelling([r[1]])
report_b("S2  RES: 1 room per apartment [2, 3]", r, True, [2.0, 3.0])

r = [make_room("APT_A"), make_room("HALL", origin_x=20)]
tag_dwelling([r[0]])
report_b("S3  RES: apartment + untagged hallway [4, 0]", r, True, [4.0, 0.0])

r = [make_room("APT_LIVING"), make_room("APT_BED", origin_x=20), make_room("APT_HALL", origin_x=40)]
tag_dwelling(r)
report_b("S4  RES: ONE apartment over 3 rooms [4, 0, 0]   <-- was the leak", r, True, [4.0, 0.0, 0.0])

r = [make_room("APT_LIVING"), make_room("APT_BED", origin_x=20), make_room("APT_HALL", origin_x=40)]
tag_dwelling(r)
report_b("S5  RES: same apartment, distributed [2, 1, 1]", r, True, [2.0, 1.0, 1.0])

r = [make_room("APT_A"), make_room("APT_B", origin_x=20)]
tag_dwelling([r[0]]); tag_dwelling([r[1]])
report_b("S6  RES: dwellings tagged, Set Occupancy NEVER run", r, False)

r = [make_room("APT_A"), make_room("RETAIL", origin_x=20)]
tag_dwelling([r[0]])
report_b("S7  MIXED: apartment + retail [4, 0]", r, True, [4.0, 0.0])
