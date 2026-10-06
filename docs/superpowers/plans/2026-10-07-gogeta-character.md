# Gogeta Character Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real ninth playable character, 오지터 (`go`), to the preserved InuYasha browser PvP build in a new public repository and deploy it on GitHub Pages.

**Architecture:** Extend the existing tag-preserving Flash build. A Manga RPG extractor produces a deterministic manifest and Gogeta figure package; a verified main-SWF patcher adds character data, move XML, selection/versus art, and card assets; browser/room code only learns the new `go` key and preserves the existing WebRTC protocol.

**Tech Stack:** Python SWF tag tooling, AVM1/ActionScript 2, JPEXS FFDec, Flasm, self-hosted Ruffle, Node 24 ES modules, Playwright/Chrome, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-10-07-gogeta-character-design.md`

## Global Constraints

- Source baseline is commit `c2fe0d8082011257ed054230776c5f24a2742f0d`; the original `honkaiDuelMAn/inuyasha-pvp` remote and Pages site must not receive any Gogeta commit.
- New repository name is `honkaiDuelMAn/inuyasha-pvp-gogeta`; deploy branch remains `pvp`.
- Character key is `go`, display name is `오지터`, and the ninth button sits in the lower-left third row without moving the original eight buttons.
- Exact move IDs, area matrices, damage, and energy values come from the spec and must be identical in the embedded move XML, `server/catalog.json`, and `public/net/catalog.mjs`.
- Only `summonShippo` is Gogeta's dedicated advanced card; common move character lists gain `go` without changing existing values.
- Existing invitation/answer links, QR, STUN-only WebRTC, room phases, report comparison, and rematch protocol remain unchanged.
- Original eight figure SWFs and untouched main-SWF tags retain verified hashes.
- Manga RPG and InuYasha input SWFs are read-only; generated output must be deterministic.

## Review Focus

- An unexpected Manga RPG or InuYasha SWF hash/layout must abort before writing a partially patched build.
- A missing animation dependency must be reported in the manifest/build error rather than silently substituting another character's gameplay data.
- Both peers choosing `go` must produce independent player state and identical reports.
- A selection button hit area, portrait, or card bitmap must not overlap or corrupt existing UI depths.
- Build and Pages staging must include `go_figure.swf` and art files while never embedding local absolute paths or build-tool binaries.

---

### Task 1: Baseline Repository and Build Inputs

**Files:**
- Modify: `.gitignore`
- Create: `source/gogeta/README.md`
- Create: `source/gogeta/input-hashes.json`
- Create: `tests/gogeta_inputs_test.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: baseline repo at `c2fe0d8`; Manga RPG source at `D:\CHAT\manga rpg\RPG.swf`.
- Produces: `source/gogeta/input-hashes.json` with SHA-256 entries for Manga RPG source, baseline main SWF, and eight original figure SWFs.

- [ ] Write `tests/gogeta_inputs_test.py` asserting the declared source hashes match the mounted files and that the original eight figure hashes match `tools/original-hashes.json`.
- [ ] Run `python -m unittest tests.gogeta_inputs_test -v` and verify RED because the input manifest does not exist.
- [ ] Add source documentation, deterministic input manifest generation, and ignore only generated previews/work folders.
- [ ] Run the input test and baseline Node/Python suites; commit `chore: pin Gogeta source inputs`.

### Task 2: Manga RPG Goku Extraction Manifest

**Files:**
- Create: `tools/swf_tags.py`
- Create: `tools/gogeta_extract.py`
- Create: `source/gogeta/manifest.json`
- Create: `source/gogeta/previews/README.md`
- Create: `tests/gogeta_extract_test.py`

**Interfaces:**
- Produces: `extract_manifest(source: Path) -> dict` and CLI `python tools/gogeta_extract.py --source <RPG.swf> --output source/gogeta/manifest.json --preview-dir scratch/gogeta-previews`.
- Manifest fields: source hash, character ID `5`, selected symbol IDs, dependency IDs, frame ranges, and semantic mappings for `idle`, `entrance`, `jump`, `aura`, `guardBase`, `hit`, `defeat`, `victory`, `bigBangKamehameha`, `dragonFist`, `superEnergyBackflow`, `superKamehameha`.

- [ ] Write tests that parse the real Manga RPG SWF, require character ID 5 evidence, require every semantic mapping, verify every referenced symbol exists, and ensure two extraction runs serialize identical JSON.
- [ ] Run the extraction tests and verify RED because the extractor is absent.
- [ ] Implement reusable SWF tag/definition/placement/dependency parsing and the Goku-specific selector with explicit structural assertions.
- [ ] Generate the manifest and preview index, run tests GREEN, and commit `feat: map Manga RPG Goku animations`.

### Task 3: Gogeta Portrait and Card Source Art

**Files:**
- Create: `source/gogeta/portraits/portrait-source.*`
- Create: `source/gogeta/portraits/versus-source.*`
- Create: `source/gogeta/portraits/attribution.json`
- Create: `tools/gogeta_art.py`
- Create: `source/gogeta/generated/portrait.png`
- Create: `source/gogeta/generated/versus.png`
- Create: `source/gogeta/generated/cards/*.png`
- Modify: `THIRD-PARTY.txt`
- Create: `tests/gogeta_art_test.py`

**Interfaces:**
- Produces: normalized transparent PNG portrait, versus image, and four 62x67 card images; all outputs are deterministic from checked-in sources.

- [ ] Add tests for exact output dimensions, alpha channel, bounded file sizes, four unique move IDs, and attribution fields.
- [ ] Run tests RED.
- [ ] Select/download redistributable source art when possible; otherwise create clearly documented replacement-ready original placeholders derived from checked-in art, then implement deterministic crop/resize/card composition.
- [ ] Run tests and visual contact-sheet generation; commit `feat: add Gogeta UI artwork`.

