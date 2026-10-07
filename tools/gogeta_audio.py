"""Extract only the original cues attached to the confirmed fusion sprites.

MP3 files preserve the source bitstream. DefineSound payloads additionally
preserve Flash's sample count and MP3 seek value for exact SWF embedding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

try:
    from .swf_tags import Tag, iter_tags, root_definitions, sprite_frame_count, sprite_placements, swf_tag_start
except ImportError:
    from swf_tags import Tag, iter_tags, root_definitions, sprite_frame_count, sprite_placements, swf_tag_start


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "source" / "gogeta" / "audio"
DEFAULT_SOURCE = Path(r"D:\CHAT\manga rpg\RPG.swf")
MOVE_SOURCES = {
    "basicPunch": (7034, "변신5공격1", 2807),
    "kiRelease": (7062, "변신5스킬z", 2843),
    "bigBangKamehameha": (7158, "변신5스킬e", 3137),
    "dragonFist": (7117, "변신5스킬q", 3026),
    "superEnergyBackflow": (7101, "변신5스킬s", 2940),
    "superKamehameha": (7109, "변신5스킬f", 2968),
}


def parse_define_sound(tag: Tag) -> dict:
    """Return MP3 metadata and bytes without the signed Flash seek field."""
    if tag.code != 14 or len(tag.payload) < 9:
        raise ValueError("expected a complete MP3 DefineSound tag")
    sound_id, flags, samples, seek = struct.unpack_from("<HBIh", tag.payload)
    if flags >> 4 != 2:
        raise ValueError("only original MP3 DefineSound tags are supported")
    rate = (5512, 11025, 22050, 44100)[(flags >> 2) & 3]
    return {
        "soundId": sound_id,
        "format": "mp3",
        "sampleRate": rate,
        "sampleBits": 16 if flags & 2 else 8,
        "channels": 2 if flags & 1 else 1,
        "sampleCount": samples,
        "seekSamples": seek,
        "durationSeconds": round(samples / rate, 6),
        "audioBytes": tag.payload[9:],
    }


def sprite_sound_events(definitions: dict[int, Tag], sprite_id: int) -> list[dict]:
    """Collect one-based cue frames, including statically placed children.

    This represents one traversal of a source animation; action-controlled
    jumps and repeated runtime traversals are deliberately not simulated.
    The selected production sprites have no child sound cues.
    """
    def visit(identifier: int, start: int, path: tuple[int, ...]) -> list[dict]:
        if identifier in path:
            raise ValueError(f"cyclic sound timeline: {path + (identifier,)}")
        sprite = definitions.get(identifier)
        if sprite is None or sprite.code != 39:
            return []
        trail = path + (identifier,)
        frame = 1
        events = []
        for child in iter_tags(sprite.payload, 4):
            if child.code == 1:
                frame += 1
            elif child.code == 15:
                if len(child.payload) < 3:
                    raise ValueError("truncated StartSound tag")
                events.append({
                    "frame": start + frame - 1,
                    "soundId": struct.unpack_from("<H", child.payload)[0],
                    "soundInfoHex": child.payload[2:].hex(),
                    "sourceSpriteId": identifier,
                    "sourceFrame": frame,
                    "spritePath": list(trail),
                })
        final_frame = start + sprite_frame_count(sprite) - 1
        for placement in sprite_placements(sprite):
            events.extend(event for event in visit(
                placement.character_id, start + placement.frame, trail
            ) if event["frame"] <= final_frame)
        return sorted(events, key=lambda event: event["frame"])

    return visit(sprite_id, 1, ())


def export_audio(source: Path = DEFAULT_SOURCE, output: Path = DEFAULT_OUTPUT) -> dict:
    """Write original MP3s, complete DefineSound payloads, and cue evidence."""
    source, output = Path(source), Path(output)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    pinned = json.loads((ROOT / "source" / "gogeta" / "input-hashes.json").read_text(encoding="utf8"))
    if source_sha != pinned["mangaRpg"]["sha256"]:
        raise ValueError("Manga RPG source digest does not match the pinned original")
    data, definitions = root_definitions(source)
    frame_rate = struct.unpack_from("<H", data, swf_tag_start(data) - 4)[0] / 256
    moves = {}
    required_sounds = set()
    for name, (sprite_id, source_label, source_label_frame) in MOVE_SOURCES.items():
        events = sprite_sound_events(definitions, sprite_id)
        required_sounds.update(event["soundId"] for event in events)
        moves[name] = {
            "spriteId": sprite_id,
            "sourceLabel": source_label,
            "sourceLabelFrame": source_label_frame,
            "sourceFrameCount": sprite_frame_count(definitions[sprite_id]),
            "events": events,
        }
    direct_usage = {sound_id: [] for sound_id in required_sounds}
    for sprite_id, sprite in definitions.items():
        if sprite.code != 39:
            continue
        frame = 1
        for child in iter_tags(sprite.payload, 4):
            if child.code == 1:
                frame += 1
            elif child.code == 15:
                sound_id = struct.unpack_from("<H", child.payload)[0]
                if sound_id in direct_usage:
                    direct_usage[sound_id].append({"spriteId": sprite_id, "frame": frame})
    (output / "sounds").mkdir(parents=True, exist_ok=True)
    sounds = []
    for sound_id in sorted(required_sounds):
        definition = definitions[sound_id]
        metadata = parse_define_sound(definition)
        audio_bytes = metadata.pop("audioBytes")
        audio_name = f"sounds/{sound_id}.mp3"
        definition_name = f"sounds/{sound_id}.define-sound.bin"
        (output / audio_name).write_bytes(audio_bytes)
        (output / definition_name).write_bytes(definition.payload)
        metadata.update({
            "audioFile": audio_name,
            "audioSha256": hashlib.sha256(audio_bytes).hexdigest(),
            "definitionFile": definition_name,
            "definitionSha256": hashlib.sha256(definition.payload).hexdigest(),
            "originalTimelineUses": direct_usage[sound_id],
        })
        sounds.append(metadata)
    manifest = {
        "schema": 1,
        "sourceFileName": source.name,
        "sourceSha256": source_sha,
        "characterTimelineId": 7169,
        "sourceForm": "변신5",
        "sourceFrameRate": frame_rate,
        "frameNumbering": "one-based",
        "audioPolicy": "only-original-StartSound-cues-from-confirmed-fusion-sprites",
        "voiceEvidence": {
            "verifiedDedicatedCharacterVoice": False,
            "finding": "No dedicated voice linkage was identified. All selected sounds are reused in other source sprite timelines. No unrelated character voice was substituted.",
        },
        "moves": moves,
        "sounds": sounds,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    return manifest


def definition_tag(sound_id: int, destination_id: int, audio_dir: Path = DEFAULT_OUTPUT) -> bytes:
    """Return a complete DefineSound tag with a collision-free runtime ID."""
    payload = (Path(audio_dir) / "sounds" / f"{sound_id}.define-sound.bin").read_bytes()
    if len(payload) < 9 or struct.unpack_from("<H", payload)[0] != sound_id:
        raise ValueError("original DefineSound payload is missing or mismatched")
    payload = struct.pack("<H", destination_id) + payload[2:]
    return struct.pack("<HI", (14 << 6) | 63, len(payload)) + payload


def start_sound_tag(event: dict, destination_id: int) -> bytes:
    """Return a complete StartSound tag preserving the original SOUNDINFO."""
    payload = struct.pack("<H", destination_id) + bytes.fromhex(event["soundInfoHex"])
    if len(payload) < 63:
        return struct.pack("<H", (15 << 6) | len(payload)) + payload
    return struct.pack("<HI", (15 << 6) | 63, len(payload)) + payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manga-rpg", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = export_audio(args.manga_rpg, args.output)
    print(f"Extracted {len(manifest['sounds'])} original sounds for {len(manifest['moves'])} fusion actions")


if __name__ == "__main__":
    main()
