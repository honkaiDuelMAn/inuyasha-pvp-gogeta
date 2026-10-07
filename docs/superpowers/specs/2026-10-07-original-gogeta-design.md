# Original-mode Gogeta and Sango parity

## Goal

Extend the `inuyasha-pvp-gogeta` GitHub Pages build so the **원본 게임** button opens the normal single-player game with the existing Sango balance patch and a selectable ninth character, 오지터 (`go`). PvP transport and the original eight characters must remain unchanged.

## Required behavior

- `game-original.swf` keeps the current Sango changes: Secret Sword damage 25 / EN 15, Poison Powder EN 20.
- The original single-player runtime installs Gogeta's exact four normal moves, common-card compatibility, `go_figure.swf` linkage, and Shippo as the only potential advanced move.
- Gogeta follows InuYasha's five-enemy progression order: `sa`, `ko`, `ka`, `s`, `n`.
- The existing browser ninth-slot button is visible on the original character-selection screen and calls an original-mode callback, not a PvP callback.
- Selecting Gogeta enters the untouched original versus, battle-loading, AI, card-picking, round, result, and progression flow.
- Original mode uses the same local Gogeta portrait, versus art, card art, and figure SWF; no external API, WebSocket, or signaling path is used.
- Returning to character selection makes the button available again; selecting an original character hides the Gogeta overlay.
- `game-pvp.swf` and the serverless invitation-link protocol keep their existing behavior.

## Architecture

Insert a small conditional loader action into `game-original.swf`. When the browser passes `originalGogeta=true`, it loads a new `original-gogeta-bridge.swf`. The bridge installs data into the already initialized original movie mediator and user-stats manager, wraps only selection/result hooks needed for browser UI events, and then delegates all gameplay to the original engine.

The browser application enables script access in original mode, listens to `originalGogetaEvent`, and reuses the current `#gogetaPick`, versus, and status overlays. Build tooling compiles both bridges and patches the original main SWF idempotently.

## Verification

- Static tests verify original callback names, exact move values, progression order, Shippo-only advanced move, and a frame-16 original loader action.
- Preservation tests verify original and PvP main SWFs share all base tags except their single loader actions and retain Flash 6 execution rules.
- A real Chrome/Ruffle test opens original mode, reaches selection, selects Gogeta, reaches card picking and completes at least one original AI round.
- A real original-mode probe confirms Sango's Secret Sword and Poison Powder values remain patched.
- Full Node, Python, PvP browser, link/QR, mobile, and public Pages smoke tests remain green.
