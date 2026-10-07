"""Install the original-mode Gogeta bridge loader into the tracked main SWF."""

from __future__ import annotations

import argparse
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME = ROOT / "public" / "game" / "game-original.swf"
DEFAULT_LOADER_SOURCE = ROOT / "flash" / "original-loader.as"
MARKER = b"original-gogeta-bridge.swf"


def unpack(raw: bytes) -> bytes:
    if raw[:3] == b"CWS":
        data = b"FWS" + raw[3:8] + zlib.decompress(raw[8:])
    elif raw[:3] == b"FWS":
        data = raw
    else:
        raise ValueError(f"unsupported SWF signature: {raw[:3]!r}")
    if len(data) != struct.unpack_from("<I", data, 4)[0]:
        raise ValueError("invalid SWF length")
    return data


def tag_start(data: bytes) -> int:
    first = data[8]
    nbits = first >> 3
    rect_bits = 5 + nbits * 4
    rect_bytes = (rect_bits + 7) // 8
    return 8 + rect_bytes + 4


def split(data: bytes) -> tuple[bytes, list[tuple[int, bytes]]]:
    start = tag_start(data)
    tags: list[tuple[int, bytes]] = []
    pos = start
    while pos < len(data):
        begin = pos
        value = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        size = value & 0x3F
        if size == 0x3F:
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        pos += size
        if pos > len(data):
            raise ValueError("truncated SWF tag")
        tags.append((value >> 6, data[begin:pos]))
        if value >> 6 == 0:
            break
    return data[:start], tags


def serialize(header: bytes, tags: list[tuple[int, bytes]], compressed: bool = True) -> bytes:
    body = header + b"".join(raw for _, raw in tags)
    body = b"FWS" + body[3:4] + struct.pack("<I", len(body)) + body[8:]
    if not compressed:
        return body
    return b"CWS" + body[3:8] + zlib.compress(body[8:])


def compile_loader_action(header: bytes, loader_source: Path, java: Path, ffdec: Path) -> tuple[int, bytes]:
    for path in (loader_source, java, ffdec):
        if not path.is_file():
            raise FileNotFoundError(path)
    one_frame_header = header[:-2] + b"\x01\x00"
    placeholder = [
        (12, b"\x01\x03\x00"),
        (1, b"\x40\x00"),
        (0, b"\x00\x00"),
    ]
    with tempfile.TemporaryDirectory(prefix="original_gogeta_loader_") as temp:
        input_path = Path(temp) / "input.swf"
        output_path = Path(temp) / "output.swf"
        input_path.write_bytes(serialize(one_frame_header, placeholder, compressed=False))
        result = subprocess.run(
            [
                str(java),
                "-Djava.awt.headless=true",
                "-jar",
                str(ffdec),
                "-replace",
                str(input_path),
                str(output_path),
                r"\frame_1\DoAction",
                str(loader_source),
            ],
            capture_output=True,
            text=True,
            encoding="utf8",
            errors="replace",
            check=False,
        )
        if result.returncode or not output_path.is_file():
            raise RuntimeError("FFDec original loader compilation failed:\n" + result.stdout + result.stderr)
        _, compiled_tags = split(unpack(output_path.read_bytes()))
        matches = [tag for tag in compiled_tags if tag[0] == 12 and MARKER in tag[1]]
        if len(matches) != 1:
            raise RuntimeError(f"compiled original loader marker count was {len(matches)}")
        return matches[0]


def patch_original_game(path: Path, loader_source: Path, java: Path, ffdec: Path) -> None:
    path = path.resolve()
    data = unpack(path.read_bytes())
    header, tags = split(data)
    loader = compile_loader_action(header, loader_source.resolve(), java.resolve(), ffdec.resolve())
    patched: list[tuple[int, bytes]] = []
    frame = 1
    installed = False
    for code, raw in tags:
        if code == 12 and MARKER in raw:
            if installed:
                continue
            patched.append(loader)
            installed = True
            continue
        if frame == 16 and code == 1 and not installed:
            patched.append(loader)
            installed = True
        patched.append((code, raw))
        if code == 1:
            frame += 1
    if not installed:
        raise RuntimeError("frame 16 ShowFrame was not found")
    encoded = serialize(header, patched, compressed=True)
    _, verified = split(unpack(encoded))
    if sum(1 for code, raw in verified if code == 12 and MARKER in raw) != 1:
        raise RuntimeError("original loader was not installed exactly once")
    path.write_bytes(encoded)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    parser.add_argument("--loader-source", type=Path, default=DEFAULT_LOADER_SOURCE)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--ffdec", type=Path, required=True)
    args = parser.parse_args()
    patch_original_game(args.game, args.loader_source, args.java, args.ffdec)
    print(f"Patched {args.game.resolve()}")


if __name__ == "__main__":
    main()
