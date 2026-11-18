#!/usr/bin/env python3
"""Validate the 22 pipe-separated 11e CSV source tables. Usage: python scripts/validate_export.py /path/to/csv"""
import csv, json, pathlib, sys

REQUIRED = [
 "Abilities.csv", "Datasheets.csv", "Datasheets_abilities.csv",
 "Datasheets_detachment_abilities.csv", "Datasheets_enhancements.csv",
 "Datasheets_keywords.csv", "Datasheets_leader.csv", "Datasheets_models.csv",
 "Datasheets_models_cost.csv", "Datasheets_options.csv", "Datasheets_stratagems.csv",
 "Datasheets_unit_composition.csv", "Datasheets_wargear.csv", "Detachment_abilities.csv",
 "Detachments.csv", "Detachments_chapter_dp.csv", "Enhancements.csv",
 "Enhancements_wargear.csv", "Factions.csv", "Last_update.csv", "Source.csv",
 "Stratagems.csv"
]
LINKS = [
 ("Datasheets.csv", "faction_id", "Factions.csv", "id"),
 ("Datasheets_wargear.csv", "datasheet_id", "Datasheets.csv", "id"),
 ("Datasheets_models.csv", "datasheet_id", "Datasheets.csv", "id"),
 ("Datasheets_models_cost.csv", "datasheet_id", "Datasheets.csv", "id"),
 ("Detachments.csv", "faction_id", "Factions.csv", "id"),
]
def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="|"))

def main(root):
    root = pathlib.Path(root)
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        print(json.dumps({"status": "missing source files", "missing": missing}, indent=2))
        return 2
    data = {name: load(root / name) for name in REQUIRED}
    report = {"files_loaded": len(data), "rows": {k: len(v) for k, v in data.items()}, "orphan_references": []}
    for child, foreign_key, parent, primary_key in LINKS:
        parent_ids = {r.get(primary_key, "") for r in data[parent]}
        orphans = [r[foreign_key] for r in data[child] if r.get(foreign_key) and r[foreign_key] not in parent_ids]
        report["orphan_references"].append({
            "from": child + "." + foreign_key,
            "to": parent + "." + primary_key,
            "rows": len(orphans), "distinct_ids": sorted(set(orphans))
        })
    report["faction_count"] = len(data["Factions.csv"])
    report["status"] = "passed" if not any(x["rows"] for x in report["orphan_references"]) else "review_required"
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
