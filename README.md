# Warhammer 40,000 11th Edition — New Recruit-format builder

> **New project baseline (22 November 2026).** This repository is being restarted around the already-working New Recruit/BattleScribe-style **catalogue format recovered from the user's offline New Recruit installation**. The old Wahapedia CSV → hand-built Aeldari catalogue pipeline is **retired from active development**, not a foundation for the new builder.

## Status

**Migration started; full roster builder not yet implemented.** The recovered snapshot is a tested input to New Recruit, but the JSON export contains **catalogue/game-system definitions**, not New Recruit's own application engine. We need to implement our own interpreter for that format before promising identical validation, roster editing or exports.

- Legacy preserved at [archive/legacy-aeldari-v7](../../tree/archive/legacy-aeldari-v7).
- **Interactive army-builder alpha:** [docs/preview/builder.html](docs/preview/builder.html). Load your offline JSON in the browser, add units, edit nested model options, split grouped models, and export/import alpha rosters.\n- Experimental catalogue browser: [docs/preview/index.html](docs/preview/index.html).
- Local import auditor: [scripts/import_newrecruit_offline.py](scripts/import_newrecruit_offline.py).
- Architecture specification: [docs/newrecruit-offline-baseline.md](docs/newrecruit-offline-baseline.md).

## Source of truth

The **local** `newrecruit-wh40k-11e-complete.json` export dated 2026-11-22 contains **35 records** sharing game-system ID `827374861`. Each `catalogues[]` item has a nested `content` document containing a `catalogue`, `gameSystem`, or auxiliary data object. This is a snapshot of cached catalogues, **not a guarantee every faction is present**.

The data is deliberately **not uploaded to this public repository**. It contains third-party rules material with redistribution restrictions. The test UI lets each tester load their own local file in their browser. Never commit source rules prose without a separate rights review.

## New implementation contract

1. **Use the recovered format directly.** Preserve source selection IDs, group IDs, catalogue references and conditions. Do not regenerate choices from inferred weapon names or manually maintained per-faction datasets.
2. **Resolve dependencies** between factions and shared libraries, including `catalogueLinks`, `entryLinks`, `selectionEntryGroupLinks`, `sharedSelectionEntries` and `sharedSelectionEntryGroups`.
3. **Treat model selections as separate instances** with equipment, count and costs of their own. Identical models may be visually grouped but must not share configuration state accidentally.
4. **Evaluate constraints/modifiers** by scope and conditions; show explicit errors instead of accepting illegal selections.
5. **Use one selection engine for every recovered faction**, with data-driven unit composition, enhancements, detachment support and roster serialization.
6. **Test real cases**, including Aeldari War Walkers, Wraithlords, Fire Dragons, Dark Reapers and equivalent units in other factions.
7. **Export and re-import rosters**, checking model ownership and weapon profiles in New Recruit/Yellowscribe-compatible formats where supported.

## Run the source audit locally

```bash
python scripts/import_newrecruit_offline.py newrecruit-wh40k-11e-complete.json --manifest local-audit.json
```

The audit reads local data, makes no network calls, and reports catalogue structure and missing links. It is not yet the legality engine.

## Project migration policy

Do **not** run the legacy Aeldari catalogue publishing workflow as part of the new build. Existing Aeldari files and scripts in `main` are legacy leftovers pending safe cleanup; the archived branch is the reference if an old result must be recovered. New changes should target the generic New Recruit-format runtime.

**Do not mistake the catalogue inspector for the finished army builder.** Our goal is to recreate equivalent behaviour using the recovered schema; that work still needs to be implemented and verified.
