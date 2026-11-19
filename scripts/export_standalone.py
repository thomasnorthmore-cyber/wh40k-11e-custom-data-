#!/usr/bin/env python3
"""Standalone JSON → BattleScribe XML exporter.

Does not read the existing .cat or .gst for generation. The v5 XML files are
used only by --check as regression fixtures. A JSON XML-tree bootstrap holds
the remaining structure while the explicit mechanics/datasheets/loadout data
layers progressively replace it.

    python scripts/export_standalone.py --check
    python scripts/export_standalone.py --self-test
    python scripts/export_standalone.py --out-dir /tmp/standalone
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import build_catalogue as legacy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "structured"
GAME_SYSTEM = "Warhammer 40,000 11e Custom TEST.gst"
CATALOGUE = "Aeldari 11e TEST.cat"
CAT_TREE = DATA / "catalogue-tree.json"
GAME_TREE = DATA / "game-system-tree.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def from_tree(record: dict, namespace: str) -> ET.Element:
    name = record["tag"]
    if name not in ("catalogue", "gameSystem") and ":" in name:
        # Only default namespace XML exists in the known v5 snapshot.
        raise ValueError(f"Unsupported namespace-qualified element {name}")
    if name in ("catalogue", "gameSystem"):
        assert record["attrs"].get("xmlns") == namespace, "Unexpected root namespace"
    attrs = {k: v for k, v in record["attrs"].items() if k != "xmlns"}
    require(all(isinstance(v, str) for v in attrs.values()), "XML attributes must be strings")
    node = ET.Element("{" + namespace + "}" + name, attrs)
    node.text = record.get("text")
    node.tail = record.get("tail")
    for item in record["children"]:
        node.append(from_tree(item, namespace))
    return node


def build_system(tree: dict | None = None) -> ET.Element:
    tree = tree if tree is not None else read_json(GAME_TREE)
    require(tree["schema_version"] == 1 and tree["format"] == "battlescribe-xml-tree",
            "Unknown game-system tree version")
    root = tree["node"]
    require(root["tag"] == "gameSystem", "Expected .gst root")
    return from_tree(root, "http://www.battlescribe.net/schema/gameSystemSchema")


def build_catalogue(
    tree: dict | None = None,
    *,
    pilot: dict | None = None,
    datasheets: dict | None = None,
    mechanics: dict | None = None,
    slots: dict | None = None,
) -> ET.Element:
    tree = tree if tree is not None else read_json(CAT_TREE)
    require(tree["schema_version"] == 1 and tree["format"] == "battlescribe-xml-tree",
            "Unknown catalogue tree version")
    require(tree["node"]["tag"] == "catalogue", "Expected .cat root")
    root = from_tree(tree["node"], "http://www.battlescribe.net/schema/catalogueSchema")
    # The overlay compiler builds the catalogue entirely in memory from JSON.
    # Its original compatibility template is NOT read or fetched.
    return legacy.apply_all(
        root,
        pilot if pilot is not None else read_json(legacy.MANIFEST),
        datasheets if datasheets is not None else read_json(legacy.DATASHEETS),
        mechanics if mechanics is not None else read_json(legacy.MECHANICS),
        slots if slots is not None else read_json(legacy.SLOTS),
    )


def canonical(node: ET.Element) -> str:
    return ET.canonicalize(ET.tostring(node, encoding="unicode"))


def serialize(node: ET.Element) -> bytes:
    uri = node.tag.split("}")[0][1:]
    ET.register_namespace("", uri)
    return ET.tostring(node, encoding="utf-8", xml_declaration=True)


def check() -> None:
    result = build_catalogue()
    system = build_system()
    published = ET.parse(ROOT / CATALOGUE).getroot()
    expected_revision = str(int(result.get("revision")) + 1)
    require(published.get("revision") in (result.get("revision"), expected_revision),
            "Unexpected published catalogue revision")
    # The version number is release metadata, not a data/rules difference.
    published.set("revision", result.get("revision"))
    require(canonical(result) == canonical(published),
            "Standalone catalogue differs from published XML beyond revision")
    require(canonical(system) == canonical(ET.parse(ROOT / GAME_SYSTEM).getroot()),
            "Standalone game system differs from existing fixture")
    require(result.get("gameSystemId") == system.get("id"), "Game system ID differs")
    # The game system revision stored in catalogue must match the source.
    require(result.get("gameSystemRevision") == system.get("revision"),
            "Game system revision differs")
    print("PASS: JSON-only exporter reproduces v5 catalogue and game system")


def self_test() -> None:
    # This demonstrates that production exports don't open or depend on the
    # legacy XML template, which is used only by the optional --check command.
    old = legacy.CATALOGUE
    try:
        legacy.CATALOGUE = ROOT / "deliberately-absent-legacy-template.cat"
        baseline = build_catalogue()
    finally:
        legacy.CATALOGUE = old
    require(baseline.get("revision") == "5", "Unexpected catalogue revision")
    tree = read_json(CAT_TREE)
    changed = copy.deepcopy(tree)
    changed["node"]["attrs"]["name"] += " Standalone Test"
    generated = build_catalogue(changed)
    require(generated.get("name").endswith("Standalone Test"),
            "Structured root metadata mutation did not affect output")
    datasheets = read_json(legacy.DATASHEETS)
    altered = copy.deepcopy(datasheets)
    profile = next(p for u in altered["units"] for p in u["profiles"]
                   if p["type_name"] == "Ranged Weapons")
    profile["characteristics"][0]["value"] = '99"'
    generated = build_catalogue(datasheets=altered)
    require(canonical(generated) != canonical(baseline),
            "Structured weapon change did not affect standalone output")
    system = build_system()
    require(serialize(system).startswith(b"<?xml"), "Game system export missing declaration")
    require(serialize(baseline).startswith(b"<?xml"), "Catalogue export missing declaration")
    print("PASS: standalone exporter needs no legacy XML template and responds to JSON edits")


def main() -> None:
    p = argparse.ArgumentParser()
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--out-dir", type=Path)
    args = p.parse_args()
    if args.check:
        check()
    elif args.self_test:
        self_test()
    else:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for filename, tree in [(CATALOGUE, build_catalogue()), (GAME_SYSTEM, build_system())]:
            output = args.out_dir / filename
            output.write_bytes(serialize(tree))
            ET.parse(output)
            print(f"Wrote {output}")


if __name__ == "__main__":
    main()
