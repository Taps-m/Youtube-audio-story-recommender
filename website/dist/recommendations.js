(function(root){
 'use strict';
 const SERIES=[['Byomkesh',/byomkesh|ব্যোমকেশ/i,'detective mystery','Saradindu Bandyopadhyay'],['Feluda',/feluda|ফেলুদা/i,'detective mystery','Satyajit Ray'],['Professor Shonku',/sh[oa]nku|শঙ্কু|শংকু/i,'science fiction','Satyajit Ray'],['Arjun',/^(?:arjun|অর্জুন)(?:\s+series)?$/i,'detective mystery','Samaresh Majumdar'],['Dipkaku O Jhinuk',/dipkaku|দীপকাকু/i,'detective mystery','Sukanta Gangopadhyay'],['Riju',/riju series/i,'spy thriller','Saswati Chowdhury'],['Chanakya',/chanakya|চাণক্য/i,null,'Abhigyan Ganguly']];
 const AUTHORS=[['Saradindu Bandyopadhyay',/s[ah]*radindu|শরদিন্দু/i],['Satyajit Ray',/satyajit (?:ray|roy)|সত্যজিৎ/i],['Samaresh Majumdar',/samaresh majumdar|সমরেশ/i],['Abhik Arjun Dutta',/abhik arjun dutta/i]];
 // Romance themes manually checked against the official video descriptions.
 const REVIEWED_ROMANCE=new Set(['IGuYKCiLxc4','RD9DiE-GqI4','piYSiRnd9KA','6sn1U8NZJno']);
 function enrich(story){
  const title=String(story.title||'').replace(/(?:best of )?sunday suspense(?: classics)?/gi,'');
  const tags=new Set(story.reviewed_tags||[]),series=new Set(story.series||[]),authors=new Set(story.authors||[]);
  if(REVIEWED_ROMANCE.has(story.video_id))tags.add('romance');
  const segments=title.split('|').map(t=>t.trim()).filter(t=>t&&!AUTHORS.some(([,rx])=>rx.test(t)));
  for(const [name,rx,genre,author] of SERIES)if(segments.some(t=>rx.test(t))){series.add(name);if(genre)tags.add(genre);authors.add(author);}
  for(const [name,rx] of AUTHORS)if(rx.test(title))authors.add(name);
  for(const [tag,rx] of [['detective mystery',/detective|goyenda|গোয়েন্দা|গোয়েন্দা/i],['mystery',/\bmystery\b|rahasya|রহস্য/i],['horror',/horror|ভৌতিক|bhuter|supernatural/i],['suspense',/\bsuspense\b|thriller/i],['psychological thriller',/psychological/i],['spy thriller',/spy thriller/i],['science fiction',/sci.fi|science fiction/i],['romance',/romantic|premer|love story/i]])if(rx.test(title))tags.add(tag);
  return {...story,title_keyword_tags:[...tags],series:[...series],authors:[...authors]};
 }
 // ---- Probabilistic ranking -------------------------------------------------------------
 // Each attribute (series, author, genre, channel) keeps a Beta(1+a, 1+b) belief that you enjoy it.
 // Evidence weights: confirmed favorite 3, "More like this" 2, Save 1. Without explicit feedback,
 // return-day evidence is only 0.1 (max 0.5). Only explicit dislikes add negative evidence.
 // Gap-derived completions and skips never shape the live ranking. Beliefs start at your overall
 // rate (base), so an attribute only helps when it beats your norm. Attributes combine on the log-odds scale; rarer genres
 // count more (inverse document frequency). Opened stories add a behavior term fitted offline by
 // fit_preferences.py; explicit feedback overrides inference.
 const EVIDENCE={favorite:3,liked:2,saved:1,returnDay:0.1,returnCap:0.5,disliked:2},PRIOR_STRENGTH=2;
 const TYPE_WEIGHT={series:1,author:0.8,genre:0.5,channel:0.3};
 const EXPLICIT_LOGIT={liked:2,saved:0.7};
 const THETA_WEIGHT=0.5,STRONG_EVIDENCE=4;
 const clamp=(x,lo,hi)=>Math.min(hi,Math.max(lo,x)),logit=p=>Math.log(p/(1-p)),sigmoid=x=>1/(1+Math.exp(-x));
 function entities(s){
  return [...(s.series||[]).map(v=>['series',v]),...(s.authors||[]).map(v=>['author',v]),
   ...(s.title_keyword_tags||[]).map(v=>['genre',v]),...(s.channel?[['channel',s.channel]]:[])].map(([type,value])=>({type,value,key:type+':'+value}));
 }
 function profile(catalog,feedback,model){
  const beliefs=new Map(),counts=new Map();let totalPos=0,totalNeg=0;
  for(const s of catalog){
   const f=feedback[s.video_id]||{},days=s.behavior?.return_days||0;
   // Explicit feedback takes precedence. Timing-based skips are not dislikes.
   const explicit=s.confirmed_favorite||f.liked||f.saved||f.disliked;
   const pos=f.disliked?0:(s.confirmed_favorite?EVIDENCE.favorite:0)+(f.liked?EVIDENCE.liked:0)+(f.saved?EVIDENCE.saved:0)+(explicit?0:Math.min(Math.max(days,0)*EVIDENCE.returnDay,EVIDENCE.returnCap));
   const neg=f.disliked?EVIDENCE.disliked:0;totalPos+=pos;totalNeg+=neg;
   for(const e of entities(s)){
    counts.set(e.key,(counts.get(e.key)||0)+1);
    if(!pos&&!neg)continue;
    const b=beliefs.get(e.key)||{a:0,b:0,type:e.type,value:e.value};b.a+=pos;b.b+=neg;beliefs.set(e.key,b);
   }
  }
  const n=Math.max(catalog.length,1),idf=new Map();
  for(const [k,c] of counts)idf.set(k,clamp(Math.log((n+1)/(c+1))/Math.log(n+1)*2,0.15,1.5));
  // Older theta models were fitted from inferred skips; ignore that evidence.
  const theta=new Map(model?.evidence_source==='explicit_feedback'?Object.entries(model.entity_theta||{}):[]);
  // Backwards-compatible views used by older callers and tests.
  const view=type=>new Map([...beliefs.values()].filter(b=>b.type===type&&b.a>b.b).map(b=>[b.value,b.a-b.b]));
  const base=clamp((1+totalPos)/(2+totalPos+totalNeg),0.05,0.95);
  return {beliefs,idf,theta,base,series:view('series'),authors:view('author'),tags:view('genre')};
 }
 // Seeded random numbers so exploration is stable within a day instead of reshuffling on every click.
 function rng(seed){let h=1779033703^seed.length;for(let i=0;i<seed.length;i++){h=Math.imul(h^seed.charCodeAt(i),3432918353);h=h<<13|h>>>19;}
  return ()=>{h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);h^=h>>>16;return (h>>>0)/4294967296;};}
 function gamma(k,rand){if(k<1)return gamma(k+1,rand)*Math.pow(rand(),1/k);const d=k-1/3,c=1/Math.sqrt(9*d);
  for(;;){let x,v;do{const u1=rand()||1e-12,u2=rand();x=Math.sqrt(-2*Math.log(u1))*Math.cos(2*Math.PI*u2);v=1+c*x;}while(v<=0);
   v=v*v*v;const u=rand();if(u<1-0.0331*x**4||Math.log(u)<0.5*x*x+d*(1-v+Math.log(v)))return d*v;}}
 function betaSample(a,b,rand){const x=gamma(a,rand),y=gamma(b,rand);return x/(x+y);}
 function evaluate(s,p,feedback,options={}){
  const f=feedback[s.video_id]||{},rand=options.explore?rng(String(options.seed||'')+'|'+s.video_id):null;
  let content=0;const matches=[];
  for(const e of entities(s)){
   const b=p.beliefs?.get(e.key),t=p.theta?.get(e.key)||0;let term=0,mean=0.5,evidence=0;
   if(b){const base=p.base??0.5,a0=PRIOR_STRENGTH*base,b0=PRIOR_STRENGTH*(1-base);evidence=b.a+b.b;
    mean=rand?betaSample(a0+b.a,b0+b.b,rand):(a0+b.a)/(a0+b0+b.a+b.b);term=TYPE_WEIGHT[e.type]*(p.idf?.get(e.key)??1)*(logit(clamp(mean,0.01,0.99))-logit(base));}
   term+=THETA_WEIGHT*t;content+=term;
   if(term)matches.push({...e,term,evidence,mean});
  }
  // Only v2 return/recency models are supported. Gap-derived legacy scores are ignored.
  const hasExplicit=s.confirmed_favorite||f.liked||f.saved||f.disliked;
  const behavior=!hasExplicit&&s.behavior?.inference_version===2?clamp(s.behavior.behavior_logit||0,-0.25,0.25):0;
  const explicit=(f.liked?EXPLICIT_LOGIT.liked:0)+(f.saved?EXPLICIT_LOGIT.saved:0);
  const z=content+behavior+explicit;
  const probability=f.disliked?Math.min(sigmoid(z),0.05):s.confirmed_favorite?Math.max(sigmoid(z),0.95):f.liked?Math.max(sigmoid(z),0.85):sigmoid(z);
  matches.sort((a,b)=>b.term-a.term);const top=matches[0];
  const strong=top&&top.evidence>=STRONG_EVIDENCE;
  let reason;
  if(f.disliked)reason='You marked this story not for you.';
  else if(s.confirmed_favorite)reason='From your YouTube history.';
  else if(f.liked)reason='You asked for more like this.';
  else if(behavior>0&&behavior>=(top?.term||0))reason='Your history records openings on '+s.behavior.return_days+' different days. This is a weak interest signal.';
  else if(top&&top.term>0&&probability<0.5)reason='Mixed match: you like '+top.value+', but other signals for this story are weaker.';
  else if(top&&top.term>0)reason=(strong?'Strong match: ':'Worth a try: ')+(top.type==='author'?'you enjoy stories by ':'you like ')+top.value+(strong?'.':', and we are still learning your taste here.');
  else reason='A different story to explore beyond your usual matches.';
  if(f.heard)reason+=' You marked it already heard, so it appears after unheard choices.';
  return {score:probability,logit:z,probability,reason,confidence:strong?'strong':'learning',matches};
 }
 function rank(items,p,feedback,options={}){
  const scored=items.map(s=>({s,score:evaluate(s,p,feedback,options).score,heard:Number(!!feedback[s.video_id]?.heard)}));
  scored.sort((a,b)=>a.heard-b.heard||b.score-a.score||a.s.title.localeCompare(b.s.title));
  return options.diversify?diversify(scored.map(x=>x.s)):scored.map(x=>x.s);
 }
 // Light diversity: avoid two stories from the same series back to back near the top.
 function diversify(list){const out=[],rest=[...list];
  while(rest.length){const last=out[out.length-1],i=last?rest.findIndex(s=>!(s.series||[]).some(x=>(last.series||[]).includes(x))):0;out.push(rest.splice(i<0?0:i,1)[0]);}
  return out;}
 function similar(seed,items,feedback){
  const tags=seed.title_keyword_tags||[];
  return items.filter(s=>s.video_id!==seed.video_id&&!feedback[s.video_id]?.disliked).map(s=>{
   const shared=(s.title_keyword_tags||[]).filter(t=>tags.includes(t));
   const series=(s.series||[]).filter(t=>(seed.series||[]).includes(t));
   const authors=(s.authors||[]).filter(t=>(seed.authors||[]).includes(t));
   const specific=shared.filter(t=>t!=='suspense');
   const score=specific.length*20+shared.filter(t=>t==='suspense').length+series.length*5+authors.length*3;
   return {story:s,score,shared,series,authors};
  }).filter(x=>x.shared.length>0).sort((a,b)=>Number(!!feedback[a.story.video_id]?.heard)-Number(!!feedback[b.story.video_id]?.heard)||b.score-a.score||a.story.title.localeCompare(b.story.title));
 }
 const api={enrich,profile,evaluate,rank,similar,betaSample,rng};root.StoryRecommendations=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
