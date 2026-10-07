import hashlib
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

from tools.swf_tags import decompress_swf, iter_tags, swf_tag_start


ROOT = Path(__file__).resolve().parents[1]
FIGURE = ROOT / "public" / "game" / "characters" / "go_figure.swf"
FRAMES = ROOT / "source" / "gogeta" / "figure-frames.json"
MANGA_SOURCE = Path(os.environ.get("MANGA_RPG_SOURCE", r"D:\CHAT\manga rpg\RPG.swf"))

REQUIRED_ACTIONS = {
    "ambient",
    "hit",
    "guard_up",
    "guard_stay",
    "guard_down",
    "perfectGuard_up",
    "perfectGuard_stay",
    "perfectGuard_down",
    "guard",
    "perfectGuard",
    "moveNone",
    "moveDown",
    "moveRight",
    "moveUp",
    "moveLeft",
    "doubleDown",
    "doubleRight",
    "doubleUp",
    "doubleLeft",
    "victory",
    "defeat",
    "heal",
    "energyUp",
    "summonShippo",
    "bigBangKamehameha",
    "dragonFist",
    "superEnergyBackflow",
    "superKamehameha",
}


def move_label(move_id: str) -> str:
    # ViewRoundPlayers sends the raw action ID to gotoAndPlay. Character
    # identity is carried by the exported ``goMoves`` linkage, not the frame
    # label itself.
    return move_id


def export_assets(payload: bytes) -> dict[str, int]:
    count = struct.unpack_from("<H", payload, 0)[0]
    offset = 2
    result = {}
    for _ in range(count):
        identifier = struct.unpack_from("<H", payload, offset)[0]
        offset += 2
        end = payload.index(0, offset)
        name = payload[offset:end].decode("utf8")
        offset = end + 1
        result[name] = identifier
    return result


class GogetaFigure(unittest.TestCase):
    def test_figure_exports_go_moves_with_every_required_label(self) -> None:
        self.assertTrue(FIGURE.is_file(), FIGURE)
        data = decompress_swf(FIGURE.read_bytes())
        exports = {}
        sprites = {}
        for tag in iter_tags(data, swf_tag_start(data)):
            if tag.code == 56:
                exports.update(export_assets(tag.payload))
            elif tag.code == 39:
                identifier = struct.unpack_from("<H", tag.payload, 0)[0]
                sprites[identifier] = tag
        self.assertIn("goMoves", exports)
        self.assertIn("goFxTop", exports)
        self.assertIn("goFxBottom", exports)
        moves = sprites[exports["goMoves"]]
        labels = set()
        for child in iter_tags(moves.payload, 4, len(moves.payload)):
            if child.code == 43:
                labels.add(child.payload.split(b"\0", 1)[0].decode("utf8"))
        required_labels = {move_label(move_id) for move_id in REQUIRED_ACTIONS}
        self.assertTrue(required_labels.issubset(labels), required_labels - labels)
        self.assertFalse(any(label.startswith("go") for label in labels))

    def test_frame_manifest_uses_fusion_sources_and_custom_guard(self) -> None:
        data = json.loads(FRAMES.read_text(encoding="utf8"))
        self.assertEqual(data["palette"], "fusion-super-saiyan")
        self.assertEqual(data["sources"]["jump"]["spriteId"], 6585)
        self.assertEqual(data["sources"]["dragonFist"]["spriteId"], 6649)
        guard_paths = [ROOT / path for path in data["generated"]["guard"]]
        self.assertEqual(len(guard_paths), 3)
        for path in guard_paths:
            self.assertTrue(path.is_file(), path)
        idle = Image.open(ROOT / data["generated"]["idle"][0]).convert("RGBA")
        guard = Image.open(guard_paths[1]).convert("RGBA")
        self.assertIsNotNone(ImageChops.difference(idle, guard).getbbox(), "guard must edit the base pose")

    def test_animation_mapping_uses_jump_guard_aura_and_distinct_big_bang_sequences(self) -> None:
        from tools.gogeta_figure import load_sequences, segments

        sequences = load_sequences()
        mapped = {label: frames for label, frames, _behavior in segments(sequences)}

        for move_id in (
            "moveLeft", "moveRight", "moveUp", "moveDown",
            "doubleLeft", "doubleRight", "doubleUp", "doubleDown",
        ):
            self.assertIs(mapped[move_id], sequences["jump"], move_id)

        for move_id in ("heal", "energyUp"):
            self.assertIs(mapped[move_id], sequences["aura"], move_id)

        guard = sequences["guard"]
        for move_id in ("guard", "perfectGuard"):
            self.assertEqual(len(mapped[move_id]), len(guard) * 2 - 1)
            for actual, expected in zip(mapped[move_id][:len(guard)], guard):
                self.assertIs(actual.image, expected.image, move_id)

        self.assertIs(mapped["bigBangKamehameha"], sequences["bigBangKamehameha"])
        self.assertIsNot(mapped["bigBangKamehameha"], sequences["jump"])

    def test_figure_build_is_byte_deterministic_and_does_not_touch_source(self) -> None:
        from tools.gogeta_figure import build_figure

        before = hashlib.sha256(MANGA_SOURCE.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="gogeta_figure_") as temp:
            first = Path(temp) / "first.swf"
            second = Path(temp) / "second.swf"
            build_figure(first)
            build_figure(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.read_bytes(), FIGURE.read_bytes())
        self.assertEqual(before, hashlib.sha256(MANGA_SOURCE.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
