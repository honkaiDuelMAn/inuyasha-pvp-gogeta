import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const app = await readFile(new URL('../public/app.mjs', import.meta.url), 'utf8');
const html = await readFile(new URL('../public/direct.html', import.meta.url), 'utf8');


test('original mode loads the Sango-balanced game with the Gogeta bridge enabled', () => {
  assert.match(app, /originalGogeta\s*:\s*['"]true['"]/);
  assert.match(app, /allowScriptAccess\s*:\s*true/);
  assert.match(app, /game-original\.swf|game-\$\{[^}]+\}\.swf/);
  assert.match(html, /id="original"/);
});


test('original Gogeta events own selection, versus, battle status and result cleanup', () => {
  assert.match(app, /window\.originalGogetaEvent\s*=/);
  for (const kind of ['ready', 'picking', 'selected', 'versus', 'battle', 'result', 'fault']) {
    assert.match(app, new RegExp(`kind === ['"]${kind}['"]`), kind);
  }
  assert.match(app, /showGogetaVersus/);
  assert.match(app, /showGogetaStatus/);
  assert.match(app, /hideGogetaStatus/);
});


test('the ninth button routes to the correct bridge callback in each mode', () => {
  assert.match(app, /mode === ['"]original['"][\s\S]*originalChooseGogeta/);
  assert.match(app, /mode === ['"]pvp['"][\s\S]*pvpChooseGogeta/);
  assert.match(app, /originalPicking/);
  assert.match(app, /gogetaPick\.hidden|gogetaPick\)\s*gogetaPick\.hidden/);
});
