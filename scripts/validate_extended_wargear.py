#!/usr/bin/env python3
"""Check CSV-derived optional wargear across all Aeldari category-test examples."""
from pathlib import Path
import xml.etree.ElementTree as ET

C="{http://www.battlescribe.net/schema/catalogueSchema}"
cat=ET.parse(Path(__file__).resolve().parents[1]/"Aeldari 11e TEST.cat").getroot()
units={x.get("id"):x for x in cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
specs={
 "582":[("staff",1,1,2)],"583":[("staff",1,1,2)],
 "591":[("bike",3,3,3)],
 "605":[("main",1,1,3),("secondary",1,1,2)],
 "589":[("platform",1,1,5)],
 "603":[("wings",1,1,2)],
 "621":[("secondary",1,1,5)],
 "599":[("turret",1,1,5),("under",1,1,2)],
}
variable = {
 "591":{"model":(3,6),"cost":(80,170),"ratio":{"bike":1}},
 "605":{"model":(1,2),"cost":(75,140),"ratio":{"main":1,"secondary":1}},
}
for id, groups in specs.items():
 u=units[f"smoke-unit-{id}"]
 all_groups={x.get("id"):x for x in u.findall(".//"+C+"selectionEntryGroup")}
 profiles=u.findall("./"+C+"profiles/"+C+"profile")
 order=list(dict.fromkeys(p.get("typeName") for p in profiles))
 expected=["Units","Ranged Weapons","Melee Weapons","Abilities","Keywords"]
 assert order==expected, f"{id}: profile order {order}"
 options=set()
 for key,low,high,noptions in groups:
  gid=f"mul-{id}-{key}"
  assert gid in all_groups, f"{id}: missing {gid}"
  group=all_groups[gid]
  constraints={x.get("type"):int(x.get("value")) for x in group.findall("./"+C+"constraints/"+C+"constraint")}
  assert constraints=={"min":low,"max":high}, f"{gid}: quantity limits {constraints}"
  children=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
  assert len(children)==noptions, f"{gid}: wrong number of options"
  childids={x.get("id") for x in children}
  assert group.get("defaultSelectionEntryId") in childids, f"{gid}: no valid default"
  if id in variable:
   model_id=f"smoke-{id}-model-0"
   model=[x for x in u.findall(".//"+C+"selectionEntry") if x.get("id")==model_id]
   assert len(model)==1, f"{id}: missing variable-size model"
   model_constraints={x.get("type"):int(x.get("value")) for x in model[0].findall("./"+C+"constraints/"+C+"constraint")}
   assert model_constraints==dict(zip(("min","max"),variable[id]["model"])), f"{id}: invalid unit size"
   assert group in u.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup"), f"{gid}: counters must be squad level"
   mods=group.findall("./"+C+"modifiers/"+C+"modifier")
   expected=2*(variable[id]["model"][1]-variable[id]["model"][0])
   assert len(mods)==expected, f"{gid}: expected {expected} dynamic count modifiers"
   ratio=variable[id]["ratio"][key]
   for size in range(variable[id]["model"][0]+1,variable[id]["model"][1]+1):
    matches=[m for m in mods if m.get("value")==str(size*ratio) and
      any(c.get("value")==str(size) and c.get("childId")==model_id for c in m.findall(".//"+C+"condition"))]
    assert len(matches)==2, f"{gid}: missing min/max weapon counts at {size} models"
   # Fixed melee profiles must show the same number of weapons as models.
   base_melee={"591":"smoke-591-weapon-0-1","605":"smoke-605-weapon-0-2","612":"smoke-612-weapon-0-2"}[id]
   relevant=[p for p in profiles if p.get("id")==base_melee or p.get("id","").startswith(base_melee+"-qty-")]
   assert len(relevant)==variable[id]["model"][1]-variable[id]["model"][0]+1, f"{id}: missing melee count variants"
   for count in range(variable[id]["model"][0]+1,variable[id]["model"][1]+1):
    profile=next((p for p in relevant if p.get("id")==base_melee+f"-qty-{count}"),None)
    assert profile is not None and f"(x{count})" in profile.get("name",""), f"{id}: missing x{count} melee label"
   cost=u.find("./"+C+"costs/"+C+"cost")
   assert float(cost.get("value"))==variable[id]["cost"][0]
   pmods=u.findall("./"+C+"modifiers/"+C+"modifier")
   assert any(m.get("value")==str(variable[id]["cost"][1]) for m in pmods), f"{id}: higher points missing"
  assert childids.isdisjoint(options), f"{gid}: duplicate child ID"
  options |= childids
  for child in children:
   limits={x.get("type"):int(x.get("value")) for x in child.findall("./"+C+"constraints/"+C+"constraint")}
   expected_max=variable[id]["model"][1]*variable[id]["ratio"][key] if id in variable else high
   assert limits=={"min":0,"max":expected_max}, f"{gid}: invalid equipment quantity limit {limits}"
 conditional=[p for p in profiles if p.get("id","").startswith(f"mul-{id}-p-")]
 assert conditional, f"{id}: missing conditional weapon profiles"
 triggers=set()
 for profile in conditional:
  assert profile.get("hidden")=="true", f"{id}: optional weapon visible by default"
  con=profile.findall("./"+C+"modifiers/"+C+"modifier/"+C+"conditions/"+C+"condition")
  assert len(con)==1, f"{id}: weapon requires one selection trigger"
  trigger=con[0].get("childId")
  assert trigger in options, f"{id}: missing selection {trigger}"
  triggers.add(trigger)
 assert triggers==options, f"{id}: option without a display profile {options-triggers}"
assert len(specs)==8
# War Walkers use the New Recruit stacked-model quantity selector:
# one 1-2 model entry, with a separate 2-of-2 weapon group on each model.
walker=units["smoke-unit-612"]
models=walker.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(models)==1 and models[0].get("id")=="smoke-612-model-0", "War Walker must be one model counter, not individual checkboxes"
model=models[0]
limits={x.get("type"):int(x.get("value")) for x in model.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":1,"max":2}, f"War Walker must have numeric model quantity 1-2, found {limits}"
assert not walker.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup"), "Shared squad weapon pool remains"
groups=model.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")
assert len(groups)==1 and groups[0].get("id")=="mul-612-mounts", "Missing per-model heavy weapon group"
group=groups[0]
limits={x.get("type"):int(x.get("value")) for x in group.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":2,"max":2}, "Each walker must have two heavy weapons"
choices=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(choices)==5
assert group.get("defaultSelectionEntryId")=="mul-612-mounts-shuriken", "Default choice must be Shuriken cannon"
for choice in choices:
 limits={x.get("type"):int(x.get("value")) for x in choice.findall("./"+C+"constraints/"+C+"constraint")}
 assert limits=={"min":0,"max":2}, f"Weapon {choice.get('name')} must support 0-2 copies"
 profiles=choice.findall("./"+C+"profiles/"+C+"profile")
 expected=2 if "missile" in choice.get("id") else 1
 assert len(profiles)==expected, f"{choice.get('name')}: missing equipment-owned weapon profiles"
 assert all(p.get("hidden")=="false" and p.find("./"+C+"modifiers") is None for p in profiles), "Weapon profile must be directly owned by its selection"
feet=next((x for x in model.findall("./"+C+"selectionEntries/"+C+"selectionEntry") if x.get("name")=="War Walker feet"),None)
assert feet is not None and len(feet.findall("./"+C+"profiles/"+C+"profile"))==1, "Per-model melee weapon missing"
types=list(dict.fromkeys(p.get("typeName") for p in walker.findall("./"+C+"profiles/"+C+"profile")))
assert types==["Units","Abilities","Keywords"], f"Detached War Walker profiles remain: {types}"
points=walker.findall("./"+C+"modifiers/"+C+"modifier")
assert any(m.get("field")=="pts-11e0" and m.get("value")=="160" and any(c.get("childId")=="smoke-612-model-0" and c.get("value")=="2" for c in m.findall(".//"+C+"condition")) for m in points), "Two-Walker points condition must trigger at two models"
print("PASS: other wargear units plus stacked 1-2 War Walkers with per-model 2-weapon loadouts")
