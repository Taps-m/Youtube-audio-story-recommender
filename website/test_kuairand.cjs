// Calls the production scorer; no translated or substitute model.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const engine=require('./dist/recommendations.js');
const input=process.argv[2]||'research/kuairand/test/prepared.json';
const data=JSON.parse(fs.readFileSync(input,'utf8')),videos=data.videos;
const popularity=new Map();
for(const u of data.users)for(const id of u.liked_ids)for(const t of videos[id].title_keyword_tags)popularity.set(t,(popularity.get(t)||0)+1);
const rows=[];
function auc(scores,labels){const pos=scores.filter((_,i)=>labels[i]),neg=scores.filter((_,i)=>!labels[i]);let wins=0;for(const p of pos)for(const n of neg)wins+=p>n?1:p===n?.5:0;return wins/(pos.length*neg.length);}
// Count expected hits within score ties so CSV row order cannot inflate Recall@10.
function recall(scores,labels){
 const groups=new Map();scores.forEach((s,i)=>{const g=groups.get(s)||{count:0,positive:0};g.count++;g.positive+=Number(labels[i]);groups.set(s,g);});
 let slots=10,hits=0;
 for(const [,g] of [...groups].sort((a,b)=>b[0]-a[0])){const take=Math.min(slots,g.count);hits+=take*g.positive/g.count;slots-=take;if(!slots)break;}
 return hits/labels.filter(Boolean).length;
}
for(const u of data.users){
 const liked=new Set(u.liked_ids);assert(u.candidates.every(c=>!liked.has(c.video_id)));
 const feedback=Object.fromEntries(u.liked_ids.map(id=>[id,{liked:true}]));
 const catalog=[...u.liked_ids,...u.candidates.map(c=>c.video_id)].map(id=>videos[id]);
 const profile=engine.profile(catalog,feedback,null);
 const scores=u.candidates.map(c=>engine.evaluate(videos[c.video_id],profile,feedback).score);
 assert(scores.every(Number.isFinite));
 const baseline=u.candidates.map(c=>videos[c.video_id].title_keyword_tags.reduce((sum,t)=>sum+(popularity.get(t)||0),0));
 const labels=u.candidates.map(c=>c.liked);
 rows.push({user_id:u.user_id,model_auc:auc(scores,labels),popularity_auc:auc(baseline,labels),model_recall_at_10:recall(scores,labels),popularity_recall_at_10:recall(baseline,labels),random_expected_recall_at_10:Math.min(10,labels.length)/labels.length});
}
const mean=key=>rows.reduce((sum,r)=>sum+r[key],0)/rows.length;
function interval(value){const random=engine.rng('kuairand-bootstrap-2026'),means=[];for(let i=0;i<2000;i++){let sum=0;for(let j=0;j<rows.length;j++)sum+=value(rows[Math.floor(random()*rows.length)]);means.push(sum/rows.length);}means.sort((a,b)=>a-b);return [means[50],means[1949]];}
const report={...data.metadata,macro_model_auc:mean('model_auc'),macro_popularity_auc:mean('popularity_auc'),random_expected_auc:.5,macro_model_recall_at_10:mean('model_recall_at_10'),macro_popularity_recall_at_10:mean('popularity_recall_at_10'),random_expected_recall_at_10:mean('random_expected_recall_at_10'),limitations:'Base category/creator scorer only; no LLM training, embeddings or LLM reranking. Unliked is not disliked. Sampled candidate metrics cannot validate full-catalog quality or Bengali YouTube stories.'};
report.model_auc_bootstrap_95_interval=interval(r=>r.model_auc);
report.paired_auc_gain_over_popularity=mean('model_auc')-mean('popularity_auc');
report.paired_auc_gain_bootstrap_95_interval=interval(r=>r.model_auc-r.popularity_auc);
fs.writeFileSync(path.join(path.dirname(input),'results.json'),JSON.stringify({report,users:rows},null,2));console.log(JSON.stringify(report,null,2));
