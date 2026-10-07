"""Regressions for the user's white-trouser fusion reference and native cards."""
import json
import struct
import unittest
from pathlib import Path

from PIL import Image

from tools.gogeta_art import make_card
from tools.gogeta_figure import load_sequences, segments
from tools.swf_tags import decompress_swf, iter_tags, swf_tag_start

ROOT = Path(__file__).resolve().parents[1]


class GogetaQuality(unittest.TestCase):
    def test_reference_fusion_bank_replaces_orange_goku_on_every_action(self):
        manifest = json.loads((ROOT / 'source/gogeta/figure-frames.json').read_text())
        self.assertEqual(manifest['sources']['idle']['spriteId'], 7020)
        self.assertEqual(manifest['sources']['bigBangKamehameha']['spriteId'], 7158)
        self.assertEqual(manifest['sources']['dragonFist']['spriteId'], 7117)
        self.assertEqual(manifest['sources']['superEnergyBackflow']['spriteId'], 7101)
        self.assertEqual(manifest['sources']['superKamehameha']['spriteId'], 7109)
        self.assertFalse({6564, 6571, 6585, 6597, 6609, 6649, 6667, 6676}.intersection(
            row['spriteId'] for row in manifest['sources'].values()))

    def test_ambient_uses_standing_fusion_and_punch_is_an_explicit_one_shot(self):
        sequences = load_sequences()
        actions = {name: (frames, behavior) for name, frames, behavior in segments(sequences)}
        self.assertIs(actions['ambient'][0], sequences['idle'])
        self.assertIn('basicPunch', list(actions))
        self.assertEqual(actions['basicPunch'][1], 'hit-done')
        self.assertNotEqual(actions['basicPunch'][0], actions['ambient'][0])
        self.assertEqual([name for name, (_, behavior) in actions.items() if behavior == 'loop'], ['ambient'])

    def test_figure_is_only_a_library_without_autonomous_root_fighter(self):
        data = decompress_swf((ROOT / 'public/game/characters/go_figure.swf').read_bytes())
        placements = [t for t in iter_tags(data, swf_tag_start(data)) if t.code in (4, 26, 70)]
        self.assertEqual(placements, [], 'root fighter bypasses engine callbacks and loops independently')

    def test_standing_fusion_feet_are_anchored_to_the_engine_cell(self):
        frame = load_sequences()['idle'][0]
        self.assertEqual(frame.y + frame.image.height, 0)
        self.assertLessEqual(abs(frame.x + frame.image.width/2), 2)

    def test_native_card_letter_s_is_a_letter_not_the_kikyo_apostrophe(self):
        from tools.gogeta_art import native_font
        glyph = native_font()['S']
        self.assertGreaterEqual(glyph.width,5)
        self.assertTrue(any(glyph.getpixel((x,4))[3] for x in range(glyph.width)))

    def test_attack_cards_preserve_native_dm_en_panel_and_card_outline(self):
        native = Image.open(ROOT / 'source/gogeta/card-templates/attack.png').convert('RGBA')
        for identifier in ('bigBangKamehameha', 'dragonFist', 'superEnergyBackflow', 'superKamehameha'):
            card = make_card(identifier)
            self.assertEqual(card.size, (62, 67))
            self.assertEqual(card.crop((4, 50, 17, 61)).tobytes(), native.crop((4, 50, 17, 61)).tobytes(), identifier)
            for box in ((0, 0, 3, 67), (59, 0, 62, 67), (0, 64, 62, 67)):
                self.assertEqual(card.crop(box).tobytes(), native.crop(box).tobytes(), identifier)

    def test_every_compatible_common_card_has_fusion_art_with_original_rules_panel(self):
        for identifier in ('moveLeft', 'moveRight', 'moveUp', 'moveDown', 'guard', 'energyUp',
                           'doubleLeft', 'doubleRight', 'heal', 'perfectGuard', 'kikyosRevenge', 'summonShippo'):
            with self.subTest(card=identifier):
                card = make_card(identifier)
                native = Image.open(ROOT / 'source/gogeta/card-templates' / (identifier + '.png')).convert('RGBA')
                self.assertEqual(card.crop((0, 47, 62, 67)).tobytes(), native.crop((0, 47, 62, 67)).tobytes())
                self.assertNotEqual(card.crop((3, 16, 59, 46)).tobytes(), native.crop((3, 16, 59, 46)).tobytes())
                self.assertTrue((ROOT / 'public/game/gogeta/common-cards' / (identifier + '.png')).is_file())

    def test_every_skill_embeds_original_sound_events_and_stops_after_completion(self):
        from tools.swf_tags import root_definitions
        _, definitions = root_definitions(ROOT / 'public/game/characters/go_figure.swf')
        self.assertEqual(sum(t.code == 14 for t in definitions.values()), 8)
        sprites = [t for t in definitions.values() if t.code == 39 and b'bigBangKamehameha\0' in t.payload]
        self.assertEqual(len(sprites), 1)
        action, sounds, last_actions = None, {}, {}
        for child in iter_tags(sprites[0].payload, 4):
            if child.code == 43:
                action = child.payload.rstrip(b'\0').decode()
                sounds[action] = []
                last_actions[action] = []
            elif child.code == 15:
                sounds[action].append(child.payload)
            elif child.code == 12:
                last_actions[action].append(child.payload)
        for action in ('basicPunch', 'energyUp', 'bigBangKamehameha', 'dragonFist', 'superEnergyBackflow', 'superKamehameha'):
            self.assertTrue(sounds[action], action)
            self.assertIn(b'\x07\0', last_actions[action], action)
        self.assertEqual(sounds['ambient'], [], 'standing aura must not repeatedly play attack audio')

    def test_both_bridges_embed_same_native_card_and_portrait_pixels(self):
        from tools.swf_tags import root_definitions
        artwork = []
        for filename in ('pvp-bridge.swf', 'original-gogeta-bridge.swf'):
            _, definitions = root_definitions(ROOT / 'public/game' / filename)
            bitmaps = [t.payload[2:] for t in definitions.values() if t.code == 36]
            self.assertEqual(len(bitmaps), 18, filename)
            artwork.append(bitmaps)
        self.assertEqual(artwork[0], artwork[1])


if __name__ == '__main__':
    unittest.main()
