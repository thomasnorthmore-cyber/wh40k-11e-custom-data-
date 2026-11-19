#!/usr/bin/env python3
"""Validate the eight user-requested Aeldari army-building categories.

The 14 CATEGORY TEST entries validate basic role placement and starter profiles.
They do not certify optional loadouts, faction restrictions or complete rules.
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
points = {
    "568":120, "582":60, "583":60, "591":80, "581":250,
    "613":125, "605":75, "609":130, "612":80, "589":90,
    "603":160, "2459":105, "621":410, "599":115,
}
tabs = g.findall("./"+G+"forceEntries/"+G+"forceEntry/"+G+"categoryLinks/"+G+"categoryLink")
assert [x.get("name") for x in tabs] == wanted, "The army tab headings/order do not match the eight requested categories"
category_names = {x.get("id"):x.get("name") for x in g.findall("./"+G+"categoryEntries/"+G+"categoryEntry")}
units = [e for e in c.findall("./"+C+"selectionEntries/"+C+"selectionEntry") if e.get("id","").startswith("smoke-unit-")]
assert len(units)==14, f"Expected 14 test units; got {len(units)}"
for unit in units:
    id = unit.get("id").replace("smoke-unit-","")
    assert id in assign, f"Unexpected test unit {id}"
    primary = [x for x in unit.findall("./"+C+"categoryLinks/"+C+"categoryLink") if x.get("primary")=="true"]
    assert len(primary)==1, f"{id}: expected exactly one primary category"
    actual = category_names[primary[0].get("targetId")]
    assert actual == assign[id], f"{id}: wanted {assign[id]}, got {actual}"
    costs = unit.findall("./"+C+"costs/"+C+"cost")
    assert len(costs)==1 and float(costs[0].get("value"))==points[id], f"{id}: base points mismatch"
    native_rules = unit.findall("./"+C+"rules/"+C+"rule")
    assert native_rules, f"{id}: no native rule entries"
    if id == "2459":
        names = {x.get("name") for x in native_rules}
        assert {"Arcane Cover", "Webway Strike", "Fortification", "Deployment"} <= names, "Webway Gate rules incomplete"
    models = unit.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
    assert models and all(m.get("type")=="model" for m in models), f"{id}: missing model entries"
    for model in models:
        profiles = model.findall("./"+C+"profiles/"+C+"profile")
        assert len(profiles)==1 and profiles[0].get("typeName")=="Units", f"{id}: missing stat profile"
        for equipment in model.findall("./"+C+"selectionEntries/"+C+"selectionEntry"):
            assert len(equipment.findall("./"+C+"profiles/"+C+"profile"))==1, f"{id}: missing equipped profile"
            constraints = equipment.findall("./"+C+"constraints/"+C+"constraint")
            assert {x.get("type") for x in constraints}=={"min","max"}, f"{id}: mandatory equipment missing"
print("PASS: 9 army tabs, 14 representative units, required native rules, base points and mandatory equipment")
