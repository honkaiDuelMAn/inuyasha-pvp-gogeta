import test from 'node:test';
import assert from 'node:assert/strict';

import {RoomService, catalog, validateMoves} from '../server/rooms.mjs';

const client = id => ({id, events: [], send(event) { this.events.push(structuredClone(event)); }});
const last = (client, type) => client.events.filter(event => event.type === type).at(-1);

const expectedMoves = {
  bigBangKamehameha: {energy: -50, damage: -40, area: '0,0,0_0,1,0_1,1,1'},
  dragonFist: {energy: -60, damage: -70, area: '0,0,0_1,1,1_0,0,0'},
  superEnergyBackflow: {energy: -25, damage: -25, area: '1,1,1_1,1,1_1,1,1'},
  superKamehameha: {energy: -20, damage: -35, area: '0,0,0_1,1,1_0,0,0'},
};

test('Gogeta catalog has the exact four requested base moves', () => {
  const byId = new Map(catalog.map(move => [move.id, move]));
  for (const [id, expected] of Object.entries(expectedMoves)) {
    const move = byId.get(id);
    assert.ok(move, id);
    assert.deepEqual(move.characters, ['go']);
    assert.equal(move.advanced, false);
    assert.equal(move.energy, expected.energy);
    assert.equal(move.damage, expected.damage);
    assert.equal(move.area, expected.area);
  }
});

test('all common actions accept Gogeta and only Shippo is his dedicated card', () => {
  const byId = new Map(catalog.map(move => [move.id, move]));
  for (const id of ['guard', 'energyUp', 'moveLeft', 'moveRight', 'moveUp', 'moveDown',
    'perfectGuard', 'heal', 'kikyosRevenge', 'doubleRight', 'doubleLeft']) {
    assert.ok(byId.get(id).characters.includes('go'), id);
  }
  const dedicated = catalog
    .filter(move => move.advanced && !['perfectGuard', 'heal', 'kikyosRevenge', 'doubleRight', 'doubleLeft'].includes(move.id))
    .filter(move => move.characters.includes('go'))
    .map(move => move.id);
  assert.deepEqual(dedicated, ['summonShippo']);
});

test('Gogeta mirror room starts and accepts a legal attack hand', () => {
  const service = new RoomService({randomInt: () => 0});
  const host = client('host'), guest = client('guest');
  service.handle(host, {type: 'create', bonusCount: 0, dedicatedEnabled: true});
  service.handle(guest, {type: 'join', code: last(host, 'joined').code});
  for (const player of [host, guest]) {
    service.handle(player, {type: 'character', character: 'go'});
    service.handle(player, {type: 'ready'});
  }
  const start = last(host, 'start');
  assert.deepEqual(start.characters, ['go', 'go']);
  assert.deepEqual(start.dedicatedCards, [['summonShippo'], ['summonShippo']]);
  for (const player of [host, guest]) service.handle(player, {type: 'loaded', match: start.match});
  const hand = ['superKamehameha', 'superEnergyBackflow', 'energyUp'];
  for (const player of [host, guest]) service.handle(player, {type: 'moves', match: start.match, round: 1, moves: hand});
  assert.deepEqual(last(host, 'play').moves, [hand, hand]);
});

test('Gogeta energy validation uses the requested costs', () => {
  const available = Object.keys(expectedMoves).concat(['guard', 'energyUp']);
  assert.equal(validateMoves(['superKamehameha', 'superEnergyBackflow', 'guard'], available, 45), true);
  assert.equal(validateMoves(['superKamehameha', 'superEnergyBackflow', 'guard'], available, 44), false);
  assert.equal(validateMoves(['energyUp', 'dragonFist', 'bigBangKamehameha'], available, 95), true);
  assert.equal(validateMoves(['energyUp', 'dragonFist', 'bigBangKamehameha'], available, 94), false);
});
