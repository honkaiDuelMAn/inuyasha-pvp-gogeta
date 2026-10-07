"""Build a compact raster-backed `goMoves` Flash figure.

The original game loads one external figure SWF per character and drives an
exported movie clip by frame labels. This builder creates that exact interface
from the checked-in Manga RPG fusion-frame selection without recompiling or
editing the source RPG SWF.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FRAME_MANIFEST = ROOT / "source" / "gogeta" / "figure-frames.json"
DEFAULT_OUTPUT = ROOT / "public" / "game" / "characters" / "go_figure.swf"
STAGE_WIDTH = 550
STAGE_HEIGHT = 400
TWIPS = 20


class Bits:
    def __init__(self) -> None:
        self.values: list[int] = []

    def unsigned(self, value: int, count: int) -> None:
        if value < 0 or value >= 1 << count:
            raise ValueError((value, count))
        self.values.extend((value >> shift) & 1 for shift in range(count - 1, -1, -1))

    def signed(self, value: int, count: int) -> None:
        minimum, maximum = -(1 << (count - 1)), (1 << (count - 1)) - 1
        if not minimum <= value <= maximum:
            raise ValueError((value, count))
        self.unsigned(value & ((1 << count) - 1), count)

    def bytes(self) -> bytes:
        values = list(self.values)
        values.extend([0] * ((8 - len(values) % 8) % 8))
        result = bytearray()
        for offset in range(0, len(values), 8):
            byte = 0
            for bit in values[offset : offset + 8]:
                byte = (byte << 1) | bit
            result.append(byte)
        return bytes(result)


def signed_bits(*values: int) -> int:
    for count in range(1, 33):
        minimum, maximum = -(1 << (count - 1)), (1 << (count - 1)) - 1
        if all(minimum <= value <= maximum for value in values):
            return count
    raise ValueError(values)


def rect(x_min: int, x_max: int, y_min: int, y_max: int) -> bytes:
    count = signed_bits(x_min, x_max, y_min, y_max)
    bits = Bits()
    bits.unsigned(count, 5)
    for value in (x_min, x_max, y_min, y_max):
        bits.signed(value, count)
    return bits.bytes()


def matrix(
    *,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    translate_x: int = 0,
    translate_y: int = 0,
) -> bytes:
    bits = Bits()
    scaled_x, scaled_y = round(scale_x * 65536), round(scale_y * 65536)
    has_scale = scaled_x != 65536 or scaled_y != 65536
    bits.unsigned(1 if has_scale else 0, 1)
    if has_scale:
        count = signed_bits(scaled_x, scaled_y)
        bits.unsigned(count, 5)
        bits.signed(scaled_x, count)
        bits.signed(scaled_y, count)
    bits.unsigned(0, 1)  # no rotate/skew
    count = signed_bits(translate_x, translate_y)
    bits.unsigned(count, 5)
    bits.signed(translate_x, count)
    bits.signed(translate_y, count)
    return bits.bytes()


def tag(code: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    if length < 0x3F:
        return struct.pack("<H", (code << 6) | length) + payload
    return struct.pack("<HI", (code << 6) | 0x3F, length) + payload


def shape_records(width: int, height: int) -> bytes:
    """Rectangle using fill style 1 and no line style."""
    w, h = width * TWIPS, height * TWIPS
    bits = Bits()
    bits.unsigned(1, 4)  # NumFillBits
    bits.unsigned(0, 4)  # NumLineBits
    # StyleChange: move to 0,0 and select FillStyle1 = 1.
    bits.unsigned(0, 1)
    bits.unsigned(0, 1)  # StateNewStyles
    bits.unsigned(0, 1)  # StateLineStyle
    bits.unsigned(1, 1)  # StateFillStyle1
    bits.unsigned(0, 1)  # StateFillStyle0
    bits.unsigned(1, 1)  # StateMoveTo
    bits.unsigned(1, 5)
    bits.signed(0, 1)
    bits.signed(0, 1)
    bits.unsigned(1, 1)  # FillStyle1 index

    def edge(dx: int, dy: int) -> None:
        count = max(2, signed_bits(dx, dy))
        bits.unsigned(1, 1)  # edge record
        bits.unsigned(1, 1)  # straight edge
        bits.unsigned(count - 2, 4)
        bits.unsigned(1, 1)  # general line
        bits.signed(dx, count)
        bits.signed(dy, count)

    edge(w, 0)
    edge(0, h)
    edge(-w, 0)
    edge(0, -h)
    bits.unsigned(0, 1)
    bits.unsigned(0, 5)  # EndShapeRecord
    return bits.bytes()


def lossless_bitmap(identifier: int, image: Image.Image) -> bytes:
    rgba = image.convert("RGBA")
    pixels = bytearray()
    for red, green, blue, alpha in rgba.getdata():
        # DefineBitsLossless2 stores premultiplied ARGB.
        pixels.extend(
            (
                alpha,
                red * alpha // 255,
                green * alpha // 255,
                blue * alpha // 255,
            )
        )
    payload = struct.pack("<HBHH", identifier, 5, rgba.width, rgba.height)
    payload += zlib.compress(bytes(pixels), level=9)
    return tag(36, payload)


def bitmap_shape(identifier: int, bitmap_id: int, width: int, height: int) -> bytes:
    payload = bytearray(struct.pack("<H", identifier))
    payload.extend(rect(0, width * TWIPS, 0, height * TWIPS))
    payload.append(1)  # one fill style
    payload.append(0x41)  # clipped bitmap fill
    payload.extend(struct.pack("<H", bitmap_id))
    payload.extend(matrix(scale_x=TWIPS, scale_y=TWIPS))
    payload.append(0)  # no line styles
    payload.extend(shape_records(width, height))
    return tag(32, bytes(payload))


def place_object(identifier: int, depth: int, x: int, y: int) -> bytes:
    flags = 0x06  # HasCharacter + HasMatrix
    payload = struct.pack("<BHH", flags, depth, identifier)
    payload += matrix(translate_x=x * TWIPS, translate_y=y * TWIPS)
    return tag(26, payload)


def remove_object(depth: int) -> bytes:
    return tag(28, struct.pack("<H", depth))


def frame_label(name: str) -> bytes:
    return tag(43, name.encode("utf8") + b"\0")


def push(*values: str | int) -> bytes:
    payload = bytearray()
    for value in values:
        if isinstance(value, str):
            payload.append(0)
            payload.extend(value.encode("utf8") + b"\0")
        elif isinstance(value, int):
            payload.append(7)
            payload.extend(struct.pack("<i", value))
        else:
            raise TypeError(value)
    return bytes((0x96,)) + struct.pack("<H", len(payload)) + payload


def event_action(event: str) -> bytes:
    actions = bytearray()
    actions.extend(push("event", event, 1))
    actions.append(0x43)  # ActionInitObject
    actions.extend(push(1, "this"))
    actions.append(0x1C)  # ActionGetVariable
    actions.extend(push("onMoveEvent"))
    actions.append(0x52)  # ActionCallMethod
    actions.append(0x17)  # ActionPop
    actions.append(0)
    return tag(12, bytes(actions))


def goto_action(label: str) -> bytes:
    actions = bytearray()
    actions.extend(push(label, 1, "this"))
    actions.append(0x1C)
    actions.extend(push("gotoAndPlay"))
    actions.append(0x52)
    actions.append(0x17)
    actions.append(0)
    return tag(12, bytes(actions))


def stop_action() -> bytes:
    return tag(12, b"\x07\x00")


@dataclass(frozen=True)
class RenderedFrame:
    image: Image.Image
    x: int
    y: int


def normalize_sequence(paths: list[Path]) -> list[RenderedFrame]:
    images = [Image.open(path).convert("RGBA") for path in paths]
    canvas_width, canvas_height = images[0].size
    if any(image.size != (canvas_width, canvas_height) for image in images):
        raise ValueError("animation source frames changed canvas size")
    # ViewRoundPlayers attaches the figure at the cell's floor coordinate.
    # Export canvas centers are unrelated to that anchor and used to offset
    # the controlled fighter hundreds of pixels away from its actual cell.
    first_box = images[0].getbbox()
    if first_box is None:
        raise ValueError('first animation frame has no fighter/effect anchor')
    anchor_x = round((first_box[0]+first_box[2])/2)
    anchor_y = first_box[3]
    # Keep the fighter's native size. Crop oversized effects to a stable
    # viewport around its origin instead of shrinking the whole character.
    viewport = (max(0,anchor_x-260),max(0,anchor_y-300),
                min(canvas_width,anchor_x+260),min(canvas_height,anchor_y+60))
    rendered: list[RenderedFrame] = []
    for image in images:
        cropped_view = image.crop(viewport)
        box = cropped_view.getbbox()
        if not box:
            box = (0, 0, 1, 1)
        cropped = cropped_view.crop(box)
        rendered.append(RenderedFrame(cropped, viewport[0]+box[0]-anchor_x, viewport[1]+box[1]-anchor_y))
    return rendered


def load_sequences() -> dict[str, list[RenderedFrame]]:
    manifest = json.loads(FRAME_MANIFEST.read_text(encoding="utf8"))
    return {
        name: normalize_sequence([ROOT / path for path in paths])
        for name, paths in manifest["generated"].items()
    }


def segments(sequences: dict[str, list[RenderedFrame]]) -> list[tuple[str, list[RenderedFrame], str]]:
    jump = sequences["jump"]
    guard = sequences["guard"]
    aura = sequences["aura"]
    return [
        ("ambient", sequences["idle"], "loop"),
        ("hit", sequences["hit"], "done"),
        ("guard_up", guard, "done"),
        ("guard_stay", [guard[-1]], "stop"),
        ("guard_down", list(reversed(guard)), "done"),
        ("perfectGuard_up", guard, "done"),
        ("perfectGuard_stay", [guard[-1]], "stop"),
        ("perfectGuard_down", list(reversed(guard)), "done"),
        ("guard", guard + list(reversed(guard[:-1])), "done"),
        ("perfectGuard", guard + list(reversed(guard[:-1])), "done"),
        ("moveNone", sequences["idle"][:3], "done"),
        ("moveDown", jump, "done"),
        ("moveRight", jump, "done"),
        ("moveUp", jump, "done"),
        ("moveLeft", jump, "done"),
        ("doubleDown", jump, "done"),
        ("doubleRight", jump, "done"),
        ("doubleUp", jump, "done"),
        ("doubleLeft", jump, "done"),
        ("victory", sequences["victory"], "done"),
        ("defeat", sequences["defeat"], "done"),
        ("heal", aura, "done"),
        ("energyUp", aura, "done"),
        ("summonShippo", aura, "hit-done"),
        ("basicPunch", sequences["basicPunch"], "hit-done"),
        ("bigBangKamehameha", sequences["bigBangKamehameha"], "hit-done"),
        ("dragonFist", sequences["dragonFist"], "hit-done"),
        ("superEnergyBackflow", sequences["superEnergyBackflow"], "hit-done"),
        ("superKamehameha", sequences["superKamehameha"], "hit-done"),
    ]


def move_label(character_id: str, move_id: str) -> str:
    """Return the frame label consumed by ViewRoundPlayers.action.

    The exported linkage name identifies the character (``goMoves``). The
    action timeline itself is addressed with raw move IDs such as
    ``bigBangKamehameha`` and ``ambient``.
    """
    if not move_id:
        raise ValueError("move id may not be empty")
    return move_id


def build_figure(output: Path = DEFAULT_OUTPUT) -> None:
    try:
        from .gogeta_audio import DEFAULT_OUTPUT as AUDIO_DIR, definition_tag, start_sound_tag
    except ImportError:
        from gogeta_audio import DEFAULT_OUTPUT as AUDIO_DIR, definition_tag, start_sound_tag
    sequences = load_sequences()
    definitions = bytearray()
    audio = json.loads((AUDIO_DIR / 'manifest.json').read_text(encoding='utf8'))
    sound_ids = {row['soundId']: 50000+index for index,row in enumerate(audio['sounds'])}
    for source_id,runtime_id in sound_ids.items():
        definitions.extend(definition_tag(source_id,runtime_id))
    timeline = bytearray()
    next_id = 1
    depth = 1
    first_frame = True
    total_frames = 0

    for action_id, frames, behavior in segments(sequences):
        label = move_label("go", action_id)
        timeline.extend(frame_label(label))
        hit_index = max(0, min(len(frames) - 1, round((len(frames) - 1) * 0.62)))
        for index, rendered in enumerate(frames):
            bitmap_id, shape_id = next_id, next_id + 1
            next_id += 2
            definitions.extend(lossless_bitmap(bitmap_id, rendered.image))
            definitions.extend(bitmap_shape(shape_id, bitmap_id, rendered.image.width, rendered.image.height))
            if not first_frame:
                timeline.extend(remove_object(depth))
            timeline.extend(place_object(shape_id, depth, rendered.x, rendered.y))
            first_frame = False
            audio_id = 'kiRelease' if action_id in ('energyUp','heal','summonShippo') else action_id
            for event in audio['moves'].get(audio_id,{}).get('events',[]):
                if event['frame'] == index+1:
                    timeline.extend(start_sound_tag(event,sound_ids[event['soundId']]))
            if behavior == "hit-done" and index == hit_index:
                timeline.extend(event_action("hit"))
            if index == len(frames) - 1:
                if behavior == "loop":
                    timeline.extend(goto_action(label))
                elif behavior == "stop":
                    timeline.extend(stop_action())
                else:
                    # Completion may be observational (no replacement attached).
                    # Never fall through into the next move's timeline.
                    timeline.extend(stop_action())
                    timeline.extend(event_action("done"))
            timeline.extend(tag(1))
            total_frames += 1

    timeline.extend(tag(0))
    moves_id = next_id
    sprite = tag(39, struct.pack("<HH", moves_id, total_frames) + bytes(timeline))
    fx_top_id, fx_bottom_id = moves_id + 1, moves_id + 2
    empty_fx = tag(1) + tag(0)
    fx_top = tag(39, struct.pack("<HH", fx_top_id, 1) + empty_fx)
    fx_bottom = tag(39, struct.pack("<HH", fx_bottom_id, 1) + empty_fx)
    exports = tag(
        56,
        struct.pack("<H", 3)
        + struct.pack("<H", moves_id) + b"goMoves\0"
        + struct.pack("<H", fx_top_id) + b"goFxTop\0"
        + struct.pack("<H", fx_bottom_id) + b"goFxBottom\0",
    )
    root = bytearray()
    root.extend(definitions)
    root.extend(sprite)
    root.extend(fx_top)
    root.extend(fx_bottom)
    root.extend(exports)
    # BattleLoadManager loads a symbol library. Only ViewRoundPlayers may
    # attach goMoves. A visible root instance bypasses its callbacks and keeps
    # playing at a fixed map cell even after the real fighter moves away.
    root.extend(stop_action())
    root.extend(tag(1))
    root.extend(tag(0))

    header_body = rect(0, STAGE_WIDTH * TWIPS, 0, STAGE_HEIGHT * TWIPS)
    header_body += struct.pack("<HH", 31 << 8, 1)
    uncompressed = b"FWS" + bytes((8,)) + b"\0\0\0\0" + header_body + bytes(root)
    uncompressed = uncompressed[:4] + struct.pack("<I", len(uncompressed)) + uncompressed[8:]
    compressed = b"CWS" + uncompressed[3:8] + zlib.compress(uncompressed[8:], level=9)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(compressed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_figure(args.output.resolve())
    print(f"Built {args.output.resolve()}")


if __name__ == "__main__":
    main()
