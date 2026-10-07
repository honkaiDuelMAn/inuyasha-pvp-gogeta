const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const {gameClick} = require('./browser.cjs');

const root = path.resolve(__dirname, '..');

async function rawGameClick(page, x, y) {
  const box = await page.locator('ruffle-player').boundingBox();
  assert.ok(box, 'Ruffle player must have a clickable box');
  await page.mouse.click(box.x + x * box.width / 432, box.y + y * box.height / 330);
}

function compileProbe() {
  const folder = path.join(root, 'scratch/original-gogeta-browser');
  fs.mkdirSync(folder, {recursive:true});
  const source = path.join(folder, 'probe.as');
  const output = path.join(folder, 'probe.swf');
  fs.writeFileSync(source,
    fs.readFileSync(path.join(root, 'flash/original-gogeta.as'), 'utf8') + '\n' +
    fs.readFileSync(path.join(root, 'tests/fixtures/original-gogeta-probe.as'), 'utf8'));
  const java = process.env.JAVA_PATH || 'C:/Program Files (x86)/NS-USBloader/jdk/bin/java.exe';
  const ffdec = process.env.FFDEC_PATH || path.join(root, '../inuyasha-pvp-github-update-20261006/scratch/test-tools/ffdec/ffdec.jar');
  const result = spawnSync(java, ['-Djava.awt.headless=true','-jar',ffdec,'-replace',
    path.join(root,'public/game/original-gogeta-bridge.swf'),output,'\\frame_1\\DoAction',source],
    {encoding:'utf8',windowsHide:true});
  assert.equal(result.status, 0, result.stdout + result.stderr);
  return output;
}

