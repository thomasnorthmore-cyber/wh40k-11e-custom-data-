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

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "Aeldari 11e TEST.cat"
MANIFEST = ROOT / "data" / "structured" / "aeldari-pilot.json"
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


def canonical(root: ET.Element) -> str:
    return ET.canonicalize(ET.tostring(root, encoding="unicode"))


def check() -> None:
    source = ET.parse(CATALOGUE).getroot()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    built = apply_pilot(copy.deepcopy(source), manifest)
    require(canonical(source) == canonical(built),
            "Structured data and checked-in catalogue differ. Regenerate and review differences.")
    require(source.get("revision") == str(manifest["source_revision"]),
            "Manifest source revision does not match checked-in catalogue")
    print(f"PASS: {len(manifest['units'])} structured units match v{source.get('revision')} "
          "without any change to their selection IDs or equipment profiles")


def self_test() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = ET.parse(CATALOGUE).getroot()
    baseline = apply_pilot(copy.deepcopy(source), manifest)
    require(canonical(source) == canonical(baseline), "Baseline parity failed")
    altered = copy.deepcopy(manifest)
    altered["units"][0]["points"]["base"] += 5
    rebuilt = apply_pilot(copy.deepcopy(source), altered)
    require(points_cost(direct_units(rebuilt)["fd-unit-root"]).get("value") ==
            str(altered["units"][0]["points"]["base"]), "Generator did not apply modified points")
    require(canonical(rebuilt) != canonical(source), "Generator ignored structured input")
    print("PASS: changing structured points changes generated catalogue, baseline preserved")


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
        result = apply_pilot(ET.parse(CATALOGUE).getroot(), manifest)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(result).write(args.out, encoding="utf-8", xml_declaration=True)
        ET.parse(args.out)
        print(f"Generated {args.out} from {len(manifest['units'])} structured pilot units")


if __name__ == "__main__":
    main()
