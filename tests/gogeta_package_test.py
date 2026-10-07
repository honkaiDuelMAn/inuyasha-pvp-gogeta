import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GogetaPackage(unittest.TestCase):
    def test_public_art_matches_the_reproducible_generated_assets(self) -> None:
        from tools.build_gogeta import sync_public_art

        with tempfile.TemporaryDirectory(prefix="gogeta_public_art_") as temp:
            output = Path(temp)
            sync_public_art(output)
            expected = ROOT / "source" / "gogeta" / "generated"
            for source in sorted(path for path in expected.rglob("*") if path.is_file()):
                relative = source.relative_to(expected)
                self.assertEqual((output / relative).read_bytes(), source.read_bytes(), relative)

        public = ROOT / "public" / "game" / "gogeta"
        for source in sorted(path for path in (ROOT / "source" / "gogeta" / "generated").rglob("*") if path.is_file()):
            relative = source.relative_to(ROOT / "source" / "gogeta" / "generated")
            self.assertEqual((public / relative).read_bytes(), source.read_bytes(), relative)

    def test_required_runtime_files_are_present(self) -> None:
        required = [
            ROOT / "public" / "game" / "characters" / "go_figure.swf",
            ROOT / "public" / "game" / "pvp-bridge.swf",
            ROOT / "public" / "game" / "original-gogeta-bridge.swf",
            ROOT / "public" / "game" / "gogeta" / "portrait.png",
            ROOT / "public" / "game" / "gogeta" / "versus.png",
        ]
        for path in required:
            self.assertTrue(path.is_file() and path.stat().st_size > 0, path)

    def test_pages_stage_contains_original_mode_release_and_documentation(self) -> None:
        from tools.pages import stage

        with tempfile.TemporaryDirectory(prefix="gogeta_pages_") as temp:
            output = Path(temp)
            stage(output)
            self.assertTrue((output / "game" / "original-gogeta-bridge.swf").is_file())
            hashes = json.loads((output / "web-hashes.json").read_text(encoding="utf8"))
            self.assertIn("game/original-gogeta-bridge.swf", hashes)
            readme = (output / "README.md").read_text(encoding="utf8")
            self.assertIn("웹 1.3.3", readme)
            self.assertIn("원본 게임에서도 오지터", readme)
            self.assertIn("Secret Sword", readme)
            package = json.loads((ROOT / "package.json").read_text(encoding="utf8"))
            self.assertEqual(package["version"], "1.3.3")


if __name__ == "__main__":
    unittest.main()
