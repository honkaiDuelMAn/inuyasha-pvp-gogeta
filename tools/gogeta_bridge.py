"""Compile the Gogeta-enabled AVM1 PvP bridge from a pinned template."""

from __future__ import annotations

import argparse
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISPLAY_SOURCE = ROOT / 'flash' / 'gogeta-display.as'
TEMPLATE = ROOT / "source" / "gogeta" / "pvp-bridge-template.swf"
SOURCE = ROOT / "flash" / "pvp.as"
ORIGINAL_SOURCE = ROOT / "flash" / "original-gogeta.as"
DEFAULT_OUTPUT = ROOT / "public" / "game" / "pvp-bridge.swf"
ORIGINAL_OUTPUT = ROOT / "public" / "game" / "original-gogeta-bridge.swf"


def expand_display(source: str) -> str:
    start = source.index('// BEGIN SHARED GOGETA DISPLAY')
    end = source.index('// END SHARED GOGETA DISPLAY', start)
    return (source[:start] + '// BEGIN SHARED GOGETA DISPLAY\n' +
            DISPLAY_SOURCE.read_text(encoding='utf8') + '\n' + source[end:])


def embed_art(raw: bytes) -> bytes:
    from PIL import Image
    try:
        from .gogeta_figure import lossless_bitmap, bitmap_shape, place_object, stop_action, tag
        from .original_gogeta import split, unpack, serialize
    except ImportError:
        from gogeta_figure import lossless_bitmap, bitmap_shape, place_object, stop_action, tag
        from original_gogeta import split, unpack, serialize
    header, tags = split(unpack(raw))
    definitions = bytearray()
    exports = []
    artwork = sorted((ROOT / 'source/gogeta/generated').rglob('*.png'))
    for index, path in enumerate(artwork):
        bitmap_id = 60000 + index*3
        image = Image.open(path).convert('RGBA')
        definitions.extend(lossless_bitmap(bitmap_id,image))
        exports.append(struct.pack('<H',bitmap_id)+('goBitmap_'+path.stem).encode()+b'\0')
    definitions.extend(tag(56,struct.pack('<H',len(exports))+b''.join(exports)))
    return serialize(header,[(0,bytes(definitions))]+tags,compressed=False)


def build_bridge(output: Path, java: Path, ffdec: Path, source: Path = SOURCE) -> None:
    source = source.resolve()
    for path in (TEMPLATE, source, java, ffdec):
        if not path.is_file():
            raise FileNotFoundError(path)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gogeta_bridge_compile_") as temp:
        input_path = Path(temp) / "input.swf"
        expanded_source = Path(temp) / 'bridge.as'
        compiled = Path(temp) / "compiled.swf"
        shutil.copyfile(TEMPLATE, input_path)
        expanded_source.write_text(expand_display(source.read_text(encoding='utf8')),encoding='utf8')
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
                str(expanded_source),
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
        output.write_bytes(embed_art(compiled.read_bytes()))


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
