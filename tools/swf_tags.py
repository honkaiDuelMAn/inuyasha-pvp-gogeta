"""Small, strict SWF tag parser used by the Gogeta build tools.

It intentionally implements only the structures needed to validate and
extract placed symbols from the two verified Flash 8 inputs.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DEFINITION_TAGS = {
    2,
    6,
    7,
    10,
    11,
    14,
    20,
    21,
    22,
    32,
    33,
    34,
    35,
    36,
    37,
    39,
    46,
    48,
    60,
    75,
    83,
    84,
    87,
    90,
    91,
}


class BitReader:
    def __init__(self, data: bytes, byte_offset: int = 0) -> None:
        self.data = data
        self.bitpos = byte_offset * 8

    def read_bits(self, count: int) -> int:
        value = 0
        for _ in range(count):
            if self.bitpos >= len(self.data) * 8:
                raise ValueError("bit field exceeds data")
            byte = self.data[self.bitpos // 8]
            shift = 7 - self.bitpos % 8
            value = (value << 1) | ((byte >> shift) & 1)
            self.bitpos += 1
        return value

    def skip_bits(self, count: int) -> None:
        if self.bitpos + count > len(self.data) * 8:
            raise ValueError("bit field exceeds data")
        self.bitpos += count

    def align(self) -> int:
        self.bitpos = (self.bitpos + 7) & ~7
        return self.bitpos // 8


@dataclass(frozen=True)
class Tag:
    code: int
    payload: bytes
    raw: bytes
    offset: int


@dataclass(frozen=True)
class Placement:
    frame: int
    character_id: int
    depth: int
    name: str | None


def decompress_swf(raw: bytes) -> bytes:
    if raw[:3] == b"FWS":
        data = raw
    elif raw[:3] == b"CWS":
        data = b"FWS" + raw[3:8] + zlib.decompress(raw[8:])
    else:
        raise ValueError(f"unsupported SWF signature: {raw[:3]!r}")
    declared = struct.unpack_from("<I", data, 4)[0]
    if declared != len(data):
        raise ValueError(f"SWF length mismatch: header={declared}, actual={len(data)}")
    return data


def swf_tag_start(data: bytes) -> int:
    reader = BitReader(data, 8)
    bits = reader.read_bits(5)
    reader.skip_bits(bits * 4)
    return reader.align() + 4  # frame rate + frame count


def tag_header(data: bytes, offset: int) -> tuple[int, int, int]:
    if offset + 2 > len(data):
        raise ValueError("truncated SWF tag")
    value = struct.unpack_from("<H", data, offset)[0]
    code = value >> 6
    length = value & 0x3F
    header_length = 2
    if length == 0x3F:
        if offset + 6 > len(data):
            raise ValueError("truncated long SWF tag")
        length = struct.unpack_from("<I", data, offset + 2)[0]
        header_length = 6
    return code, length, header_length


def iter_tags(data: bytes, start: int, end: int | None = None) -> Iterator[Tag]:
    limit = len(data) if end is None else end
    offset = start
    while offset < limit:
        code, length, header_length = tag_header(data, offset)
        payload_start = offset + header_length
        payload_end = payload_start + length
        if payload_end > limit:
            raise ValueError(f"tag {code} at {offset} exceeds containing timeline")
        yield Tag(code, data[payload_start:payload_end], data[offset:payload_end], offset)
        offset = payload_end
        if code == 0:
            if offset != limit:
                # Some producers pad the root movie; sprite timelines in the
                # verified inputs do not. Root callers may ignore this tail.
                pass
            return


def read_c_string(data: bytes, offset: int) -> tuple[str, int]:
    end = data.index(0, offset)
    return data[offset:end].decode("utf8", errors="replace"), end + 1


def skip_matrix(data: bytes, offset: int) -> int:
    reader = BitReader(data, offset)
    if reader.read_bits(1):
        count = reader.read_bits(5)
        reader.skip_bits(count * 2)
    if reader.read_bits(1):
        count = reader.read_bits(5)
        reader.skip_bits(count * 2)
    count = reader.read_bits(5)
    reader.skip_bits(count * 2)
    return reader.align()


def skip_cxform_with_alpha(data: bytes, offset: int) -> int:
    reader = BitReader(data, offset)
    has_add = reader.read_bits(1)
    has_mult = reader.read_bits(1)
    count = reader.read_bits(4)
    if has_mult:
        reader.skip_bits(count * 4)
    if has_add:
        reader.skip_bits(count * 4)
    return reader.align()


def parse_place_object(code: int, payload: bytes) -> tuple[int | None, int, str | None]:
    if code == 4:
        if len(payload) < 4:
            raise ValueError("PlaceObject payload too short")
        return struct.unpack_from("<H", payload, 0)[0], struct.unpack_from("<H", payload, 2)[0], None

    if code == 26:
        if len(payload) < 3:
            raise ValueError("PlaceObject2 payload too short")
        flags = payload[0]
        depth = struct.unpack_from("<H", payload, 1)[0]
        offset = 3
        character_id = None
        if flags & 0x02:
            character_id = struct.unpack_from("<H", payload, offset)[0]
            offset += 2
        if flags & 0x04:
            offset = skip_matrix(payload, offset)
        if flags & 0x08:
            offset = skip_cxform_with_alpha(payload, offset)
        if flags & 0x10:
            offset += 2
        name = None
        if flags & 0x20:
            name, offset = read_c_string(payload, offset)
        return character_id, depth, name

    if code == 70:
        if len(payload) < 4:
            raise ValueError("PlaceObject3 payload too short")
        flags1, flags2 = payload[0], payload[1]
        depth = struct.unpack_from("<H", payload, 2)[0]
        offset = 4
        if (flags2 & 0x08) or ((flags2 & 0x10) and (flags1 & 0x02)):
            _, offset = read_c_string(payload, offset)
        character_id = None
        if flags1 & 0x02:
            character_id = struct.unpack_from("<H", payload, offset)[0]
            offset += 2
        if flags1 & 0x04:
            offset = skip_matrix(payload, offset)
        if flags1 & 0x08:
            offset = skip_cxform_with_alpha(payload, offset)
        if flags1 & 0x10:
            offset += 2
        name = None
        if flags1 & 0x20:
            name, offset = read_c_string(payload, offset)
        return character_id, depth, name

    raise ValueError(f"unsupported placement tag {code}")


def root_definitions(path: Path) -> tuple[bytes, dict[int, Tag]]:
    data = decompress_swf(path.read_bytes())
    result: dict[int, Tag] = {}
    for tag in iter_tags(data, swf_tag_start(data)):
        if tag.code in DEFINITION_TAGS and len(tag.payload) >= 2:
            character_id = struct.unpack_from("<H", tag.payload, 0)[0]
            if character_id in result:
                raise ValueError(f"duplicate character definition {character_id}")
            result[character_id] = tag
    return data, result


def sprite_frame_count(tag: Tag) -> int:
    if tag.code != 39 or len(tag.payload) < 4:
        raise ValueError("tag is not DefineSprite")
    return struct.unpack_from("<H", tag.payload, 2)[0]


def sprite_placements(tag: Tag) -> list[Placement]:
    if tag.code != 39 or len(tag.payload) < 4:
        raise ValueError("tag is not DefineSprite")
    frame = 0
    placements: list[Placement] = []
    for child in iter_tags(tag.payload, 4, len(tag.payload)):
        if child.code == 1:
            frame += 1
        elif child.code in (4, 26, 70):
            character_id, depth, name = parse_place_object(child.code, child.payload)
            if character_id is not None:
                placements.append(Placement(frame, character_id, depth, name))
    return placements
