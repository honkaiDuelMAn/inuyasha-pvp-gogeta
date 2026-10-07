"""Select compact, deterministic Gogeta frame sequences from FFDec exports."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "source" / "gogeta" / "frames"

SELECTIONS = {
    "idle": (6564, [1, 3, 5, 7, 9, 11, 12]),
    "entrance": (6571, [1, 3, 5, 7, 9, 11]),
    "jump": (6585, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20]),
    "aura": (6609, [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 33]),
    "hit": (6585, [1, 5, 10, 15, 20]),
    "defeat": (6571, [11, 9, 7, 5, 3, 1]),
    "victory": (6676, [1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 64]),
    "bigBangKamehameha": (6667, [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46, 49, 51]),
    "dragonFist": (6649, [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 73, 77]),
    "superEnergyBackflow": (6609, [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 33]),
    "superKamehameha": (6597, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 24]),
}


def edit_guard(source: Path, destination: Path, phase: int) -> None:
    image = Image.open(source).convert("RGBA")
    box = image.getbbox()
    if not box:
        raise ValueError(f"guard source is transparent: {source}")
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    draw = ImageDraw.Draw(image)
    center_x = left + width // 2
    shoulder_y = top + round(height * 0.38)
    hand_y = top + round(height * (0.48 + phase * 0.025))
    sleeve = max(2, round(width * 0.08))
    skin = max(2, round(width * 0.06))
    # Blue sleeves lead into two crossed forearms and visible hands. The small
    # edit deliberately stays inside the source sprite's original silhouette.
    draw.line((left + round(width * 0.25), shoulder_y, center_x - 2, hand_y), fill=(35, 72, 205, 255), width=sleeve)
    draw.line((right - round(width * 0.25), shoulder_y, center_x + 2, hand_y), fill=(35, 72, 205, 255), width=sleeve)
    draw.line((center_x - round(width * 0.18), hand_y - 2, center_x + round(width * 0.17), hand_y + 3), fill=(241, 181, 124, 255), width=skin)
    draw.line((center_x + round(width * 0.18), hand_y - 2, center_x - round(width * 0.17), hand_y + 3), fill=(241, 181, 124, 255), width=skin)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, "PNG", optimize=True)


def build(export_root: Path, output: Path = OUTPUT) -> dict[str, object]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    generated: dict[str, list[str]] = {}
    sources: dict[str, object] = {}
    for semantic, (sprite_id, frames) in SELECTIONS.items():
        directory = output / semantic
        directory.mkdir(parents=True)
        paths = []
        for index, frame in enumerate(frames, start=1):
            source = export_root / f"DefineSprite_{sprite_id}" / f"{frame}.png"
            if not source.is_file():
                raise FileNotFoundError(source)
            destination = directory / f"{index:02d}.png"
            shutil.copyfile(source, destination)
            paths.append(destination.relative_to(ROOT).as_posix())
        generated[semantic] = paths
        sources[semantic] = {"spriteId": sprite_id, "frames": frames}

    guard_sources = [output / "idle" / "02.png", output / "idle" / "04.png", output / "idle" / "06.png"]
    guard_paths = []
    for phase, source in enumerate(guard_sources):
        destination = output / "guard" / f"{phase + 1:02d}.png"
        edit_guard(source, destination, phase)
        guard_paths.append(destination.relative_to(ROOT).as_posix())
    generated["guard"] = guard_paths

    manifest = {
        "schema": 1,
        "palette": "fusion-super-saiyan",
        "sources": sources,
        "generated": generated,
    }
    (ROOT / "source" / "gogeta" / "figure-frames.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
        newline="\n",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build(args.export_root.resolve(), args.output.resolve())
    print(f"Selected {sum(map(len, result['generated'].values()))} Gogeta frames")


if __name__ == "__main__":
    main()
