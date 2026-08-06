"""S8 - the common single-family case: many rooms, ONE dwelling, people on bedrooms only."""
import importlib.util, sys, types, io, contextlib

stub = types.ModuleType("ph_gh_component_io"); stub.gh_io = types.SimpleNamespace(IGH=object)
sys.modules["ph_gh_component_io"] = stub
_p = "/Users/em/Dropbox/bldgtyp-00/00_PH_Tools/honeybee_grasshopper_ph/honeybee_ph_rhino/gh_compo_io/program/set_res_occupancy.py"
_s = importlib.util.spec_from_file_location("sro", _p); sro = importlib.util.module_from_spec(_s); _s.loader.exec_module(sro)

from honeybee.room import Room
from honeybee_energy.lib.programtypes import program_type_by_identifier
from honeybee_energy_ph.properties.load.people import PhDwellings
from honeybee_energy_ph.dwellings import get_dwelling_obj
from ladybug_geometry.geometry3d.pointvector import Point3D
from PHX.from_HBJSON import cleanup


class FakeIGH:
    def get_rhino_areas_unit_name(self): return "M2"
    def warning(self, m): print("   ! warn:", m)


def make_room(name, w, d, x):
    r = Room.from_box(name, w, d, 2.6, origin=Point3D(x, 0, 0))
    r.properties.energy.program_type = program_type_by_identifier("2019::MidriseApartment::Apartment")
    r.properties.energy.people = r.properties.energy.people.duplicate()
    return r


# -- a 3-bed single-family house, six HB-Rooms, ONE dwelling
specs = [("BED_1", 4, 4), ("BED_2", 3.5, 4), ("BED_3", 3.5, 3.5),
         ("LIVING", 6, 5), ("KITCHEN", 4, 3.5), ("BATH", 2.5, 2.5)]
rooms, x = [], 0.0
for n, w, d in specs:
    rooms.append(make_room(n, w, d, x)); x += w + 2

# -- "HBPH - Set Dwelling": all six rooms share ONE PhDwellings instance
dwelling = PhDwellings(_num_dwellings=1)
for r in rooms:
    r.properties.energy.people.properties.ph.dwellings = dwelling

# -- "HBPH - Set Occupancy": people + bedrooms on the BEDROOMS only
num_people   = [2.0, 1.0, 1.0, 0.0, 0.0, 0.0]   # 4 occupants total
num_bedrooms = [1,   1,   1,   0,   0,   0]     # 3 bedrooms
with contextlib.redirect_stdout(io.StringIO()):
    sro.set_ph_res_occ_schedule(rooms)
    sro.set_number_of_bedrooms(rooms, num_bedrooms)
    sro.set_number_of_people(rooms, num_people)
    sro.set_people_per_m2(rooms, FakeIGH())


def group_key(r):
    d = get_dwelling_obj(r)
    return ("dwelling", d.identifier) if d else ("untagged", r.identifier)


totals = {}
for r in rooms:
    totals[group_key(r)] = totals.get(group_key(r), 0.0) + r.properties.energy.people.properties.ph.number_people

print("=" * 96)
print("S8  SINGLE-FAMILY: 6 HB-Rooms, ONE PhDwelling, occupancy on bedrooms only")
print("=" * 96)
print(f"{'room':10s} {'fa m2':>7s} {'n_ppl':>6s} {'n_bed':>6s} {'grp_tot':>8s} {'ppl/m2':>9s} "
      f"{'GateA(room)':>12s} {'GateB(group)':>13s}")
a_tot = b_tot = 0.0
for r in rooms:
    ppl = r.properties.energy.people; pph = ppl.properties.ph
    a = ppl.people_per_area * r.floor_area if not pph.number_people else 0.0
    b = ppl.people_per_area * r.floor_area if not totals[group_key(r)] else 0.0
    a_tot += a; b_tot += b
    print(f"{r.display_name:10s} {r.floor_area:7.2f} {pph.number_people:6} {pph.number_bedrooms:6} "
          f"{totals[group_key(r)]:8} {ppl.people_per_area:9.5f} {a:12.2f} {b:13.2f}")

print("-" * 96)
merged = cleanup.merge_occupancies(rooms)
mp = merged.properties.ph
print(f"CHANNEL A (merge_occupancies -> PhxZone.res_occupant_quantity):")
print(f"   number_people   = {mp.number_people}      <- expect 4.0")
print(f"   number_bedrooms = {mp.number_bedrooms}        <- expect 3")
print(f"   num_dwellings   = {mp.number_dwelling_units}        <- expect 1")
print(f"   merged ppl/m2   = {merged.people_per_area:.5f}")
print(f"CHANNEL B (per-space NumberOccupants):")
print(f"   Gate A (per-room)  = {a_tot:6.2f}   <- LEAK: phantom occupants")
print(f"   Gate B (per-group) = {b_tot:6.2f}   <- correct")
occ_sched = rooms[0].properties.energy.people.occupancy_schedule
from statistics import mean
print(f"\n   PH occ schedule '{occ_sched.display_name}' mean = {mean(occ_sched.values()):.4f}")
print(f"   peak equivalent of 4 avg occupants = {4/mean(occ_sched.values()):.2f}")
