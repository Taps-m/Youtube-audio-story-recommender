'use strict';
async function boot(){
 const $=id=>document.getElementById(id),engine=StoryRecommendations;
 let catalog=[],privateLoaded=false,model=null;
 try{const response=await fetch('discovery-catalog.json');if(response.ok)catalog=(await response.json()).map(s=>({...s,eligible_as_new_discovery:true}));}catch{}
 if(['localhost','127.0.0.1','::1','[::1]'].includes(location.hostname)){
  try{const response=await fetch('/__private/catalog');if(response.ok){const data=await response.json();catalog=data;privateLoaded=true;}}catch{}
  try{const response=await fetch('/__private/model');if(response.ok)model=await response.json();}catch{/* Behavior model is optional. */}
 }
 catalog=[...new Map(catalog.filter(s=>/^[\w-]{11}$/.test(s.video_id)&&typeof s.title==='string').map(s=>[s.video_id,engine.enrich(s)])).values()];
 const KEY='story-compass-feedback-v1';let feedback={},storageAvailable=true,limit=9;
 try{const data=JSON.parse(localStorage.getItem(KEY)||'{}');if(data&&typeof data==='object'&&!Array.isArray(data))feedback=data;}catch{storageAvailable=false;}
 function persist(){try{localStorage.setItem(KEY,JSON.stringify(feedback));}catch{storageAvailable=false;}}
 function card(s,p,hidden=false){
  const el=document.createElement('article');el.className='card';el.dataset.video=s.video_id;
  const cover=document.createElement('div');cover.className='cover';cover.setAttribute('aria-hidden','true');
  const tags=s.title_keyword_tags;cover.dataset.theme=tags.includes('romance')?'romance':tags.includes('science fiction')?'cosmic':tags.includes('horror')?'haunted':'mystery';
  const scene=document.createElement('span');scene.className='cover-scene';cover.append(scene);
  const word=document.createElement('span');word.className='cover-word';word.textContent=s.title.replace(/^Sunday Suspense(?: Classics)?\s*\|\s*/,'').split('|')[0].trim();
  const symbol=document.createElement('span');symbol.className='cover-symbol';symbol.textContent='◈';cover.append(word,symbol);el.append(cover);
  const badge=document.createElement('div');badge.className='badge';badge.textContent=hidden?'HIDDEN':s.confirmed_favorite?'CONFIRMED FAVORITE':!privateLoaded?'CURATED SUGGESTION':s.eligible_as_new_discovery?'DISCOVERY CANDIDATE':'PREVIOUSLY OPENED';el.append(badge);
  const h=document.createElement('h3');h.textContent=s.title.replace(/^Sunday Suspense(?: Classics)?\s*\|\s*/,'');el.append(h);
  const meta=document.createElement('div');meta.className='meta';meta.textContent=s.channel+' · '+(s.duration_minutes?Math.round(s.duration_minutes)+' min':'Duration unverified');el.append(meta);
  const reason=document.createElement('p');reason.className='reason';reason.textContent=engine.evaluate(s,p,feedback).reason;el.append(reason);
  const a=document.createElement('a');a.className='listen';a.textContent='Listen on YouTube';a.href='https://www.youtube.com/watch?v='+s.video_id;a.target='_blank';a.rel='noopener noreferrer';el.append(a);
  const actions=document.createElement('div');actions.className='actions';
  const buttons=hidden?[['restore','Restore story']]:[['liked','More like this'],['disliked','Not for me'],['saved','Save'],['heard','Already heard']];
  for(const [field,label] of buttons){
   const b=document.createElement('button');b.textContent=label;b.dataset.video=s.video_id;b.dataset.action=field;b.setAttribute('aria-label',label+': '+s.title);if(field!=='restore')b.setAttribute('aria-pressed',String(!!feedback[s.video_id]?.[field]));
   b.onclick=()=>{const f=feedback[s.video_id]||={};if(field==='restore')f.disliked=false;else f[field]=!f[field];if(field==='liked'&&f.liked)f.disliked=false;if(field==='disliked'&&f.disliked)f.liked=false;persist();render({video:s.video_id,action:field});$('status').textContent=storageAvailable?(field==='disliked'?'Story hidden. Restore it from Hidden stories.':'Feedback updated.'):'Feedback updated for this session; storage is unavailable.';};actions.append(b);
  }el.append(actions);return el;
 }
 function render(focus){
  const active=document.activeElement,scrollY=window.scrollY,anchor=focus?active?.closest('.card'):null,oldTop=anchor?.getBoundingClientRect().top;
  const genre=$('genre').value,duration=$('duration').value,collection=$('collection').value,p=engine.profile(catalog,feedback,model),today=new Date().toISOString().slice(0,10);
  const items=catalog.filter(s=>(genre==='all'||s.title_keyword_tags.includes(genre))&&(collection!=='saved'||feedback[s.video_id]?.saved)&&(duration==='any'||(Number.isFinite(s.duration_minutes)&&(duration==='medium'?s.duration_minutes>=30&&s.duration_minutes<=60:s.duration_minutes>60))));
  const visible=items.filter(s=>!feedback[s.video_id]?.disliked),hidden=collection==='hidden';
  const favorites=hidden?[]:visible.filter(s=>s.confirmed_favorite);
  const discoveries=hidden?[]:engine.rank(visible.filter(s=>s.eligible_as_new_discovery&&!feedback[s.video_id]?.heard),p,feedback,{explore:true,seed:today,diversify:true});
  const allHistory=hidden?engine.rank(items.filter(s=>feedback[s.video_id]?.disliked),p,feedback):engine.rank(visible.filter(s=>!s.confirmed_favorite&&(!s.eligible_as_new_discovery||feedback[s.video_id]?.heard)),p,feedback);
  for(const [id,list] of [['favorites',favorites],['discoveries',discoveries.slice(0,6)],['history',allHistory.slice(0,limit)]]){
   const container=$(id);container.replaceChildren();if(!list.length){const message=document.createElement('p');message.className='empty';message.textContent=id==='discoveries'?'No new candidates match these controls. Try another story type.':hidden&&id==='history'?'No hidden stories.':'No stories match these controls.';container.append(message);}else list.forEach(s=>container.append(card(s,p,hidden&&id==='history')));
  }
  $('history-heading').textContent=hidden?'Hidden stories':privateLoaded?'Pick up a familiar thread':'Stories you marked already heard';$('history-note').textContent=hidden?'Restore any story to bring it back.':privateLoaded?'Previously opened · enjoyment unconfirmed':'Based on feedback in this browser';
  $('favorite-count').textContent=favorites.length+' shown';$('show-more').hidden=allHistory.length<=limit;$('show-more').textContent='Show more ('+(allHistory.length-limit)+' remaining)';
  if(focus){const next=[...document.querySelectorAll('.card')].find(c=>c.dataset.video===focus.video),button=next?[...next.querySelectorAll('button')].find(b=>b.dataset.action===focus.action):null;
   (button||$('collection')).focus({preventScroll:true});if(next&&oldTop!==undefined)window.scrollBy(0,next.getBoundingClientRect().top-oldTop);else window.scrollTo(0,scrollY);
  }
 }
 const knownDurations=catalog.filter(s=>Number.isFinite(s.duration_minutes)&&s.duration_minutes>0).length;
 $('duration').disabled=!knownDurations;
 $('duration-note').textContent=knownDurations===catalog.length&&catalog.length?'Story durations fetched from YouTube.':knownDurations?'Duration filters include only records with verified duration.':'Duration filtering is unavailable until real durations are verified.';
 ['genre','duration','collection'].forEach(id=>$(id).addEventListener('change',()=>{limit=9;render();}));
 $('show-more').onclick=()=>{limit+=9;render();if($('show-more').hidden)$('history-heading').focus();else $('show-more').focus();};
 $('reset').onclick=()=>{feedback={};persist();render();$('status').textContent='Feedback cleared. Your confirmed favorites remain.';};render();
}
boot().catch(()=>{document.getElementById('status').textContent='The catalog could not load. Refresh the page or check the local server.';});
