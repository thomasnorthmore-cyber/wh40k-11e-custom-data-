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
 "612":[("mounts",2,2,5)],
 "589":[("platform",1,1,5)],
 "603":[("wings",1,1,2)],
 "621":[("secondary",1,1,5)],
 "599":[("turret",1,1,5),("under",1,1,2)],
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
  assert childids.isdisjoint(options), f"{gid}: duplicate child ID"
  options |= childids
  for child in children:
   limits={x.get("type"):int(x.get("value")) for x in child.findall("./"+C+"constraints/"+C+"constraint")}
   assert limits=={"min":0,"max":high}, f"{gid}: invalid model quantity control"
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
assert len(specs)==9
print("PASS: 9 additional test units have source-based weapon alternatives, quantity limits, default selections, conditional profiles and display order")
