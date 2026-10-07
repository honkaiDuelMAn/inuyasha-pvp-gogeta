import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASHES = json.loads((ROOT / 'tools/original-hashes.json').read_text(encoding='utf8'))


def tags(path):
    data = path.read_bytes()
    if data[:3] == b'CWS':
        data = data[:8] + zlib.decompress(data[8:])
    assert len(data) == struct.unpack_from('<I', data, 4)[0]
    pos = 8 + (5 + 4 * (data[8] >> 3) + 7) // 8 + 4
    result = []
    while pos < len(data):
        start = pos
        value = struct.unpack_from('<H', data, pos)[0]
        pos += 2
        size = value & 63
        if size == 63:
            size = struct.unpack_from('<I', data, pos)[0]
            pos += 4
        result.append((value >> 6, data[start:pos + size]))
        pos += size
    return result


class Preservation(unittest.TestCase):
    def test_both_modes_preserve_the_same_balanced_tags_with_one_loader_each(self):
        original = tags(ROOT / 'public/game/game-original.swf')
        pvp = tags(ROOT / 'public/game/game-pvp.swf')

        def without_loader(values, marker):
            frame = 1
            filtered = []
            removed = []
            for tag in values:
                if tag[0] == 12 and marker in tag[1]:
                    removed.append((frame, tag))
                else:
                    filtered.append(tag)
                if tag[0] == 1:
                    frame += 1
            self.assertEqual(len(removed), 1)
            self.assertEqual(removed[0][0], 16)
            return filtered

        balanced_original = without_loader(original, b'original-gogeta-bridge.swf')
        balanced_pvp = without_loader(pvp, b'pvp-bridge.swf')
        self.assertEqual(balanced_original, balanced_pvp)

    def test_character_files_are_unchanged(self):
        self.assertEqual(len(HASHES), 12)
        for name, expected in HASHES.items():
            if name == 'game.swf':
                continue  # Three authorized Sango tags are checked by sango_test.
            target = ROOT / 'public/game/characters' / name
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), expected)

    def test_flash_versions_preserve_original_execution_rules(self):
        for name in ['game-original.swf', 'game-pvp.swf']:
            self.assertEqual((ROOT / 'public/game' / name).read_bytes()[3], 6)
        self.assertEqual((ROOT / 'public/game/pvp-bridge.swf').read_bytes()[3], 8)
        self.assertEqual((ROOT / 'public/game/original-gogeta-bridge.swf').read_bytes()[3], 8)


if __name__ == '__main__':
    unittest.main()
