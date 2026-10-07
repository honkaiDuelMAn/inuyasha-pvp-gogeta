"""Create a deterministic Manga RPG Goku/fusion animation manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__:
    from .swf_tags import root_definitions, sprite_frame_count, sprite_placements
else:  # Support `python tools/gogeta_extract.py ...` from the repository root.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from swf_tags import root_definitions, sprite_frame_count, sprite_placements


ROOT = Path(__file__).resolve().parents[1]

# Character 5 owns several transformations. Only transformation 5 has the
# user's fusion vest, blue sash and white trousers. The second bank is orange
# Goku and must never be used for Gogeta, regardless of its yellow hair.
CHARACTER_ID = 5
SELECTOR_SPRITE_ID = 8503
SELECTOR_FRAME = 4
CHARACTER_TIMELINE_ID = 7169

ANIMATION_SOURCES = {
    "idle": 7020,
    "entrance": 7020,
    "jump": 7042,
    "aura": 7062,
    "guardBase": 7020,
    "hit": 7027,
    "defeat": 7027,
    "victory": 7062,
    "basicPunch": 7034,
    "bigBangKamehameha": 7158,
    "dragonFist": 7117,
    "superEnergyBackflow": 7101,
    "superKamehameha": 7109,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_manifest(source: Path) -> dict[str, object]:
    source = source.resolve()
    expected = json.loads((ROOT / "source" / "gogeta" / "input-hashes.json").read_text(encoding="utf8"))
    digest = sha256(source)
    if digest != expected["mangaRpg"]["sha256"]:
        raise ValueError("Manga RPG source hash differs from the approved input")

    _, definitions = root_definitions(source)
    for identifier in {SELECTOR_SPRITE_ID, CHARACTER_TIMELINE_ID, *ANIMATION_SOURCES.values()}:
        if identifier not in definitions:
            raise ValueError(f"required Manga RPG definition {identifier} is missing")
        if definitions[identifier].code != 39:
            raise ValueError(f"required Manga RPG definition {identifier} is not a sprite")

    selector = sprite_placements(definitions[SELECTOR_SPRITE_ID])
    selected = [p for p in selector if p.frame == SELECTOR_FRAME and p.name == "crt"]
    if len(selected) != 1 or selected[0].character_id != CHARACTER_TIMELINE_ID:
        raise ValueError("Goku selector frame no longer points to the approved character timeline")

    timeline = sprite_placements(definitions[CHARACTER_TIMELINE_ID])
    timeline_ids = {p.character_id for p in timeline}
    missing = set(ANIMATION_SOURCES.values()) - timeline_ids
    if missing:
        raise ValueError(f"Goku timeline no longer places approved animation sprites: {sorted(missing)}")

    used = sorted(set(ANIMATION_SOURCES.values()))
    definition_rows = []
    for identifier in used:
        tag = definitions[identifier]
        dependencies = sorted({
            placement.character_id
            for placement in sprite_placements(tag)
            if placement.character_id in definitions
        })
        definition_rows.append({
            "id": identifier,
            "frames": sprite_frame_count(tag),
            "dependencies": dependencies,
        })

    frame_counts = {row["id"]: row["frames"] for row in definition_rows}
    animations = {
        name: {
            "spriteId": identifier,
            "startFrame": 1,
            "endFrame": frame_counts[identifier],
        }
        for name, identifier in ANIMATION_SOURCES.items()
    }
    return {
        "schema": 1,
        "sourceFile": source.name,
        "sourceSha256": digest,
        "characterId": CHARACTER_ID,
        "selectorSpriteId": SELECTOR_SPRITE_ID,
        "selectorFrame": SELECTOR_FRAME,
        "characterTimelineId": CHARACTER_TIMELINE_ID,
        "palette": "fusion-super-saiyan",
        "transformation": 5,
        "appearance": "gold hair, black fusion vest, orange shoulders, blue sash, white trousers",
        "definitions": definition_rows,
        "animations": animations,
    }


def write_manifest(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(extract_manifest(source), ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "source" / "gogeta" / "manifest.json",
    )
    args = parser.parse_args()
    write_manifest(args.source.resolve(), args.output.resolve())
    print(f"Wrote {args.output.resolve()}")


if __name__ == "__main__":
    main()