### Task 4: Build `go_figure.swf`

**Files:**
- Create: `tools/gogeta_figure.py`
- Create: `flash/gogeta_figure.as`
- Create: `public/game/characters/go_figure.swf`
- Create: `tests/gogeta_figure_test.py`
- Create: `tests/fixtures/gogeta-figure-probe.as`

**Interfaces:**
- CLI: `python tools/gogeta_figure.py --source <RPG.swf> --manifest source/gogeta/manifest.json --output public/game/characters/go_figure.swf --java <java.exe> --ffdec <ffdec.jar>`.
- Output exposes the shell/linkage/frame names consumed by `ManageBattleLoad` for figure, movement, guard/perfectGuard, common-card aura, hit/defeat/victory, and all four attacks.

- [ ] Write structural tests that reject missing mappings and assert a valid SWF, required labels/linkages, deterministic SHA-256, and no mutation of Manga RPG or original figure files.
- [ ] Run tests RED.
- [ ] Build a wrapper figure from the extracted Goku dependencies, remap IDs, add the two/three-frame two-hand guard edit, and map jump/aura/attack sequences to InuYasha-compatible action labels.
- [ ] Run structural tests plus a Ruffle load probe; commit `feat: build Gogeta combat figure`.

### Task 5: Verified Main-SWF Gogeta Patch

**Files:**
- Create: `tools/gogeta_patch.py`
- Modify: `tools/build.py`
- Modify: `tools/original-tag-hashes.json` only by adding named verified Gogeta patch targets metadata, not changing baseline hashes.
- Modify: generated `public/game/game-original.swf`
- Modify: generated `public/game/game-pvp.swf`
- Modify: generated `server/catalog.json`
- Modify: generated `public/net/catalog.mjs`
- Create: `tests/gogeta_patch_test.py`

**Interfaces:**
- `patch_gogeta(tags, assets, manifest) -> list[tuple[int, bytes]]` validates exact source tag hashes before changing character config, move XML, selection/versus UI, card bitmaps, and keyed shell tables.
- Four move definitions use the exact spec matrices and negative energy/life impacts.

- [ ] Write failing tests that inspect both built SWFs for key `go`, ninth selection entry, figure prefix, four exact moves, `summonShippo` compatibility, and unchanged original-eight tags/resources.
- [ ] Run RED.
- [ ] Implement verified patch points and orchestrate Sango patch → Gogeta patch → PvP bridge insertion → catalog generation → figure copy.
- [ ] Build twice and assert byte-identical outputs; run Python preservation tests; commit `feat: patch Gogeta into the game SWF`.

### Task 6: Room and Browser Integration

**Files:**
- Modify: `public/net/room-rules.mjs`
- Modify: `public/app.mjs`
- Modify: `tests/rooms.test.mjs`
- Modify: `tests/card-settings.test.mjs`
- Create: `tests/gogeta-rules.test.mjs`

**Interfaces:**
- Accepted character list includes `go`; `names.go === '오지터'`; dedicated-card lookup yields only `summonShippo` for `go`.

- [ ] Add tests for all 81 pairings with nine characters, `go` move validation, mirror match startup, exact dedicated card, and rejection of other summons.
- [ ] Run Node tests RED.
- [ ] Add `go` to room/browser maps without touching protocol types or connection code.
- [ ] Run all Node tests GREEN; commit `feat: integrate Gogeta room rules`.

### Task 7: Gogeta Browser Gameplay and Animation Verification

**Files:**
- Create: `tests/fixtures/gogeta-probe.as`
- Create: `tests/gogeta-browser.cjs`
- Modify: `tests/browser.cjs` only for reusable coordinate/state helpers if necessary.

**Interfaces:**
- Probe callback returns character-button bounds, selected character ID, current body animation label, effect-layer visibility, and move metadata.

- [ ] Write browser test selecting the lower-left ninth button on both peers and asserting room UI says 오지터 and start event characters are `['go','go']`.
- [ ] Add exact attack tests for area/damage/energy and equal peer reports.
- [ ] Assert Big Bang Kamehameha is not mapped to jump, movement/double movement uses jump, guard/perfectGuard uses guard pose, and heal/energyUp uses aura with no effect clip.
- [ ] Exercise dedicated Shippo, victory, rematch, disconnect/replacement, and direct-link transport.
- [ ] Run RED before final SWF mapping, fix discovered defects with regression tests, then run GREEN and commit `test: verify Gogeta browser gameplay`.

### Task 8: Documentation, Packaging, New Repository, and Pages

**Files:**
- Modify: `package.json`
- Modify: `README.md`
- Modify: `README.txt`
- Modify: `THIRD-PARTY.txt`
- Modify: `검증결과.txt`
- Modify: `progress.md`
- Modify: `.github/workflows/pages.yml` only if repository name assumptions require it.

**Interfaces:**
- Public repository: `honkaiDuelMAn/inuyasha-pvp-gogeta`; deploy branch `pvp`; Pages URL `https://honkaiduelman.github.io/inuyasha-pvp-gogeta/`.

- [ ] Update commands, provenance, move table, animation mappings, known limitations, and verification results.
- [ ] Run full Node/Python/browser suites, static Pages staging, package build, `git diff --check`, and original-hash verification.
- [ ] Create the new public GitHub repository, replace only this workspace's remote, rename/merge the implementation branch to `pvp`, and push without changing the original remote.
- [ ] Confirm the Pages workflow succeeds; run public-site smoke tests for file loading, ninth-button selection, Gogeta mirror start, and link exchange.
- [ ] Record public URL and deployed commit; commit/push final verification documentation.
