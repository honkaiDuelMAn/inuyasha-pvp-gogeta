# Gogeta character expansion for InuYasha PvP

## Purpose

Create a new public repository, `honkaiDuelMAn/inuyasha-pvp-gogeta`, from the verified browser PvP baseline at commit `c2fe0d8082011257ed054230776c5f24a2742f0d`. The existing `honkaiDuelMAn/inuyasha-pvp` repository and its GitHub Pages deployment must remain unchanged.

The new repository adds a real ninth playable character, **오지터 (Gogeta)**, using sprite and animation material extracted from `D:\CHAT\manga rpg\RPG.swf`, while preserving the current serverless invitation-link WebRTC transport, host-authoritative room rules, original Flash combat flow, Ruffle packaging, mobile support, and all eight existing characters.

## Source inputs

- Verified browser PvP baseline: `D:\CHAT\inuyasha-pvp-github-update-20261006`, commit `c2fe0d8`.
- Manga RPG source: `D:\CHAT\manga rpg\RPG.swf`.
- Manga RPG original backup: `D:\CHAT\manga rpg\RPG_원본백업.swf`.
- Manga RPG analysis/build tools: `D:\CHAT\manga rpg\_mod_work`.
- User-provided target layout image: ninth slot at the empty lower-left position below the current two-row character grid.

The Manga RPG inspection already establishes that Son Goku is internal character ID `5`. Exact symbol IDs and frame ranges for the fusion pose, jump, aura release, beam attacks, hit, defeat, and other required animations must be recorded in a generated extraction manifest before building the final figure file.

## Repository and deployment isolation

The new repository will be public and will preserve the current static GitHub Pages architecture. It will use a dedicated local workspace at `D:\CHAT\inuyasha-pvp-gogeta` and a new GitHub remote. No commit will be pushed to the original repository after this design branch.

To minimize deployment changes, the new repository keeps `pvp` as the deploy branch and retains the existing Pages workflow. Its intended public URL is:

`https://honkaiduelman.github.io/inuyasha-pvp-gogeta/`

The first code commit in the new repository must reproduce the current working baseline before any Gogeta change is added. This provides a clean comparison point and a rollback target.

## Character identity and resource layout

Gogeta uses the internal character key `go` and the display name `오지터`.

New or generated resources:

- `public/game/characters/go_figure.swf`: combat figure, movement, attacks, guard, damage, and common-card animations.
- Selection portrait asset embedded into the main game SWF.
- Versus/match-screen full-body art embedded into the main game SWF.
- Four normal attack-card images embedded into the card picker.
- Build-time extraction manifest under `source/gogeta/manifest.json`.
- Source images and attribution notes under `source/gogeta/portraits/` and `THIRD-PARTY.txt`.

Internet-sourced face and full-body art will be selected for visual fit, cropped and compressed locally, and kept isolated so it can be replaced without rebuilding the sprite extraction pipeline. Source URLs and attribution will be recorded. Development may use a clearly marked placeholder until the selected final art is confirmed and processed.

## Character-selection layout

The existing eight character buttons remain at their current positions. Gogeta is placed in the empty lower-left area shown by the user, forming a third row with one entry:

```text
이누야샤  가영      카구라     코우가
산고      미륵      셋쇼마루   나락
오지터
```

The new button follows the original visual language:

- same gold frame and rollover behavior;
- Gogeta face portrait inside the frame;
- `오지터` or a legible matching Romanized label inside the original nameplate style, depending on the bitmap-font constraints found in the source;
- selection event returns character key `go`;
- button occupies an independent depth and hit area and must not overlap Sango or the game boundary.

The character description and versus components must recognize `go`; both 1P and 2P may choose Gogeta, including Gogeta versus Gogeta.

## Figure extraction and animation mapping

### Extraction strategy

The Manga RPG source is a monolithic AVM1 SWF rather than a separate character package. The implementation will therefore:

