# Using this repository as New Recruit's update source

New Recruit supports **MySystems → Add from GitHub**. Supply the repository
name `thomasnorthmore-cyber/wh40k-11e-custom-data-` and choose **Latest
Commit (Head)** when prompted. This works only once the repository contains
valid game-system and catalogue files that you are entitled to distribute.

## Source-of-truth workflow

- Preserve the downloaded New Recruit 11th Edition `books_data` backup locally.
- Use `python scripts/export_newrecruit_github.py NEWRECRUIT_BACKUP.json --out ./newrecruit-repository-export` to produce root-ready JSON files that keep the original content format and IDs intact.
- Test the exported game system in New Recruit before publishing.
- **Do not upload a removed third-party copyrighted catalogue into a public repo without permission.** A private repo could be used as a personal backup, but New Recruit's public repository installer may not read private repos without authorised access.
- Once distribution rights are established, publish the game system and faction JSON files at the root of the repo (not the wrapper export). New Recruit discovers them from GitHub.
- Add the repository under **MySystems → Add from GitHub**, select Latest Commit (Head), and confirm. Later pushes can be pulled via the app's update mechanism.
- Keep the historical Aeldari code archived, rather than publishing it over the recovered catalogues.

References:
- https://www.newrecruit.eu/tutorials/data
- https://www.newrecruit.eu/tutorials/homebrew

## Current status

This GitHub repository currently contains the conversion/audit tooling and an
experimental page. It does **not** yet contain a complete distributable
11th Edition game-system catalogue. Do not claim that the repo can already be
imported into New Recruit. The local export contains 35 records, of which one
is a non-catalogue Stratagems record; the recovered cache itself is partial.
