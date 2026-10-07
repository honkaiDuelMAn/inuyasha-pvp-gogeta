const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const {newPlayer, boot, finishRound, gameClick, hand} = require('./browser.cjs');
const {assertStunOnly} = require('./rtc-config.cjs');

(async () => {
  const root = path.resolve(process.env.STATIC_ROOT || 'public');
  const types = {'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.wasm':'application/wasm','.swf':'application/x-shockwave-flash','.png':'image/png'};
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, 'http://localhost');
    let relative;
    try { relative = decodeURIComponent(url.pathname.replace(/^\/inuyasha-pvp-gogeta\//, '')); }
    catch { response.writeHead(400); response.end(); return; }
    if (!relative) relative = 'direct.html';
    const file = path.resolve(root, relative);
    if (!file.startsWith(root + path.sep)) { response.writeHead(404); response.end(); return; }
    try {
      const bytes = fs.readFileSync(file);
      response.writeHead(200, {'Content-Type': types[path.extname(file)] || 'application/octet-stream'});
      response.end(bytes);
    } catch { response.writeHead(404); response.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/inuyasha-pvp-gogeta/`;
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH, headless: true, args:['--autoplay-policy=no-user-gesture-required']});
  const pages = [], errors = [], badRequests = [], cardAssetRequests = [], cardAssetResponses = [];

  async function player() {
    const page = await newPlayer(browser, 'about:blank');
    page.setDefaultTimeout(20000);
    await page.addInitScript(() => {
      window.__rtcConfigs = [];
      const Native = RTCPeerConnection;
      window.RTCPeerConnection = class extends Native {
        constructor(config) { window.__rtcConfigs.push(config); super(config); }
      };
      window.WebSocket = class { constructor() { throw Error('Gogeta static test must not use WebSocket'); } };
    });
    await page.route('**/app.mjs', async route => {
      const response = await route.fetch();
      const text = await response.text();
      await route.fulfill({response, body: text.replace('export function handle(event) {', 'export function handle(event) { window.__networkEvents.push(structuredClone(event));')});
    });
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      const requested = new URL(request.url());
      if (requested.origin !== new URL(url).origin || /\/api\/|\/pvp$/.test(requested.pathname)) badRequests.push(request.url());
      if (requested.pathname.includes('/game/gogeta/cards/')) cardAssetRequests.push(requested.pathname);
    });
    page.on('response', response => {
      const requested = new URL(response.url());
      if (requested.pathname.includes('/game/gogeta/cards/')) {
        cardAssetResponses.push({path:requested.pathname,status:response.status()});
      }
    });
    await page.goto(url);
    pages.push(page);
    return page;
  }

  const external = (page, name, ...args) => page.evaluate(
    ({name, args}) => document.querySelector('ruffle-player').ruffle().callExternalInterface(name, ...args),
    {name, args},
  );

  try {
    const host = await player();
    await host.locator('#create').click();
    await boot(host);
    await host.waitForFunction(() => document.querySelector('#outputCode').value.startsWith('IY2-'));
    await host.locator('#dedicatedEnabled').selectOption('on');

    const guest = await player();
    await guest.locator('#roomCode').fill(await host.locator('#outputLink').inputValue());
    await guest.locator('#joinForm button').click();
    await guest.waitForFunction(() => document.querySelector('#outputCode').value.startsWith('IY2-'));
    await host.locator('#responseCode').fill(await guest.locator('#outputLink').inputValue());
    await host.locator('#acceptAnswer').click();
    await boot(guest);
    await host.waitForFunction(() => document.getElementById('player1').textContent.includes('캐릭터 선택 중'));

    for (const page of pages) await page.locator('#gogetaPick').waitFor({state:'visible'});
    const gameBox = await host.locator('#gameContainer').boundingBox();
    const pickBox = await host.locator('#gogetaPick').boundingBox();
    const centerX = pickBox.x + pickBox.width / 2 - gameBox.x;
    const centerY = pickBox.y + pickBox.height / 2 - gameBox.y;
    assert.ok(centerX / gameBox.width < 0.25, 'Gogeta must occupy the lower-left column');
    assert.ok(centerY / gameBox.height > 0.62, 'Gogeta must occupy the third row');

    for (const page of pages) await page.locator('#gogetaPick').click();
    await Promise.all(pages.map(page => page.waitForFunction(() => document.querySelector('#player0').textContent.includes('오지터') || document.querySelector('#player1').textContent.includes('오지터'))));

    const states = await Promise.all(pages.map(page => external(page, 'pvpGogetaState')));
    for (const state of states) {
      assert.equal(state.installed, true);
      assert.equal(state.character, true);
      assert.equal(state.linkage.figure, 'goMoves');
      assert.deepEqual(state.moves.bigBangKamehameha, {energy:-50, damage:-40, area:[[0,0,0],[0,1,0],[1,1,1]]});
      assert.deepEqual(state.moves.dragonFist, {energy:-60, damage:-70, area:[[0,0,0],[1,1,1],[0,0,0]]});
      assert.deepEqual(state.moves.superEnergyBackflow, {energy:-25, damage:-25, area:[[1,1,1],[1,1,1],[1,1,1]]});
      assert.deepEqual(state.moves.superKamehameha, {energy:-20, damage:-35, area:[[0,0,0],[1,1,1],[0,0,0]]});
      assert.deepEqual([...state.regularMoves].sort(), [
        'bigBangKamehameha','dragonFist','energyUp','guard','moveDown',
        'moveLeft','moveRight','moveUp','superEnergyBackflow','superKamehameha',
      ].sort());
    }

    await Promise.all(pages.map(page => page.locator('#ready').click()));
    await host.locator('#gogetaVersus').waitFor({state:'visible'});
    await host.locator('#gogetaStatus').waitFor({state:'visible'});
    assert.equal(await host.locator('#gogetaStatus .gogeta-status-side.active').count(), 2);
    await Promise.all(pages.map(page => page.locator('#roomPanel[data-phase="picking"]').waitFor({timeout:30000})));
    const starts = await Promise.all(pages.map(page => page.evaluate(() => __networkEvents.find(event => event.type === 'start'))));
    assert.deepEqual(starts[0].characters, ['go','go']);
    assert.deepEqual(starts[0].dedicatedCards, [['summonShippo'],['summonShippo']]);
    assert.deepEqual(starts[0], starts[1]);

    await host.waitForTimeout(1200); // allow the original help dialog to finish opening
    for (const page of pages) await gameClick(page,358,82); // close original help overlay
    await host.waitForTimeout(800);
    assert.deepEqual(new Set(cardAssetRequests.map(value => value.split('/').at(-1))), new Set([
      'bigBangKamehameha.png','dragonFist.png','superEnergyBackflow.png','superKamehameha.png',
    ]));
    assert.ok(cardAssetResponses.length >= 8, 'both peers must load all four card images');
    assert.ok(cardAssetResponses.every(item => item.status === 200), JSON.stringify(cardAssetResponses));
    fs.mkdirSync('scratch/gogeta-browser', {recursive:true});
    await host.locator('ruffle-player').screenshot({path:'scratch/gogeta-browser/cards.png'});
    const rounds = [
      {id:'dragonFist', points:[[216,140],[92,140],[92,72]], energy:55},
      {id:'superKamehameha', points:[[340,140],[92,140],[92,72]], energy:65},
      {id:'superEnergyBackflow', points:[[278,140],[92,140],[92,72]], energy:70},
      {id:'bigBangKamehameha', points:[[154,140],[92,140],[92,72]], energy:50},
    ];
    for (let index=0; index<rounds.length; index++) {
      const round = index + 1, expected = rounds[index];
      for (const page of pages) await hand(page, expected.points);
      await Promise.all(pages.map(page => page.waitForFunction(
        roundNumber => __gameEvents.some(event => event[0] === 'resolved' && event[1].round === roundNumber),
        round,
        {timeout:30000},
      )));
      const reports = await Promise.all(pages.map(page => page.evaluate(
        roundNumber => __gameEvents.find(event => event[0] === 'resolved' && event[1].round === roundNumber)[1],
        round,
      )));
      assert.deepEqual(reports[0], reports[1], expected.id);
      assert.deepEqual(reports[0].players.map(player => player.energy), [expected.energy,expected.energy], expected.id);
      assert.equal(reports[0].result, 'none', `${expected.id} unexpectedly ended the mirror match`);
      await finishRound(pages, round);
    }

    await host.screenshot({path:'scratch/gogeta-browser/host.png', fullPage:true});
    assert.deepEqual(errors, []);
    assert.deepEqual(badRequests, []);
    for (const page of pages) assertStunOnly(await page.evaluate(() => __rtcConfigs));
    console.log('PASS Gogeta ninth-slot mirror match, four clickable attacks, Shippo card, figure load and equal original-engine reports.');
  } catch (error) {
    fs.mkdirSync('scratch/gogeta-browser', {recursive:true});
    for (let index=0; index<pages.length; index++) {
      if (!pages[index].isClosed()) {
        await pages[index].screenshot({path:`scratch/gogeta-browser/failure-${index}.png`, fullPage:true});
        console.log('DIAGNOSTIC', index, JSON.stringify(await pages[index].evaluate(() => ({
          game:window.__gameEvents,
          network:window.__networkEvents,
          message:document.getElementById('message')?.textContent,
          room:document.getElementById('roomPanel')?.dataset,
        }))));
      }
    }
    throw error;
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
