const assert=require('node:assert/strict');
const e=require('./dist/recommendations.js');
const favorite=e.enrich({video_id:'favorite001',title:'Sunday Suspense | Byomkesh | Saradindu Bandyopadhyay',confirmed_favorite:true,channel:'Mirchi Bangla'});
const related=e.enrich({video_id:'related0001',title:'Byomkesh | Saradindu Bandyopadhyay',channel:'Mirchi Bangla'});
const generic=e.enrich({video_id:'generic0001',title:'A suspense story',channel:'Other'});
const plain=e.enrich({video_id:'plain000001',title:'Sunday Suspense | A literary story'});
const shonku=e.enrich({video_id:'shonku00001',title:'Prof Shonku O Moru Rahasya'});
const unrelated=e.enrich({video_id:'other000001',title:'Romantic Premer Golpo',channel:'Kahon'});
const score=(s,p,f={},o)=>e.evaluate(s,p,f,o).score;

// Tagging
assert(!plain.title_keyword_tags.includes('suspense'),'Show branding must not become a genre');
assert(shonku.title_keyword_tags.includes('science fiction'));
assert(shonku.authors.includes('Satyajit Ray'));
const romanceAuthor=e.enrich({video_id:'author00001',title:'Biswa Mitra Upakhyan | Abhik Arjun Dutta | Romantic Premer Golpo'});
assert(!romanceAuthor.series.includes('Arjun'));
assert(!romanceAuthor.authors.includes('Samaresh Majumdar'));
assert(!romanceAuthor.title_keyword_tags.includes('detective mystery'));
const arjun=e.enrich({video_id:'arjun000001',title:'Arjun | Hishebe Bhul Chhilo | Samaresh Majumdar'});
assert(arjun.series.includes('Arjun'));
assert(e.enrich({title:'অর্জুন | একটি গল্প'}).series.includes('Arjun'));

// Favorites shape taste without any click
const catalog=[favorite,related,generic,unrelated];
let p=e.profile(catalog,{});
assert(p.beliefs.get('series:Byomkesh').a===3,'Confirmed favorite adds 3 units of evidence');
assert(score(related,p)>score(generic,p),'Series match beats a generic story');
assert(score(related,p)>score(unrelated,p));
assert.match(e.evaluate(related,p,{}).reason,/you like Byomkesh/);
for(const s of catalog){const x=score(s,p);assert(x>0&&x<1,'Scores are probabilities');}
assert(score(favorite,p)>=0.95,'Confirmed favorites stay near certain');

// Explicit feedback
assert(score(related,p,{related0001:{saved:true}})>score(related,p),'Save raises probability');
const liked=e.profile(catalog,{other000001:{liked:true}});
assert(score(unrelated,liked,{other000001:{liked:true}})>score(unrelated,p),'Like raises probability');
assert.equal(e.rank([related,unrelated],p,{related0001:{heard:true}})[1].video_id,related.video_id,'Heard stories go below unheard choices');

// Hiding a favorite turns its evidence negative instead of positive
const hidden=e.profile(catalog,{favorite001:{disliked:true}});
assert(hidden.beliefs.get('series:Byomkesh').b>hidden.beliefs.get('series:Byomkesh').a);
assert(score(related,hidden)<score(related,p),'Hidden favorite stops boosting its series');
assert(score(related,hidden)<0.5,'Hidden favorite pushes its series below neutral');

// Common genres count less than rare ones (inverse document frequency)
const many=Array.from({length:20},(_,i)=>e.enrich({video_id:'common'+String(i).padStart(5,'0'),title:'A thriller story '+i}));
const rare=e.enrich({video_id:'rarehorror1',title:'A horror story',channel:'X'});
const idfP=e.profile([...many,rare],{});
assert(idfP.idf.get('genre:horror')>idfP.idf.get('genre:suspense'),'Rare genre gets higher weight');

