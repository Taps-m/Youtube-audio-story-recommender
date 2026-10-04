(function(root){
 'use strict';
 const SERIES=[['Byomkesh',/byomkesh|ব্যোমকেশ/i,'detective mystery','Saradindu Bandyopadhyay'],['Feluda',/feluda|ফেলুদা/i,'detective mystery','Satyajit Ray'],['Professor Shonku',/sh[oa]nku|শঙ্কু|শংকু/i,'science fiction','Satyajit Ray'],['Arjun',/\barjun\b|অর্জুন/i,'detective mystery','Samaresh Majumdar'],['Dipkaku O Jhinuk',/dipkaku|দীপকাকু/i,'detective mystery','Sukanta Gangopadhyay'],['Riju',/riju series/i,'spy thriller','Saswati Chowdhury'],['Chanakya',/chanakya|চাণক্য/i,null,'Abhigyan Ganguly']];
 const AUTHORS=[['Saradindu Bandyopadhyay',/s[ah]*radindu|শরদিন্দু/i],['Satyajit Ray',/satyajit (?:ray|roy)|সত্যজিৎ/i],['Samaresh Majumdar',/samaresh majumdar|সমরেশ/i],['Abhik Arjun Dutta',/abhik arjun dutta/i]];
 function enrich(story){
  const title=String(story.title||'').replace(/(?:best of )?sunday suspense(?: classics)?/gi,'');
  const tags=new Set(story.reviewed_tags||[]),series=new Set(story.series||[]),authors=new Set(story.authors||[]);
  for(const [name,rx,genre,author] of SERIES)if(rx.test(title)){series.add(name);if(genre)tags.add(genre);authors.add(author);}
  for(const [name,rx] of AUTHORS)if(rx.test(title))authors.add(name);
  for(const [tag,rx] of [['detective mystery',/detective|goyenda|গোয়েন্দা|গোয়েন্দা/i],['mystery',/\bmystery\b|rahasya|রহস্য/i],['horror',/horror|ভৌতিক|bhuter|supernatural/i],['suspense',/\bsuspense\b|thriller/i],['psychological thriller',/psychological/i],['spy thriller',/spy thriller/i],['science fiction',/sci.fi|science fiction/i],['romance',/romantic|premer|love story/i]])if(rx.test(title))tags.add(tag);
  return {...story,title_keyword_tags:[...tags],series:[...series],authors:[...authors]};
 }
 function profile(catalog,feedback){
  const p={tags:new Map(),series:new Map(),authors:new Map()};
  for(const s of catalog){const f=feedback[s.video_id]||{};if(f.disliked)continue;const weight=s.confirmed_favorite?3:f.liked?1:0;if(!weight)continue;
   for(const [field,map] of [['title_keyword_tags',p.tags],['series',p.series],['authors',p.authors]])for(const value of s[field]||[])map.set(value,(map.get(value)||0)+weight);
  }return p;
 }
 function evaluate(s,p,feedback){
  const f=feedback[s.video_id]||{};let score=0;const matches=[];
  for(const [field,map,weight] of [['series',p.series,9],['authors',p.authors,7],['title_keyword_tags',p.tags,3]])for(const value of s[field]||[]){const affinity=map.get(value)||0;if(affinity){const points=(value==='suspense'?0.5:weight)*affinity;score+=points;matches.push({value,points,field});}}
  if(f.liked)score+=6;if(f.saved)score+=2;if(f.heard)score-=1000;
  matches.sort((a,b)=>b.points-a.points);
  let reason=s.confirmed_favorite?'You told us you enjoyed this story.':matches.length?(matches[0].field==='authors'?'Because you enjoy stories by ':'Because you like ')+matches[0].value+'.':'A different story to explore beyond your usual matches.';
  if(f.heard)reason+=' You marked it already heard, so it appears after unheard choices.';
  return {score,reason};
 }
 function rank(items,p,feedback){return [...items].sort((a,b)=>Number(!!feedback[a.video_id]?.heard)-Number(!!feedback[b.video_id]?.heard)||evaluate(b,p,feedback).score-evaluate(a,p,feedback).score||a.title.localeCompare(b.title));}
 const api={enrich,profile,evaluate,rank};root.StoryRecommendations=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
