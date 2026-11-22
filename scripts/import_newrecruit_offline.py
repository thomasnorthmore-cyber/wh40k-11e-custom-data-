#!/usr/bin/env python3
"""Inspect and locally import a New Recruit IndexedDB books_data export.

No network calls. Does not publish or redistribute source catalogue content.
The original downloaded data remains in the user's local file.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

EXPECTED_SYSTEM_ID = 827374861
ROOT_COLLECTIONS = (
    "selectionEntries", "sharedSelectionEntries",
    "selectionEntryGroups", "sharedSelectionEntryGroups",
    "entryLinks", "selectionEntryGroupLinks", "catalogueLinks",
    "sharedProfiles", "sharedRules", "rules", "categoryEntries",
)

def load_export(path: Path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("catalogues"), list):
        raise ValueError("Expected an export object with a catalogues array")
    source = doc["catalogues"]
    if not source:
        raise ValueError("Export contains no catalogue records")
    return doc, source

def parse_record(record, expected_id):
    if not isinstance(record, dict):
        raise ValueError("Catalogue record is not an object")
    if str(record.get("id_game_system")) != str(expected_id):
        raise ValueError("Mixed game-system IDs in input")
    raw = record.get("content")
    if isinstance(raw, str):
        data = json.loads(raw)
    elif isinstance(raw, dict):
        data = raw
    else:
        raise ValueError("Catalogue has no readable content")
    if not isinstance(data, dict):
        raise ValueError("Catalogue content must decode to an object")
    root_type = "gameSystem" if "gameSystem" in data else "catalogue" if "catalogue" in data else "data"
    root = data.get(root_type, data)
    if not isinstance(root, dict):
        raise ValueError("Catalogue root must be an object")
    return root_type, root, data

def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)

def audit(path: Path, manifest_path: Path | None):
    doc, records = load_export(path)
    system = doc.get("system") or {}
    expected_id = system.get("id_game_system") or system.get("id") or EXPECTED_SYSTEM_ID
    parsed = []
    failures = []
    for idx, record in enumerate(records):
        try:
            root_type, root, _ = parse_record(record, expected_id)
            counts = {k: len(root[k]) for k in ROOT_COLLECTIONS if isinstance(root.get(k), list)}
            parsed.append({"index": idx, "name": record.get("name"), "filename": record.get("filename"),
                           "id": record.get("id"), "bsid": record.get("bsid"),
                           "gameSystemId": record.get("id_game_system"),
                           "rootId": root.get("id"), "rootType": root_type,
                           "revision": root.get("revision"), "collections": counts,
                           "references": sorted({str(n["targetId"]) for n in walk(root)
                                                  if n.get("type") == "catalogue" and n.get("targetId")})})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            failures.append({"index": idx, "name": record.get("name"), "error": str(exc)})
    root_ids = {str(r["rootId"]) for r in parsed if r.get("rootId")}
    unresolved = []
    for entry in parsed:
        for target in entry["references"]:
            if target not in root_ids:
                unresolved.append({"catalogue": entry["name"], "targetId": target})
    summary = {
        "format": "newrecruit-indexeddb-books-data-v1",
        "sourceSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "systemId": expected_id,
        "recordCount": len(records),
        "parsedCount": len(parsed),
        "failedCount": len(failures),
        "rootTypes": dict(Counter(x["rootType"] for x in parsed)),
        "unresolvedCatalogueLinks": unresolved,
        "failures": failures,
        "catalogues": parsed,
    }
    print(f"System {expected_id}: {len(parsed)}/{len(records)} parsed; "
          f"{len(unresolved)} unresolved catalogue links")
    for entry in parsed:
        print(f"  [{entry['rootType']}] {entry['name']} ({entry['filename']})")
    if failures:
        for problem in failures:
            print(f"ERROR: {problem}")
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote local audit: {manifest_path}")
    return 1 if failures or unresolved else 0

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="New Recruit locally exported JSON")
    parser.add_argument("--manifest", type=Path, help="Optional LOCAL audit file (do not commit source data)")
    args = parser.parse_args()
    raise SystemExit(audit(args.export, args.manifest))

if __name__ == "__main__":
    main()
