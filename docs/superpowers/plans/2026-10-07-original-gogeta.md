# Original-mode Gogeta and Sango Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the GitHub Pages **원본 게임** mode retain the Sango balance patch and support playable Gogeta through the original single-player engine.

**Architecture:** `game-original.swf` receives one conditional frame-16 loader action which loads a dedicated AVM1 bridge only when `originalGogeta=true`. The bridge installs Gogeta data after the original engine initializes, delegates selection and combat to original methods, and emits browser-only UI events. The existing HTML overlay is shared between PvP and original mode.

**Tech Stack:** Python SWF tag tooling, AVM1/ActionScript 2, JPEXS FFDec, Ruffle, Node test runner, Playwright/Chrome, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-10-07-original-gogeta-design.md`

## Global Constraints

- Existing public repository is `honkaiDuelMAn/inuyasha-pvp-gogeta`, deploy branch `pvp`.
- Original repository `honkaiDuelMAn/inuyasha-pvp` remains unchanged.
- Sango values remain Secret Sword damage 25 / EN 15 and Poison Powder EN 20.
- Gogeta move IDs, costs, damage, areas, figure linkage, and Shippo mapping remain identical to PvP.
- Original single-player AI/progression/card/round/result code is not replaced.
- PvP offer/answer, QR, STUN-only transport, room protocol, and current tests remain unchanged.

## Review Focus

- Original loader must be idempotent and must not stack actions after repeated builds.
- Gogeta user stats require `_enemyLevelKey.go`; missing it would crash selection before versus.
- Original bridge wrappers must delegate with the correct `this` context and not suppress original character selection.
- Original mode must not invoke WebSocket or direct-room signaling.
- Browser overlays must hide after selection/results and reappear when original selection returns.

---

### Task 1: Original Bridge and Idempotent Main-SWF Loader

**Files:**
- Create: `flash/original-gogeta.as`
- Create: `flash/original-loader.as`
- Modify: `tools/gogeta_bridge.py`
- Create: `tools/original_gogeta.py`
- Modify: `tools/build_gogeta.py`
- Modify: `.gitignore`
- Create/Modify: `public/game/original-gogeta-bridge.swf`
- Modify: `public/game/game-original.swf`
- Create: `tests/original_gogeta_build_test.py`
- Modify: `tests/build_test.py`

**Interfaces:**
- `build_bridge(output, java, ffdec, source=SOURCE)` compiles either bridge from the pinned template.
- `patch_original_game(path, loader_source, java, ffdec) -> None` inserts or replaces exactly one marked original loader action at frame 16.
- Original bridge callbacks: `originalChooseGogeta`, `originalGogetaState`; event sink: `originalGogetaEvent(kind, data)`.

- [ ] Write failing structural tests for bridge callbacks, exact move/progression data, original loader marker, idempotent rebuild, and one-loader-per-main-SWF preservation.
- [ ] Run the focused Python tests and confirm RED because original bridge/loader are absent.
- [ ] Implement the original bridge, generalized bridge compiler, and idempotent loader patch.
- [ ] Build artifacts twice, verify byte-identical second output, run focused tests GREEN, and commit.

### Task 2: Browser Original-mode Selection and Overlay Integration

**Files:**
- Modify: `public/app.mjs`
- Modify: `tests/gogeta-page.test.mjs`
- Create: `tests/original-gogeta-app.test.mjs`

**Interfaces:**
- `window.originalGogetaEvent(kind, data)` handles `ready`, `picking`, `selected`, `versus`, `battle`, and `result`.
- `#gogetaPick` calls `originalChooseGogeta` in original mode and `pvpChooseGogeta` in PvP mode.

- [ ] Add failing static tests for original parameters, script access, event handling, callback routing, and overlay visibility conditions.
- [ ] Run focused Node tests RED.
- [ ] Implement original-mode state/event handling while leaving room/network code untouched.
- [ ] Run focused and full Node suites GREEN and commit.

### Task 3: Real Original Single-player Browser Verification

**Files:**
- Create: `tests/original-gogeta-browser.cjs`
- Create: `tests/fixtures/original-gogeta-probe.as`
- Modify: browser helpers only if a reusable original-mode helper is required.

**Interfaces:**
- Test opens the static page, clicks **원본 게임**, enters NORMAL, selects `#gogetaPick`, confirms `originalGogetaState`, closes versus/help screens, selects cards, and observes original-engine battle progress.
- Probe exposes Sango move values from the same original runtime without replacing original gameplay.

- [ ] Write the browser test first and run it RED against the current build.
- [ ] Fix original bridge/runtime integration until Gogeta reaches original card picking and one AI round completes.
- [ ] Verify Sango's two patched values in original mode and verify no signaling/API requests occur.
- [ ] Run original browser test, PvP Gogeta browser test, and browser regression suite GREEN; commit.

### Task 4: Documentation, Release, and Public Pages Verification

**Files:**
- Modify: `README.md`
- Modify: `README.txt`
- Modify: `THIRD-PARTY.txt` only if artifact provenance changes.
- Modify: `package.json`
- Modify: `검증결과.txt`

**Interfaces:**
- Version becomes `1.3.1`.
- Public Pages retains `https://honkaiduelman.github.io/inuyasha-pvp-gogeta/`.

- [ ] Add documentation assertions or package tests that require the original bridge and original-mode instructions in Pages staging.
- [ ] Run them RED, then update documentation/version/staging as required.
- [ ] Run full Node, Python, original/PvP browser, link/QR/mobile regressions and Pages staging.
- [ ] Commit, push `pvp`, wait for Actions success, verify public HTTP assets and a live original-mode Gogeta smoke test.
