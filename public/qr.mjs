import {qrcodegen} from './vendor/qrcodegen.mjs';
export function drawQR(canvas,text){
  const qr=qrcodegen.QrCode.encodeText(text,qrcodegen.QrCode.Ecc.MEDIUM);
  const border=4,scale=8,size=(qr.size+border*2)*scale;
  // Whole screen pixels per module avoid uneven bars after CSS downscaling.
  // WebRTC reply links produce a dense QR. At 280px they only receive three
  // visible pixels per module, which some phone cameras and OpenCV decode
  // inconsistently. Give the QR up to 360px so long replies retain four.
  const modules=qr.size+border*2,available=Math.min(360,canvas.parentElement.clientWidth||360);
  canvas.style.width=modules*Math.max(1,Math.floor(available/modules))+'px';
  canvas.width=canvas.height=size;
  const context=canvas.getContext('2d');context.fillStyle='#fff';context.fillRect(0,0,size,size);context.fillStyle='#000';
  for(let y=0;y<qr.size;y++)for(let x=0;x<qr.size;x++)if(qr.getModule(x,y))context.fillRect((x+border)*scale,(y+border)*scale,scale,scale);
}
