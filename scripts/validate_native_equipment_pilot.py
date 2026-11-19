#!/usr/bin/env python3
"""Pilot: weapon profiles belong to selected equipment, not detached unit profiles.

This validates catalogue structure. New Recruit UI/import tests still required.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter

C="{http://www.battlescribe.net/schema/catalogueSchema}"
G="{http://www.battlescribe.net/schema/gameSystemSchema}"
base=Path(__file__).resolve().parents[1]
cat=ET.parse(base/"Aeldari 11e TEST.cat").getroot()
gst=ET.parse(base/"Warhammer 40,000 11e Custom TEST.gst").getroot()
assert cat.get("gameSystemId")==gst.get("id")
units={u.get("id"):u for u in cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
expected={
 "smoke-unit-591":{
   "mul-591-bike-catapult":1,"mul-591-bike-scatter":1,
   "mul-591-bike-shuriken":1,"smoke-591-equipment-0-1":1},
 "smoke-unit-612":{
   "mul-612-mounts-shuriken":1,"mul-612-mounts-missile":2,
   "mul-612-mounts-bright":1,"mul-612-mounts-scatter":1,
   "mul-612-mounts-star":1,"smoke-612-equipment-0-2":1},
 "smoke-unit-613":{
   "wl-arms-catapult":1,"wl-arms-flamer":1,
   "wl-heavy-missile":2,"wl-heavy-bright":1,"wl-heavy-scatter":1,
   "wl-heavy-shuriken":1,"wl-heavy-star":1,
   "wl-wargear-ghost":2,"smoke-613-equipment-0-2":1},
}
all_profile_ids=[]
for unit in units.values():
 for p in unit.iter(C+"profile"):
  all_profile_ids.append(p.get("id"))
assert len(all_profile_ids)==len(set(all_profile_ids)), "Repeated profile ID across Aeldari catalogue"
for uid, choices in expected.items():
 unit=units[uid]
 options={e.get("id"):e for e in unit.iter(C+"selectionEntry")}
 root_weapons=[p for p in unit.findall("./"+C+"profiles/"+C+"profile") if p.get("typeName") in ("Ranged Weapons","Melee Weapons")]
 assert not root_weapons, f"{uid}: detached unit-level weapon profile(s) remain"
 for id, number in choices.items():
  assert id in options, f"{uid}: missing equipment {id}"
  profiles=options[id].findall("./"+C+"profiles/"+C+"profile")
  assert len(profiles)==number, f"{uid}: {id} expected {number} equipped profiles, got {len(profiles)}"
  for p in profiles:
   assert p.get("hidden")=="false", f"{uid}: equipped {id} profile hidden"
   assert p.find("./"+C+"modifiers") is None, f"{uid}: obsolete detached trigger on {id}"
   assert p.get("typeName") in ("Ranged Weapons","Melee Weapons"),f"{uid}: wrong weapon type"
 w=unit.find("./"+C+"costs/"+C+"cost")
 assert w is not None and float(w.get("value"))>=0
# Preserve all legal model and equipment selection constraints from baseline.
for uid,model_id,low,high in (
 ("smoke-unit-591","smoke-591-model-0",3,6),
 ("smoke-unit-612","smoke-612-model-0",1,2),
 ("smoke-unit-613","smoke-613-model-0",1,1)):
 m=next(x for x in units[uid].iter(C+"selectionEntry") if x.get("id")==model_id)
 limits={c.get("type"):int(c.get("value")) for c in m.findall("./"+C+"constraints/"+C+"constraint")}
 assert limits=={"min":low,"max":high}, (uid,limits)
walker=units["smoke-unit-612"]
mount=next(g for g in walker.iter(C+"selectionEntryGroup") if g.get("id")=="mul-612-mounts")
assert {c.get("type"):int(c.get("value")) for c in mount.findall("./"+C+"constraints/"+C+"constraint")}=={"min":2,"max":2}
wraith=units["smoke-unit-613"]
for gid,lo,hi in (("wl-group-arms",2,2),("wl-group-heavy",0,2),("wl-group-wargear",0,1)):
 g=next(g for g in wraith.iter(C+"selectionEntryGroup") if g.get("id")==gid)
 assert {c.get("type"):int(c.get("value")) for c in g.findall("./"+C+"constraints/"+C+"constraint")}=={"min":lo,"max":hi}
wind=units["smoke-unit-591"]
bike=next(g for g in wind.iter(C+"selectionEntryGroup") if g.get("id")=="mul-591-bike")
assert {c.get("type"):int(c.get("value")) for c in bike.findall("./"+C+"constraints/"+C+"constraint")}=={"min":3,"max":3}
print("PASS: 3 pilot units have native equipment-owned profiles, preserved size/equipment limits, and unique weapon IDs")
