#!/usr/bin/env python3
"""產生「簡譜/鋼琴捲簾 瀏覽器編輯器」單檔 HTML
用法: python make_editor.py --mid song.mid [--audio hum.m4a] [--out editor.html] [--name 曲名]
產出: 一個自足的 HTML（旋律資料+原哼唱音訊內嵌），瀏覽器開啟即可編輯:
      鋼琴捲簾改音/改時值/加休止 → Web Audio 即時試聽 → 存 .jianpu.txt / .wav / .json
      存回的 .jianpu.txt 可直接餵 jianpu2midi.py 重新生曲
依賴: pretty_midi（讀 .mid）；原哼唱音訊轉 base64 嵌入（可選）
"""
import argparse
import base64
import json
import os

import pretty_midi
from mid2jianpu import detect_key, PC_NAMES  # 同資料夾：調性偵測複用

MIME = {".m4a": "audio/mp4", ".mp4": "audio/mp4", ".mp3": "audio/mpeg",
        ".wav": "audio/wav", ".ogg": "audio/ogg", ".flac": "audio/flac"}


def load_mid(path):
    pm = pretty_midi.PrettyMIDI(path)
    notes = [n for i in pm.instruments for n in i.notes]
    if not notes:
        raise SystemExit("MIDI 內沒有音符")
    notes.sort(key=lambda n: n.start)
    tempos, _ = pm.get_tempo_changes()
    bpm = float(tempos[0]) if len(tempos) else 0.0
    if not (20 <= bpm <= 300):
        bpm = float(pm.estimate_tempo())
    if not (20 <= bpm <= 300):
        bpm = 100.0
    pitches = [n.pitch for n in notes]
    return {
        "bpm": round(bpm, 2),
        "keyPc": detect_key(pitches),
        "meter": 4,
        "notes": [{"pitch": n.pitch,
                   "start": round(n.start, 4),
                   "end": round(n.end, 4)} for n in notes],
    }


def embed_audio(path):
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build(data, audio_uri, out_path):
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__AUDIO__", json.dumps(audio_uri))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"written: {out_path} ({os.path.getsize(out_path):,} bytes, "
          f"{len(data['notes'])} notes, bpm={data['bpm']}, "
          f"key=1={PC_NAMES[data['keyPc']]}, audio={'yes' if audio_uri else 'no'})")


TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>簡譜編輯器 — 鋼琴捲簾</title>
<style>
  * { box-sizing: border-box; }
  body { margin:0; font-family:"Microsoft JhengHei",system-ui,sans-serif;
         background:#f4f5f7; color:#222; }
  header { background:#fff; border-bottom:1px solid #ddd; padding:8px 12px; }
  h1 { font-size:15px; margin:0 0 6px; }
  h1 small { color:#888; font-weight:normal; }
  .bar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:4px 0; }
  .bar label { font-size:13px; color:#444; }
  input,select,button { font-family:inherit; font-size:13px; }
  input[type=number] { width:58px; }
  input#fname { width:160px; }
  button { padding:4px 10px; border:1px solid #bbb; background:#fff;
           border-radius:5px; cursor:pointer; }
  button:hover { background:#eef3fa; }
  button.primary { background:#2f6fb3; color:#fff; border-color:#2f6fb3; }
  button.primary:hover { background:#28609b; }
  .hint { font-size:12px; color:#777; margin-top:4px; }
  main { padding:10px 12px; }
  #cv { width:100%; background:#fff; border:1px solid #ddd; border-radius:6px;
        display:block; cursor:crosshair; touch-action:none; }
  #status { font-size:13px; color:#345; margin-top:6px; min-height:20px; }
  #status b { color:#2f6fb3; }
  .sep { flex:1; }
  #orig[disabled] { opacity:.4; cursor:default; }
</style>
</head>
<body>
<header>
  <h1>🎵 簡譜編輯器（鋼琴捲簾） <small id="title"></small></h1>
  <div class="bar">
    <button id="btnPlay" class="primary">▶ 試聽編輯後</button>
    <button id="btnStop">■ 停止</button>
    <span id="pos" style="font-size:12px;color:#666;width:64px">0.0 s</span>
    <button id="btnOrig">▶ 原哼唱對照</button>
    <label>BPM <input id="bpm" type="number" min="30" max="240" step="1"></label>
    <label>調 1=<select id="key"></select></label>
    <label>拍號 <select id="meter"><option value="4">4/4</option><option value="3">3/4</option><option value="2">2/4</option><option value="6">6/4</option></select></label>
    <label>吸附 <select id="snap"><option value="0.5">半拍</option><option value="1">一拍</option><option value="0.25">1/4 拍</option><option value="0">關</option></select></label>
  </div>
  <div class="bar">
    <span>檔名 <input id="fname" placeholder="my-song"></span>
    <button id="btnTxt" class="primary">存檔 .jianpu.txt</button>
    <button id="btnWav">存檔 .wav 試聽</button>
    <button id="btnJson">存檔 .json</button>
    <button id="btnLoad">載入 .json</button>
    <input type="file" id="fileIn" accept=".json" style="display:none">
    <button id="btnUndo">↶ 復原</button>
    <span class="sep"></span>
    <span id="count" style="font-size:12px;color:#666"></span>
  </div>
  <div class="hint">Shift+點空白=加音符 · 拖曳移動 · 拖音符右緣=改時值 · 右鍵或 Del=刪除 ·
    空白鍵=播放/停止 · Ctrl+Z=復原 · 按住 Alt 拖曳=不對齊節拍</div>
</header>
<main>
  <canvas id="cv"></canvas>
  <div id="status">就緒。左邊欄是音高（C4=中央C），橫軸是時間。</div>
</main>
<script>
"use strict";
/* ========== 資料（由產生器嵌入） ========== */
const DATA = __DATA__;
const ORIG = __AUDIO__;          // data URI 或 ""
const NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
const MAJOR = [0,2,4,5,7,9,11];
const PC2DEG = {0:1,2:2,4:3,5:4,7:5,9:6,11:7};

let S = null;                    // 編輯狀態
let selId = null, undoStack = [];
let play = {ctx:null, nodes:[], t0:0, raf:0, orig:null};

function initState(d){
  S = {name:d.name||"", bpm:d.bpm, keyPc:d.keyPc, meter:d.meter,
       notes:d.notes.map((n,i)=>({id:i+1, pitch:n.pitch,
                                  start:n.start, end:n.end}))};
  selId = null; undoStack = [];
  document.getElementById("fname").value = S.name || "my-song";
  syncControls();
}
function snapshot(){ undoStack.push(JSON.stringify(S)); if(undoStack.length>50) undoStack.shift(); }
function undo(){ if(!undoStack.length){status("沒有可復原的動作");return;}
  S = JSON.parse(undoStack.pop()); selId=null; syncControls(); draw(); status("已復原"); }
function syncControls(){
  document.getElementById("bpm").value = Math.round(S.bpm);
  document.getElementById("key").value = S.keyPc;
  document.getElementById("meter").value = S.meter;
}
function status(msg){ document.getElementById("status").innerHTML = msg; }
function updCount(){
  document.getElementById("count").textContent =
    S.notes.length + " 音 · " + endT().toFixed(1) + "s";
}
function endT(){ return S.notes.reduce((m,n)=>Math.max(m,n.end),0); }
function stepSec(){ const v=parseFloat(document.getElementById("snap").value);
  return v>0 ? v*60/S.bpm : 0; }
function snapT(t){ const st=stepSec(); return st>0 ? Math.round(t/st)*st : t; }

/* ========== 畫布 ========== */
const cv = document.getElementById("cv"), ctx2 = cv.getContext("2d");
const GUT=48, RULER=22, LH=20;
let rects=[], pps=1, minP=48, maxP=72;

function rangeP(){ // 音高範圍（動態含邊距）
  let lo=127, hi=0;
  S.notes.forEach(n=>{lo=Math.min(lo,n.pitch); hi=Math.max(hi,n.pitch);});
  lo=Math.min(lo,60)-2; hi=Math.max(hi,64)+2;
  return [Math.max(0,lo), Math.min(127,hi)];
}
function layout(){
  const dpr=window.devicePixelRatio||1;
  const w=cv.clientWidth||900;
  [minP,maxP]=rangeP();
  const h=RULER+(maxP-minP+1)*LH+4;
  cv.style.height=h+"px";
  cv.width=w*dpr; cv.height=h*dpr;
  ctx2.setTransform(dpr,0,0,dpr,0,0);
  pps=(w-GUT-8)/Math.max(endT()+1.0, 12);
}
const xOf=t=>GUT+t*pps;
const yOf=p=>RULER+(maxP-p)*LH;

function draw(){
  layout();
  const w=cv.clientWidth, h=parseInt(cv.style.height);
  ctx2.clearRect(0,0,w,h);
  ctx2.fillStyle="#fff"; ctx2.fillRect(0,0,w,h);
  // 音高列
  for(let p=minP;p<=maxP;p++){
    const y=yOf(p), black=[1,3,6,8,10].includes(p%12);
    ctx2.fillStyle=black?"#f1f1f5":"#fafafa";
    ctx2.fillRect(GUT,y,w-GUT,LH);
    ctx2.strokeStyle="#e6e6ea"; ctx2.beginPath();
    ctx2.moveTo(GUT,y+LH+.5); ctx2.lineTo(w,y+LH+.5); ctx2.stroke();
    if(p%12===0){ ctx2.fillStyle="#5a8"; ctx2.font="10px sans-serif";
      ctx2.fillText("C"+(Math.floor(p/12)-1),4,y+LH-5); }
  }
  // 節拍/小節線 + 拍號尺
  const beat=60/S.bpm, bar=beat*S.meter;
  ctx2.fillStyle="#f4f5f7"; ctx2.fillRect(0,0,w,RULER);
  ctx2.strokeStyle="#ccc"; ctx2.beginPath(); ctx2.moveTo(0,RULER+.5); ctx2.lineTo(w,RULER+.5); ctx2.stroke();
  const total=endT()+1.5;
  for(let t=0;t<=total;t+=beat){
    const x=xOf(t);
    if(x>w) break;
    const isBar=Math.abs((t/bar)-Math.round(t/bar))<1e-6;
    ctx2.strokeStyle=isBar?"#999":"#eee";
    ctx2.beginPath(); ctx2.moveTo(x+.5,isBar?RULER*0.3:RULER*0.6); ctx2.lineTo(x+.5,h); ctx2.stroke();
    if(isBar){ ctx2.fillStyle="#666"; ctx2.font="11px sans-serif";
      ctx2.fillText(String(Math.round(t/bar)+1), x+3, 14); }
  }
  // 音符
  rects=[];
  S.notes.forEach(n=>{
    const x=xOf(n.start), y=yOf(n.pitch),
          wd=Math.max(4,(n.end-n.start)*pps), hgt=LH-3;
    const isSel=n.id===selId;
    ctx2.fillStyle=isSel?"#e67e22":"#3b82c4";
    roundRect(x,y+1,wd,hgt,3); ctx2.fill();
    if(isSel){ ctx2.strokeStyle="#b35c10"; ctx2.lineWidth=2;
      ctx2.strokeRect(x+.5,y+1.5,wd-1,hgt-1); ctx2.lineWidth=1; }
    // 右緣手柄
    if(isSel){ ctx2.fillStyle="#fff"; ctx2.fillRect(x+wd-5,y+3,3,hgt-4); }
    rects.push({id:n.id,x,y,w:wd,h:hgt});
  });
  // 播放頭
  if(play.t0 && play.ctx){
    const t=play.ctx.currentTime-play.t0;
    if(t>0){ ctx2.strokeStyle="#e33"; ctx2.lineWidth=2;
      ctx2.beginPath(); ctx2.moveTo(xOf(t),RULER); ctx2.lineTo(xOf(t),h); ctx2.stroke();
      ctx2.lineWidth=1;
      document.getElementById("pos").textContent=t.toFixed(1)+" s"; }
  }
  updCount();
}
function roundRect(x,y,w,h,r){
  ctx2.beginPath();
  ctx2.moveTo(x+r,y); ctx2.arcTo(x+w,y,x+w,y+h,r); ctx2.arcTo(x+w,y+h,x,y+h,r);
  ctx2.arcTo(x,y+h,x,y,r); ctx2.arcTo(x,y,x+w,y,r); ctx2.closePath();
}

/* ========== 互動 ========== */
let drag=null;
function hit(ev){
  const r=cv.getBoundingClientRect();
  const x=ev.clientX-r.left, y=ev.clientY-r.top;
  for(let i=rects.length-1;i>=0;i--){
    const q=rects[i];
    if(x>=q.x&&x<=q.x+q.w&&y>=q.y&&y<=q.y+q.h)
      return {id:q.id, edge:(x>q.x+q.w-8), x, y};
  }
  return {id:null, x, y};
}
const noteById=id=>S.notes.find(n=>n.id===id);

cv.addEventListener("mousedown",ev=>{
  if(ev.button===2) return;               // 右鍵走 contextmenu
  const h=hit(ev);
  if(ev.shiftKey && h.id===null){         // 新增
    snapshot();
    const p=maxP-Math.floor((h.y-RULER)/LH);
    const st=stepSec()>0?snapT(Math.max(0,(h.x-GUT)/pps)) : Math.max(0,(h.x-GUT)/pps);
    const dur=stepSec()>0?stepSec():60/S.bpm;
    const id=Math.max(0,...S.notes.map(n=>n.id))+1;
    S.notes.push({id,pitch:Math.min(127,Math.max(0,p)),start:st,end:st+dur});
    selId=id; draw(); status("已新增音符"); return;
  }
  if(h.id===null){ selId=null; draw(); return; }
  selId=h.id;
  const n=noteById(h.id);
  drag={mode:h.edge?"resize":"move", id:h.id, ox:h.x, oy:h.y,
        s0:n.start, e0:n.end, p0:n.pitch, touched:false};
  draw();
});
window.addEventListener("mousemove",ev=>{
  if(!drag) return;
  const r=cv.getBoundingClientRect();
  const dx=(ev.clientX-r.left-drag.ox)/pps;
  const n=noteById(drag.id); if(!n) return;
  if(!drag.touched){ snapshot(); drag.touched=true; }
  const free=ev.altKey;
  if(drag.mode==="move"){
    let st=free?drag.s0+dx:snapT(drag.s0+dx);
    st=Math.max(0,st);
    const dur=drag.e0-drag.s0;
    n.start=st; n.end=st+dur;
    const lane=maxP-Math.floor(((ev.clientY-r.top)-RULER)/LH);
    n.pitch=Math.min(127,Math.max(0,lane));
  }else{
    let en=free?drag.e0+dx:snapT(drag.e0+dx);
    n.end=Math.max(n.start+ (stepSec()>0?stepSec():60/S.bpm/4), en);
  }
  draw(); ev.preventDefault();
});
window.addEventListener("mouseup",()=>{
  if(drag&&drag.touched) status(selInfo());
  drag=null;
});
cv.addEventListener("contextmenu",ev=>{
  ev.preventDefault();
  const h=hit(ev);
  if(h.id!==null){ snapshot(); S.notes=S.notes.filter(n=>n.id!==h.id);
    selId=null; draw(); status("已刪除音符"); }
});
window.addEventListener("keydown",ev=>{
  const inField=/INPUT|SELECT/.test(document.activeElement.tagName);
  if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==="z"){ ev.preventDefault(); undo(); return; }
  if(inField) return;
  if(ev.code==="Space"){ ev.preventDefault(); play.t0?stopAll():startPlay(); return; }
  if((ev.key==="Delete"||ev.key==="Backspace")&&selId!==null){
    snapshot(); S.notes=S.notes.filter(n=>n.id!==selId); selId=null;
    draw(); status("已刪除音符");
  }
});
function selInfo(){
  const n=noteById(selId); if(!n) return "";
  const deg=PC2DEG[n.pitch%12]||"?";
  return `選取: <b>${NOTE_NAMES[n.pitch%12]}${Math.floor(n.pitch/12)-1}</b>
    （MIDI ${n.pitch}，首調 ${deg}）· ${n.start.toFixed(2)}s → ${n.end.toFixed(2)}s
    · 時值 ${((n.end-n.start)*S.bpm/60).toFixed(1)} 拍`;
}

/* ========== Web Audio 試聽 ========== */
function ensureCtx(){ if(!play.ctx) play.ctx=new (window.AudioContext||window.webkitAudioContext)(); return play.ctx; }
function scheduleNote(c, dest, pitch, t, dur){
  const f=440*Math.pow(2,(pitch-69)/12);
  const o=c.createOscillator(), o2=c.createOscillator(), g=c.createGain();
  o.type="triangle"; o.frequency.value=f;
  o2.type="sine"; o2.frequency.value=f*2;
  const g2=c.createGain(); g2.gain.value=0.18;
  g.gain.setValueAtTime(0.0001,t);
  g.gain.linearRampToValueAtTime(0.26,t+0.012);
  g.gain.exponentialRampToValueAtTime(0.05,Math.max(t+0.05,t+dur*0.7));
  g.gain.linearRampToValueAtTime(0.0001,t+dur+0.12);
  o.connect(g); o2.connect(g2); g2.connect(g); g.connect(dest);
  o.start(t); o2.start(t); o.stop(t+dur+0.2); o2.stop(t+dur+0.2);
  play.nodes.push(o,o2);
}
function startPlay(){
  const c=ensureCtx(); if(c.state==="suspended") c.resume();
  stopAll(true);
  const master=c.createGain(); master.gain.value=0.9; master.connect(c.destination);
  const t0=c.currentTime+0.08;
  [...S.notes].sort((a,b)=>a.start-b.start)
    .forEach(n=>scheduleNote(c,master,n.pitch,t0+n.start,Math.max(0.08,n.end-n.start)));
  play.t0=t0; status("試聽中…（Web Audio 合成音；最終曲用 FluidSynth 真鋼琴渲染）");
  tick();
}
function tick(){
  play.raf=requestAnimationFrame(()=>{ draw(); if(play.t0) tick(); });
}
function stopAll(keepT0){
  play.nodes.forEach(n=>{try{n.stop();}catch(e){}}); play.nodes=[];
  if(!keepT0){ play.t0=0; if(ORIG_A) ORIG_A.pause();
    document.getElementById("pos").textContent="0.0 s"; draw(); }
}
const ORIG_A = ORIG ? new Audio(ORIG) : null;

/* ========== 匯出：jianpu.txt ========== */
function durTok(b){
  if(b<1){ const u=Math.max(1,Math.round(-Math.log2(b))); return "_".repeat(u); }
  const whole=Math.round(b), frac=b-whole;
  if(Math.abs(frac-0.5)<0.01) return "."+"-".repeat(Math.max(0,whole-1));
  return "-".repeat(Math.max(0,whole-1));
}
function restTok(b){
  if(b<1){ const u=Math.max(1,Math.round(-Math.log2(b))); return "0"+"_".repeat(u); }
  return "0"+"-".repeat(Math.max(0,Math.round(b)-1));
}
function toJianpu(){
  const bpm=S.bpm, keyPc=S.keyPc, meter=S.meter, beat=60/bpm;
  const tonicBase=keyPc+12*Math.round((60-keyPc)/12);
  const notes=[...S.notes].sort((a,b)=>a.start-b.start);
  const tokens=[], snapped=[]; let cursor=0;
  const Q=0.5;  // 半拍格線
  notes.forEach(n=>{
    let sb=Math.round((n.start/beat)/Q)*Q;
    let eb=sb+Math.max(Q,Math.round(((n.end-n.start)/beat)/Q)*Q);
    if(sb>cursor+0.3){ const g=Math.round((sb-cursor)/Q)*Q; tokens.push(restTok(g)); cursor+=g; }
    let rel=n.pitch-tonicBase, pc=((rel%12)+12)%12;
    if(!MAJOR.includes(pc)){
      let best=MAJOR.reduce((a,d)=>{
        const d0=Math.min(Math.abs(pc-d),12-Math.abs(pc-d));
        return d0<a.d0?{d,d0}:a;},{d:MAJOR[0],d0:99}).d;
      snapped.push(`${n.start.toFixed(1)}s ${NOTE_NAMES[pc]}->${NOTE_NAMES[(keyPc+best)%12]}`);
      rel+=best-pc; pc=best;
    }
    const deg=PC2DEG[pc], oct=Math.floor(rel/12);
    const mark=oct>0?"'".repeat(oct):",".repeat(-oct);
    tokens.push(`${deg}${mark}${durTok(eb-sb)}`);
    cursor=eb;
  });
  // 排版（每 meter 拍一行）
  const lines=[]; let line=[], cost=0;
  tokens.forEach(tk=>{
    const c=1+ (tk.match(/-/g)||[]).length + 0.5*(tk.match(/_/g)||[]).length + (tk.includes(".")?0.5:0);
    if(cost+c>meter+0.01){ lines.push(line.join(" ")+" |"); line=[]; cost=0; }
    line.push(tk); cost+=c;
  });
  if(line.length) lines.push(line.join(" ")+" |");
  let out=`# 1=${NOTE_NAMES[keyPc]}  bpm=${Math.round(bpm)}  拍號=${meter}/4  `+
          `(編輯器輸出; ${notes.length} 音符)\n`;
  if(snapped.length) out+=`# 非調內音已吸附 ${snapped.length} 處: ${snapped.slice(0,8).join("; ")}\n`;
  return out+lines.join("\n")+"\n";
}

/* ========== 匯出：wav（離線渲染） ========== */
function bufToWav(buf){
  const ch=buf.numberOfChannels, sr=buf.sampleRate, n=buf.length;
  const bytes=44+n*ch*2, ab=new ArrayBuffer(bytes), v=new DataView(ab);
  const wr=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};
  wr(0,"RIFF"); v.setUint32(4,36+n*ch*2,true); wr(8,"WAVEfmt ");
  v.setUint32(16,16,true); v.setUint16(20,1,true); v.setUint16(22,ch,true);
  v.setUint32(24,sr,true); v.setUint32(28,sr*ch*2,true);
  v.setUint16(32,ch*2,true); v.setUint16(34,16,true);
  wr(36,"data"); v.setUint32(40,n*ch*2,true);
  let o=44;
  for(let i=0;i<n;i++) for(let c=0;c<ch;c++){
    let s=Math.max(-1,Math.min(1,buf.getChannelData(c)[i]));
    v.setInt16(o,s<0?s*0x8000:s*0x7FFF,true); o+=2;
  }
  return new Blob([ab],{type:"audio/wav"});
}
async function renderWav(){
  const sr=44100, dur=endT()+0.8;
  const oc=new OfflineAudioContext(2,Math.ceil(dur*sr),sr);
  const master=oc.createGain(); master.gain.value=0.8; master.connect(oc.destination);
  [...S.notes].sort((a,b)=>a.start-b.start)
    .forEach(n=>scheduleNote(oc,master,n.pitch,n.start+0.02,Math.max(0.08,n.end-n.start)));
  status("離線渲染中…");
  const buf=await oc.startRendering();
  return bufToWav(buf);
}

/* ========== 存檔 ========== */
function fname(){ return (document.getElementById("fname").value||"my-song").replace(/[\\/:*?"<>|]/g,"_"); }
function dl(blob,name){
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob); a.download=name; a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),5000);
}
document.getElementById("btnTxt").onclick=()=>{
  dl(new Blob([toJianpu()],{type:"text/plain;charset=utf-8"}), fname()+".jianpu.txt");
  status(`已存 <b>${fname()}.jianpu.txt</b> — 傳回即可重新生曲（jianpu2midi → FluidSynth）`);
};
document.getElementById("btnWav").onclick=async()=>{
  const b=await renderWav(); dl(b,fname()+"_preview.wav");
  status(`已存 <b>${fname()}_preview.wav</b>（Web Audio 合成音試聽版）`);
};
document.getElementById("btnJson").onclick=()=>{
  S.name=document.getElementById("fname").value;
  dl(new Blob([JSON.stringify(S,null,1)],{type:"application/json"}), fname()+".score.json");
  status(`已存 <b>${fname()}.score.json</b>（編輯狀態，可日後載入續編）`);
};
document.getElementById("btnLoad").onclick=()=>document.getElementById("fileIn").click();
document.getElementById("fileIn").onchange=ev=>{
  const f=ev.target.files[0]; if(!f) return;
  const rd=new FileReader();
  rd.onload=()=>{ try{ snapshot(); initState(JSON.parse(rd.result));
    draw(); status(`已載入 <b>${f.name}</b>`); }
    catch(e){ status("載入失敗: "+e.message); } };
  rd.readAsText(f); ev.target.value="";
};

/* ========== 控制項 ========== */
document.getElementById("btnPlay").onclick=startPlay;
document.getElementById("btnStop").onclick=()=>stopAll();
document.getElementById("btnUndo").onclick=undo;
document.getElementById("btnOrig").onclick=()=>{
  if(!ORIG_A) return;
  if(ORIG_A.paused){ stopAll(); ORIG_A.currentTime=0; ORIG_A.play();
    status("播放原哼唱對照…"); } else { ORIG_A.pause(); }
};
document.getElementById("bpm").onchange=e=>{
  snapshot(); S.bpm=Math.min(240,Math.max(30,+e.target.value||100));
  draw(); status(`BPM → ${Math.round(S.bpm)}`);
};
document.getElementById("key").onchange=e=>{
  snapshot(); S.keyPc=+e.target.value;
  status(`首調 → 1=${NOTE_NAMES[S.keyPc]}（僅影響輸出簡譜數字，音高不變）`);
};
document.getElementById("meter").onchange=e=>{ snapshot(); S.meter=+e.target.value; draw(); };
document.getElementById("snap").onchange=()=>status("吸附格線已更新");
window.addEventListener("resize",draw);

/* ========== 啟動 ========== */
(function(){
  const ks=document.getElementById("key");
  NOTE_NAMES.forEach((n,i)=>{ const o=document.createElement("option");
    o.value=i; o.textContent=n; ks.appendChild(o); });
  if(!ORIG) document.getElementById("btnOrig").disabled=true;
  document.getElementById("title").textContent =
    (DATA.name? "《"+DATA.name+"》 " : "") + "1=" + NOTE_NAMES[DATA.keyPc];
  initState(DATA);
  draw();
  status("就緒：Shift+點空白加音符、拖曳移動、右緣改時值、右鍵刪除。完成後按「存檔 .jianpu.txt」。");
})();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mid", required=True, help="旋律 MIDI（hum2midi / jianpu2midi 產出）")
    ap.add_argument("--audio", default=None, help="原哼唱錄音（m4a/mp3/wav），內嵌供對照播放")
    ap.add_argument("--out", default="score-editor.html")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    data = load_mid(a.mid)
    data["name"] = a.name or os.path.splitext(os.path.basename(a.mid))[0]
    audio = embed_audio(a.audio) if a.audio else ""
    build(data, audio, a.out)
