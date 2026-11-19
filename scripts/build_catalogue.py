#!/usr/bin/env python3
"""Aeldari data-first catalogue pilot.

The current v5 .cat remains the compatibility template. The JSON manifest is
authoritative for selected model counts, unit points, and choice-group bounds.
This deliberately does not claim to generate all 17 units or their abilities.
The tool builds an XML catalogue (for import) or verifies that the checked-in
template agrees with its structured pilot data.

Usage:
  python scripts/build_catalogue.py --check
  python scripts/build_catalogue.py --out /tmp/Aeldari.cat
  python scripts/build_catalogue.py --self-test
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from apply_mechanics import apply_mechanics

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "Aeldari 11e TEST.cat"
MANIFEST = ROOT / "data" / "structured" / "aeldari-pilot.json"
DATASHEETS = ROOT / "data" / "structured" / "aeldari-datasheets.json"
MECHANICS = ROOT / "data" / "structured" / "aeldari-mechanics.json"
NS_URI = "http://www.battlescribe.net/schema/catalogueSchema"
N = "{" + NS_URI + "}"
ET.register_namespace("", NS_URI)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def local(node: ET.Element, tag: str):
    return node.find(N + tag)


def one(items, title: str):
    require(len(items) == 1, f"Expected one {title}, found {len(items)}")
    return items[0]


def direct_units(catalogue: ET.Element):
    entries = catalogue.find("./" + N + "selectionEntries")
    require(entries is not None, "Missing top-level units")
    return {u.get("id"): u for u in entries.findall(N + "selectionEntry")}


def get_entry(parent: ET.Element, entry_id: str, kind: str = "selectionEntry"):
    return one([e for e in parent.iter(N + kind) if e.get("id") == entry_id], entry_id)


def bounds(entry: ET.Element):
    return {c.get("type"): c for c in entry.findall("./" + N + "constraints/" + N + "constraint")
            if c.get("field") == "selections"}


def set_bounds(entry: ET.Element, low: int, high: int, name: str):
    require(0 <= low <= high, f"{name}: invalid bounds {low}–{high}")
    items = bounds(entry)
    require("min" in items and "max" in items,
            f"{name}: missing min/max selection constraints")
    items["min"].set("value", str(low))
    items["max"].set("value", str(high))


def points_cost(unit: ET.Element):
    return one([p for p in unit.findall("./" + N + "costs/" + N + "cost")
                if p.get("name") == "pts"], "pts cost")


def points_modifier(unit: ET.Element, model_id: str, threshold: int):
    matches = []
    for modifier in unit.findall("./" + N + "modifiers/" + N + "modifier"):
        if modifier.get("type") != "set" or modifier.get("field") != "pts-11e0":
            continue
        for condition in modifier.findall(".//" + N + "condition"):
            if condition.get("childId") == model_id and condition.get("value") == str(threshold):
                matches.append(modifier)
    return one(matches, f"points tier for {model_id} at {threshold}")


def direct_profile_types(unit: ET.Element):
    return [p.get("typeName") for p in unit.findall("./" + N + "profiles/" + N + "profile")]


def apply_pilot(template: ET.Element, manifest: dict):
    require(manifest.get("schema_version") == 1, "Unknown pilot manifest schema")
    require(manifest.get("edition") == "11th", "Wrong edition")
    require(manifest.get("faction") == "aeldari", "Wrong faction")
    units = direct_units(template)
    require(len(units) == 17, f"Expected 17 preserved baseline units, got {len(units)}")
    declared_ids = [u["id"] for u in manifest["units"]]
    require(len(declared_ids) == len(set(declared_ids)), "Duplicate structured unit IDs")
    for spec in manifest["units"]:
        name = spec["name"]
        require(spec["id"] in units, f"Unknown catalogue unit {name}")
        unit = units[spec["id"]]
        require(unit.get("name") == name, f"{name}: catalogue name mismatch")
        points_cost(unit).set("value", str(spec["points"]["base"]))
        for model in spec["models"]:
            row = get_entry(unit, model["id"])
            require(row.get("type") == "model", f"{name}: {model['id']} is not a model")
            set_bounds(row, model["min"], model["max"], model["id"])
        for tier in spec["points"].get("tiers", []):
            modifier = points_modifier(unit, tier["model_id"], tier["threshold"])
            modifier.set("value", str(tier["value"]))
            require(tier["models"] >= 1, f"{name}: bad tier count")
        for group in spec.get("equipment_groups", []):
            entry = get_entry(unit, group["id"], "selectionEntryGroup")
            if "default" in group:
                choices = {e.get("id") for e in entry.findall("./" + N + "selectionEntries/" + N + "selectionEntry")}
                require(group["default"] in choices, f"{name}: missing default {group['default']}")
                entry.set("defaultSelectionEntryId", group["default"])
            if "min" in group or "max" in group:
                require("min" in group and "max" in group, f"{name}: incomplete slot limits")
                set_bounds(entry, group["min"], group["max"], group["id"])
        types = direct_profile_types(unit)
        if spec["weapon_display"] == "unit-conditional":
            expected = ["Units", "Ranged Weapons", "Melee Weapons", "Abilities", "Rules", "Keywords"]
            ordered = list(dict.fromkeys(types))
            require(ordered == expected, f"{name}: weapon-first section order lost: {ordered}")
            require(any(p.get("hidden") == "true" and p.find(N + "modifiers") is not None
                        for p in unit.findall("./" + N + "profiles/" + N + "profile")
                        if p.get("typeName") in ("Ranged Weapons", "Melee Weapons")),
                    f"{name}: no loadout-conditional unit weapons")
        elif spec["weapon_display"] == "model-owned":
            require("Ranged Weapons" not in types and "Melee Weapons" not in types,
                    f"{name}: accidental detached weapon profiles")
            require(any(p.get("typeName") in ("Ranged Weapons", "Melee Weapons")
                        for row in unit.iter(N + "selectionEntry")
                        for p in row.iter(N + "profile")),
                    f"{name}: model weapons missing")
        else:
            raise ValueError(f"{name}: unknown weapon display strategy")
    return template



def apply_datasheets(template: ET.Element, data: dict) -> ET.Element:
    """Apply canonical weapon stats, abilities, selection labels and equipment constraints."""
    require(data["schema_version"] == 1 and data["edition"] == "11th", "Unsupported datasheet format")
    units = direct_units(template)
    names = [u["id"] for u in data["units"]]
    require(len(names) == len(set(names)), "Duplicate structured unit IDs")
    require(set(names) == set(units),
            f"Structured datasheets must cover all units, missing={sorted(set(units)-set(names))}")
    for record in data["units"]:
        uid = record["id"]
        require(uid in units and units[uid].get("name") == record["name"], f"Missing unit {uid}")
        unit = units[uid]
        parents = {child: parent for parent in unit.iter() for child in parent}
        entries = {node.get("id"): node for node in unit.iter()
                   if node is not unit and node.tag in (N+"selectionEntry", N+"selectionEntryGroup")}
        require(set(entries) == {e["id"] for e in record["selections"]},
                f"{uid}: selection tree changed")
        for spec in record["selections"]:
            node = entries[spec["id"]]
            kind = "group" if node.tag == N+"selectionEntryGroup" else node.get("type")
            ancestor = parents[node]
            while ancestor.get("id") is None and ancestor is not unit:
                ancestor = parents[ancestor]
            require(kind == spec["kind"] and ancestor.get("id") == spec["parent_id"],
                    f"{uid}/{spec['id']}: equipment ownership changed")
            node.set("name", spec["name"])
            existing = bounds(node)
            require(set(existing) == set(spec.get("bounds", {})), f"{uid}/{spec['id']}: constraint keys changed")
            for bound, value in spec.get("bounds", {}).items():
                require(isinstance(value, int) and value >= 0, f"{uid}: invalid {bound}")
                existing[bound].set("value", str(value))
            if "min" in existing and "max" in existing:
                require(int(existing["min"].get("value")) <= int(existing["max"].get("value")),
                        f"{uid}/{spec['id']}: invalid bounds")
            default = spec.get("default_id")
            require(bool(node.get("defaultSelectionEntryId")) == bool(default),
                    f"{uid}/{spec['id']}: unexpected default selection")
            if default:
                choices = {e.get("id") for e in node.findall("./"+N+"selectionEntries/"+N+"selectionEntry")}
                require(default in choices, f"{uid}/{spec['id']}: missing default {default}")
                node.set("defaultSelectionEntryId", default)
        profiles = {p.get("id"): p for p in unit.iter(N+"profile")
                    if p.get("typeName") in ("Ranged Weapons", "Melee Weapons", "Abilities")}
        require(set(profiles) == {p["id"] for p in record["profiles"]}, f"{uid}: profiles changed")
        for spec in record["profiles"]:
            p = profiles[spec["id"]]
            require(p.get("typeName") == spec["type_name"], f"{uid}/{spec['id']}: profile type changed")
            require(parents[parents[p]].get("id") == spec["owner_id"],
                    f"{uid}/{spec['id']}: profile ownership changed")
            owner = parents[parents[p]]
            ancestors = []
            while owner is not unit:
                if owner.get("id") is not None:
                    ancestors.append(owner.get("id"))
                owner = parents[owner]
            require([uid] + ancestors[::-1] == spec["owner_path"], f"{uid}/{spec['id']}: model ancestry changed")
            require((p.find(N+"modifiers") is not None) == spec["has_modifiers"],
                    f"{uid}/{spec['id']}: visibility modifier lost")
            p.set("name", spec["name"])
            p.set("hidden", "true" if spec["hidden"] else "false")
            chars = p.findall("./"+N+"characteristics/"+N+"characteristic")
            require(len(chars) == len(spec["characteristics"]), f"{uid}/{spec['id']}: stats length changed")
            for char, datum in zip(chars, spec["characteristics"]):
                require(char.get("name") == datum["name"] and char.get("typeId") == datum["type_id"],
                        f"{uid}/{spec['id']}: stat field changed")
                char.text = datum["value"]
    return template


def apply_all(template: ET.Element, manifest: dict, datasheets: dict,
              mechanics: dict | None = None) -> ET.Element:
    if mechanics is None:
        mechanics = json.loads(MECHANICS.read_text(encoding="utf-8"))
    # Apply mechanics first; the dedicated points and equipment datasets
    # intentionally take precedence over overlapping generic metadata.
    apply_mechanics(template, mechanics, datasheets)
    apply_pilot(template, manifest)
    apply_datasheets(template, datasheets)
    return template


def canonical(root: ET.Element) -> str:
    return ET.canonicalize(ET.tostring(root, encoding="unicode"))


def check() -> None:
    source = ET.parse(CATALOGUE).getroot()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    datasheets = json.loads(DATASHEETS.read_text(encoding="utf-8"))
    built = apply_all(copy.deepcopy(source), manifest, datasheets)
    require(canonical(source) == canonical(built),
            "Structured data and checked-in catalogue differ. Regenerate and review differences.")
    require(source.get("revision") == str(manifest["source_revision"]),
            "Manifest source revision does not match checked-in catalogue")
    print(f"PASS: {len(datasheets['units'])} structured units, "
          f"{sum(len(u['profiles']) for u in datasheets['units'])} weapon/ability profiles, "
          f"{sum(len(u['selections']) for u in datasheets['units'])} model/gear entries "
          f"match v{source.get('revision')} with no XML changes")


def self_test() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ET.parse(CATALOGUE).getroot()
    datasheets = json.loads(DATASHEETS.read_text(encoding="utf-8"))
    baseline = apply_all(copy.deepcopy(source), manifest, datasheets)
    require(canonical(source) == canonical(baseline), "Baseline parity failed")
    altered = copy.deepcopy(manifest)
    altered["units"][0]["points"]["base"] += 5
    rebuilt = apply_all(copy.deepcopy(source), altered, datasheets)
    require(points_cost(direct_units(rebuilt)["fd-unit-root"]).get("value") ==
            str(altered["units"][0]["points"]["base"]), "Generator did not apply modified points")
    require(canonical(rebuilt) != canonical(source), "Generator ignored structured input")
    alternate = copy.deepcopy(datasheets)
    first = next(p for u in alternate["units"] for p in u["profiles"]
                 if p["type_name"] == "Ranged Weapons")
    stat = next(c for c in first["characteristics"] if c["name"] == "S")
    stat["value"] = "999"
    changed = apply_all(copy.deepcopy(source), manifest, alternate)
    require(canonical(changed) != canonical(source),
            "Changing structured weapon characteristics did not alter generated catalogue")
    ability_variant = copy.deepcopy(datasheets)
    ability = next(p for u in ability_variant["units"] for p in u["profiles"]
                   if p["type_name"] == "Abilities")
    ability["characteristics"][0]["value"] += " [STRUCTURED EDIT TEST]"
    assert canonical(apply_all(copy.deepcopy(source), manifest, ability_variant)) != canonical(source), (
        "Structured ability edits were ignored")
    selection_variant = copy.deepcopy(datasheets)
    choice = next(e for u in selection_variant["units"] for e in u["selections"]
                  if e["kind"] == "upgrade" and "bounds" not in e)
    choice["name"] += " (STRUCTURED EDIT TEST)"
    assert canonical(apply_all(copy.deepcopy(source), manifest, selection_variant)) != canonical(source), (
        "Structured wargear choice labels were ignored")
    mechanics = json.loads(MECHANICS.read_text(encoding="utf-8"))
    changed_rules = copy.deepcopy(mechanics)
    rule = next(r for u in changed_rules["units"] for r in u["native_rules"])
    rule["description"] += " [STRUCTURED EDIT TEST]"
    assert canonical(apply_all(copy.deepcopy(source), manifest, datasheets, changed_rules)) != canonical(source), (
        "Native rules text does not drive generation")
    changed_keywords = copy.deepcopy(mechanics)
    keyword = next(p for u in changed_keywords["units"] for p in u["unit_profiles"]
                   if p["attrs"].get("typeName") == "Keywords")
    keyword["characteristics"][0]["value"] += ", Structured Test"
    assert canonical(apply_all(copy.deepcopy(source), manifest, datasheets, changed_keywords)) != canonical(source), (
        "Structured keywords do not drive generation")
    changed_condition = copy.deepcopy(mechanics)
    condition = next(c for u in changed_condition["units"] for c in u["conditions"])
    condition["attrs"]["value"] = str(int(condition["attrs"]["value"]) + 1)
    assert canonical(apply_all(copy.deepcopy(source), manifest, datasheets, changed_condition)) != canonical(source), (
        "Structured modifier conditions do not drive generation")
    modified_cost = copy.deepcopy(mechanics)
    independent_unit = next(u for u in modified_cost["units"] if u["id"] == "unit-rangers-11e0")
    independent_unit["costs"][0]["attrs"]["value"] = str(
        int(independent_unit["costs"][0]["attrs"]["value"]) + 1)
    assert canonical(apply_all(copy.deepcopy(source), manifest, datasheets, modified_cost)) != canonical(source), (
        "Structured non-pilot point cost did not change generated catalogue")
    modified_category = copy.deepcopy(mechanics)
    category = next(c for u in modified_category["units"] for c in u["category_links"])
    category["name"] += " Test"
    assert canonical(apply_all(copy.deepcopy(source), manifest, datasheets, modified_category)) != canonical(source), (
        "Structured unit categories did not change generated catalogue")
    modified_constraints = copy.deepcopy(mechanics)
    ranger = next(u for u in modified_constraints["units"] if u["id"] == "unit-rangers-11e0")
    min_constraint = next(c for c in ranger["constraints"] if c["attrs"].get("type") == "min")
    min_constraint["attrs"]["shared"] = ("false" if min_constraint["attrs"].get("shared") == "true" else "true")
    assert canonical(apply_all(copy.deepcopy(source), manifest, datasheets, modified_constraints)) != canonical(source), (
        "Structured non-overlapping constraint attributes did not change generated catalogue")
    print("PASS: JSON controls points, weapons, abilities, gear labels, native rules, keywords, "
          "categories, limits and visibility conditions")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.check:
        check()
    elif args.self_test:
        self_test()
    else:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        datasheets = json.loads(DATASHEETS.read_text(encoding="utf-8"))
        result = apply_all(ET.parse(CATALOGUE).getroot(), manifest, datasheets)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(result).write(args.out, encoding="utf-8", xml_declaration=True)
        ET.parse(args.out)
        print(f"Generated {args.out} from {len(manifest['units'])} structured pilot units")


if __name__ == "__main__":
    main()
