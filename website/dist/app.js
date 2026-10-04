'use strict';
async function boot(){
window.STORY_CATALOG=[];
if(['localhost','127.0.0.1','::1','[::1]'].includes(location.hostname)){
 try{const response=await fetch('local-test-catalog.json');if(response.ok){const data=await response.json();if(Array.isArray(data))window.STORY_CATALOG=data;}}catch{/* A clean checkout has no private catalog. */}
}
const KEY='story-compass-feedback-v1';
let feedback={};let storageAvailable=true;
try{feedback=JSON.parse(localStorage.getItem(KEY)||'{}');if(!feedback||Array.isArray(feedback)||typeof feedback!=='object')feedback={};}catch{feedback={};storageAvailable=false;}
const $=id=>document.getElementById(id);
function persist(){try{localStorage.setItem(KEY,JSON.stringify(feedback));}catch{storageAvailable=false;} }
function card(s){
 const el=document.createElement('article');el.className='card';
 const badge=document.createElement('div');badge.className='badge';badge.textContent=s.confirmed_favorite?'CONFIRMED FAVORITE':'PREVIOUSLY OPENED';el.append(badge);
 const heading=document.createElement('h3');heading.textContent=s.title.replace(/^Sunday Suspense\s*\|\s*/,'');el.append(heading);
 const meta=document.createElement('div');meta.className='meta';meta.textContent=s.channel+' · Duration unverified';el.append(meta);
 const reason=document.createElement('p');reason.className='reason';reason.textContent=s.confirmed_favorite?'You told us you enjoyed this story.':(s.title_keyword_tags.length?'Title signals: '+s.title_keyword_tags.join(', ')+'. You previously opened this story.':'You previously opened this story. Tell us whether it fits your taste.');el.append(reason);
 const a=document.createElement('a');a.className='listen';a.textContent='Listen on YouTube';a.href='https://www.youtube.com/watch?v='+encodeURIComponent(s.video_id);a.target='_blank';a.rel='noopener noreferrer';el.append(a);
 const actions=document.createElement('div');actions.className='actions';
 for(const [field,label] of [['liked','More like this'],['disliked','Not for me'],['saved','Save'],['heard','Already heard']]){
  const b=document.createElement('button');b.textContent=label;b.setAttribute('aria-pressed',String(!!feedback[s.video_id]?.[field]));b.setAttribute('aria-label',label+': '+s.title);
  b.onclick=()=>{const f=feedback[s.video_id]||={};f[field]=!f[field];if(field==='liked'&&f.liked)f.disliked=false;if(field==='disliked'&&f.disliked)f.liked=false;persist();render();$('status').textContent=storageAvailable?'Feedback updated.': 'Feedback updated for this session; browser storage is unavailable.';};actions.append(b);
 }el.append(actions);return el;
}
function render(){
 const genre=$('genre').value,duration=$('duration').value,saved=$('collection').value==='saved';
 $('duration-note').textContent=duration==='any'?'Duration data is still being verified.':'No verified duration matches yet. Clear the duration filter to browse the test catalog.';
 const likedGenres=new Set(window.STORY_CATALOG.filter(s=>feedback[s.video_id]?.liked).flatMap(s=>s.title_keyword_tags));
 const items=window.STORY_CATALOG.filter(s=>(genre==='all'||s.title_keyword_tags.includes(genre))&&(!saved||feedback[s.video_id]?.saved)&&duration==='any');
 const favorites=items.filter(s=>s.confirmed_favorite);const history=items.filter(s=>!s.confirmed_favorite&&!feedback[s.video_id]?.disliked).sort((a,b)=>Number(!!feedback[b.video_id]?.liked)-Number(!!feedback[a.video_id]?.liked)+b.title_keyword_tags.filter(t=>likedGenres.has(t)).length-a.title_keyword_tags.filter(t=>likedGenres.has(t)).length).slice(0,9);
 for(const [id,list] of [['favorites',favorites],['history',history]]){const container=$(id);container.replaceChildren();if(!list.length){const p=document.createElement('p');p.className='empty';p.textContent='No stories match these controls yet.';container.append(p);}else list.forEach(s=>container.append(card(s)));}
 $('favorite-count').textContent=favorites.length+' shown';
}
['genre','duration','collection'].forEach(id=>$(id).addEventListener('change',render));
$('reset').onclick=()=>{feedback={};persist();render();$('status').textContent='Feedback cleared. Your confirmed favorites remain.';};render();
}
boot();
