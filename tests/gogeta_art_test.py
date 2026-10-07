import json
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "source" / "gogeta" / "generated"
CARDS = {
    "bigBangKamehameha",
    "dragonFist",
    "superEnergyBackflow",
    "superKamehameha",
}


class GogetaArtwork(unittest.TestCase):
    def test_normalized_art_has_the_expected_dimensions_and_alpha(self) -> None:
        expected = {
            GENERATED / "portrait.png": (120, 120),
            GENERATED / "versus.png": (400, 300),
            **{GENERATED / "cards" / f"{name}.png": (62, 67) for name in CARDS},
        }
        for path, dimensions in expected.items():
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)
                with Image.open(path) as image:
                    self.assertEqual(image.size, dimensions)
                    self.assertEqual(image.mode, "RGBA")
                    alpha = image.getchannel("A")
                    self.assertLess(alpha.getextrema()[0], 255, "art must preserve transparent pixels")
                    self.assertGreater(alpha.getextrema()[1], 0, "art must contain visible pixels")
                self.assertLess(path.stat().st_size, 250_000)

    def test_card_set_and_attribution_are_complete(self) -> None:
        card_names = {path.stem for path in (GENERATED / "cards").glob("*.png")}
        self.assertEqual(card_names, CARDS)
        attribution = json.loads(
            (ROOT / "source" / "gogeta" / "portraits" / "attribution.json").read_text(encoding="utf8")
        )
        self.assertEqual(attribution["character"], "오지터")
        self.assertEqual(attribution["sourceType"], "derived-user-provided-game-sprite")
        self.assertIn("RPG.swf", attribution["source"])
        self.assertTrue(attribution["replaceable"])


if __name__ == "__main__":
    unittest.main()
