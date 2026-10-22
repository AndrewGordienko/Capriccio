'use strict';
const $ = id => document.getElementById(id);
const a = $('original'), b = $('reference');
const state = {mode:'matched',speed:1.02,pitch:0,offset:0,audio:'a',linked:false,baseSpeed:1.02,loading:false};
const duration = 20;
const clamp = (n,min,max) => Math.max(min,Math.min(max,n));
const say = text => { $('status').textContent = text; };
const format = t => `00:${Math.floor(clamp(t,0,59)).toString().padStart(2,'0')}`;
function setAudio(which){
  state.audio = which;
  a.muted = which === 'b'; b.muted = which === 'a';
  document.querySelectorAll('[data-audio]').forEach(el => {
    const selected = el.dataset.audio === which;
    el.classList.toggle('selected',selected); el.setAttribute('aria-pressed',String(selected));
  });
}
function updateButtons(){
  const playing = !a.paused || !b.paused;
  $('play-label').textContent = playing ? 'Pause both' : 'Play together';
  $('play-icon').textContent = playing ? 'Ⅱ' : '▶';
}
function pause(){ state.linked=false; a.pause(); b.pause(); updateButtons(); }
function bTime(t){return clamp(t * state.speed / state.baseSpeed + state.offset,0,Number.isFinite(b.duration) ? b.duration-.01 : 30);}
function sync(force=false){
  if(b.readyState < 1 || b.seeking) return;
  const target=bTime(a.currentTime);
  if(force || Math.abs(b.currentTime-target)>.12) b.currentTime=target;
}
function rates(){
  a.defaultPlaybackRate=1; a.playbackRate=1;
  b.preservesPitch=true;
  if('webkitPreservesPitch' in b) b.webkitPreservesPitch=true;
  b.playbackRate=state.speed/state.baseSpeed;
  b.defaultPlaybackRate=b.playbackRate;
}
async function play(){
  if(state.loading){say('The reference is loading. Please try again in a moment.');return;}
  if(!a.paused || !b.paused){pause();say('Paused.');return;}
  if(a.currentTime>=duration-.08) a.currentTime=0;
  rates();sync(true);setAudio(state.audio);state.linked=true;
  try{await Promise.all([a.play(),b.play()]);say('Playing both videos. Switch A / B to compare.');}
  catch(e){pause();say('Playback could not start. Use the video controls or press Play together again.');}
  updateButtons();
}
function seek(t){a.currentTime=clamp(t,0,duration);sync(true);$('timeline').value=a.currentTime;}
function reflect(){
  $('speed').value=state.speed; $('pitch').value=state.pitch; $('offset').value=state.offset;
  const pct=(state.speed-1)*100;
  $('speed-value').innerHTML=`${state.speed.toFixed(3)}× <small>${pct>=0?'+':''}${pct.toFixed(1)}%</small>`;
  $('offset-value').textContent=`${state.offset>0?'+':''}${state.offset.toFixed(2)} s`;
  const measured=state.mode==='matched';
  $('matched-mode').classList.toggle('selected',measured);$('matched-mode').setAttribute('aria-pressed',String(measured));
  $('raw-mode').classList.toggle('selected',!measured);$('raw-mode').setAttribute('aria-pressed',String(!measured));
  $('video-badge').textContent=state.pitch ? `${state.pitch>0?'+':''}${state.pitch} SEMITONES · SPEED ADJUSTED` : measured ? 'TIMING ADJUSTED' : 'UNTOUCHED REFERENCE';
}
function sourceFor(){
  if(state.pitch===-2) return ['media/reference-minus2.mp4',1.02];
  if(state.pitch===2) return ['media/reference-plus2.mp4',1.02];
  return state.mode==='raw' ? ['media/reference.mp4',1] : ['media/reference-adjusted.mp4',1.02];
}
function updateSource(){
  pause();const [url,base]=sourceFor();state.baseSpeed=base;
  state.loading=true;
  b.src=url; b.load();reflect();say('Loading reference…');
}
b.addEventListener('loadedmetadata',()=>{state.loading=false;rates();sync(true);say('Reference ready. Press Play together.');});
for(const video of [a,b]){
  video.addEventListener('play',updateButtons);video.addEventListener('pause',updateButtons);
  video.addEventListener('error',()=>{state.loading=false;pause();say('A video failed to load. Refresh the page or open its YouTube source.');});
}
a.addEventListener('seeking',()=>{if(state.linked)sync(true);});
a.addEventListener('ended',()=>{pause();say('End of the passage. Press Play together to replay.');});
b.addEventListener('ended',()=>{if(state.linked){pause();say('End of the reference. Restart or adjust its timing.');}});
$('play').addEventListener('click',play);
$('restart').addEventListener('click',()=>{pause();seek(0);say('Both videos reset.');});
$('timeline').addEventListener('input',e=>seek(Number(e.target.value)));
document.querySelectorAll('[data-audio]').forEach(el=>el.addEventListener('click',()=>setAudio(el.dataset.audio)));
$('speed').addEventListener('input',e=>{state.speed=Number(e.target.value);rates();reflect();sync(true);});
$('offset').addEventListener('input',e=>{state.offset=Number(e.target.value);reflect();sync(true);});
$('pitch').addEventListener('change',e=>{state.pitch=Number(e.target.value);if(state.pitch)state.mode='matched';updateSource();});
$('raw-mode').addEventListener('click',()=>{Object.assign(state,{mode:'raw',speed:1,pitch:0,offset:0});updateSource();});
function reset(){Object.assign(state,{mode:'matched',speed:1.02,pitch:0,offset:0});updateSource();}
$('matched-mode').addEventListener('click',reset);$('reset').addEventListener('click',reset);
$('share').addEventListener('click',async()=>{
  const url=new URL(location.href);url.hash=new URLSearchParams({mode:state.mode,speed:state.speed,pitch:state.pitch,offset:state.offset,audio:state.audio}).toString();
  try{await navigator.clipboard.writeText(url.href);$('share').textContent='Link copied ✓';say('Share link copied, including your comparison settings.');setTimeout(()=>{$('share').innerHTML='Copy share link <span aria-hidden="true">↗</span>';},2500);}
  catch{say(`Copy this link: ${url.href}`);}
});
const params=new URLSearchParams(location.hash.slice(1));
if(params.size){
  state.mode=params.get('mode')==='raw'?'raw':'matched';
  for(const [name,min,max] of [['speed',.85,1.15],['offset',-1,1]]){const n=Number(params.get(name));if(params.has(name)&&Number.isFinite(n))state[name]=clamp(n,min,max);}
  const pitch=Number(params.get('pitch'));state.pitch=[-2,0,2].includes(pitch)?pitch:0;
  if(['a','b','both'].includes(params.get('audio')))state.audio=params.get('audio');
  updateSource();
}
setAudio(state.audio);reflect();rates();
function tick(){
  $('timeline').value=clamp(a.currentTime,0,duration);$('time').textContent=`${format(a.currentTime)} / 00:20`;
  if(state.linked && !a.paused && !b.paused) sync();
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
