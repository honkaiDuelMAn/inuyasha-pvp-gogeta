import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const html = await readFile(new URL('../public/direct.html', import.meta.url), 'utf8');
const app = await readFile(new URL('../public/app.mjs', import.meta.url), 'utf8');
const css = await readFile(new URL('../public/style.css', import.meta.url), 'utf8');

test('the web game exposes a ninth lower-left Gogeta picker', () => {
  assert.match(html, /id="gogetaPick"/);
  assert.match(html, /game\/gogeta\/portrait\.png/);
  assert.match(html, /오지터/);
  assert.match(css, /#gogetaPick/);
  assert.match(css, /left:15%/);
  assert.match(css, /top:72%/);
  assert.match(app, /pvpChooseGogeta/);
  assert.match(app, /kind === 'picking'/);
});

test('Gogeta versus art is local and shown for either seat', () => {
  assert.match(html, /id="gogetaVersus"/);
  assert.match(html, /game\/gogeta\/versus\.png/);
  assert.match(app, /showGogetaVersus/);
  assert.doesNotMatch(html + app + css, /https?:\/\//i);
});

test('Gogeta battle status covers the original fallback portrait and name', () => {
  assert.match(html, /id="gogetaStatus"/);
  assert.match(html, /class="gogeta-status-side" data-seat="0"/);
  assert.match(html, /class="gogeta-status-side right" data-seat="1"/);
  assert.match(app, /showGogetaStatus/);
  assert.match(app, /hideGogetaStatus/);
  assert.match(css, /#gogetaStatus/);
  assert.match(css, /pointer-events:none/);
});
