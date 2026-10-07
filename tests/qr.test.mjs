import test from 'node:test';
import assert from 'node:assert/strict';

import {drawQR} from '../public/qr.mjs';

test('long WebRTC reply QR keeps at least four visible pixels per module', () => {
  const operations=[];
  const canvas={
    parentElement:{clientWidth:360},
    style:{},
    width:0,
    height:0,
    getContext(){return {
      fillStyle:'',
      fillRect(...args){operations.push(args);},
    };},
  };
  const reply=`https://example.test/inuyasha-pvp-gogeta/#answer=${'IY2-'+('A'.repeat(330))}`;
  drawQR(canvas,reply);
  assert.ok(parseInt(canvas.style.width,10)>280,canvas.style.width);
  assert.ok(canvas.width>=600,canvas.width);
  assert.equal(canvas.width,canvas.height);
  assert.ok(operations.length>100);
});
