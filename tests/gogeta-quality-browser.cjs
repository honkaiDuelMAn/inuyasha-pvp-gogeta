const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {spawnSync} = require('node:child_process');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const {newPlayer,boot,gameClick,finishRound,hand} = require('./browser.cjs');
const root = path.resolve(__dirname,'..');
const output = path.resolve(process.env.QUALITY_OUTPUT || 'scratch/gogeta-quality-browser');
fs.mkdirSync(output,{recursive:true});
const java = process.env.JAVA_PATH || 'C:/Program Files (x86)/NS-USBloader/jdk/bin/java.exe';
const ffdec = process.env.FFDEC_PATH || 'D:/CHAT/inuyasha-pvp-github-update-20261006/scratch/test-tools/ffdec/ffdec.jar';
const fixture = fs.readFileSync(path.join(root,'tests/fixtures/gogeta-quality-probe.as'),'utf8');
function probe(mode) {
  const filename = mode==='pvp' ? 'pvp.as' : 'original-gogeta.as';
  let source = process.env.QUALITY_BASELINE ? spawnSync('git',['show',`a2b6c43:flash/${filename}`],{cwd:root,encoding:'utf8'}).stdout : fs.readFileSync(path.join(root,'flash',filename),'utf8');
  if(process.env.QUALITY_STAGE_BASELINE) source=source.replace(/    roundView.gogetaNativeStart[\s\S]*?    roundView.gogetaNativeCards/,'    roundView.gogetaNativeCards');
  const sourcePath = path.join(output,`${mode}-probe.as`);
  const outputPath = path.join(output,`${mode}-probe.swf`);
  fs.writeFileSync(sourcePath,source+'\n'+fixture);
  const result = spawnSync(java,['-Djava.awt.headless=true','-jar',ffdec,'-replace',path.join(root,'public/game',mode==='pvp'?'pvp-bridge.swf':'original-gogeta-bridge.swf'),outputPath,'\\frame_1\\DoAction',sourcePath],{encoding:'utf8',windowsHide:true});
  assert.equal(result.status,0,result.stdout+result.stderr);
  return outputPath;
}
const external = (page,name,...args) => page.evaluate(({name,args}) => document.querySelector('ruffle-player').ruffle().callExternalInterface(name,...args),{name,args});
async function captureAudio(page) {
  await page.addInitScript(() => {
    window.__audioStarts=[];
    const original=AudioBufferSourceNode.prototype.start;
    AudioBufferSourceNode.prototype.start=function(...args) {
      const buffer=this.buffer;
      if(buffer) {
        const values=buffer.getChannelData(0);
        let energy=0;
        for(let i=0;i<values.length;i++) energy+=values[i]*values[i];
        __audioStarts.push({time:performance.now(),samples:buffer.length,rate:buffer.sampleRate,duration:buffer.duration,rms:Math.sqrt(energy/values.length)});
      }
      return original.apply(this,args);
    };
  });
}
async function stablePicker(page,label,observations) {
  const samples=[];
  for(let i=0;i<24;i++) {
    samples.push(await external(page,'gogetaQualityState'));
    await page.waitForTimeout(50);
  }
  assert.equal(new Set(samples.map(s=>s.background)).size,1,`${label}: background timeline cycles`);
  for(let seat=0;seat<2;seat++) assert.equal(new Set(samples.map(s=>s.hud[seat].nameFrame)).size,1,`${label}: HUD names cycle`);
  const state=samples[0];
  assert.equal(state.character,'go');
  const cards=state.cards.filter(c=>c.visible&&c.id);
  assert.equal(cards.length>=10,true,JSON.stringify(cards));
  for(const card of cards) {
    assert.equal(card.art,true,`${label}/${card.id}: missing embedded fusion card`);
    assert.equal(card.artWidth,62,`${label}/${card.id}: incorrect native card width`);
    assert.equal(card.artId,card.id);
  }
  const box=await page.locator('ruffle-player').boundingBox();
  const grid={x:box.x+55/432*box.width,y:box.y+38/330*box.height,width:320/432*box.width,height:210/330*box.height};
  const before=await page.screenshot({clip:grid});
  for(let i=0;i<6;i++) await external(page,'gogetaQualityRefresh');
  const after=await page.screenshot({clip:grid});
  fs.writeFileSync(path.join(output,label+'-before-refresh.png'),before);
  fs.writeFileSync(path.join(output,label+'-after-refresh.png'),after);
  assert.equal(before.equals(after),true,`${label}: redraw changes static card pixels`);
  observations.push({label,backgroundFrames:[...new Set(samples.map(s=>s.background))],state});
  await page.locator('ruffle-player').screenshot({path:path.join(output,label+'-cards.png')});
}
(async()=>{
  const probes={pvp:probe('pvp'),original:probe('original')};
  const staticRoot=path.join(root,'public');
  const types={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.swf':'application/x-shockwave-flash','.png':'image/png'};
  const server=http.createServer((req,res)=>{
    const parsed=new URL(req.url,'http://localhost');
    const relative=decodeURIComponent(parsed.pathname.replace(/^\/inuyasha-pvp-gogeta\//,'')) || 'direct.html';
    const target=path.resolve(staticRoot,relative);
    if(!target.startsWith(staticRoot+path.sep)){res.writeHead(404);res.end();return;}
    try{res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream'});res.end(fs.readFileSync(target));}catch{res.writeHead(404);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const url=process.env.QUALITY_URL || `http://127.0.0.1:${server.address().port}/inuyasha-pvp-gogeta/`;
  const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--autoplay-policy=no-user-gesture-required']});
  const pages=[],observations=[],errors=[],failures=[];
  async function player() {
    const page=await newPlayer(browser,'about:blank');
    await captureAudio(page);
    await page.addInitScript(()=>{
      window.__originalEvents=[];
      let handler;
      Object.defineProperty(window,'originalGogetaEvent',{configurable:true,set(fn){handler=fn;},get(){return (...args)=>{__originalEvents.push(JSON.parse(JSON.stringify(args)));return handler?.(...args);};}});
    });
    await page.route('**/app.mjs',async route=>{
      const response=await route.fetch();
      await route.fulfill({response,body:(await response.text()).replace('export function handle(event) {','export function handle(event) { window.__networkEvents.push(structuredClone(event));')});
    });
    if(!process.env.QUALITY_NO_PROBE) {
      await page.route('**/game/pvp-bridge.swf',route=>route.fulfill({path:probes.pvp,contentType:'application/x-shockwave-flash'}));
      await page.route('**/game/original-gogeta-bridge.swf',route=>route.fulfill({path:probes.original,contentType:'application/x-shockwave-flash'}));
    }
    page.on('pageerror',e=>errors.push(e.message));
    page.on('response',r=>{if(r.status()>=400)failures.push({url:r.url(),status:r.status()});});
    pages.push(page);await page.goto(url);return page;
  }
  try {
    const original=await player();
    await original.locator('#original:not([disabled])').click();
    for(let i=0;i<40;i++) {
      if(await original.locator('#gogetaPick').isVisible())break;
      await gameClick(original,217,302);await gameClick(original,175,315);await original.waitForTimeout(250);
    }
    await original.locator('#gogetaPick').waitFor({state:'visible'});
    await original.locator('#gogetaPick').click();
    await original.locator('#gogetaVersus').waitFor({state:'visible'});
    await original.screenshot({path:path.join(output,'original-versus.png'),fullPage:true});
    await gameClick(original,253,306);
    await original.waitForFunction(()=>__originalEvents.some(e=>e[0]==='battle'));
    await original.waitForTimeout(1200);await gameClick(original,358,82);await original.waitForTimeout(500);
    await stablePicker(original,'original',observations);

    const host=await player();await host.locator('#create').click();await boot(host);
    await host.waitForFunction(()=>document.querySelector('#outputCode').value.startsWith('IY2-'));
    await host.locator('#bonusCount').selectOption('5');
    await host.locator('#dedicatedEnabled').selectOption('on');
    const guest=await player();await guest.locator('#roomCode').fill(await host.locator('#outputLink').inputValue());
    await guest.locator('#joinForm button').click();
    await guest.waitForFunction(()=>document.querySelector('#outputCode').value.startsWith('IY2-'));
    await host.locator('#responseCode').fill(await guest.locator('#outputLink').inputValue());await host.locator('#acceptAnswer').click();await boot(guest);
    await host.waitForFunction(()=>document.querySelector('#player1').textContent.includes('캐릭터 선택 중'));
    for(const page of [host,guest]) {await page.locator('#gogetaPick').waitFor({state:'visible'});await page.locator('#gogetaPick').click();}
    await Promise.all([host,guest].map(p=>p.locator('#ready').click()));
    await Promise.all([host,guest].map(p=>p.locator('#roomPanel[data-phase="picking"]').waitFor({timeout:30000})));
    await host.waitForTimeout(1200);
    for(const page of [host,guest])await gameClick(page,358,82);
    await host.waitForTimeout(500);
    await stablePicker(host,'pvp-host',observations);await stablePicker(guest,'pvp-guest',observations);
    const complete=await external(host,'gogetaQualityState');
    for(const id of ['moveDown','moveUp','moveRight','moveLeft','guard','energyUp','heal','perfectGuard','kikyosRevenge','doubleLeft','doubleRight','summonShippo']) {
      assert.ok(complete.cards.some(c=>c.id===id&&c.art&&c.visible),`common card not rendered: ${id}`);
    }
    await gameClick(host,216,140);
    const selection=await external(host,'gogetaQualityState');
    const selectedSource=selection.cards.find(c=>c.id==='dragonFist');
    assert.equal(selectedSource.frame,15,'source card must show the native selected placeholder');
    assert.equal(selectedSource.art,false,'full illustration must not hide the native selected placeholder');
    assert.equal(selection.selectedCards[0].art,true,'selected hand retains the fusion card');
    await external(host,'gogetaQualityClearSelection');
    const rounds=[['dragonFist',216],['superKamehameha',340],['superEnergyBackflow',278],['bigBangKamehameha',154]];
    for(let i=0;i<rounds.length;i++) {
      const [id,x]=rounds[i],round=i+1;
      const audioBefore=await host.evaluate(()=>__audioStarts.length);
      for(const page of [host,guest])await hand(page,[[x,140],[92,140],[92,72]]);
      await host.waitForFunction(r=>__gameEvents.some(e=>e[0]==='resolved'&&e[1].round===r),round);
      await host.waitForTimeout(1200);
      const battleState=await external(host,'gogetaQualityState');
      assert.equal(battleState.roundBackground,5,`${id}: missing native battle stage`);
      for(const reveal of battleState.revealCards) {
        assert.equal(reveal.art,true,`${id}: reveal FX must use fusion illustration`);
        assert.equal(reveal.id,id,`${id}: reveal FX must show the actual move's DM/EN`);
      }
      await host.locator('ruffle-player').screenshot({path:path.join(output,id+'-battle.png')});
      await finishRound([host,guest],round);
      const state=await external(host,'gogetaQualityState');
      for(const shell of state.shells) assert.ok(shell.children.every(key=>/^x[01]_mc$/.test(key)),`unmanaged fighter in ${JSON.stringify(shell)}`);
      const sounds=await host.evaluate(n=>__audioStarts.slice(n),audioBefore);
      assert.ok(sounds.some(s=>s.rms>0.01&&s.duration<2),`${id}: no audible short effect`);
      observations.push({label:id,state,sounds});
    }
    assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
    const sourceFrames={basicPunch:13,energyUp:10,dragonFist:50,superKamehameha:57,superEnergyBackflow:27,bigBangKamehameha:87};
    for(const [id,frames] of Object.entries(sourceFrames)) {
      const before=await host.evaluate(()=>__audioStarts.length);
      assert.equal(await external(host,'gogetaQualityAction',id),true,id);
      await host.waitForTimeout(frames/31*1000+350);
      const ended=await external(host,'gogetaQualityActionState');
      assert.equal(ended.events.filter(e=>e.event==='done').length,1,id);
      if(id!=='energyUp')assert.equal(ended.events.filter(e=>e.event==='hit').length,1,id);
      await host.waitForTimeout(500);
      const later=await external(host,'gogetaQualityActionState');
      assert.deepEqual(later,ended,`${id}: one-shot continued or looped after done`);
      const sounds=await host.evaluate(n=>__audioStarts.slice(n),before);
      assert.ok(sounds.some(s=>s.rms>0.005),`${id}: isolated source action was silent`);
      observations.push({label:'isolated-'+id,ended,audibleChunks:sounds.filter(s=>s.rms>0.005).length,maxRms:Math.max(...sounds.map(s=>s.rms))});
      await external(host,'gogetaQualityClearAction');
    }
    fs.writeFileSync(path.join(output,'observations.json'),JSON.stringify(observations,null,2));
    console.log('PASS true-fusion original and PvP mirror; stable picker/HUD/redraw; native embedded cards; no unmanaged root fighter; four skills with audible audio.');
  } catch(error) {
    for(let i=0;i<pages.length;i++)if(!pages[i].isClosed()) {
      await pages[i].screenshot({path:path.join(output,`failure-${i}.png`),fullPage:true});
      try{console.log('STATE',i,JSON.stringify(await external(pages[i],'gogetaQualityState')));}catch{}
    }
    throw error;
  } finally {await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
