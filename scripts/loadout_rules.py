#!/usr/bin/env python3
"""Validate structured equipment slots and apply legal limits to a catalogue.

This records exact slot membership, weapon bindings and model-specific choice
budgets. A slot is an equipment replacement *only* within its own model row.
It does NOT claim to derive every rulebook swap prerequisite from the template.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

N = "{http://www.battlescribe.net/schema/catalogueSchema}"
ROOT = Path(__file__).resolve().parents[1]
SLOTS = ROOT / "data" / "structured" / "aeldari-loadout-slots.json"
SHEETS = ROOT / "data" / "structured" / "aeldari-datasheets.json"
CAT = ROOT / "Aeldari 11e TEST.cat"


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def configurations(slot):
    """All one-model/one-unit choice vectors respecting limits and total picks."""
    choices = slot["choices"]
    for counts in itertools.product(*(range(c["max"] + 1) for c in choices)):
        if slot["min"] <= sum(counts) <= slot["max"]:
            yield dict(zip((c["id"] for c in choices), counts))


def valid(slot, counts):
    allowed = {c["id"]: c["max"] for c in slot["choices"]}
    if set(counts) - set(allowed):
        return False
    if any(not isinstance(n, int) or n < 0 or n > allowed[c] for c,n in counts.items()):
        return False
    return slot["min"] <= sum(counts.values()) <= slot["max"]


def assert_model_scope(unit, slot):
    entries = {s["id"]: s for s in unit["selections"]}
    gid = slot["slot_id"]
    require(gid in entries and entries[gid]["kind"] == "group",
            f"{unit['name']}: slot group missing {gid}")
    group = entries[gid]
    require(group.get("bounds") == {"min": slot["min"], "max": slot["max"]},
            f"{unit['name']}/{gid}: selection limits differ")
    require(group.get("default_id") == slot["default_choice_id"],
            f"{unit['name']}/{gid}: default selection differs")
    expect = sorted(x["id"] for x in unit["selections"]
                    if x["parent_id"] == gid and x["kind"] == "upgrade")
    actual = sorted(x["id"] for x in slot["choices"])
    require(actual == expect, f"{unit['name']}/{gid}: choice set drift")
    parent = entries.get(group["parent_id"])
    while parent is not None and parent["kind"] != "model":
        parent = entries.get(parent["parent_id"])
    model = parent["id"] if parent else None
    require(slot["model_id"] == model, f"{unit['name']}/{gid}: not scoped to correct model")
    require(slot["scope"] == ("per_model" if model else "per_unit"),
            f"{unit['name']}/{gid}: incorrect model budget scope")
    for c in slot["choices"]:
        choice = entries[c["id"]]
        # Human-readable choice names are owned by aeldari-datasheets.json;
        # renames must not invalidate a stable-ID equipment relationship.
        require(c["max"] == choice.get("bounds", {}).get("max", slot["max"]),
                f"{unit['name']}/{gid}/{c['id']}: max differs")
        profiles = sorted(p["id"] for p in unit["profiles"]
                          if c["id"] in p["owner_path"]
                          and p["type_name"] in ("Ranged Weapons","Melee Weapons"))
        require(sorted(c["weapon_profile_ids"]) == profiles,
                f"{unit['name']}/{gid}/{c['id']}: weapon/profile bindings changed")
        require(c["max"] <= slot["max"], f"{unit['name']}/{gid}: gear exceeds slot budget")


def validate(data, sheets):
    require(data.get("schema_version") == 1 and data.get("edition") == "11th",
            "Unknown slot data version")
    by_id = {u["id"]:u for u in sheets["units"]}
    require(len(data["units"]) == len(by_id), "Slot coverage must contain all 17 units")
    require({u["id"] for u in data["units"]} == set(by_id), "Missing unit slot metadata")
    count = 0
    for row in data["units"]:
        unit = by_id[row["id"]]
        require(row["name"] == unit["name"], "Unit name drift")
        seen = set()
        for slot in row["slots"]:
            gid=slot["slot_id"]
            require(gid not in seen, f"Duplicate slot {gid}")
            seen.add(gid)
            require(0 <= slot["min"] <= slot["max"] <= 20,
                    f"{gid}: unsupported pick count")
            require(slot["kind"] in ("exclusive_replacement","counted_replacement",
                                    "optional_addition","required_choice"), f"{gid}: invalid kind")
            if slot["kind"] == "exclusive_replacement":
                require(slot["min"] == slot["max"] == 1, f"{gid}: not exclusive")
            if slot["default_choice_id"]:
                require(slot["default_choice_id"] in {c["id"] for c in slot["choices"]},
                        f"{gid}: missing default option")
            assert_model_scope(unit,slot)
            legal = list(configurations(slot))
            require(legal, f"{gid}: no valid loadout")
            require(all(valid(slot, x) for x in legal), f"{gid}: enumeration invalid")
            for c in slot["choices"]:
                require(not valid(slot, {c["id"]: c["max"] + 1}),
                        f"{gid}: exceeding per-item bound should be illegal")
            if slot["min"] > 0:
                require(not valid(slot, {}), f"{gid}: empty loadout wrongly legal")
            if slot["max"] < sum(c["max"] for c in slot["choices"]):
                require(not valid(slot, {c["id"]:c["max"] for c in slot["choices"]}),
                        f"{gid}: over-filling slot must be illegal")
            count += 1
    return count


def apply(catalogue, data, sheets):
    validate(data, sheets)
    units = {u.get("id"):u for u in catalogue.findall("./"+N+"selectionEntries/"+N+"selectionEntry")}
    for row in data["units"]:
        unit=units[row["id"]]
        nodes={n.get("id"):n for n in unit.iter() if n.get("id")}
        for slot in row["slots"]:
            node=nodes[slot["slot_id"]]
            limits={c.get("type"):c for c in node.findall("./"+N+"constraints/"+N+"constraint") if c.get("field")=="selections"}
            require("min" in limits and "max" in limits, f"{slot['slot_id']}: missing bounds")
            limits["min"].set("value",str(slot["min"]))
            limits["max"].set("value",str(slot["max"]))
            if slot["default_choice_id"]:
                node.set("defaultSelectionEntryId",slot["default_choice_id"])
            for choice in slot["choices"]:
                item=nodes[choice["id"]]
                bound=[c for c in item.findall("./"+N+"constraints/"+N+"constraint") if c.get("type")=="max" and c.get("field")=="selections"]
                if bound:
                    bound[0].set("value",str(choice["max"]))
                else:
                    require(choice["max"] == slot["max"],
                            f"{slot['slot_id']}/{choice['id']}: need explicit choice max")
    return catalogue


def self_test():
    data=json.loads(SLOTS.read_text())
    sheets=json.loads(SHEETS.read_text())
    n=validate(data,sheets)
    byid={u["id"]:u for u in data["units"]}
    checks=[
        ("fd-unit-root","fd-exarch-gear-5",
         [{"fd-gear-default-5":1},{"fd-gear-flamer-5":1},
          {"fd-gear-default-5":1,"fd-gear-flamer-5":1},{}],
         [True,True,False,False]),
        ("dr-unit-root","dr-exarch-gear",
         [{"dr-exarch-choice-missile":1},{"dr-exarch-choice-missile":1,
          "dr-exarch-choice-tempest":1}], [True,False]),
        ("smoke-unit-591","mul-591-bike",
         [{"mul-591-bike-scatter":1},
          {"mul-591-bike-scatter":1,"mul-591-bike-shuriken":1}], [True,False]),
        ("smoke-unit-612","mul-612-mounts",
         [{"mul-612-mounts-bright":2},
          {"mul-612-mounts-bright":1,"mul-612-mounts-star":1},
          {"mul-612-mounts-bright":3},
          {"mul-612-mounts-bright":1}], [True,True,False,False]),
        ("smoke-unit-613","wl-group-arms",
         [{"wl-arms-flamer":2},
          {"wl-arms-flamer":1,"wl-arms-catapult":1},
          {"wl-arms-flamer":1}], [True,True,False]),
        ("smoke-unit-613","wl-group-heavy",
         [{},{"wl-heavy-bright":2},{"wl-heavy-bright":2,"wl-heavy-star":1}],
         [True,True,False]),
    ]
    for unit,gid,cases,expected in checks:
        slot=next(s for s in byid[unit]["slots"] if s["slot_id"]==gid)
        actual=[valid(slot,x) for x in cases]
        require(actual==expected, f"{gid}: illegal/valid loadout regression {actual} != {expected}")
    root=ET.parse(CAT).getroot()
    before=ET.canonicalize(ET.tostring(root,encoding="unicode"))
    apply(root,data,sheets)
    after=ET.canonicalize(ET.tostring(root,encoding="unicode"))
    require(before==after, "Slot constraints do not reproduce live v5 catalogue")
    print(f"PASS: {n} scoped equipment slots match catalogue; loadout legality fixtures pass")


if __name__=="__main__":
    self_test()
