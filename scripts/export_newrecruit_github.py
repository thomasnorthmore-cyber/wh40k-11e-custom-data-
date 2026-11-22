#!/usr/bin/env python3
"""Convert a local New Recruit IndexedDB books_data export to repo-ready JSON files.

Writes to a local directory, not GitHub. Preserves original nested content JSON.
Use only with data you have permission to publish or distribute.
"""
import argparse
import json
import re
from pathlib import Path

def safe_filename(value):
    value = Path(str(value or "")).name
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(". ")
    return value if value.endswith(".json") else value + ".json"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("backup", type=Path)
    p.add_argument("--out", type=Path, default=Path("newrecruit-repository-export"))
    args = p.parse_args()
    obj = json.loads(args.backup.read_text(encoding="utf-8"))
    system = obj.get("system", {})
    expected = str(system.get("id_game_system", system.get("id", "")))
    if not expected or not isinstance(obj.get("catalogues"), list):
        raise SystemExit("Not a recognized New Recruit books_data export")
    args.out.mkdir(parents=True, exist_ok=True)
    names = set()
    records = []
    for r in obj["catalogues"]:
        if str(r.get("id_game_system")) != expected:
            raise SystemExit("Mixed game systems; refusing to export")
        raw = r.get("content")
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(parsed, dict):
            raise SystemExit(f"Missing content in {r.get('name')}")
        if "catalogue" not in parsed and "gameSystem" not in parsed:
            # Auxiliary metadata, not a New Recruit game catalogue.
            continue
        name = safe_filename(r.get("filename") or r.get("name"))
        if name in names:
            name = safe_filename(str(r.get("id", "")) + "-" + name)
        names.add(name)
        dest = args.out / name
        dest.write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        records.append((name, r.get("name")))
    print(f"Wrote {len(records)} game/catalogue JSON files to {args.out}")
    for filename, title in records:
        print(f"{filename} <- {title}")
    print("Review licence and permissions before uploading the output to a public repository.")

if __name__ == "__main__":
    main()
