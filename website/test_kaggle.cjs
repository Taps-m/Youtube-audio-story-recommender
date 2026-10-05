// Synthetic category-only benchmark of the current base preference scorer.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const engine=require('./dist/recommendations.js');
const dir=path.join(__dirname,'../research/kaggle');
const data=JSON.parse(fs.readFileSync(path.join(dir,'users-100.json'),'utf8'));
assert.equal(data.users.length,100);
const popularity=new Map();
for(const u of data.users)for(const r of u.train)if(r.liked)popularity.set(r.category,(popularity.get(r.category)||0)+1);
let modelWins=0,baselineWins=0,ties=0;
const story=r=>({video_id:r.video_id,title:r.video_id,title_keyword_tags:[r.category],series:[],authors:[]});
for(const u of data.users){
 const ids=new Set(u.train.map(r=>r.video_id));assert(u.test.every(r=>!ids.has(r.video_id)));
 const feedback=Object.fromEntries(u.train.filter(r=>r.liked).map(r=>[r.video_id,{liked:true}]));
 const catalog=[...u.train,...u.test].map(story),profile=engine.profile(catalog,feedback,null);
 const [positive,negative]=u.test;assert(positive.liked&&!negative.liked);
 const a=engine.evaluate(story(positive),profile,feedback).probability,b=engine.evaluate(story(negative),profile,feedback).probability;
 assert(Number.isFinite(a)&&Number.isFinite(b));
 if(a===b)ties++;modelWins+=a>b?1:a===b?.5:0;
 const pa=popularity.get(positive.category)||0,pb=popularity.get(negative.category)||0;baselineWins+=pa>pb?1:pa===pb?.5:0;
}
const report={synthetic:true,users:100,held_out_pairs:100,model_pair_accuracy:modelWins/100,popularity_pair_accuracy:baselineWins/100,random_expected_accuracy:.5,model_ties:ties,limitations:'Category-only random holdout; no descriptions, real YouTube IDs, explicit dislikes, embeddings or LLM reranking. Unliked does not mean disliked. No evidence of real-world recommendation quality.'};
fs.writeFileSync(path.join(dir,'evaluation-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
