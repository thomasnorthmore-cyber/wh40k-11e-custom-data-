#!/usr/bin/env python3
"""Regression: every armed Aeldari model owns selectable weapons and profiles.

This checks catalogue ownership and weapon characteristics, not the exact
presentation New Recruit chooses for its weapon table or source-rule accuracy.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

C="{http://www.battlescribe.net/schema/catalogueSchema}"
G="{http://www.battlescribe.net/schema/gameSystemSchema}"
base=Path(__file__).resolve().parents[1]
cat=ET.parse(base/"Aeldari 11e TEST.cat").getroot()
gst=ET.parse(base/"Warhammer 40,000 11e Custom TEST.gst").getroot()
assert cat.get("gameSystemId")==gst.get("id")
units=cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(units)==17,f"Expected 17 units, got {len(units)}"
unit_ids={u.get("id") for u in units}
assert len(unit_ids)==17,"Duplicate unit IDs"
seen_profiles=set()
nmodels=0
owned=0
for unit in units:
 uid=unit.get("id")
 assert unit.get("type")=="unit"
 roots=unit.findall("./"+C+"profiles/"+C+"profile")
 stats=[p for p in roots if p.get("typeName")=="Units"]
 assert stats,f"{uid}: missing model characteristics"
 detached=[p for p in roots if p.get("typeName") in ("Ranged Weapons","Melee Weapons")]
 assert not detached,f"{uid}: detached weapon profiles {[p.get('name') for p in detached]}"
 models=[e for e in unit.iter(C+"selectionEntry") if e.get("type")=="model"]
 assert models,f"{uid}: no selectable models"
 for model in models:
  nmodels+=1
  weapons=[p for p in model.iter(C+"profile") if p.get("typeName") in ("Ranged Weapons","Melee Weapons")]
  if uid=="smoke-unit-2459":
   assert not weapons,"Webway Gate must not receive invented weapons"
   continue
  ranged=[p for p in weapons if p.get("typeName")=="Ranged Weapons"]
  melee=[p for p in weapons if p.get("typeName")=="Melee Weapons"]
  assert ranged,f"{uid}/{model.get('name')}: no ranged weapon equipment"
  assert melee,f"{uid}/{model.get('name')}: no melee weapon equipment"
  for p in weapons:
   pid=p.get("id")
   assert pid not in seen_profiles,f"Duplicate weapon profile ID: {pid}"
   seen_profiles.add(pid)
   assert p.get("hidden")=="false",f"{uid}: equipped {pid} is hidden"
   assert p.find("./"+C+"modifiers") is None,f"{uid}: owned weapon {pid} has detached visibility modifiers"
   vals={x.get("name"):(x.text or "").strip() for x in p.findall("./"+C+"characteristics/"+C+"characteristic")}
   expected={"Range","A","S","AP","D","BS" if p.get("typeName")=="Ranged Weapons" else "WS"}
   assert expected <= vals.keys(),f"{uid}: incomplete weapon characteristics {pid}"
   assert all(vals[x] for x in expected),f"{uid}: blank weapon characteristic {pid}"
   owned+=1
# Ensure the two War Walker choices retain their preferred quantity interface.
walker=next(u for u in units if u.get("id")=="smoke-unit-612")
wmodel=next(m for m in walker.iter(C+"selectionEntry") if m.get("id")=="smoke-612-model-0")
limits={c.get("type"):int(c.get("value")) for c in wmodel.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":1,"max":2},"War Walkers reverted to checkboxes"
wg=next(g for g in wmodel.iter(C+"selectionEntryGroup") if g.get("id")=="mul-612-mounts")
limits={c.get("type"):int(c.get("value")) for c in wg.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":2,"max":2},"War Walker requires two heavy weapons per model"
# Ensure multi-model Windriders and Vypers choose equipment within their model.
for uid,modelid,groups in (
 ("smoke-unit-591","smoke-591-model-0",["mul-591-bike"]),
 ("smoke-unit-605","smoke-605-model-0",["mul-605-main","mul-605-secondary"]),
):
 unit=next(u for u in units if u.get("id")==uid)
 model=next(m for m in unit.iter(C+"selectionEntry") if m.get("id")==modelid)
 local={g.get("id"):g for g in model.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")}
 assert set(groups)<=set(local),f"{uid}: squad-level weapon pool remains"
 for key in groups:
  limits={c.get("type"):int(c.get("value")) for c in local[key].findall("./"+C+"constraints/"+C+"constraint")}
  assert limits=={"min":1,"max":1},f"{uid}/{key}: each model must select exactly one"
print(f"PASS: {len(units)} units, {nmodels} model types, {owned} owned weapon profiles, War Walker numeric selector")
