# Structured catalogue: 17-unit Aeldari migration

This is our incremental data-first architecture, based on the separation of
composition, weapons and wargear rules demonstrated by
[40kdc-data](https://github.com/wn-mitch/40kdc-data).
The existing **v5 catalogue remains the tested New Recruit layout**.

## Four structured source layers

- `aeldari-pilot.json`: model-count limits, points tiers, selected wargear
  group bounds/defaults and weapon-display strategy for the initial five units
  (Fire Dragons, Dark Reapers, Windriders, War Walkers, Wraithlord).
- `aeldari-datasheets.json`: **all 17 units**, capturing 145 ranged/melee
  weapon and ability profiles (names, characteristics, conditional visibility
  metadata and exact model/gear ownership paths), plus 152 model/gear selection
  entries (type, name, bounds, parent relationship and default where set).

- `aeldari-mechanics.json`: **all 17 units**, recording 48 remaining
  non-weapon/ability profiles (including characteristics and keyword tables),
  24 native rules, 40 category links, 23 modifier records with their
  conditions, 258 selection constraints and 19 points-cost entries.

- `aeldari-loadout-slots.json`: 19 model- or unit-scoped equipment
  slots, containing their choice IDs, allowed pick counts, recorded defaults,
  attached weapon profile IDs and their replacement/optional semantics.
  These form a **validated selection-budget model**; they do not yet encode
  every rules-text prerequisite for individual swaps.

The generator reads all four datasets and applies those values to
`Aeldari 11e TEST.cat` as a compatibility template. Thus changes to
weapon/ability fields and equipment labels/constraints in JSON are reflected
in the generated catalogue. The XML still supplies the structural skeleton, conditional expression
*nesting*, source equipment-option relationships, shared game-system
definitions and anything not yet independently represented in JSON. All
current 17-unit native rule and category values, profile statistics, cost
attributes, and modifier/condition attributes are represented in JSON.

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
statistics, abilities, native rules, keyword tables, category links,
constraints, visibility conditions and equipment names in memory and checks
the generated XML responds. Both run automatically in GitHub Actions.

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

1. Extend slot budgets into explicit *source-verified* item replacement
   prerequisites (which weapon is removed and added) and evaluate unit-wide
   restrictions that span more than one slot.
2. Make the complete XML AST—including nesting of selection/condition groups,
   shared identifiers, limits and all points tiers—reconstructible independently
   of the checked-in v5 catalogue.
3. Produce a fully independent New Recruit JSON and BattleScribe XML exporter;
   add roster XML and Yellowscribe integration fixtures with real-world exports.
4. Verify current 11th Edition points, model options and ability mechanics
   from authorised sources before release.

No 40kdc dataset is copied here; the examples guided this design.

## Precedence and migration safety

The generic mechanics layer is applied **first**, then the original five-unit
points/choice-group pilot and the full 17-unit datasheet profile/selection
layer. If a field appears in two layers, the more specific dataset wins.
Catalogue XML is not updated in place. CI requires generated XML to remain
canonically identical to the current v5 template before any new data changes
are accepted. Modifiers and constraints use checked traversal indexes plus
nearest owner IDs until a fully independent expression schema is implemented;
changing their nesting requires a reviewed migration.

## Loadout legality checks

Run `python scripts/loadout_rules.py` to validate the 19 recorded slots
and enumerate legal choice vectors. The fixtures reject double-picked Exarch
weapons, too many Windrider guns, three heavy mounts on one War Walker,
and invalid Wraithlord arm/heavy selections. A slot's `model_id` is verified
against its actual catalogue parent model. IDs and weapon-profile bindings
are stable while display labels may be edited in the datasheet layer.

The enumerator tests *each individual model's slot*. It does not yet prove
whole-roster legality or New Recruit's evaluated squad-point modifiers. Those
need exported roster fixtures and a rules source check before public release.
