# Structured catalogue pilot

This folder starts migrating from hand-edited BattleScribe XML to a canonical
data layer, inspired by the separation of unit composition, weapons, and
wargear rules in [40kdc-data](https://github.com/wn-mitch/40kdc-data).

## Current scope

`aeldari-pilot.json` owns **model-count constraints, points tiers, selected
wargear group bounds/defaults, and display strategy** for exactly five units:
Fire Dragons, Dark Reapers, Windriders, War Walkers and Wraithlord.

The existing checked-in `Aeldari 11e TEST.cat` remains the **template and
authority for other fields** (weapons, statistics, abilities, keywords, rules,
unit selection trees), and for the other 12 units. This is a **transitional
generator**, not yet a full 40kdc-style exporter or a second independent
rules dataset.

## Building and testing

```sh
python scripts/build_catalogue.py --check
python scripts/build_catalogue.py --self-test
python scripts/build_catalogue.py --out /tmp/Aeldari-generated.cat
```

`--check` asserts the catalogue and structured pilot agree structurally with
**zero changes**. `--self-test` changes a points value in memory and asserts
the generated catalogue changes. Both run in CI.

Do not push the generated `.cat` over the main catalogue without verifying
its New Recruit presentation and an exported `.rosz`. XML layout preservation
and exact visual rendering are NOT proven by a structural XML parity test.

## Rules for the next stage

- Keep all internal IDs stable across generation.
- Preserve the weapon-first display strategy for Fire Dragons/Dark Reapers
  until a verified replacement is available; don't move weapon profiles solely
  to satisfy an ownership test.
- Keep per-model equipment groups on Windriders and War Walkers.
- Migrate weapons, default equipment, full-model variants, explicit replacement
  rules, conditional abilities, detachment rules and provenance next.
- Validate model-count **behaviour**, not just condition strings.
- Run the generated roster through New Recruit and Yellowscribe before release.
- Treat data imported from either public repository as unverified until
  checked against the current official 11th Edition source.
- The 40kdc-data schemas are CC0; its data is CC BY 4.0. This pilot carries
  only pre-existing project values and does not bundle 40kdc data.
