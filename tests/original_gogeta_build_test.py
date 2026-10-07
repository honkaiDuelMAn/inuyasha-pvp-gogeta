import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.swf_tags import decompress_swf, iter_tags, swf_tag_start


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "flash" / "original-gogeta.as"
LOADER_SOURCE = ROOT / "flash" / "original-loader.as"
TOOL = ROOT / "tools" / "original_gogeta.py"
BRIDGE = ROOT / "public" / "game" / "original-gogeta-bridge.swf"
ORIGINAL = ROOT / "public" / "game" / "game-original.swf"
PVP = ROOT / "public" / "game" / "game-pvp.swf"
JAVA = Path(os.environ.get("JAVA_PATH", r"C:\Program Files (x86)\NS-USBloader\jdk\bin\java.exe"))
FFDEC = Path(os.environ.get(
    "FFDEC_PATH",
    r"D:\CHAT\inuyasha-pvp-github-update-20261006\scratch\test-tools\ffdec\ffdec.jar",
))


def frame_actions(path: Path) -> list[tuple[int, bytes]]:
    data = decompress_swf(path.read_bytes())
    frame = 1
    actions: list[tuple[int, bytes]] = []
    for tag in iter_tags(data, swf_tag_start(data)):
        if tag.code == 12:
            actions.append((frame, tag.raw))
        if tag.code == 1:
            frame += 1
    return actions


class OriginalGogetaBuild(unittest.TestCase):
    def test_original_bridge_sources_tool_and_output_exist(self) -> None:
        for path in [SOURCE, LOADER_SOURCE, TOOL, BRIDGE]:
            self.assertTrue(path.is_file(), path)

    @unittest.skipUnless(SOURCE.is_file() and BRIDGE.is_file(), "original bridge not implemented yet")
    def test_original_bridge_has_exact_contract_and_progression(self) -> None:
        source = SOURCE.read_text(encoding="utf8")
        binary = BRIDGE.read_bytes()
        for value in [
            "originalChooseGogeta",
            "originalGogetaState",
            "originalGogetaEvent",
            "bigBangKamehameha",
            "dragonFist",
            "superEnergyBackflow",
            "superKamehameha",
            "summonShippo",
            "goMoves",
        ]:
            self.assertIn(value, source)
            self.assertIn(value.encode("utf8"), binary)
        self.assertIn('["sa","ko","ka","s","n"]', source.replace(" ", ""))
        compact = source.replace(" ", "")
        self.assertRegex(compact, r'addGogetaMove\("bigBangKamehameha","[^"]+",-50,-40')
        self.assertRegex(compact, r'addGogetaMove\("dragonFist","[^"]+",-60,-70')
        self.assertRegex(compact, r'addGogetaMove\("superEnergyBackflow","[^"]+",-25,-25')
        self.assertRegex(compact, r'addGogetaMove\("superKamehameha","[^"]+",-20,-35')
        self.assertIn("originalGogetaRedraw", source)
        self.assertIn('playerA:"i"', compact)

    def test_original_main_has_one_original_loader_and_pvp_has_one_pvp_loader(self) -> None:
        original = [raw for frame, raw in frame_actions(ORIGINAL) if frame == 16 and b"original-gogeta-bridge.swf" in raw]
        pvp = [raw for frame, raw in frame_actions(PVP) if frame == 16 and b"pvp-bridge.swf" in raw]
        self.assertEqual(len(original), 1)
        self.assertEqual(len(pvp), 1)

    @unittest.skipUnless(TOOL.is_file(), "original game patcher not implemented yet")
    def test_original_main_patch_is_idempotent(self) -> None:
        from tools.original_gogeta import patch_original_game

        with tempfile.TemporaryDirectory(prefix="original_gogeta_") as temp:
            target = Path(temp) / "game-original.swf"
            shutil.copyfile(ORIGINAL, target)
            patch_original_game(target, LOADER_SOURCE, JAVA, FFDEC)
            first = target.read_bytes()
            patch_original_game(target, LOADER_SOURCE, JAVA, FFDEC)
            second = target.read_bytes()
            self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
