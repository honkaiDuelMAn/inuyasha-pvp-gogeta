import hashlib
import json
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "source" / "gogeta" / "input-hashes.json"
MANGA_SOURCE = Path(os.environ.get("MANGA_RPG_SOURCE", r"D:\CHAT\manga rpg\RPG.swf"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GogetaInputHashes(unittest.TestCase):
    def test_declared_inputs_match_real_files(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing {MANIFEST}")
        data = json.loads(MANIFEST.read_text(encoding="utf8"))
        self.assertEqual(data["mangaRpg"]["sha256"], sha256(MANGA_SOURCE))
        self.assertEqual(
            data["inuYasha"]["mainSwfSha256"],
            sha256(ROOT / "public" / "game" / "game-original.swf"),
        )

    def test_original_figure_hashes_remain_the_verified_baseline(self) -> None:
        declared = json.loads(MANIFEST.read_text(encoding="utf8"))["inuYasha"]["figureSha256"]
        baseline = json.loads((ROOT / "tools" / "original-hashes.json").read_text(encoding="utf8"))
        expected = {name: digest for name, digest in baseline.items() if name.endswith("_figure.swf")}
        self.assertEqual(declared, expected)
        for name, digest in declared.items():
            with self.subTest(name=name):
                self.assertEqual(sha256(ROOT / "public" / "game" / "characters" / name), digest)


if __name__ == "__main__":
    unittest.main()