// Behavior from listening history (fit_preferences.py) separates stories with equal content
const a={...related,video_id:'behavior001',behavior:{inference_version:2,behavior_logit:0.2,return_days:6}};
const b={...related,video_id:'behavior002',behavior:{inference_version:2,behavior_logit:-0.2,return_days:1}};
assert.equal(e.rank([b,a],p,{})[0].video_id,'behavior001','Returning on many days ranks higher');
assert.match(e.evaluate({...generic,behavior:{inference_version:2,behavior_logit:0.2,return_days:7}},p,{}).reason,/openings on 7 different days/);
const withDays=e.profile([{...favorite,confirmed_favorite:false,behavior:{return_days:10}}],{});
assert(Math.abs(withDays.beliefs.get('series:Byomkesh').a-0.5)<1e-9,'Return-day evidence is weak and capped');

const weak={...related,video_id:'weakstory01',behavior:{behavior_logit:-6,return_days:1}};
assert.equal(score(weak,p),score({...weak,behavior:undefined},p),'Legacy gap-derived model scores are ignored');
const likedWeak={...weak,behavior:{inference_version:2,behavior_logit:-100,return_days:30,skipped:100}};
assert(score(likedWeak,p,{weakstory01:{liked:true}})>=0.85,'Direct likes override inferred negative behavior');
assert.equal(score(likedWeak,p,{weakstory01:{liked:true}}),score({...likedWeak,behavior:undefined},p,{weakstory01:{liked:true}}));
const dislikedReturns={...favorite,behavior:{inference_version:2,return_days:500,behavior_logit:100}};
const negative=e.profile([dislikedReturns],{favorite001:{disliked:true,saved:true,liked:true}});
assert.equal(negative.beliefs.get('series:Byomkesh').a,0,'Dislike eliminates positive history and stale saved evidence');
assert.equal(negative.beliefs.get('series:Byomkesh').b,2);
assert(score(dislikedReturns,negative,{favorite001:{disliked:true}})<=0.05);
const skipOnly=e.profile([{...related,behavior:{skipped:100}}],{});
assert.equal(skipOnly.beliefs.size,0,'Inferred skips must not become dislikes');

// Head-to-head (Bradley-Terry) scores from the offline model shift attributes
const theta=e.profile(catalog,{},{evidence_source:'explicit_feedback',entity_theta:{'channel:Kahon':-1.5}});
assert(score(unrelated,theta)<score(unrelated,p),'Negative head-to-head score lowers probability');
assert.equal(score(unrelated,e.profile(catalog,{},{entity_theta:{'channel:Kahon':-100}})),score(unrelated,p),'Legacy skip-pair entity scores are ignored');

// Thompson sampling: deterministic for a seed, varies across seeds, Beta sampler is sane
const o1={explore:true,seed:'2026-10-05'};
assert.equal(score(related,p,{},o1),score(related,p,{},o1),'Same day gives the same sample');
const samples=new Set(['a','b','c','d','e'].map(seed=>score(related,p,{},{explore:true,seed})));
assert(samples.size>1,'Different days explore differently');
const r=e.rng('beta-check');let m=0;for(let i=0;i<4000;i++)m+=e.betaSample(4,2,r);m/=4000;
assert(Math.abs(m-4/6)<0.02,'Beta(4,2) sample mean is about 0.667, got '+m.toFixed(3));

// Diversity keeps the same series from stacking back to back
const s2={...related,video_id:'related0002'},s3={...unrelated,video_id:'other000002'};
const div=e.rank([related,s2,s3],p,{},{diversify:true});
assert.notDeepEqual(div[0].series,div[1].series,'Second slot goes to a different series');

