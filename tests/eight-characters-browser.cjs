const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const {gameClick}=require('./browser.cjs');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'scratch/eight-characters');
fs.mkdirSync(folder,{recursive:true});
const source=path.join(folder,'probe.as'),probe=path.join(folder,'probe.swf');
fs.writeFileSync(source,fs.readFileSync(path.join(root,'flash/original-gogeta.as'),'utf8')+'\n'+fs.readFileSync(path.join(root,'tests/fixtures/original-gogeta-probe.as'),'utf8'));
const compiled=spawnSync(process.env.JAVA_PATH||'C:/Program Files (x86)/NS-USBloader/jdk/bin/java.exe',['-Djava.awt.headless=true','-jar',process.env.FFDEC_PATH||'D:/CHAT/inuyasha-pvp-github-update-20261006/scratch/test-tools/ffdec/ffdec.jar','-replace',path.join(root,'public/game/original-gogeta-bridge.swf'),probe,'\\frame_1\\DoAction',source],{encoding:'utf8',windowsHide:true});
assert.equal(compiled.status,0,compiled.stdout+compiled.stderr);
(async()=>{
  const {createApp}=await import('../server/main.mjs');const app=createApp();
  await new Promise(resolve=>app.server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--autoplay-policy=no-user-gesture-required']});
  const characters=[['i',100,140],['ke',170,140],['m',250,140],['ka',329,140],['sa',100,220],['ko',170,220],['s',250,220],['n',329,220]].filter(c=>!process.argv[2]||c[0]===process.argv[2]),results=[];
  let currentPage,currentId;
  try {
    for(const [id,x,y] of characters) {
      const context=await browser.newContext({viewport:{width:1280,height:1100}});
      await context.addInitScript(()=>{window.__originalEvents=[];let handler;Object.defineProperty(window,'originalGogetaEvent',{configurable:true,set(fn){handler=fn;},get(){return (...args)=>{__originalEvents.push(JSON.parse(JSON.stringify(args)));return handler?.(...args);};}});});
      const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
      currentPage=page;currentId=id;
      await page.route('**/game/original-gogeta-bridge.swf',route=>route.fulfill({path:probe,contentType:'application/x-shockwave-flash'}));
      const state=()=>page.evaluate(()=>document.querySelector('ruffle-player').ruffle().callExternalInterface('originalTestState'));
      await page.goto(`http://127.0.0.1:${app.server.address().port}/direct.html`);await page.locator('#original').click();
      for(let i=0;i<40;i++){if(await page.locator('#gogetaPick').isVisible())break;await gameClick(page,217,302);await gameClick(page,175,315);await page.waitForTimeout(250);}
      await page.locator('#gogetaPick').waitFor({state:'visible'});
      const characterButton=(await state()).characterButtons.find(button=>button.id===id);
      assert.ok(characterButton?.press,`${id}: native selection handler missing`);
      console.log('PICK',id,JSON.stringify(characterButton));
      await page.locator('ruffle-player').screenshot({path:path.join(folder,'select-'+id+'.png')});
      await gameClick(page,characterButton.x,characterButton.y);
      await page.waitForFunction(character=>__originalEvents.some(e=>e[0]==='selected'&&e[1].character===character),id);
      await page.waitForFunction(()=>__originalEvents.some(e=>e[0]==='versus'));
      await page.waitForTimeout(700); // native VS panel entrance, including Naraku's longer animation
      assert.equal((await state()).userStats.id,id);
      assert.equal(await page.locator('#gogetaVersus').isVisible(),false);
      await gameClick(page,253,306);await page.waitForFunction(()=>__originalEvents.some(e=>e[0]==='battle'));
      await page.waitForTimeout(1200);await gameClick(page,358,82);await page.waitForTimeout(500);
      let current=await state();assert.equal(current.players[0].character,id);
      assert.ok(current.slots.every(c=>!c.art),`${id}: Gogeta illustration leaked into a native card`);
      for(const move of ['guard','energyUp','moveDown']) {
        const card=current.slots.find(c=>c.id===move&&c.press&&c.visible);
        assert.ok(card,`${id}: common action ${move} missing`);await gameClick(page,card.x,card.y);current=await state();
      }
      await gameClick(page,current.continueButton.x,current.continueButton.y);
      for(let i=0;i<120;i++){current=await state();if(current.roundsCount>=2&&current.pickerVisible)break;await gameClick(page,215,251);await page.waitForTimeout(250);}
      assert.ok(current.roundsCount>=2&&current.pickerVisible,`${id}: original battle failed to complete`);
      assert.equal(current.players[0].character,id);assert.deepEqual(errors,[]);
      await page.locator('ruffle-player').screenshot({path:path.join(folder,id+'.png')});
      results.push({character:id,rounds:current.roundsCount,players:current.players});console.log(`PASS original character ${id}: native cards, actual AI round and next picker.`);
      await context.close();
    }
    fs.writeFileSync(path.join(folder,'results.json'),JSON.stringify(results,null,2));
  } catch(error) {
    await currentPage.screenshot({path:path.join(folder,'failure-'+currentId+'.png'),fullPage:true});
    console.log('FAILURE',currentId,JSON.stringify(await currentPage.evaluate(()=>({events:__originalEvents,state:document.querySelector('ruffle-player').ruffle().callExternalInterface('originalTestState')}))));
    throw error;
  } finally {await browser.close();await app.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
