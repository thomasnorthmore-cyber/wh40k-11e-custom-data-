#!/usr/bin/env python3
"""Apply structured Aeldari rules, categories, points and modifier metadata.

The v5 XML acts as a compatibility template. Structural parity prevents
accidental re-parenting: every record is matched by stable ID or validated
preorder index *and* its nearest identified owner. Never silently insert or
delete conditions, profiles, or weapon options.
"""
from __future__ import annotations

from collections import Counter
import xml.etree.ElementTree as ET

N = "{http://www.battlescribe.net/schema/catalogueSchema}"


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def ancestor_owner(node: ET.Element, unit: ET.Element, parents: dict) -> str:
    parent = parents[node]
    while parent is not unit and parent.get("id") is None:
        parent = parents[parent]
    return parent.get("id")


def apply_attributes(node: ET.Element, attrs: dict, label: str) -> None:
    need(set(node.attrib) == set(attrs),
         f"{label}: XML attribute keys changed: {set(node.attrib) ^ set(attrs)}")
    # Values are structured inputs; existing ID references and shape cannot
    # change without a reviewed schema/logic migration.
    for key in ("id", "typeId", "targetId", "childId"):
        if key in attrs:
            need(node.get(key) == attrs[key], f"{label}: forbidden {key} reference change")
    for key, value in attrs.items():
        need(isinstance(value, str), f"{label}: non-string XML attribute {key}")
        node.set(key, value)


def apply_mechanics(catalogue: ET.Element, data: dict, existing_datasheets: dict) -> ET.Element:
    need(data.get("schema_version") == 1 and data.get("edition") == "11th",
         "Unsupported structured mechanics version")
    entries = catalogue.find("./" + N + "selectionEntries")
    need(entries is not None, "Missing top-level unit entries")
    units = {node.get("id"): node for node in entries.findall(N + "selectionEntry")
             if node.get("type") == "unit"}
    names = [u["id"] for u in data["units"]]
    need(len(names) == len(set(names)) and set(names) == set(units),
         "Mechanics must describe each unit once, with no omissions")
    recorded = {u["id"]: {p["id"] for p in u["profiles"]}
                for u in existing_datasheets["units"]}
    for spec in data["units"]:
        uid = spec["id"]
        unit = units[uid]
        parents = {child: parent for parent in unit.iter() for child in parent}
        all_profiles = {p.get("id"): p for p in unit.iter(N + "profile")}
        extras = spec["unit_profiles"]
        extra_ids = [p["attrs"]["id"] for p in extras]
        need(len(extra_ids) == len(set(extra_ids)), f"{uid}: duplicate profile IDs")
        need(set(extra_ids) == set(all_profiles) - recorded[uid],
             f"{uid}: non-weapon/profile coverage differs from XML")
        for profile in extras:
            attrs = profile["attrs"]
            pid = attrs["id"]
            node = all_profiles[pid]
            need(ancestor_owner(node, unit, parents) == profile["owner_id"],
                 f"{uid}/{pid}: profile owner changed")
            apply_attributes(node, attrs, f"{uid}/{pid}")
            chars = node.findall("./" + N + "characteristics/" + N + "characteristic")
            need(len(chars) == len(profile["characteristics"]),
                 f"{uid}/{pid}: characteristic count changed")
            for item, value in zip(chars, profile["characteristics"]):
                apply_attributes(item, value["attrs"], f"{uid}/{pid}/characteristic")
                need(isinstance(value["value"], str), f"{uid}/{pid}: non-string characteristic")
                item.text = value["value"]
        rules = unit.findall("./" + N + "rules/" + N + "rule")
        need(len(rules) == len(spec["native_rules"]), f"{uid}: native rule count changed")
        for node, item in zip(rules, spec["native_rules"]):
            apply_attributes(node, item["attrs"], f"{uid}/rule")
            desc = node.find(N + "description")
            need(desc is not None, f"{uid}: native rule description missing")
            desc.text = item["description"]
        categories = unit.findall("./" + N + "categoryLinks/" + N + "categoryLink")
        need(len(categories) == len(spec["category_links"]),
             f"{uid}: category count changed")
        for node, attrs in zip(categories, spec["category_links"]):
            apply_attributes(node, attrs, f"{uid}/category")
        for key, tag in (
            ("modifiers", "modifier"),
            ("conditions", "condition"),
            ("condition_groups", "conditionGroup"),
            ("modifier_groups", "modifierGroup"),
            ("constraints", "constraint"),
            ("costs", "cost"),
        ):
            live = list(unit.iter(N + tag))
            saved = spec[key]
            need(len(live) == len(saved), f"{uid}: {tag} count changed")
            for index, (node, item) in enumerate(zip(live, saved)):
                need(item["index"] == index, f"{uid}: {tag} order mismatch")
                need(ancestor_owner(node, unit, parents) == item["owner_id"],
                     f"{uid}/{tag}[{index}]: owner changed")
                apply_attributes(node, item["attrs"], f"{uid}/{tag}[{index}]")
        need(unit.get("id") == uid, f"{uid}: unit ID changed")
    return catalogue
