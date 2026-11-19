#!/usr/bin/env python3
"""Regression checks for display-first Aeldari category-test units.

Checks the PDF-inspired structure:
Models -> Units -> Ranged Weapons -> Melee Weapons -> Abilities ->
Keywords -> native Rules -> Categories.

The category units are still test entries; this does not validate all optional
wargear, transport capacity or special army-building legality.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
c = ET.parse(root / "Aeldari 11e TEST.cat").getroot()
g = ET.parse(root / "Warhammer 40,000 11e Custom TEST.gst").getroot()
C = "{http://www.battlescribe.net/schema/catalogueSchema}"
G = "{http://www.battlescribe.net/schema/gameSystemSchema}"
wanted = ["Epic Hero", "Character", "Battleline", "Infantry", "Mounted", "Monster", "Vehicle", "Fortification", "Dedicated Transport"]
assign = {
    "568":"Epic Hero", "582":"Character", "583":"Character",
    "591":"Mounted", "581":"Epic Hero", "613":"Monster",
    "605":"Vehicle", "609":"Vehicle", "612":"Vehicle",
    "589":"Battleline", "603":"Vehicle", "2459":"Fortification",
    "621":"Vehicle", "599":"Dedicated Transport",
}
points = {"568":120,"582":60,"583":60,"591":80,"581":250,"613":125,
          "605":75,"609":130,"612":80,"589":90,"603":160,
          "2459":105,"621":410,"599":115}
tabs = g.findall("./"+G+"forceEntries/"+G+"forceEntry/"+G+"categoryLinks/"+G+"categoryLink")
assert [x.get("name") for x in tabs]==wanted, "Incorrect army-building tabs or order"
names = {x.get("id"):x.get("name") for x in g.findall("./"+G+"categoryEntries/"+G+"categoryEntry")}
units = [x for x in c.findall("./"+C+"selectionEntries/"+C+"selectionEntry") if x.get("id","").startswith("smoke-unit-")]
assert len(units)==14, f"Expected 14 CATEGORY TEST entries, got {len(units)}"
for unit in units:
    id = unit.get("id").replace("smoke-unit-","")
    primaries = [x for x in unit.findall("./"+C+"categoryLinks/"+C+"categoryLink") if x.get("primary")=="true"]
    assert len(primaries)==1 and names[primaries[0].get("targetId")]==assign[id], f"{id}: wrong category"
    costs = unit.findall("./"+C+"costs/"+C+"cost")
    assert len(costs)==1 and float(costs[0].get("value"))==points[id], f"{id}: incorrect points"
    profiles = unit.findall("./"+C+"profiles/"+C+"profile")
    types = list(dict.fromkeys(x.get("typeName") for x in profiles))
    assert types[0]=="Units", f"{id}: unit characteristics not first"
    if "Ranged Weapons" in types and "Melee Weapons" in types:
        assert types.index("Ranged Weapons") < types.index("Melee Weapons"), f"{id}: ranged below melee"
    assert types[-2:]==["Abilities","Keywords"] or types[-1:]==["Keywords"], f"{id}: Abilities/Keywords order wrong: {types}"
    keywords = [p for p in profiles if p.get("typeName")=="Keywords"]
    assert len(keywords)==1, f"{id}: missing Keywords profile"
    fields = keywords[0].findall("./"+C+"characteristics/"+C+"characteristic")
    assert {x.get("name") for x in fields}=={"Keywords","Faction Keywords"}, f"{id}: keyword fields missing"
    for p in [x for x in profiles if x.get("typeName")=="Abilities"]:
        descriptions = p.findall("./"+C+"characteristics/"+C+"characteristic")
        assert descriptions and descriptions[0].text, f"{id}: no ability text"
    rules = unit.findall("./"+C+"rules/"+C+"rule")
    assert all(r.find("./"+C+"description") is not None for r in rules), f"{id}: native rule has no description"
    if id=="2459":
        assert {"Arcane Cover","Webway Strike","Fortification","Deployment"} <= {x.get("name") for x in rules}, "Webway Gate rules missing"
    models = unit.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
    assert models and all(m.get("type")=="model" for m in models), f"{id}: model choices lost"
    for model in models:
        equipment=model.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
        for item in equipment:
            constraints=item.findall("./"+C+"constraints/"+C+"constraint")
            assert {x.get("type") for x in constraints}=={"min","max"}, f"{id}: mandatory equipment choice missing"
print("PASS: nine tabs, 14 unit roles, points, ordered stats/weapons/abilities/keywords, written rules and equipment")
