// Public verification: no SWF, PNG, JS or network response replacement.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const {gameClick}=require('./browser.cjs');
const url=process.env.LIVE_URL,output=path.resolve(process.env.LIVE_OUTPUT||'scratch/public-quality');
assert.ok(url,'LIVE_URL is required');fs.mkdirSync(output,{recursive:true});
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--autoplay-policy=no-user-gesture-required']});
  const context=await browser.newContext({viewport:{width:1280,height:1100}});
  await context.addInitScript(()=>{
    window.__originalEvents=[];let handler;
    Object.defineProperty(window,'originalGogetaEvent',{configurable:true,set(fn){handler=fn;},get(){return (...args)=>{__originalEvents.push(JSON.parse(JSON.stringify(args)));return handler?.(...args);};}});
  });
  const page=await context.newPage(),errors=[],responses=[],assetTasks=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{
    if(r.status()>=400)responses.push({url:r.url(),status:r.status()});
    if(/\/game\/(game-original\.swf|original-gogeta-bridge\.swf|characters\/go_figure\.swf)$/.test(new URL(r.url()).pathname)) {
      assetTasks.push(r.body().then(body=>({url:r.url(),status:r.status(),sha256:crypto.createHash('sha256').update(body).digest('hex')})));
    }
  });
  try {
    await page.goto(url);await page.locator('#original').click();
    for(let i=0;i<40;i++){if(await page.locator('#gogetaPick').isVisible())break;await gameClick(page,217,302);await gameClick(page,175,315);await page.waitForTimeout(250);}
    await page.locator('#gogetaPick').waitFor({state:'visible'});
    await page.screenshot({path:path.join(output,'public-original-selection.png'),fullPage:true});
    const installed=await page.evaluate(()=>document.querySelector('ruffle-player').ruffle().callExternalInterface('originalGogetaState'));
    assert.equal(installed.installed,true);assert.equal(installed.linkage.figure,'goMoves');assert.deepEqual(installed.sango.secretSword,{energy:-15,damage:-25});
    await page.locator('#gogetaPick').click();await page.locator('#gogetaVersus').waitFor({state:'visible'});
    await page.screenshot({path:path.join(output,'public-original-versus.png'),fullPage:true});
    await page.waitForTimeout(700);await gameClick(page,253,306);
    await page.waitForFunction(()=>__originalEvents.some(e=>e[0]==='battle'));
    await page.waitForTimeout(1400);await gameClick(page,358,82);await page.waitForTimeout(500);
    await page.locator('ruffle-player').screenshot({path:path.join(output,'public-original-cards.png')});
    await gameClick(page,92,140);await gameClick(page,340,140);await gameClick(page,340,72);await gameClick(page,245,295);
    await page.waitForTimeout(1800);
    await page.locator('ruffle-player').screenshot({path:path.join(output,'public-original-battle.png')});
    for(let i=0;i<30;i++){await gameClick(page,215,251);await page.waitForTimeout(250);}
    await page.locator('ruffle-player').screenshot({path:path.join(output,'public-original-next-round.png')});
    const assets=await Promise.all(assetTasks);
    for(const asset of assets) {
      const relative=new URL(asset.url).pathname.split('/game/')[1];
      const local=fs.readFileSync(path.resolve('public/game',relative));
      assert.equal(asset.sha256,crypto.createHash('sha256').update(local).digest('hex'),relative);
    }
    assert.equal(new Set(assets.map(asset=>new URL(asset.url).pathname)).size,3);
    assert.deepEqual(errors,[]);assert.deepEqual(responses,[]);
    fs.writeFileSync(path.join(output,'public-original-evidence.json'),JSON.stringify({url,installed,assets,events:await page.evaluate(()=>__originalEvents),errors,responses},null,2));
    console.log('PASS actual public original-mode Gogeta selection, VS, cards and battle; original game/bridge/figure responses match local SHA-256; no asset overrides.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
