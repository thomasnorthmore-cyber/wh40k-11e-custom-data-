#!/usr/bin/env python3
"""Regression checks for Falcon and Wraithlord wargear selection controls."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
C = "{http://www.battlescribe.net/schema/catalogueSchema}"
cat = ET.parse(ROOT/"Aeldari 11e TEST.cat").getroot()
units = {x.get("id"):x for x in cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}

def get(parent,tag,id):
    items = [x for x in parent.findall(".//"+C+tag) if x.get("id")==id]
    assert len(items)==1, f"Expected one {tag} {id}, got {len(items)}"
    return items[0]

def limits(group,minimum,maximum):
    c = group.findall("./"+C+"constraints/"+C+"constraint")
    got = {x.get("type"):int(x.get("value")) for x in c}
    assert got=={"min":minimum,"max":maximum}, f"{group.get('id')}: unexpected constraints {got}"

def profile_order(unit):
    ps=unit.findall("./"+C+"profiles/"+C+"profile")
    types=list(dict.fromkeys(x.get("typeName") for x in ps))
    expected=["Units","Ranged Weapons","Melee Weapons","Abilities","Keywords"]
    assert types==expected, f"{unit.get('id')}: display order changed: {types}"
    return ps

falcon=units["smoke-unit-609"]
assert falcon.find("./"+C+"costs/"+C+"cost").get("value")=="130"
fmodel=get(falcon,"selectionEntry","smoke-609-model-0")
for name,count in [("falcon-group-turret",5),("falcon-group-underside",2)]:
    group=get(fmodel,"selectionEntryGroup",name)
    limits(group,1,1)
    options=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
    assert len(options)==count
    assert group.get("defaultSelectionEntryId") in {x.get("id") for x in options}
profile_order(falcon)

wraith=units["smoke-unit-613"]
assert wraith.find("./"+C+"costs/"+C+"cost").get("value")=="125"
wmodel=get(wraith,"selectionEntry","smoke-613-model-0")
arms=get(wmodel,"selectionEntryGroup","wl-group-arms")
heavy=get(wmodel,"selectionEntryGroup","wl-group-heavy")
wargear=get(wmodel,"selectionEntryGroup","wl-group-wargear")
limits(arms,2,2)
limits(heavy,0,2)
limits(wargear,0,1)
assert arms.get("defaultSelectionEntryId")=="wl-arms-catapult"
expected_groups = {
    "wl-group-arms":{"wl-arms-catapult","wl-arms-flamer"},
    "wl-group-heavy":{"wl-heavy-missile","wl-heavy-bright","wl-heavy-scatter","wl-heavy-shuriken","wl-heavy-star"},
    "wl-group-wargear":{"wl-wargear-ghost"},
}
for group in [arms,heavy,wargear]:
    selections=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
    assert {x.get("id") for x in selections}==expected_groups[group.get("id")]
    for item in selections:
        c={x.get("type"):int(x.get("value")) for x in item.findall("./"+C+"constraints/"+C+"constraint")}
        assert c["min"]==0 and c["max"] in (1,2)
p=profile_order(wraith)
conditional=[x for x in p if x.get("id","").startswith("wl-profile-")]
assert len(conditional)==18
valid_ids=set().union(*expected_groups.values())
for profile in conditional:
    conditions=profile.findall("./"+C+"modifiers/"+C+"modifier/"+C+"conditions/"+C+"condition")
    assert len(conditions)==1, profile.get("id")
    condition=conditions[0]
    assert condition.get("childId") in valid_ids, profile.get("id")
    assert int(condition.get("value")) in (1,2), profile.get("id")
print("PASS: Falcon two exclusive weapon slots; Wraithlord 2/2 arm count, 0/2 heavy count, Ghostglaive toggle, points, profile order and conditions")
