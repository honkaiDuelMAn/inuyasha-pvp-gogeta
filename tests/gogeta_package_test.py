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
            ROOT / "public" / "game" / "gogeta" / "portrait.png",
            ROOT / "public" / "game" / "gogeta" / "versus.png",
        ]
        for path in required:
            self.assertTrue(path.is_file() and path.stat().st_size > 0, path)


if __name__ == "__main__":
    unittest.main()
