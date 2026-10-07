# Gogeta public quality repair implementation plan

> For agentic workers: execute inline using superpowers:executing-plans; independently investigate original audio using superpowers:dispatching-parallel-agents. No commits before all requested local checks pass.

Goal: match the user's attached fusion appearance in both game modes, preserve native cards and game behavior, remove timeline flicker and autonomous fighter playback, map original Manga RPG sounds, and verify the actual Pages deployment.

Architecture: retain the original balanced game SWF tags and eight character assets. Correct the checked-in extracted animation sources, build native-style raster cards, and install shared display hooks in the existing two bridges. Keep the original battle engine, links, invitation and response protocol.

Tech stack: Python/Pillow/SWF tags, AVM1 bridge compiled with FFDec, Node and real Chromium/Ruffle browser checks.

Spec: the user's six-part request in this chat, including A/B/C acceptance criteria. The direct request authorizes implementation, commit/push and Pages release after successful local validation.

Global constraints: preserve Sango -25/-15 Secret Sword and -20 Poison Powder; preserve all eight originals and original-mode Gogeta; preserve PvP exchange protocol; no Goku appearance, autonomous punch loop or unrelated voice; no completion claim based only on local results.

Review focus: invalid go timeline labels in backgrounds/HUD/cards; reused picker clips during selection and rematch; figures loaded as both library and visible root instance; asynchronous PNG loads and repeated picker refreshes; all four attack completion/hit callbacks and original single-player progression.

## Task 1: Video and asset provenance
- [x] Decode all 252 frames of 1.mp4 and 409 frames of 2.mp4; save frame timestamps and contact sheets.
- [x] Trace original ViewPickMoves.showPicker, card label generation, ViewRoundPlayers attachment and generated figure root.
- [x] Locate actual white-trouser fusion sprites 7034..7158 rather than incorrect orange-clothed 6564..6676.
- [x] Record exact stance, action source frames, audio provenance and root-cause evidence.

## Task 2: Correct figure and native-style art
Files: tools/gogeta_extract.py, tools/gogeta_frame_sources.py, tools/gogeta_figure.py, tools/gogeta_art.py, source/gogeta, tests/gogeta_quality_test.py.
- [x] Add failing regressions for true fusion identity, non-punch ambient, empty figure library root, one-shot stop/completion, native frame/DM/EN/range pixels and common card character art.
- [x] Re-extract fusion stance and actions; keep ambient as a stationary stance; separate basic punch from ambient.
- [x] Use native 62x67 frame, native DM/EN numerals and range grid. Generate all four attacks and compatible common cards from correct fusion sources.
- [x] Rebuild and verify focused and existing tests.

## Task 3: Shared display repair and original audio
Files: flash/gogeta-display.as, flash/pvp.as, flash/original-gogeta.as, tools/gogeta_bridge.py, tools/gogeta_audio.py, tools/build_gogeta.py, tests/fixtures/gogeta-quality-probe.as, tests/gogeta-quality-browser.cjs.
- [x] Add real-browser failing regression: picker/HUD frame stability, one library fighter per side, unchanged original identity, persistent card art, correct actions.
- [x] Install same display hooks in both bridges: valid native card label before overlay; freeze background/HUD onto valid frames; persistent loaded images; decorate picker, selected cards and battle cards; maintain original tint/selection behavior.
- [x] Extract source StartSound events into checked-in audio assets and embed/map on action entry rather than on idle. Include voices only if they exist in the correct original source.
- [x] Test audio output and original behavior in actual browser.

## Task 4: Full local acceptance and review
- [x] Run every Node and Python suite, requested new regressions and rebuilt artifact reproducibility checks.
- [x] Run actual PvP Gogeta mirror four skills, original-mode selection/progression, stable card picker, every common/attack card, normal battle motions and audio output; save screenshots and observation JSON.
- [x] Run existing eight-character/browser and Sango checks appropriate to shared display changes.
- [x] Review final diff; resolve findings; bump release version only after checks.

## Task 5: Authorized release and actual Pages verification
- [ ] Commit validated final files and push only gogeta remote pvp target.
- [ ] Verify GitHub Actions deployment success for the exact commit.
- [ ] Fetch actual public files with cache-busting query and compare SHA-256 to local staged files; perform actual public browser verification and save screenshots.
- [ ] Deliver public URL, final SHA, file/reason summary, appearance/card/UI/motion/audio changes, test counts and evidence, with unresolved limitations explicitly stated.