(async () => {
  const staticRoot = path.join(root, 'public');
  const types = {'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.wasm':'application/wasm','.swf':'application/x-shockwave-flash','.png':'image/png'};
  const server = http.createServer((request,response) => {
    const url = new URL(request.url,'http://localhost');
    let relative;
    try { relative = decodeURIComponent(url.pathname.replace(/^\/inuyasha-pvp-gogeta\//,'')); }
    catch { response.writeHead(400); response.end(); return; }
    if (!relative) relative = 'direct.html';
    const file = path.resolve(staticRoot, relative);
    if (!file.startsWith(staticRoot + path.sep)) { response.writeHead(404); response.end(); return; }
    try {
      const bytes = fs.readFileSync(file);
      response.writeHead(200, {'Content-Type':types[path.extname(file)] || 'application/octet-stream'});
      response.end(bytes);
    } catch { response.writeHead(404); response.end(); }
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const url = `${origin}/inuyasha-pvp-gogeta/`;
  const browser = await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true,args:['--autoplay-policy=no-user-gesture-required']});
  const errors = [], badRequests = [], requests = [];
  const probe = compileProbe();
  let page;
  try {
    const context = await browser.newContext({viewport:{width:1280,height:1100}});
    await context.addInitScript(() => {
      window.__originalEvents = [];
      let handler;
      Object.defineProperty(window,'originalGogetaEvent',{
        configurable:true,
        set(fn){handler=fn;},
        get(){return (...args)=>{window.__originalEvents.push(JSON.parse(JSON.stringify(args)));return handler?.(...args);};}
      });
      window.WebSocket = class { constructor(){ throw Error('Original mode must not use WebSocket'); } };
    });
    page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      const requested = new URL(request.url());
      requests.push(requested.pathname);
      if (requested.origin !== origin || /\/api\/|\/pvp$/.test(requested.pathname)) badRequests.push(request.url());
    });
    await page.route('**/game/original-gogeta-bridge.swf', route => route.fulfill({path:probe,contentType:'application/x-shockwave-flash'}));
    await page.goto(url);
    await page.locator('#original:not([disabled])').click();
    await page.locator('ruffle-player').waitFor();

    for (let attempt=0; attempt<40; attempt++) {
      if (await page.locator('#gogetaPick').isVisible()) break;
      await gameClick(page,217,302);
      await gameClick(page,175,315);
      await page.waitForTimeout(250);
    }
    await page.locator('#gogetaPick').waitFor({state:'visible',timeout:15000});

    const external = (name,...args) => page.evaluate(({name,args}) =>
      document.querySelector('ruffle-player').ruffle().callExternalInterface(name,...args), {name,args});
    const installed = await external('originalGogetaState');
    assert.equal(installed.installed,true);
    assert.equal(installed.character,true);
    assert.deepEqual(installed.enemyOrder,['sa','ko','ka','s','n']);
    assert.deepEqual(installed.summons,['summonShippo']);
    assert.deepEqual(installed.sango.secretSword,{energy:-15,damage:-25});
    assert.equal(installed.sango.poisonPowder.energy,-20);

    await page.locator('#gogetaPick').click();
    await page.waitForFunction(() => __originalEvents.some(event => event[0] === 'selected' && event[1].character === 'go'));
    await page.waitForFunction(() => __originalEvents.some(event => event[0] === 'versus'), null, {timeout:30000});
    await page.locator('#gogetaVersus').waitFor({state:'visible'});

    let runtime = await external('originalTestState');
    assert.equal(runtime.userStats.id,'go');
    assert.equal(runtime.versusVisible,true);
    assert.ok(runtime.fightButton?.press, JSON.stringify(runtime.fightButton));
    // The original button clip reports bounds below the 330px stage because
    // its parent panel is animated. Click its stable visual center instead.
    await rawGameClick(page,253,306);
    await page.waitForFunction(() => __originalEvents.some(event => event[0] === 'battle'), null, {timeout:30000});
    await page.waitForFunction(() => document.querySelector('#gogetaStatus .gogeta-status-side.active'));

    await page.waitForTimeout(1200);
    await rawGameClick(page,358,82);
    await page.waitForFunction(() => {
      const state = document.querySelector('ruffle-player').ruffle().callExternalInterface('originalTestState');
      return state?.pickerVisible && state.slots.some(slot => slot.id === 'superKamehameha' && slot.press);
    }, null, {timeout:15000});
    runtime = await external('originalTestState');
    const selectedIds = ['superKamehameha','guard','energyUp'];
    for (const id of selectedIds) {
      const slot = runtime.slots.find(item => item.id === id && item.visible && item.press);
      assert.ok(slot, `missing selectable ${id}: ${JSON.stringify(runtime.slots)}`);
      await rawGameClick(page,slot.x,slot.y);
      runtime = await external('originalTestState');
    }
    assert.ok(runtime.continueButton?.press, JSON.stringify(runtime.continueButton));
    await rawGameClick(page,runtime.continueButton.x,runtime.continueButton.y);
    await page.waitForFunction(() => {
      const state = document.querySelector('ruffle-player').ruffle().callExternalInterface('originalTestState');
      return state?.roundSummary?.roundNumber === 1 && state.players[0]?.energy < 100;
    }, null, {timeout:15000});

    for (let attempt=0; attempt<100; attempt++) {
      runtime = await external('originalTestState');
      if (runtime.roundsCount >= 2 && runtime.pickerVisible) break;
      await rawGameClick(page,215,251);
      await page.waitForTimeout(300);
    }
    runtime = await external('originalTestState');
    assert.ok(runtime.roundsCount >= 2 && runtime.pickerVisible, JSON.stringify(runtime));
    assert.equal(runtime.players[0].character,'go');
    assert.ok(requests.some(value => value.endsWith('/game/game-original.swf')));
    assert.ok(requests.some(value => value.endsWith('/game/original-gogeta-bridge.swf')));
    assert.ok(requests.some(value => value.endsWith('/game/characters/go_figure.swf')));
    for (const id of ['bigBangKamehameha','dragonFist','superEnergyBackflow','superKamehameha']) {
      assert.ok(requests.some(value => value.endsWith(`/game/gogeta/cards/${id}.png`)), `missing card art request: ${id}`);
    }
    assert.deepEqual(errors,[]);
    assert.deepEqual(badRequests,[]);

    fs.mkdirSync(path.join(root,'scratch/original-gogeta-browser'),{recursive:true});
    await page.screenshot({path:path.join(root,'scratch/original-gogeta-browser/original-round2.png'),fullPage:true});
    console.log('PASS original mode keeps Sango balance, selects Gogeta, loads his figure/cards and completes one AI round.');
  } catch (error) {
    if (page && !page.isClosed()) {
      fs.mkdirSync(path.join(root,'scratch/original-gogeta-browser'),{recursive:true});
      await page.screenshot({path:path.join(root,'scratch/original-gogeta-browser/failure.png'),fullPage:true});
      console.log('DIAGNOSTIC',JSON.stringify(await page.evaluate(() => ({events:window.__originalEvents,message:document.getElementById('message')?.textContent,pickHidden:document.getElementById('gogetaPick')?.hidden}))));
    }
    throw error;
  } finally {
    await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error);process.exitCode=1;});
