#!/usr/bin/env python3
"""Reject redundant ability/rule descriptions in New Recruit test datasheets.

The Abilities section owns written unit-specific rules. Native Rules should
contain only distinct faction, core, deployment or other rules.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
C = "{http://www.battlescribe.net/schema/catalogueSchema}"
cat = ET.parse(ROOT / "Aeldari 11e TEST.cat").getroot()

def normal(text):
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()

units = cat.findall("./" + C + "selectionEntries/" + C + "selectionEntry")
checked = 0
for unit in units:
    if unit.get("type") != "unit":
        continue
    abilities = [
        p for p in unit.iter(C + "profile")
        if p.get("typeName") == "Abilities"
    ]
    rules = unit.findall("./" + C + "rules/" + C + "rule")
    described = {normal(p.get("name")) for p in abilities}
    native = {normal(r.get("name")) for r in rules}
    duplicates = described & native
    assert not duplicates, (
        f"{unit.get('name')}: Abilities repeated under Rules: "
        + ", ".join(sorted(duplicates))
    )
    ability_names = [normal(p.get("name")) for p in abilities]
    assert len(ability_names) == len(set(ability_names)), (
        f"{unit.get('name')}: duplicated Abilities profiles"
    )
    rule_names = [normal(r.get("name")) for r in rules]
    assert len(rule_names) == len(set(rule_names)), (
        f"{unit.get('name')}: duplicated native Rules"
    )
    for p in abilities:
        text = p.find("./" + C + "characteristics/" + C + "characteristic")
        assert text is not None and (text.text or "").strip(), (
            f"{unit.get('name')}: {p.get('name')} has no written explanation"
        )
    checked += 1

assert checked >= 17, f"Expected at least 17 unit entries, found {checked}"
print(f"PASS: {checked} units have no redundant Abilities/Rules entries and written ability descriptions")
