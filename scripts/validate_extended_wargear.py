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
# War Walkers follow the native New Recruit model-counter approach.
# Model count is 1–2; each model carries its own 2/2 weapon group.
walker=units["smoke-unit-612"]
walker_models=walker.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(walker_models)==1 and walker_models[0].get("id")=="smoke-612-model-0", "War Walkers must use one 1–2 model counter"
model=walker_models[0]
model_limits={x.get("type"):int(x.get("value")) for x in model.findall("./"+C+"constraints/"+C+"constraint")}
assert model_limits=={"min":1,"max":2}, f"Incorrect War Walker model limits: {model_limits}"
assert model.get("name")=="War Walker", "War Walker model must have the shared counter label"
assert not walker.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup"), "Shared squad-level weapon pool remains"
groups=model.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")
assert len(groups)==1 and groups[0].get("id")=="mul-612-mounts", "Missing nested per-model heavy weapons"
group=groups[0]
limits={x.get("type"):int(x.get("value")) for x in group.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":2,"max":2}, "Each War Walker must have exactly two heavy weapons"
choices=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(choices)==5, "Missing War Walker heavy weapon options"
ids={x.get("id") for x in choices}
assert group.get("defaultSelectionEntryId") in ids, "Invalid default weapon"
for choice in choices:
 values={x.get("type"):int(x.get("value")) for x in choice.findall("./"+C+"constraints/"+C+"constraint")}
 assert values=={"min":0,"max":2}, f"Weapon {choice.get('name')} must allow 0–2"
pmods=walker.findall("./"+C+"modifiers/"+C+"modifier")
assert any(m.get("field")=="pts-11e0" and m.get("value")=="160" and
 any(c.get("childId")=="smoke-612-model-0" and c.get("value")=="2" for c in m.findall(".//"+C+"condition"))
 for m in pmods), "160 points must trigger at 2 models"
profiles=walker.findall("./"+C+"profiles/"+C+"profile")
types=list(dict.fromkeys(p.get("typeName") for p in profiles))
assert types==["Units","Ranged Weapons","Melee Weapons","Abilities","Keywords"], f"Wrong War Walker profile order: {types}"
weapon_profiles=[p for p in profiles if p.get("id","").startswith("mul-612-p-")]
assert len(weapon_profiles)==24, f"Expected 24 ranged profiles (six profiles for each of 1–4 copies), found {len(weapon_profiles)}"
triggers={x.get("childId") for p in weapon_profiles for x in p.findall(".//"+C+"condition")}
assert ids==triggers, f"Wrong per-model weapon triggers: {ids^triggers}"
for qty in range(1,5):
 for weapon in ("shuriken","missile","bright","scatter","star"):
  matching=[p for p in weapon_profiles if p.get("id","").startswith(f"mul-612-p-{weapon}-") and ((qty==1 and "-count-" not in p.get("id","")) or p.get("id","").endswith(f"-count-{qty}"))]
  expected=2 if weapon=="missile" else 1
  assert len(matching)==expected, f"War Walker {weapon} x{qty}: profile count {len(matching)}"
print("PASS: 8 other wargear units plus War Walker 1–2 model counter with nested 2/2 gear and 80/160 pricing")
