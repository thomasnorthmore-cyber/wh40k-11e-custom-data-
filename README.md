# Warhammer 40,000 11th Edition — Custom New Recruit data

This project aims to provide New Recruit-compatible custom game-system and faction catalogues covering **all 25 factions** in the source export.

> **Status: full Aeldari v7 preview generation (99 source datasheets), preserving the 17 verified v6 units.** New Recruit rendering still requires manual verification, and Yellowscribe compatibility remains unresolved. Raw Wahapedia CSV exports are not directly importable as game catalogues.

## All Aeldari datasheets from the user's export

The original user-uploaded 11th Edition Wahapedia source archive includes
**99 Aeldari datasheets**. The first 17 were already hand-tested in v6.
The new source datasets include all 99 datasheet records plus their Aeldari
model stats, weapons, costs, composition, options, abilities, keywords, and
Leader attachment relationships.

- `data/structured/aeldari-source-datasheets.json`
- `data/structured/source/` (source-specific linked tables)

`scripts/expand_aeldari.py` reconstructs the Aeldari catalogue with
**82 additional datasheets** while retaining the entire set of original
17 v6 entries unchanged. To generate a preview:

```sh
python scripts/expand_aeldari.py --out /tmp/aeldari-full-preview.cat
python scripts/validate_full_aeldari.py /tmp/aeldari-full-preview.cat
```

The new source-driven units include their model characteristics, all ranged
and melee weapon profiles, abilities, unit composition, keyword definitions,
points tables and written wargear options. **Replacement restrictions for
complex new units are not yet translated into fully enforced selectors.**
Those entries show their exact source options in Rules and expose provisional
model-level weapons, pending detailed legal-loadout configuration. The existing
17 tested units are not changed.

The `publish-aeldari-full.yml` GitHub Action validates and publishes v7 to
`main` when the source importer is merged. New Recruit can then refresh
the existing custom Aeldari catalogue from the same GitHub file.

## New Recruit preview release — v6

The catalogue revision is now **v6** for New Recruit refresh testing.
The content of the unit definitions, profiles, costs and equipment selections
is intentionally **identical to v5**. The revision bump exposes the mature
JSON exporter pipeline to the same GitHub-based update path; the CI release
check asserts that only the revision changed.

Refresh the Aeldari test catalogue in New Recruit and confirm its version
shows v6. There are **no new visible weapon or model-layout changes in this
release**. Yellowscribe compatibility also remains a separate workstream.

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
