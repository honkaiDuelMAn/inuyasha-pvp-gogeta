"""Original sound bytes and one-based cue frames must survive extraction."""

import hashlib
import importlib.util
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path

from tools.swf_tags import Tag, root_definitions


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("MANGA_RPG_SOURCE", r"D:\CHAT\manga rpg\RPG.swf"))
if importlib.util.find_spec("tools.gogeta_audio"):
    from tools import gogeta_audio
else:
    gogeta_audio = None


def fixture_tag(code, payload):
    if len(payload) < 63:
        raw = struct.pack("<H", (code << 6) | len(payload)) + payload
    else:
        raw = struct.pack("<HI", (code << 6) | 63, len(payload)) + payload
    return Tag(code, payload, raw, 0)


class GogetaOriginalAudio(unittest.TestCase):
    def implementation(self):
        self.assertIsNotNone(gogeta_audio, "Original Gogeta audio extraction is missing")
        return gogeta_audio

    def test_mp3_extraction_preserves_the_sound_and_excludes_seek_header(self):
        # Removing or misplacing the MP3 seek field corrupts playback or timing.
        audio = self.implementation()
        payload = struct.pack("<HBIh", 9, 0x26, 2205, 1661) + b"\xff\xe3original-mp3"
        sound = audio.parse_define_sound(fixture_tag(14, payload))
        self.assertEqual(sound["soundId"], 9)
        self.assertEqual(sound["sampleRate"], 11025)
        self.assertEqual(sound["channels"], 1)
        self.assertEqual(sound["sampleCount"], 2205)
        self.assertEqual(sound["seekSamples"], 1661)
        self.assertEqual(sound["audioBytes"], b"\xff\xe3original-mp3")

    def test_nested_sound_cues_use_one_based_parent_frames(self):
        # An off-by-one in placement timing plays the nested cue on frame 3.
        audio = self.implementation()
        show = fixture_tag(1, b"").raw
        end = fixture_tag(0, b"").raw
        child = fixture_tag(39, struct.pack("<HH", 11, 2) + show
                            + fixture_tag(15, struct.pack("<H", 9) + b"\x00").raw
                            + show + end)
        placement = fixture_tag(26, struct.pack("<BHH", 2, 1, 11)).raw
        parent = fixture_tag(39, struct.pack("<HH", 12, 5) + show + show
                             + placement + show + show + show + end)
        events = audio.sprite_sound_events({11: child, 12: parent}, 12)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["frame"], 4)
        self.assertEqual(events[0]["sourceSpriteId"], 11)
        self.assertEqual(events[0]["sourceFrame"], 2)
        self.assertEqual(events[0]["soundId"], 9)
        self.assertEqual(events[0]["soundInfoHex"], "00")

    def test_malformed_or_non_mp3_definitions_are_rejected(self):
        audio = self.implementation()
        with self.assertRaises(ValueError):
            audio.parse_define_sound(fixture_tag(14, b"\x09\x00\x26"))
        with self.assertRaises(ValueError):
            audio.parse_define_sound(fixture_tag(14, struct.pack("<HBI", 9, 0x16, 22) + b"data"))

    def test_real_source_extracts_only_cues_from_the_confirmed_fusion_form(self):
        # Reusing orange-Goku timelines or guessing voice IDs changes these cues.
        audio = self.implementation()
        _, definitions = root_definitions(SOURCE)
        expected = {
            7034: [(6, 2456)],
            7062: [(3, 1927)],
            7158: [(2, 93), (13, 100), (36, 3763), (73, 93)],
            7117: [(39, 1990)],
            7101: [(17, 3712)],
            7109: [(2, 100), (50, 1704)],
        }
        for sprite_id, cues in expected.items():
            with self.subTest(sprite_id=sprite_id):
                self.assertEqual([(e["frame"], e["soundId"])
                                  for e in audio.sprite_sound_events(definitions, sprite_id)], cues)

    def test_export_is_deterministic_and_sound_bytes_match_original(self):
        # Transcoding, including unrelated sounds, or dropping cues must fail.
        audio = self.implementation()
        _, definitions = root_definitions(SOURCE)
        with tempfile.TemporaryDirectory(prefix="gogeta_audio_") as tmp:
            output = Path(tmp)
            first = audio.export_audio(SOURCE, output)
            manifest_bytes = (output / "manifest.json").read_bytes()
            second = audio.export_audio(SOURCE, output)
            self.assertEqual(first, second)
            self.assertEqual((output / "manifest.json").read_bytes(), manifest_bytes)
            self.assertEqual(first["sourceSha256"],
                             "7bb23abfdad7ef49979c8d535926fc0a86ec54b485c2bf9676bc78b9f333c106")
            self.assertEqual([s["soundId"] for s in first["sounds"]],
                             [93, 100, 1704, 1927, 1990, 2456, 3712, 3763])
            for sound in first["sounds"]:
                original = definitions[sound["soundId"]].payload
                self.assertEqual((output / sound["definitionFile"]).read_bytes(), original)
                self.assertEqual((output / sound["audioFile"]).read_bytes(), original[9:])
                self.assertEqual(hashlib.sha256(original[9:]).hexdigest(), sound["audioSha256"])
            self.assertEqual(first["moves"]["basicPunch"]["spriteId"], 7034)
            self.assertEqual(first["moves"]["kiRelease"]["spriteId"], 7062)
            self.assertEqual(first["moves"]["bigBangKamehameha"]["spriteId"], 7158)
            self.assertEqual(first["moves"]["dragonFist"]["spriteId"], 7117)
            self.assertEqual(first["moves"]["superEnergyBackflow"]["spriteId"], 7101)
            self.assertEqual(first["moves"]["superKamehameha"]["spriteId"], 7109)

    def test_embedded_tags_remap_ids_and_preserve_original_soundinfo(self):
        # Reusing the original IDs can collide with bitmap IDs in go_figure.
        audio = self.implementation()
        with tempfile.TemporaryDirectory(prefix="gogeta_audio_") as tmp:
            output = Path(tmp)
            manifest = audio.export_audio(SOURCE, output)
            _, definitions = root_definitions(SOURCE)
            definition = audio.definition_tag(2456, 60001, output)
            self.assertEqual(definition[6:8], struct.pack("<H", 60001))
            self.assertEqual(definition[8:], definitions[2456].payload[2:])
            event = manifest["moves"]["basicPunch"]["events"][0]
            self.assertEqual(audio.start_sound_tag(event, 60001),
                             struct.pack("<H", (15 << 6) | 3) + struct.pack("<H", 60001) + b"\x00")


if __name__ == "__main__":
    unittest.main()
