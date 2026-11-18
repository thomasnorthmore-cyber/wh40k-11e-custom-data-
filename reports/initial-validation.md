# Initial 22-file CSV validation — 18 November 2026

The audit was run against the user's uploaded 22 pipe-separated CSV files. The original data is **not** committed to this public repository.

| Check | Result |
| --- | --- |
| Source files readable | 22 of 22 |
| Faction records | 25 |
| Datasheet records | 1,485 |
| Datasheet faction reference failures | 0 |
| Weapon parent-datasheet reference failures | 24 rows, 18 distinct IDs |
| Model parent-datasheet reference failures | 4 rows, 4 distinct IDs |
| Points parent-datasheet reference failures | 0 |
| Detachment faction reference failures | 0 |

**Result: source-link audit needs review.**

These results do not establish whether all units, rules or legal selections are correct. They also do not establish New Recruit compatibility: the repository currently has no tested `.gst` or `.cat` catalogues.

Run the test with all 22 source files in a local folder:

```bash
python scripts/validate_export.py /path/to/csv-folder
```

The script returns a nonzero exit code if missing source files or orphaned references are detected.
