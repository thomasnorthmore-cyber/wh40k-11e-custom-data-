# Structured catalogue: 17-unit Aeldari migration

This is our incremental data-first architecture, based on the separation of
composition, weapons and wargear rules demonstrated by
[40kdc-data](https://github.com/wn-mitch/40kdc-data).
The existing **v5 catalogue remains the tested New Recruit layout**.

## Two source layers

- `aeldari-pilot.json`: model-count limits, points tiers, selected wargear
  group bounds/defaults and weapon-display strategy for the initial five units
  (Fire Dragons, Dark Reapers, Windriders, War Walkers, Wraithlord).
- `aeldari-datasheets.json`: **all 17 units**, capturing 145 ranged/melee
  weapon and ability profiles (names, characteristics, conditional visibility
  metadata and exact model/gear ownership paths), plus 152 model/gear selection
  entries (type, name, bounds, parent relationship and default where set).

The generator reads both datasets and applies those values to
`Aeldari 11e TEST.cat` as a compatibility template. Thus changes to
weapon/ability fields and equipment labels/constraints in JSON are reflected
in the generated catalogue. The XML still supplies un-migrated unit profiles,
rules, keywords, profile visibility *conditions*, points and constraints not
present in these JSON files, and the wider game-system links.

**This is not yet an independent JSON → catalogue compiler.** Do not delete
the v5 XML template. The structured entries reflect *current project data*,
not independent official-rules verification.

## Run

```sh
python scripts/build_catalogue.py --check
python scripts/build_catalogue.py --self-test
python scripts/build_catalogue.py --out /tmp/Aeldari-generated.cat
```

`--check` verifies **zero semantic changes** compared with the checked-in
v5 catalogue; `--self-test` deliberately changes structured points, weapon
statistics, ability text and equipment names in memory and checks the
generated XML responds. Both run automatically in GitHub Actions.

## Hard-earned compatibility rules

- **Fire Dragons / Dark Reapers:** keep unit-level conditional ranged/melee
  profile tables before Abilities/Rules/Keywords. Moving them into individual
  equipment entries previously broke New Recruit's visible section order.
- **War Walkers / Windriders:** retain model-scoped choice groups and integer
  equipment selections; no squad-wide shared weapon checkbox.
- **Default equipment:** preserve selected model counts, gear minima,
  maximums and group default IDs; test both 5- and 10-model Aspect squads.
- **Yellowscribe:** our custom game-system ID and profile-type conventions
  differ from the IDs expected by its parser. A generated catalogue being
  structurally valid does **not** prove a .rosz export will work in Yellowscribe.
- **Never publish a generated revision** without a New Recruit visual check,
  saved roster export check and points/loadout regression tests.

## Remaining migration tasks

1. Lift exact *replacement semantics* (which item is removed/added) from the
   current selection tree and primary datasheet into explicit JSON swaps/slots.
   Existing hierarchy alone doesn't prove legal combinations.
2. Migrate all points tiers, non-weapon profiles, native Rules, keywords and
   visibility-condition expressions from the XML template.
3. Replace the template-dependent writer with a fully independent XML/JSON
   exporter; add roster XML and Yellowscribe integration fixtures.
4. Verify current 11th Edition points, model options and ability mechanics
   from authorised sources before release.

No 40kdc dataset is copied here; the examples guided this design.
