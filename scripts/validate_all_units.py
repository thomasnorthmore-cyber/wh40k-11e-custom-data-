#!/usr/bin/env python3
"""Review every existing Aeldari unit for consistent New Recruit catalogue structure.

This is a structural check, not proof that the Wahapedia source text or
all 11th-edition army-building interactions are correct.
"""
from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
C="{http://www.battlescribe.net/schema/catalogueSchema}"
G="{http://www.battlescribe.net/schema/gameSystemSchema}"
catalogue=ET.parse(ROOT/"Aeldari 11e TEST.cat").getroot()
system=ET.parse(ROOT/"Warhammer 40,000 11e Custom TEST.gst").getroot()
expected_sections=["Units","Ranged Weapons","Melee Weapons","Abilities","Keywords"]
units=catalogue.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
assert catalogue.get("gameSystemId")==system.get("id")
assert len(units)==17, f"Expected 17 Aeldari review units, found {len(units)}"
seen=set()
for unit in units:
    uid=unit.get("id")
    assert uid not in seen, f"Duplicate unit ID: {uid}"
    seen.add(uid)
    assert unit.get("type")=="unit", f"{uid}: not a unit selection"
    profiles=unit.findall("./"+C+"profiles/"+C+"profile")
    sections=list(dict.fromkeys(p.get("typeName") for p in profiles))
    assert sections==expected_sections or sections==["Units","Ranged Weapons","Melee Weapons","Abilities","Rules","Keywords"] or (uid=="smoke-unit-2459" and sections==["Units","Abilities","Keywords"]), f"{uid}: unexpected section order {sections}"
    assert len([p for p in profiles if p.get("typeName")=="Keywords"])==1, f"{uid}: missing/duplicate Keywords"
    costs=unit.findall("./"+C+"costs/"+C+"cost")
    assert len(costs)==1 and float(costs[0].get("value"))>=0, f"{uid}: invalid unit cost"
    cats=unit.findall("./"+C+"categoryLinks/"+C+"categoryLink")
    assert len([x for x in cats if x.get("primary")=="true"])==1, f"{uid}: expected one primary category"
    for group in unit.iter(C+"selectionEntryGroup"):
        options=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
        assert options, f"{uid}: empty option group {group.get('id')}"
        default=group.get("defaultSelectionEntryId")
        if default:
            assert default in {x.get("id") for x in options}, f"{uid}: invalid default in {group.get('id')}"
        constraints={x.get("type"):int(x.get("value")) for x in group.findall("./"+C+"constraints/"+C+"constraint")}
        if constraints:
            assert constraints.get("min",0)<=constraints.get("max",9999), f"{uid}: invalid group limits"
    for entry in unit.iter(C+"selectionEntry"):
        if entry is unit:
            continue
        constraints={x.get("type"):int(x.get("value")) for x in entry.findall("./"+C+"constraints/"+C+"constraint")}
        if constraints:
            assert constraints.get("min",0)<=constraints.get("max",9999), f"{uid}: invalid model/wargear limits {entry.get('id')}"
    # Unit-specific ability descriptions must not be repeated under native Rules.
    names={p.get("name","").strip().casefold() for p in profiles if p.get("typeName")=="Abilities"}
    rules={r.get("name","").strip().casefold() for r in unit.findall("./"+C+"rules/"+C+"rule")}
    assert not names.intersection(rules), f"{uid}: repeated Abilities/Rules"
rangers=next(x for x in units if x.get("id")=="unit-rangers-11e0")
for size in (5,10):
    suffix="five" if size==5 else "ten"
    choice=next(x for x in rangers.iter(C+"selectionEntry") if x.get("id")==f"rangers-{suffix}-11e0")
    equipment=[x.get("name") for x in choice.findall("./"+C+"selectionEntries/"+C+"selectionEntry")]
    assert equipment==[f"{w} (x{size})" for w in ("Long rifle","Shuriken pistol","Close combat weapon")], f"Rangers {size}: wrong default loadout"
print("PASS: 17 Aeldari unit entries audited; section order, costs, categories, option limits and Ranger defaults")
