# Warhammer 40,000 11th Edition — Custom New Recruit data

This project aims to provide New Recruit-compatible custom game-system and faction catalogues covering **all 25 factions** in the source export.

> **Status: working Aeldari v5 test catalogue (17 units), with an incremental data-first generator pilot.** New Recruit rendering still requires manual verification, and Yellowscribe compatibility remains unresolved. Raw Wahapedia CSV exports are not directly importable as game catalogues.

## Structured-data generator pilot

Inspired by the explicit unit compositions, equipment constraints, and BSData
exporter in [40kdc-data](https://github.com/wn-mitch/40kdc-data), this
repository now has a **five-unit structured pilot** in
[`data/structured/aeldari-pilot.json`](data/structured/aeldari-pilot.json).

The generator currently reads structured model counts, squad points, and
selected wargear choice limits into the existing catalogue template. It **does
not** yet generate every weapon, model, ability or faction. The original
catalogue is still the compatibility baseline while that migration proceeds.

```sh
python scripts/build_catalogue.py --check
python scripts/build_catalogue.py --self-test
python scripts/build_catalogue.py --out /tmp/Aeldari-generated.cat
```

See [structured migration documentation](data/structured/README.md).

## Roadmap

- [x] Establish a New Recruit-compatible test catalogue with 17 Aeldari units.
- [ ] Audit and map all 22 source CSV tables and their identifiers.
- [ ] Generate the entire game system and faction catalogues from structured data (five-unit pilot started).
- [ ] Translate unit sizes, points, equipment options, leaders, detachments and enhancements into enforceable selections.
- [ ] Validate every faction, New Recruit display and Yellowscribe roster export end-to-end.
- [ ] Document update and installation workflow.

## Data and licensing

The original 22 CSV tables were supplied separately and **are not committed here**. This repository is public: verify rights to redistribute source rules text and third-party data before publishing it.

We will preserve source IDs for traceability and flag unresolved links instead of silently discarding records.
