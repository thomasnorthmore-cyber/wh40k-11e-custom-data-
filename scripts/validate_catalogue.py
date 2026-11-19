#!/usr/bin/env python3
"""Regression checks for New Recruit Aeldari test catalogue."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "tests/fixtures/aeldari-v6.cat"
GST = ROOT / "Warhammer 40,000 11e Custom TEST.gst"
NS = "{http://www.battlescribe.net/schema/catalogueSchema}"
GN = "{http://www.battlescribe.net/schema/gameSystemSchema}"

def require(cond, message):
    if not cond:
        raise AssertionError(message)

def check():
    c, g = ET.parse(CAT).getroot(), ET.parse(GST).getroot()
    require(c.get("gameSystemId") == g.get("id"), "Catalogue game system ID mismatch")
    entries = c.find(NS + "selectionEntries")
    unit_map = {e.get("id"): e for e in entries.findall(NS + "selectionEntry")}
    require(set(["unit-rangers-11e0", "fd-unit-root", "dr-unit-root"]).issubset(unit_map), "Missing a top-level unit")
    types = [p.get("name") for p in g.findall("./" + GN + "profileTypes/" + GN + "profileType")]
    require(types == ["Units", "Ranged Weapons", "Melee Weapons", "Abilities", "Rules", "Keywords"], f"Unexpected profile definitions: {types}")
    for unit_id, model_id, choice_prefix, points in [
        ("fd-unit-root", "fd-regular-5", "fd-gear-", "240"),
        ("dr-unit-root", "dr-regular", "dr-exarch-choice-", "200")
    ]:
        u = unit_map[unit_id]
        cats = u.findall("./" + NS + "categoryLinks/" + NS + "categoryLink")
        require(any(x.get("primary") == "true" and x.get("name") == "Infantry" for x in cats), f"{unit_id}: not Infantry")
        profiles = u.findall("./" + NS + "profiles/" + NS + "profile")
        sections = list(dict.fromkeys(p.get("typeName") for p in profiles))
        require(sections == ["Units", "Ranged Weapons", "Melee Weapons", "Abilities", "Rules", "Keywords"], f"{unit_id}: wrong display order: {sections}")
        root_weapons = [p for p in profiles if p.get("typeName") in ("Ranged Weapons", "Melee Weapons")]
        require(len(root_weapons) >= 7, f"{unit_id}: missing display-first weapon profiles")
        require(any(p.get("hidden") == "true" and p.find("./" + NS + "modifiers") is not None for p in root_weapons), f"{unit_id}: missing loadout-dependent visibility")
        models = [e for e in u.findall(".//" + NS + "selectionEntry") if e.get("id") == model_id]
        require(len(models) == 1, f"{unit_id}: missing regular model")
        names = [e.get("name") for e in models[0].findall("./" + NS + "selectionEntries/" + NS + "selectionEntry")]
        require(len(names) >= 2 and "Close combat weapon" in names, f"{unit_id}: models lack explicit ranged and melee equipment")
        require(any("fusion" in x.lower() or "launcher" in x.lower() for x in names), f"{unit_id}: regular ranged weapon missing")
        modifiers = u.findall("./" + NS + "modifiers/" + NS + "modifier")
        require(any(m.get("value") == points for m in modifiers), f"{unit_id}: higher squad-size points missing")
        choices = [x for x in u.findall(".//" + NS + "selectionEntry") if x.get("id", "").startswith(choice_prefix) and x.get("id", "").count("-") <= (4 if unit_id == "dr-unit-root" else 5)]
        require(len(choices) >= 4, f"{unit_id}: expected four Exarch weapon choices")
    print("PASS: three independent units, Infantry, section order, model equipment, Exarch options and pricing modifiers")

if __name__ == "__main__":
    try: check()
    except (AssertionError, ET.ParseError, OSError) as error:
        print("FAIL:", error, file=sys.stderr)
        sys.exit(1)