1. locate Goku ID `5` runtime placements and the symbol dependency graph for the requested animations;
2. identify the specific fusion visual used as Gogeta's base sprite;
3. copy only the required definitions, bitmaps, shapes, sprites, and sounds into an isolated intermediate SWF;
4. remap colliding character IDs and linkage names;
5. expose the frame labels and shell structure expected by the InuYasha figure loader;
6. build `go_figure.swf` reproducibly from the manifest rather than relying on manual editor state.

The original Manga RPG SWF and the original InuYasha character files remain byte-for-byte unchanged.

### Required animations

At minimum the new figure must provide:

- idle/ambient;
- selection or entrance pose;
- hit reaction;
- defeat state;
- victory state if the engine requests one;
- jump-derived movement for `moveLeft`, `moveRight`, `moveUp`, and `moveDown`;
- the same jump-derived movement for `doubleLeft` and `doubleRight` when those common cards are awarded;
- a custom two-hand blocking pose for `guard` and `perfectGuard`;
- aura-release animation, without a separate effect layer, for `energyUp`, `heal`, `guard`, and `perfectGuard`;
- four attack animations listed below.

Horizontal direction changes will use the engine's facing/scale mechanism wherever possible. New mirrored bitmaps are created only when the extracted animation cannot be mirrored safely.

### Guard edit

The guard animation is a small sprite edit derived from the closest Goku fusion stance:

- preserve the torso, head, palette, and silhouette;
- move or redraw both forearms and hands in front of the body;
- create a short two- or three-frame block loop;
- do not add a shield, aura, or external effect;
- reuse the same body pose for perfect guard, with the gameplay protection value still controlled by the move data.

## Move data

The coordinate notation is:

```text
7 8 9
4 5 6
1 2 3
```

All four moves are normal selectable character moves (`advanced = false`) available only to `go`.

### 1. Big Bang Kamehameha

- Internal ID: `bigBangKamehameha`
- Korean display name: `빅뱅 애네르기파`
- Area: `5123`
- Area matrix: `0,0,0_0,1,0_1,1,1`
- Damage: `40`
- Energy cost: `50`
- Animation requirement: charge and fire from the current square; the character must not jump.

### 2. Dragon Fist

- Internal ID: `dragonFist`
- Korean display name: `용권`
- Area: `456`
- Area matrix: `0,0,0_1,1,1_0,0,0`
- Damage: `70`
- Energy cost: `60`
- Animation requirement: use the closest extracted Dragon Fist or forward strike sequence; gameplay location remains unchanged unless the original engine's action system requires a visual-only translation.

### 3. Super Energy Backflow

- Internal ID: `superEnergyBackflow`
- Korean display name: `초 에너지 역류`
- Area: `789456123`
- Area matrix: `1,1,1_1,1,1_1,1,1`
- Damage: `25`
- Energy cost: `25`
- Animation requirement: radial energy-release sequence.

### 4. Super Kamehameha

- Internal ID: `superKamehameha`
- Korean display name: `초 에네르기파`
- Area: `456`
- Area matrix: `0,0,0_1,1,1_0,0,0`
- Damage: `35`
- Energy cost: `20`
- Animation requirement: shorter and faster beam sequence than Big Bang Kamehameha.

The move XML inside the main SWF, generated `server/catalog.json`, and `public/net/catalog.mjs` must remain derived from the same source so browser and Node modes cannot disagree.

## Dedicated and common cards

Gogeta's dedicated card is the existing `summonShippo` move. When dedicated cards are enabled, a Gogeta player receives exactly this existing card and no other summon card.

The common move character lists are expanded to include `go` where appropriate:

- `guard`
- `energyUp`
- `moveLeft`
- `moveRight`
- `moveUp`
- `moveDown`
- `perfectGuard`
- `heal`
- `kikyosRevenge`
- `doubleRight`
- `doubleLeft`

Only `summonShippo` is added as Gogeta's character-specific advanced move. Existing characters retain their current dedicated cards.

For Gogeta, `heal`, `energyUp`, `guard`, and `perfectGuard` all play the same effectless aura-release body animation. Their existing gameplay types and values remain distinct.

## Main SWF patching

The implementation extends the current tag-preserving build approach rather than recompiling the original game wholesale.

The Gogeta patcher must update only verified targets:

- character descriptions/configuration with key `go`;
- character constructor data and fight lists;
- character-to-figure linkage map;
- move XML and generated catalogs;
- character-selection button timeline and its ninth position;
- versus portrait/full-body asset tables;
- card bitmaps for the four normal moves;
- any battle-loading shell prefix tables that are explicitly keyed to the original eight character IDs.

All patch points require baseline tag hashes or structural assertions. The patcher must stop with a clear error if the input SWF does not match the verified baseline.

## Browser and room integration

The browser application and room rules add `go` to the accepted character set and display-name map. Existing invitation links, QR flow, STUN-only WebRTC logic, manual offer/answer format, host-authoritative room service, round barriers, state comparison, and rematch behavior remain unchanged.

The protocol does not need a new message type. Gogeta is carried through existing `character`, `start`, `moves`, `resolved`, and `result` events using the new ID.

Because this is a separate repository, both players must load the Gogeta repository URL. Cross-version play with the original repository is not supported and should fail through normal missing-character/version behavior rather than silently substituting another character.

## Build tooling

New build tools will be separated by responsibility:

- `tools/gogeta_extract.py`: analyzes Manga RPG ID `5`, resolves symbol dependencies, and writes an extraction manifest plus preview sheets.
- `tools/gogeta_figure.py`: builds `go_figure.swf` from the manifest and source symbol data.
- `tools/gogeta_patch.py`: applies verified main-SWF character, move, UI, portrait, and card changes.
- `tools/build.py`: orchestrates the existing Sango patch, Gogeta patch, PvP bridge insertion, catalog generation, and character-resource copy.

Generated assets must be deterministic: identical verified inputs produce identical output hashes.

## Validation

### Static and structural tests

- Original eight figure SWFs retain their baseline SHA-256 hashes.
- Existing untouched main-SWF tags retain their baseline hashes.
- Exactly the expected Gogeta-related tags and generated catalogs change.
- `go_figure.swf` is valid, loadable, and contains every required action/frame label.
- The four moves have exact area, damage, and energy values.
- `summonShippo` accepts `go`; other summons do not.
- Common-card and movement validation accepts `go` without changing existing character behavior.

### Browser tests

Automated Ruffle/Chrome tests must demonstrate:

1. the ninth button is visible and clickable at the intended lower-left location;
2. selecting it reports `go` and displays `오지터` in the room UI;
3. Gogeta versus Gogeta loads successfully;
4. each of the four attacks can be selected and produces identical state reports on both peers;
5. Big Bang Kamehameha does not use the jump animation;
6. movement uses the extracted Goku jump motion;
7. guard and perfect guard show the edited two-hand pose;
8. heal and energy up use the effectless aura-release animation;
9. dedicated-card ON grants Shippo to Gogeta;
10. full victory, character reselection, rematch, disconnect, and replacement remain functional.

### Regression suite

The current Node, Python preservation, static Pages, link/QR, mobile touch, real original-engine round, and external WebRTC tests must continue to pass in the new repository. A public Pages smoke test must be run after deployment.

## Failure handling and fallback

If the Manga RPG fusion animation cannot be isolated as a self-contained dependency graph, the fallback is a wrapper figure SWF that embeds the extracted definitions and exposes InuYasha-compatible labels. Replacing an existing InuYasha character is not an acceptable fallback.

If an internet portrait cannot be redistributed responsibly, the code and layout work proceeds with a replaceable placeholder and the public release is not described as final art until the user approves the selected source.

If a visual animation cannot be mapped exactly, the gameplay move values and area must remain exact while the closest extracted animation is used and documented. No move may silently inherit another character's gameplay data.

## Completion criteria

The feature is complete only when:

- the new repository exists and the original repository remains unchanged;
- the ninth Gogeta slot appears at the specified lower-left position;
- both peers can select Gogeta, including mirror matches;
- all four move values and areas match this specification;
- Shippo is Gogeta's dedicated card;
- movement, guard, common-card animation requirements are met;
- existing eight characters and network behavior pass regression tests;
- the new GitHub Pages URL is deployed and verified from the public site;
- source provenance, build commands, limitations, and validation results are documented.