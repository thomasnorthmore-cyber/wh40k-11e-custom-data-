#!/usr/bin/env python3
"""Validate full Aeldari source coverage plus preservation of the 17 tested units."""
import argparse
from collections import Counter,defaultdict
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
N="{http://www.battlescribe.net/schema/catalogueSchema}"
p=argparse.ArgumentParser();p.add_argument("catalogue",type=Path);args=p.parse_args()
root=ET.parse(args.catalogue).getroot()
fixture=ET.parse(ROOT/"tests/fixtures/aeldari-v6.cat").getroot()
source=json.loads((ROOT/"data/structured/aeldari-source-datasheets.json").read_text())["datasheets"]
units=root.findall("./"+N+"selectionEntries/"+N+"selectionEntry")
base=fixture.findall("./"+N+"selectionEntries/"+N+"selectionEntry")
names={u.get("name") for u in units}
assert len(units)==99, f"Expected 99, got {len(units)}"
assert len(names)==99, "Duplicate Aeldari unit names"
assert all(s["name"] in names for s in source), "Source includes missing datasheet"
baseline={u.get("name"):u for u in base}
for unit in units:
    if unit.get("name") in baseline:
        a=ET.canonicalize(ET.tostring(unit,encoding="unicode"))
        b=ET.canonicalize(ET.tostring(baseline[unit.get("name")],encoding="unicode"))
        assert a==b, f"Verified v6 loadout was modified: {unit.get('name')}"
ids=[x.get("id") for x in root.iter() if x.get("id")]
assert len(ids)==len(set(ids)), "Duplicate XML IDs"
new=[u for u in units if u.get("name") not in baseline]
assert len(new)==82
for u in new:
    name=u.get("name")
    types=[p.get("typeName") for p in u.iter(N+"profile")]
    assert "Units" in types and "Keywords" in types,name
    assert any(t in ("Ranged Weapons","Melee Weapons") for t in types),name
    assert u.find("./"+N+"costs/"+N+"cost") is not None,name
    assert u.find("./"+N+"selectionEntries/"+N+"selectionEntry") is not None,name
    source_rules=[r.get("name") for r in u.findall("./"+N+"rules/"+N+"rule")]
    assert "Source Points Table" in source_rules and "Starting Equipment" in source_rules,name
profiles=sum(len([p for p in u.iter(N+"profile") if p.get("typeName") in ("Ranged Weapons","Melee Weapons")]) for u in new)
print(f"PASS: {len(units)} source Aeldari datasheets, {len(new)} added, {profiles} generated model weapon profiles")
print("PASS: all 17 verified v6 unit selections canonically unchanged; IDs globally unique")
print("NOTE: source equipment replacement prerequisites require a later semantic legality pass")
