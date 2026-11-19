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
# War Walkers: two separately equipped models, each with independent 2/2 guns.
walker=units["smoke-unit-612"]
walker_models={m.get("id"):m for m in walker.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
assert set(walker_models)=={"smoke-612-model-0","smoke-612-model-1"}, "War Walkers must be separate model selections"
for index,expected in ((0,{"min":1,"max":1}),(1,{"min":0,"max":1})):
 model=walker_models[f"smoke-612-model-{index}"]
 model_limits={c.get("type"):int(c.get("value")) for c in model.findall("./"+C+"constraints/"+C+"constraint")}
 assert model_limits==expected, f"Walker {index+1}: model limits wrong"
 gid="mul-612-mounts"+("-2" if index else "")
 groups=model.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")
 assert len(groups)==1 and groups[0].get("id")==gid, f"Walker {index+1}: missing independent weapon group"
 group=groups[0]
 limits={c.get("type"):int(c.get("value")) for c in group.findall("./"+C+"constraints/"+C+"constraint")}
 assert limits=={"min":2,"max":2}, f"Walker {index+1}: must equip exactly two guns"
 choices=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
 assert len(choices)==5, f"Walker {index+1}: missing weapon options"
 ids={c.get("id") for c in choices}
 assert group.get("defaultSelectionEntryId") in ids, f"Walker {index+1}: invalid default"
 for choice in choices:
  max_value=next(c.get("value") for c in choice.findall("./"+C+"constraints/"+C+"constraint") if c.get("type")=="max")
  assert int(max_value)==2, f"Walker {index+1}: max per weapon should be two"
assert not walker.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup"), "Shared squad-level weapon pool still present"
pmods=walker.findall("./"+C+"modifiers/"+C+"modifier")
assert any(m.get("field")=="pts-11e0" and m.get("value")=="160" and
 any(c.get("childId")=="smoke-612-model-1" and c.get("value")=="1" for c in m.findall(".//"+C+"condition"))
 for m in pmods), "160-point price does not trigger on second model"
wprofiles=[p for p in walker.findall("./"+C+"profiles/"+C+"profile") if p.get("id","").startswith("mul-612-p-")]
assert len(wprofiles)==12, f"Expected 6 weapon modes per walker; found {len(wprofiles)}"
triggers={c.get("childId") for p in wprofiles for c in p.findall(".//"+C+"condition")}
for index in (0,1):
 group=walker_models[f"smoke-612-model-{index}"].find("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")
 assert {c.get("id") for c in group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")} <= triggers
print("PASS: 8 other wargear test units plus separately equipped two-model War Walkers, 80/160 pricing and per-model heavy weapons")
