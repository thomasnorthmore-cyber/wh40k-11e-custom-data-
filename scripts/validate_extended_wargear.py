#!/usr/bin/env python3
"""Validate alternate wargear, point tiers, and model-scoped choices."""
from pathlib import Path
import xml.etree.ElementTree as ET

C="{http://www.battlescribe.net/schema/catalogueSchema}"
cat=ET.parse(Path(__file__).resolve().parents[1]/"tests/fixtures/aeldari-v6.cat").getroot()
units={u.get("id"):u for u in cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
specs={
 "582":{"staff":2},
 "583":{"staff":2},
 "591":{"bike":3},
 "605":{"main":3,"secondary":2},
 "589":{"platform":5},
 "603":{"wings":2},
 "621":{"secondary":5},
 "599":{"turret":5,"under":2},
}
for id, groups in specs.items():
 unit=units[f"smoke-unit-{id}"]
 model=next((m for m in unit.iter(C+"selectionEntry") if m.get("id")==f"smoke-{id}-model-0"),None)
 assert model is not None,f"{id}: missing model"
 for group_name, nchoices in groups.items():
  gid=f"mul-{id}-{group_name}"
  matches=[g for g in unit.iter(C+"selectionEntryGroup") if g.get("id")==gid]
  assert len(matches)==1, f"{id}: missing/duplicate group {gid}"
  group=matches[0]
  limits={c.get("type"):int(c.get("value")) for c in group.findall("./"+C+"constraints/"+C+"constraint")}
  assert limits=={"min":1,"max":1}, f"{gid}: expected one weapon per model/slot, got {limits}"
  choices=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
  assert len(choices)==nchoices, f"{gid}: wrong number of weapon options"
  assert group.get("defaultSelectionEntryId") in {e.get("id") for e in choices}, f"{gid}: missing default"
  if id in ("591","605"):
   assert group in model.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup"),f"{gid}: must belong to model, not squad"
  for option in choices:
   limit={c.get("type"):int(c.get("value")) for c in option.findall("./"+C+"constraints/"+C+"constraint")}
   assert limit=={"min":0,"max":1}, f"{option.get('id')}: wrong equipment limit {limit}"
   profiles=option.findall("./"+C+"profiles/"+C+"profile")
   assert profiles,f"{option.get('id')}: selected weapon lacks characteristics"
   assert all(p.get("typeName") in ("Ranged Weapons","Melee Weapons") and p.get("hidden")=="false" for p in profiles)
for id,model_id,min_models,max_models,cost_min,cost_max in (
 ("591","smoke-591-model-0",3,6,80,170),
 ("605","smoke-605-model-0",1,2,75,140),
):
 unit=units[f"smoke-unit-{id}"]
 model=next(m for m in unit.iter(C+"selectionEntry") if m.get("id")==model_id)
 limits={c.get("type"):int(c.get("value")) for c in model.findall("./"+C+"constraints/"+C+"constraint")}
 assert limits=={"min":min_models,"max":max_models},f"{id}: incorrect model sizes"
 assert float(unit.find("./"+C+"costs/"+C+"cost").get("value"))==cost_min
 assert any(m.get("value")==str(cost_max) and any(c.get("childId")==model_id for c in m.findall(".//"+C+"condition")) for m in unit.findall("./"+C+"modifiers/"+C+"modifier")),f"{id}: points modifier absent"
walker=units["smoke-unit-612"]
models=walker.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(models)==1 and models[0].get("id")=="smoke-612-model-0","War Walkers must use one 1-2 model counter"
m=models[0]
limits={c.get("type"):int(c.get("value")) for c in m.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":1,"max":2},"War Walker counter must select 1-2"
groups=m.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")
assert len(groups)==1 and groups[0].get("id")=="mul-612-mounts"
group=groups[0]
limits={c.get("type"):int(c.get("value")) for c in group.findall("./"+C+"constraints/"+C+"constraint")}
assert limits=={"min":2,"max":2},"Each War Walker must have two heavy weapons"
choices=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert len(choices)==5
for choice in choices:
 limits={c.get("type"):int(c.get("value")) for c in choice.findall("./"+C+"constraints/"+C+"constraint")}
 assert limits=={"min":0,"max":2},f"{choice.get('name')}: incorrect quantity"
 profiles=choice.findall("./"+C+"profiles/"+C+"profile")
 assert len(profiles)==(2 if "missile" in choice.get("id") else 1),f"{choice.get('id')}: missing weapon modes"
assert any(m.get("value")=="160" and any(c.get("childId")=="smoke-612-model-0" and c.get("value")=="2" for c in m.findall(".//"+C+"condition")) for m in walker.findall("./"+C+"modifiers/"+C+"modifier")),"War Walker size pricing broken"
print("PASS: eight alternate wargear unit patterns, Windrider/Vyper model ownership and War Walker quantity controls")
