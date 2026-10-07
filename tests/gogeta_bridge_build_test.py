import hashlib
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "source" / "gogeta" / "pvp-bridge-template.swf"
OUTPUT = ROOT / "public" / "game" / "pvp-bridge.swf"


class GogetaBridgeBuild(unittest.TestCase):
    def test_bridge_is_built_from_a_pinned_template_and_contains_gogeta_callbacks(self) -> None:
        self.assertTrue(TEMPLATE.is_file(), TEMPLATE)
        self.assertTrue(OUTPUT.is_file(), OUTPUT)
        data = OUTPUT.read_bytes()
        for value in [
            b"pvpChooseGogeta",
            b"pvpGogetaState",
            b"bigBangKamehameha",
            b"superEnergyBackflow",
            b"goMoves",
        ]:
            self.assertIn(value, data)

    def test_bridge_build_is_deterministic(self) -> None:
        from tools.gogeta_bridge import build_bridge

        java = Path(os.environ.get("JAVA_PATH", r"C:\Program Files (x86)\NS-USBloader\jdk\bin\java.exe"))
        ffdec = Path(os.environ.get(
            "FFDEC_PATH",
            r"D:\CHAT\inuyasha-pvp-github-update-20261006\scratch\test-tools\ffdec\ffdec.jar",
        ))
        with tempfile.TemporaryDirectory(prefix="gogeta_bridge_") as temp:
            first, second = Path(temp) / "first.swf", Path(temp) / "second.swf"
            build_bridge(first, java, ffdec)
            build_bridge(second, java, ffdec)
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), hashlib.sha256(second.read_bytes()).hexdigest())
            self.assertEqual(first.read_bytes(), OUTPUT.read_bytes())


if __name__ == "__main__":
    unittest.main()
