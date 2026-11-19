#!/usr/bin/env python3
"""Whole-catalogue structural checks for Aeldari 11e New Recruit test units.

This validates XML and selectable-equipment structure. It does not prove
datasheet accuracy or New Recruit renderer layout.
"""
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "Aeldari 11e TEST.cat"
GST = ROOT / "Warhammer 40,000 11e Custom TEST.gst"
NS = "{http://www.battlescribe.net/schema/catalogueSchema}"
GN = "{http://www.battlescribe.net/schema/gameSystemSchema}"

catalogue = ET.parse(CAT).getroot()
system = ET.parse(GST).getroot()
assert catalogue.get("gameSystemId") == system.get("id"), "Mismatched catalogue/system"
units = catalogue.findall("./" + NS + "selectionEntries/" + NS + "selectionEntry")
assert len(units) == 17, f"Expected 17 units, got {len(units)}"
assert all(u.get("type") == "unit" for u in units)

all_ids = [e.get("id") for e in catalogue.iter() if e.get("id")]
duplicates = [id for id, n in Counter(all_ids).items() if n > 1]
assert not duplicates, f"Duplicate XML identifiers: {duplicates[:12]}"

checked_groups = checked_models = checked_weapons = 0
for unit in units:
    uid = unit.get("id")
    name = unit.get("name")
    assert "[CATEGORY TEST]" not in name, f"{name}: debug label left in UI"
    roots = unit.findall("./" + NS + "profiles/" + NS + "profile")
    types = [p.get("typeName") for p in roots]
    assert "Units" in types, f"{name}: no characteristic profile"
    assert "Keywords" in types, f"{name}: no keyword profile"
    assert types[-1] == "Keywords", f"{name}: keywords must be the final root profile"
    assert not ({"Ranged Weapons", "Melee Weapons"} & set(types)), (
        f"{name}: detached weapons found at unit level"
    )
    abilities = [p.get("name") for p in roots if p.get("typeName") == "Abilities"]
    assert len(abilities) == len(set(abilities)), f"{name}: duplicate ability names"
    models = [e for e in unit.iter(NS + "selectionEntry") if e.get("type") == "model"]
    assert models, f"{name}: no model entries"
    for model in models:
        checked_models += 1
        limits = {c.get("type"): c.get("value")
                  for c in model.findall("./" + NS + "constraints/" + NS + "constraint")
                  if c.get("field") == "selections"}
        if limits:
            assert "min" in limits and "max" in limits, (
                f"{name}/{model.get('name')}: missing squad limit"
            )
            assert 0 <= int(limits["min"]) <= int(limits["max"]), (
                f"{name}/{model.get('name')}: impossible squad limit"
            )
    for group in unit.iter(NS + "selectionEntryGroup"):
        checked_groups += 1
        assert not group.get("name", "").startswith(tuple(f"{i}. " for i in range(1,10))), (
            f"{name}: numbered legacy group name {group.get('name')}"
        )
        options = group.findall("./" + NS + "selectionEntries/" + NS + "selectionEntry")
        if not options:
            continue
        default = group.get("defaultSelectionEntryId")
        if default:
            assert default in {o.get("id") for o in options}, (
                f"{name}/{group.get('name')}: default points outside choice group"
            )
        bounds = {c.get("type"): int(c.get("value"))
                  for c in group.findall("./" + NS + "constraints/" + NS + "constraint")
                  if c.get("field") == "selections"}
        if bounds:
            assert "min" in bounds and "max" in bounds, (
                f"{name}/{group.get('name')}: incomplete selection bounds"
            )
            assert 0 <= bounds["min"] <= bounds["max"], (
                f"{name}/{group.get('name')}: inverted selection bounds"
            )
    for profile in unit.iter(NS + "profile"):
        if profile.get("typeName") not in ("Ranged Weapons", "Melee Weapons"):
            continue
        checked_weapons += 1
        assert profile.get("hidden") == "false", (
            f"{name}: hidden equipped weapon {profile.get('name')}"
        )
        assert profile.find("./" + NS + "modifiers") is None, (
            f"{name}: visibility modifier on equipment-owned weapon"
        )
        ch = {x.get("name") for x in
              profile.findall("./" + NS + "characteristics/" + NS + "characteristic")}
        skill = "BS" if profile.get("typeName") == "Ranged Weapons" else "WS"
        assert {"Range", "A", skill, "S", "AP", "D"} <= ch, (
            f"{name}: missing weapon characteristics for {profile.get('name')}"
        )

# Shared aspect equipment labels must remain consistent across units.
by_id = {u.get("id"): u for u in units}
token_names = []
for uid, token_id in (("fd-unit-root", "fd-token-5"),
                      ("dr-unit-root", "dr-aspect-token")):
    token = next((e for e in by_id[uid].iter(NS + "selectionEntry")
                  if e.get("id") == token_id), None)
    assert token is not None, f"{uid}: missing Aspect Shrine Token"
    token_names.append(token.get("name"))
assert token_names == ["Aspect Shrine Token (1 per 5 models)"] * 2, (
    f"Nonstandard Aspect Shrine Token labels: {token_names}"
)

# Squad-size points conditions must count the chosen models, not their wargear.
for uid, model_id, size_trigger, full_size_points in (
    ("smoke-unit-591", "smoke-591-model-0", "4", "170"),
    ("smoke-unit-605", "smoke-605-model-0", "2", "140"),
    ("smoke-unit-612", "smoke-612-model-0", "2", "160"),
):
    matches = [
        modifier for modifier in by_id[uid].findall(
            "./" + NS + "modifiers/" + NS + "modifier"
        )
        if modifier.get("field") == "pts-11e0"
        and modifier.get("value") == full_size_points
    ]
    assert len(matches) == 1, f"{uid}: missing large-squad points tier"
    conditions = matches[0].findall(
        "./" + NS + "conditions/" + NS + "condition"
    )
    assert len(conditions) == 1, f"{uid}: unexpected points conditions"
    c = conditions[0]
    assert (c.get("childId") == model_id
            and c.get("value") == size_trigger
            and c.get("includeChildSelections") == "true"), (
        f"{uid}: model-count points condition not configured consistently"
    )
assert int(catalogue.get("revision")) >= 3, "Updated catalogue must publish v3"

print(f"PASS: {len(units)} units, {checked_models} model entries, "
      f"{checked_groups} choice groups, {checked_weapons} weapon profiles")
