#!/usr/bin/env python3
"""Validate custom 11e catalogue against model/equipment ownership rules.

Source-of-truth example: original 265-point New Recruit .rosz export.
Also checks structural constraints for our three-unit test catalogue.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = "{http://www.battlescribe.net/schema/catalogueSchema}"
G = "{http://www.battlescribe.net/schema/gameSystemSchema}"

def need(ok, message):
    if not ok:
        raise AssertionError(message)

def entries(parent):
    return parent.findall(".//" + C + "selectionEntry")

def child(parent, ident):
    matches = [node for node in entries(parent) if node.get("id") == ident]
    need(len(matches) == 1, f"Expected one selection {ident}, found {len(matches)}")
    return matches[0]

def own_profiles(node):
    return node.findall("./" + C + "profiles/" + C + "profile")

def types(node):
    return [p.get("typeName") for p in own_profiles(node)]

def validate():
    cat = ET.parse(ROOT / "Aeldari 11e TEST.cat").getroot()
    game = ET.parse(ROOT / "Warhammer 40,000 11e Custom TEST.gst").getroot()
    need(cat.get("gameSystemId") == game.get("id"), "Game-system ID mismatch")
    tops = cat.findall("./" + C + "selectionEntries/" + C + "selectionEntry")
    units = {e.get("id"): e for e in tops}
    need({"unit-rangers-11e0", "fd-unit-root", "dr-unit-root"} <= set(units), "Three independent infantry units missing")
    for uid in ("unit-rangers-11e0", "fd-unit-root", "dr-unit-root"):
        links = units[uid].findall("./" + C + "categoryLinks/" + C + "categoryLink")
        need(any(x.get("name") == "Infantry" and x.get("primary") == "true" for x in links), f"{uid}: Infantry category missing")

    for uid, regular, exarch, normal_ranged, normal_melee, choices, higher in [
        ("fd-unit-root", "fd-regular-5", "fd-exarch-5", "fd-equip-regular-ranged", "fd-equip-regular-melee",
          ["fd-gear-default-5", "fd-gear-flamer-5", "fd-gear-pistol-5", "fd-gear-pike-5"], 240),
        ("dr-unit-root", "dr-regular", "dr-exarch", "dr-equip-regular-ranged", "dr-equip-regular-melee",
          ["dr-exarch-choice-reaper", "dr-exarch-choice-missile", "dr-exarch-choice-shuriken", "dr-exarch-choice-tempest"], 200),
    ]:
        unit = units[uid]
        need(not any(t in ("Units", "Ranged Weapons", "Melee Weapons") for t in types(unit)),
             f"{uid}: profiles should belong to models and equipped weapons, not parent unit")
        for mid in (regular, exarch):
            model = child(unit, mid)
            need(model.get("type") == "model", f"{mid}: not a model")
            need("Units" in types(model), f"{mid}: no model characteristics")
        rm = child(unit, regular)
        need("Ranged Weapons" in types(child(rm, normal_ranged)), f"{uid}: regular gun not equipped with profile")
        need("Melee Weapons" in types(child(rm, normal_melee)), f"{uid}: regular melee not equipped with profile")
        em = child(unit, exarch)
        for choice_id in choices:
            option = child(em, choice_id)
            need("Ranged Weapons" in types(option), f"{choice_id}: missing selected ranged profile")
            melee = child(option, choice_id + "-melee-equip-0")
            need("Melee Weapons" in types(melee), f"{choice_id}: missing selected melee profile")
        costs = unit.findall("./" + C + "modifiers/" + C + "modifier")
        need(any(x.get("value") == str(higher) for x in costs), f"{uid}: large squad cost missing")
        need(bool(unit.findall("./" + C + "rules/" + C + "rule")), f"{uid}: native rules missing")

    rangers = units["unit-rangers-11e0"]
    for size, choice in ((5, "rangers-five-11e0"), (10, "rangers-ten-11e0")):
        model = child(child(rangers, choice), f"rangers-model-{size}")
        need(model.get("type") == "model" and "Units" in types(model), f"Rangers x{size}: model stats missing")
        weapons = [p for e in entries(model) for p in own_profiles(e)]
        need(sum(p.get("typeName") == "Ranged Weapons" for p in weapons) == 2,
             f"Rangers x{size}: expected two ranged weapons")
        need(sum(p.get("typeName") == "Melee Weapons" for p in weapons) == 1,
             f"Rangers x{size}: expected one melee weapon")
    print("PASS: model stat ownership, equipped weapon profiles, Exarch options, native rules, layout-independent structure and point modifiers")

if __name__ == "__main__":
    try:
        validate()
    except (AssertionError, ET.ParseError, OSError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
