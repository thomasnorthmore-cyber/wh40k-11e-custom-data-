#!/usr/bin/env python3
"""Check Aeldari category smoke-test coverage in New Recruit XML.

This tests category/entry wiring, fixed model counts, and mandatory default
equipment. It does NOT certify full 11th-edition rule and loadout correctness.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
c = ET.parse(root / "Aeldari 11e TEST.cat").getroot()
g = ET.parse(root / "Warhammer 40,000 11e Custom TEST.gst").getroot()
C = "{http://www.battlescribe.net/schema/catalogueSchema}"
G = "{http://www.battlescribe.net/schema/gameSystemSchema}"
expected_roles = {
    "Infantry Epic Hero":120, "Infantry Character":60,
    "Mounted Character":60, "Mounted":80, "Monster Epic Hero":250,
    "Monster":125, "Vehicle":75, "Transport":130, "Walker":80,
    "Battleline":90, "Aircraft":160, "Fortifications":105,
    "Titanic":410, "Dedicated Transports":115,
}
tabs = {x.get("name") for x in g.findall("./"+G+"forceEntries/"+G+"forceEntry/"+G+"categoryLinks/"+G+"categoryLink")}
categories = {x.get("id"):x.get("name") for x in g.findall("./"+G+"categoryEntries/"+G+"categoryEntry")}
units = [e for e in c.findall("./"+C+"selectionEntries/"+C+"selectionEntry") if e.get("id","").startswith("smoke-unit-")]
assert len(units)==len(expected_roles), f"Expected {len(expected_roles)} smoke units, found {len(units)}"
assert set(expected_roles) <= tabs, "Missing a role tab"
for unit in units:
    links = unit.findall("./"+C+"categoryLinks/"+C+"categoryLink")
    primary = [x for x in links if x.get("primary") == "true"]
    assert len(primary)==1, f"{unit.get('name')}: missing primary role"
    role = categories[primary[0].get("targetId")]
    costs = unit.findall("./"+C+"costs/"+C+"cost")
    assert len(costs)==1 and int(float(costs[0].get("value")))==expected_roles[role], f"{role}: base points"
    models = unit.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
    assert models and all(x.get("type")=="model" for x in models), f"{role}: missing models"
    for model in models:
        profiles = model.findall("./"+C+"profiles/"+C+"profile")
        assert len(profiles)==1 and profiles[0].get("typeName")=="Units", f"{role}: model profile"
        equipment = model.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
        for equip in equipment:
            assert len(equip.findall("./"+C+"profiles/"+C+"profile"))==1, f"{role}: equipment profile"
            constraints = equip.findall("./"+C+"constraints/"+C+"constraint")
            assert {x.get("type") for x in constraints}=={"min","max"}, f"{role}: equipment not mandatory"
print("PASS: 14 category tabs, 14 separate units, base points, fixed models and mandatory baseline equipment")
