# Local New Recruit 11th Edition source baseline

The **source of truth for the next data-engine migration** is the user's offline
New Recruit IndexedDB `books_data` export, **not** the older Aeldari-only
Wahapedia-driven preview. The legacy Aeldari v6/v7 work stays available during
migration; do not silently overwrite or discard it.

## Recovered snapshot

- Export date: 2026-11-22
- Game-system identifier: `827374861`
- Input format: JSON with `system` and `catalogues[]`. Every record contains
  `content`, itself JSON encoded as a string.
- The supplied snapshot has **35 records**, including the core `gameSystem`,
  shared libraries, playable faction catalogues and separate Stratagems data.
- An individual faction catalogue may contain only `entryLinks` to shared
  selections in a linked library. Do not interpret empty local
  `sharedSelectionEntries` as an empty faction.
- This snapshot is a **partial local cache**, not proof that every 11th Edition
  faction or sub-faction has been recovered.

## Privacy and publication boundary

The source export contains third-party catalogue/rules content. The repository
is public. **Do not commit the original export, converted full catalogues,
verbatim rules text, or generated source-content dumps** without a separate
rights review. Keep the original backup offline. Code here is designed to
process user-provided files locally without downloading or publishing content.

Run locally:

```sh
python scripts/import_newrecruit_offline.py ./newrecruit-wh40k-11e-complete.json --manifest ./local-audit.json
```

The generated audit includes catalogue names, identifiers, root types,
collection counts and dependency checks, *not* individual rules prose.
The input and the generated manifest should remain local until reviewed.

## Required future importer behaviour

1. Load `catalogues[].content` as a second-level JSON document.
2. Support `catalogue`, `gameSystem` and auxiliary `data` roots.
3. Build a global index of catalogue IDs and shared selection/group IDs;
   resolve `catalogueLinks`, `entryLinks` and group links using `targetId`.
4. Preserve exact source IDs and track provenance; never fabricate missing
   options or quietly merge conflicting versions.
5. Treat model entries as independently configured instances; implement
   `constraints` by `scope` (`self`/`parent` etc.), `field`,
   `includeChildSelections`, and condition-bearing `modifiers`.
6. Preserve option defaults, model counts, conditional costs and catalogue
   dependencies. Repeated models must not share mutable equipment state.
7. Produce distinct **data import**, **semantic selection engine**,
   **New Recruit export**, and **Yellowscribe compatibility** layers.
8. Validate across factions, beginning with War Walkers, Wraithlords, Fire
   Dragons and Dark Reapers, then expanding to other recovered factions.

## Non-goals of the first commit

The included Python script is a **read-only import-audit foundation**. It
does not yet implement BattleScribe constraint evaluation, generate full
New Recruit catalogues, validate every weapon choice, or upload the source.
Use the audit as an objective gate before attempting those next stages.
