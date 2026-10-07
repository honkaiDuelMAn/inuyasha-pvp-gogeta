import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source = await readFile(new URL('../flash/pvp.as', import.meta.url), 'utf8');

test('PvP bridge installs Gogeta with exact combat data', () => {
  for (const snippet of [
    'bigBangKamehameha", "빅뱅 애네르기파", -50, -40',
    'dragonFist", "용권", -60, -70',
    'superEnergyBackflow", "초 에너지 역류", -25, -25',
    'superKamehameha", "초 에네르기파", -20, -35',
    '[[0,0,0],[0,1,0],[1,1,1]]',
    '[[0,0,0],[1,1,1],[0,0,0]]',
    '[[1,1,1],[1,1,1],[1,1,1]]',
  ]) assert.ok(source.includes(snippet), snippet);
  assert.match(source, /compatibleCharacters.*go|addCompatible/);
  assert.match(source, /summonShippo/);
});

test('PvP bridge exposes Gogeta selection and picker state without changing transport', () => {
  assert.match(source, /pvpChooseGogeta/);
  assert.match(source, /pvpGogetaState/);
  assert.doesNotMatch(source, /pvpTestSubmitMoves|pvpGogetaPrereqs/);
  assert.match(source, /emit\("picking"/);
  assert.match(source, /characterIdToLinkageIdKey/);
  assert.match(source, /goMoves/);
});
