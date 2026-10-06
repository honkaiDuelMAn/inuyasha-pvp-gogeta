import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("MANGA_RPG_SOURCE", r"D:\CHAT\manga rpg\RPG.swf"))
MANIFEST = ROOT / "source" / "gogeta" / "manifest.json"


class GogetaExtractionManifest(unittest.TestCase):
    def test_manifest_maps_goku_fusion_animations_to_real_sprites(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing {MANIFEST}")
        data = json.loads(MANIFEST.read_text(encoding="utf8"))
        self.assertEqual(data["characterId"], 5)
        self.assertEqual(data["selectorFrame"], 4)
        self.assertEqual(data["characterTimelineId"], 7169)
        required = {
            "idle",
            "entrance",
            "jump",
            "aura",
            "guardBase",
            "hit",
            "defeat",
            "victory",
            "bigBangKamehameha",
            "dragonFist",
            "superEnergyBackflow",
            "superKamehameha",
        }
        self.assertEqual(set(data["animations"]), required)
        definitions = {entry["id"]: entry for entry in data["definitions"]}
        for name, animation in data["animations"].items():
            with self.subTest(name=name):
                self.assertIn(animation["spriteId"], definitions)
                self.assertGreater(definitions[animation["spriteId"]]["frames"], 0)
                self.assertGreaterEqual(animation["startFrame"], 1)
                self.assertLessEqual(animation["endFrame"], definitions[animation["spriteId"]]["frames"])

    def test_extractor_is_deterministic_for_the_real_source(self) -> None:
        from tools.gogeta_extract import extract_manifest

        first = extract_manifest(SOURCE)
        second = extract_manifest(SOURCE)
        self.assertEqual(first, second)
        self.assertEqual(
            json.loads(MANIFEST.read_text(encoding="utf8")),
            first,
        )

    def test_cli_writes_the_same_manifest(self) -> None:
        from tools.gogeta_extract import write_manifest

        with tempfile.TemporaryDirectory(prefix="gogeta_manifest_") as temp:
            output = Path(temp) / "manifest.json"
            write_manifest(SOURCE, output)
            self.assertEqual(output.read_bytes(), MANIFEST.read_bytes())


if __name__ == "__main__":
    unittest.main()
