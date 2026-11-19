# Warhammer 40,000 11th Edition — Custom New Recruit data

This project aims to provide New Recruit-compatible custom game-system and faction catalogues covering **all 25 factions** in the source export.

> **Status: working Aeldari v5 test catalogue (17 units), with an incremental data-first generator pilot.** New Recruit rendering still requires manual verification, and Yellowscribe compatibility remains unresolved. Raw Wahapedia CSV exports are not directly importable as game catalogues.

## Structured-data generator

The repository now includes a **17-unit Aeldari structured-datasheet layer**
[`aeldari-datasheets.json`](data/structured/aeldari-datasheets.json) with
145 weapon/ability profiles and 152 model/equipment choice records, alongside
the original five-unit structured model-count/points pilot in
[`aeldari-pilot.json`](data/structured/aeldari-pilot.json).

The generator applies all structured weapon statistics, ability descriptions,
equipment selection labels, model/gear hierarchy, bounds and recorded defaults
to the preserved v5 catalogue template. A no-change parity check verifies that
the generated catalogue still exactly matches the working baseline. This is
**not yet a fully standalone BSData exporter**: other unit profiles and
conditional modifier expressions still come from the XML template.

```sh
python scripts/build_catalogue.py --check
python scripts/build_catalogue.py --self-test
python scripts/build_catalogue.py --out /tmp/Aeldari-generated.cat
```

See [structured migration documentation](data/structured/README.md).

## Standalone catalogue export

Both the Aeldari catalogue and custom 11th Edition game-system XML can now
be generated directly from JSON, without loading the existing XML template.

```sh
python scripts/export_standalone.py --check
python scripts/export_standalone.py --out-dir /tmp/standalone
python scripts/yellowscribe_compat.py --audit my-roster.rosz
```

The first version uses a JSON representation of the legacy XML structure,
overlaid with our four structured Aeldari data layers. It is independent of
the original `.cat` as a generation input, but it is not yet a fully
semantic, faction-generic New Recruit JSON exporter.

Yellowscribe formatting can be checked and normalized with
`scripts/yellowscribe_compat.py`; models with root-level weapons may
still require a proper model-ownership export fix.

## Roadmap

- [x] Establish a New Recruit-compatible test catalogue with 17 Aeldari units.
- [ ] Audit and map all 22 source CSV tables and their identifiers.
- [ ] Generate the entire game system and faction catalogues from structured data (all 17 units have structured weapon/ability and equipment records; full independent exporter still pending).
- [ ] Translate unit sizes, points, equipment options, leaders, detachments and enhancements into enforceable selections.
- [ ] Validate every faction, New Recruit display and Yellowscribe roster export end-to-end.
- [ ] Document update and installation workflow.

## Data and licensing

The original 22 CSV tables were supplied separately and **are not committed here**. This repository is public: verify rights to redistribute source rules text and third-party data before publishing it.

We will preserve source IDs for traceability and flag unresolved links instead of silently discarding records.
