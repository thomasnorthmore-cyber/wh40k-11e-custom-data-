#!/usr/bin/env python3
"""Audit and optionally normalize .ros/.rosz for Yellowscribe's 11e parser.

Yellowscribe's current parser dispatches on the exact 11e game-system ID and
expects profile type "Unit" rather than the custom catalogue's "Units".
This adapter fixes *only* those two format issues; it does not silently
duplicate, move or invent weapons. A report flags weapon profiles attached
directly to the unit: the parser's model-level weapon handler will not see them.

Usage:
  python scripts/yellowscribe_compat.py --self-test
  python scripts/yellowscribe_compat.py --audit "list.rosz"
  python scripts/yellowscribe_compat.py --convert "list.rosz" --out "converted.rosz"
"""
from __future__ import annotations

import argparse
from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

EXPECTED_ID = "sys-352e-adc2-7639-d610"
CUSTOM_ID = "a78e-11e0-40k0-0001"
WEAPONS = {"Ranged Weapons", "Melee Weapons"}


def read_roster(path: Path):
    raw = path.read_bytes()
    zipped = raw[:4] == b"PK\\x03\\x04"
    if zipped:
        with ZipFile(BytesIO(raw)) as archive:
            filenames = [n for n in archive.namelist() if not n.endswith("/")]
            if len(filenames) != 1:
                raise ValueError("Yellowscribe expects exactly one roster XML file per .rosz")
            name = filenames[0]
            xml = archive.read(name)
    else:
        name, xml = path.name, raw
    root = ET.fromstring(xml)
    if root.tag.split("}")[-1] != "roster":
        raise ValueError("Not a BattleScribe roster XML root")
    return root, zipped, name


def selection_profiles(selection):
    return selection.findall("./{*}profiles/{*}profile")


def inspect(root):
    unit_roots = [e for e in root.iter()
                  if e.tag.split("}")[-1] == "selection" and e.get("type") == "unit"]
    found = Counter(p.get("typeName") for p in root.iter()
                    if p.tag.split("}")[-1] == "profile")
    detached = [(u.get("name"), p.get("name")) for u in unit_roots
                for p in selection_profiles(u) if p.get("typeName") in WEAPONS]
    return {"system_id": root.get("gameSystemId"),
            "units": len(unit_roots), "profiles": dict(found),
            "unit_root_weapons": detached}


def normalize(root):
    if root.get("gameSystemId") not in (CUSTOM_ID, EXPECTED_ID):
        raise ValueError("Not our custom game system or the expected 11e system")
    root.set("gameSystemId", EXPECTED_ID)
    corrected = 0
    for p in root.iter():
        if p.tag.split("}")[-1] == "profile" and p.get("typeName") == "Units":
            p.set("typeName", "Unit")
            corrected += 1
    return corrected


def write_roster(root, path, zipped, name):
    uri = root.tag.split("}")[0][1:] if "}" in root.tag else ""
    if uri:
        ET.register_namespace("", uri)
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if zipped:
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr(name, xml)
    else:
        path.write_bytes(xml)


def self_test():
    sample = ET.fromstring('''<roster gameSystemId="a78e-11e0-40k0-0001">
        <forces><force><selections><selection name="Test squad" type="unit">
        <profiles><profile name="Test" typeName="Units"/></profiles>
        <selections><selection name="Test model" type="model">
        <profiles><profile name="Ranged" typeName="Ranged Weapons"/></profiles>
        </selection></selections></selection></selections></force></forces></roster>''')
    first = inspect(sample)
    assert first["profiles"]["Units"] == 1
    assert first["profiles"]["Ranged Weapons"] == 1
    assert normalize(sample) == 1
    second = inspect(sample)
    assert second["system_id"] == EXPECTED_ID
    assert second["profiles"]["Unit"] == 1
    assert second["unit_root_weapons"] == []
    unit = next(x for x in sample.iter("selection") if x.get("type") == "unit")
    ET.SubElement(unit.find("profiles"), "profile", name="Root gun", typeName="Ranged Weapons")
    assert inspect(sample)["unit_root_weapons"] == [("Test squad", "Root gun")]
    print("PASS: 11e ID and Unit-profile normalization; root-weapon incompatibility flagged")


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--audit", type=Path)
    mode.add_argument("--convert", type=Path)
    p.add_argument("--out", type=Path)
    opts = p.parse_args()
    if opts.self_test:
        self_test()
        return
    source = opts.audit or opts.convert
    root, zipped, name = read_roster(source)
    if opts.convert:
        if not opts.out:
            p.error("--convert requires --out")
        changes = normalize(root)
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        write_roster(root, opts.out, zipped, name)
        print(f"Normalized {changes} Unit profile types; exported {opts.out}")
    report = inspect(root)
    print(f"Roster system={report['system_id']}, units={report['units']}, "
          f"profile types={report['profiles']}")
    for unit, weapon in report["unit_root_weapons"]:
        print(f"WARNING: unit-root weapon may be ignored by Yellowscribe: {unit}: {weapon}")


if __name__ == "__main__":
    main()
