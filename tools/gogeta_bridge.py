"""Compile the Gogeta-enabled AVM1 PvP bridge from a pinned template."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "source" / "gogeta" / "pvp-bridge-template.swf"
SOURCE = ROOT / "flash" / "pvp.as"
ORIGINAL_SOURCE = ROOT / "flash" / "original-gogeta.as"
DEFAULT_OUTPUT = ROOT / "public" / "game" / "pvp-bridge.swf"
ORIGINAL_OUTPUT = ROOT / "public" / "game" / "original-gogeta-bridge.swf"


def build_bridge(output: Path, java: Path, ffdec: Path, source: Path = SOURCE) -> None:
    source = source.resolve()
    for path in (TEMPLATE, source, java, ffdec):
        if not path.is_file():
            raise FileNotFoundError(path)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gogeta_bridge_compile_") as temp:
        input_path = Path(temp) / "input.swf"
        compiled = Path(temp) / "compiled.swf"
        shutil.copyfile(TEMPLATE, input_path)
        result = subprocess.run(
            [
                str(java),
                "-Djava.awt.headless=true",
                "-jar",
                str(ffdec),
                "-replace",
                str(input_path),
                str(compiled),
                r"\frame_1\DoAction",
                str(source),
            ],
            capture_output=True,
            text=True,
            encoding="utf8",
            errors="replace",
            check=False,
        )
        if result.returncode or not compiled.is_file():
            raise RuntimeError(
                "FFDec Gogeta bridge compilation failed:\n"
                + result.stdout
                + result.stderr
            )
        output.write_bytes(compiled.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--ffdec", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    build_bridge(args.output, args.java.resolve(), args.ffdec.resolve(), args.source)
    print(f"Built {args.output.resolve()}")


if __name__ == "__main__":
    main()