// Stage 1 plot/mood embedding term
const plain2=(id,extra={})=>({...e.enrich({video_id:id,title:'Story '+id,channel:'C'}),...extra});
const lovedN=plain2('lovednb0001',{confirmed_favorite:true}),hatedN=plain2('hatednb0001');
const near=(ids)=>ids.map(([id,cos,title])=>({id,cos,title:title||id}));
const candA=plain2('candidate01',{neighbors:near([['lovednb0001',0.9,'Sunday Suspense | Rakter Daag | x']]),neighbor_baseline:0.6});
const candB=plain2('candidate02',{neighbors:near([['hatednb0001',0.9]]),neighbor_baseline:0.6});
const candC=plain2('candidate03');
const embCat=[lovedN,hatedN,candA,candB,candC];
const ep=e.profile(embCat,{hatednb0001:{disliked:true}},{model:{weights:{embedding:1},r_mean:0}});
const ev=s=>e.evaluate(s,ep,{hatednb0001:{disliked:true}});
assert(ev(candA).embedding>0,'Neighbor of a loved story gets a positive plot/mood term');
assert(ev(candB).embedding<0,'Neighbor of a disliked story gets a negative term');
assert.equal(ev(candC).embedding,0,'No neighbors means no embedding term');
assert(ev(candA).score>ev(candC).score&&ev(candC).score>ev(candB).score);
assert.equal(ev(candA).reason,'Similar in plot and mood to Rakter Daag.');
const belowBase=plain2('candidate04',{neighbors:near([['lovednb0001',0.5]]),neighbor_baseline:0.6});
assert.equal(ev(belowBase).embedding,0,'Similarity below the baseline carries no weight');
const offCatalog=plain2('candidate05',{neighbors:[{id:'notincat001',cos:0.9,return_days:50,title:'x'}],neighbor_baseline:0.6});
const offTerm=ev(offCatalog).embedding;assert(offTerm>0&&offTerm<=0.25+1e-9,'Opened-only neighbors count at most 0.25');
const gamma0=e.profile(embCat,{},{model:{weights:{embedding:0}}});
assert.equal(e.evaluate(candA,gamma0,{}).embedding,0,'A fitted gamma of 0 switches the term off');
const liveLike=e.profile(embCat,{candidate03:{liked:true}},{});
const cD=plain2('candidate06',{neighbors:near([['candidate03',0.9]]),neighbor_baseline:0.6});
assert(e.evaluate(cD,liveLike,{candidate03:{liked:true}}).embedding>e.evaluate(cD,e.profile(embCat,{},{}),{}).embedding,'A new like updates neighbors immediately');

// Stage 2 LLM rerank: only the top candidates, only with offline scores
const twin=(id,llm)=>plain2(id,llm?{llm}:{});
const hi=twin('llmzhigh001',{score:0.95,reason:'Atmospheric hill-station mystery like Feluda.'}),lo=twin('llmlow00001',{score:0.05,reason:'x'});
const lp=e.profile([hi,lo],{},{});
assert.equal(e.rank([lo,hi],lp,{})[0].video_id,'llmzhigh001','LLM score lifts a story Stage 1 placed second');
assert.equal(e.rank([lo,hi],lp,{},{stage2:false})[0].video_id,'llmlow00001','stage2:false keeps Stage 1 order');
assert.equal(e.evaluate(hi,lp,{}).llm,0,'Card probabilities stay Stage 1 unless stage2 is requested');
assert(e.evaluate(hi,lp,{},{stage2:true}).score>e.evaluate(hi,lp,{}).score);
assert.match(e.evaluate(hi,lp,{}).reason,/^AI-reviewed: Atmospheric/);
const many2=Array.from({length:25},(_,i)=>twin('fill'+String(i).padStart(7,'0')));
const tail=twin('zzzzlast001',{score:0.98,reason:'y'});
const pp=e.profile([...many2,tail],{},{});
assert.equal(e.rank([...many2,tail],pp,{}).at(-1).video_id,'zzzzlast001','Candidates outside the top 20 are not lifted by the LLM');
const heardHi={...hi,video_id:'llmheard001'};
assert.equal(e.rank([heardHi,lo],lp,{llmheard001:{heard:true}})[0].video_id,'llmlow00001','Heard stories stay after unheard ones');

console.log('Passed tagging, probability scoring, feedback overrides, IDF, behavior, head-to-head, Thompson sampling and diversity, plot/mood embedding and LLM rerank checks.');
