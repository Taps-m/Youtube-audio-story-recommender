"""Temporal KuaiRand-1K adapter for the existing browser recommendation scorer."""
import argparse,json
from pathlib import Path
from collections import Counter
import pandas as pd

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--out',default='research/kuairand/test');parser.add_argument('--users',type=int,default=100);args=parser.parse_args()
 root=Path(args.data);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 users=pd.read_csv(root/'user_features_1k.csv')['user_id'].sample(n=args.users,random_state=2026).tolist()
 def read(name):
  parts=[]
  for chunk in pd.read_csv(root/name,usecols=['user_id','video_id','is_like','time_ms'],chunksize=200000):parts.append(chunk[chunk.user_id.isin(users)])
  frame=pd.concat(parts,ignore_index=True).dropna()
  return frame[frame.is_like.isin([0,1])].sort_values('time_ms')
 train=read('log_standard_4_08_to_4_21_1k.csv');test=read('log_standard_4_22_to_5_08_1k.csv')
 # Real logs have a small timestamp overlap despite their non-overlapping date labels.
 # Derive the cutoff from training alone and discard earlier test events.
 cutoff=int(train.time_ms.max())+1
 overlap=int((test.time_ms<cutoff).sum());test=test[test.time_ms>=cutoff].copy()
 assert not test.empty and train.time_ms.max()<test.time_ms.min(),'No strictly later test events'
 # Exclude every earlier exposure, not only earlier likes, from test candidates.
 liked=train[train.is_like==1].drop_duplicates(['user_id','video_id'])
 prepared=[];needed=set(liked.video_id.astype(int));excluded=Counter()
 for user in users:
  history=train[train.user_id==user];positives=liked[liked.user_id==user]
  if positives.empty:excluded['no_training_likes']+=1;continue
  later=test[(test.user_id==user)&~test.video_id.isin(history.video_id)]
  # Positive if any later observation records a like; absence of like is not dislike.
  later=later.groupby('video_id',as_index=False).agg(is_like=('is_like','max'))
  yes=later[later.is_like==1];no=later[later.is_like==0]
  if yes.empty or no.empty:excluded['no_evaluable_test_pair']+=1;continue
  seed=2026+int(user)
  candidates=pd.concat([yes.sample(n=min(20,len(yes)),random_state=seed),no.sample(n=min(20,len(no)),random_state=seed)])
  needed.update(candidates.video_id.astype(int))
  prepared.append({'user_id':str(user),'liked_ids':[str(int(v)) for v in positives.video_id],'candidates':[{'video_id':str(int(r.video_id)),'liked':bool(r.is_like)} for r in candidates.itertuples()]})
 metadata={}
 for chunk in pd.read_csv(root/'video_features_basic_1k.csv',usecols=['video_id','author_id','tag'],chunksize=200000):
  for row in chunk[chunk.video_id.isin(needed)].itertuples():
   tags=[] if pd.isna(row.tag) else ['category:'+t.strip() for t in str(row.tag).split(',') if t.strip() not in {'','-1','UNKNOWN'}]
   authors=[] if pd.isna(row.author_id) or row.author_id<0 else ['creator:'+str(int(row.author_id))]
   metadata[str(int(row.video_id))]={'video_id':str(int(row.video_id)),'title':'Video '+str(int(row.video_id)),'title_keyword_tags':tags,'authors':authors,'series':[]}
 missing=needed-{int(v) for v in metadata}
 if missing:raise ValueError(f'Missing basic metadata for {len(missing)} videos')
 report={'source':'KuaiRand-1K, Kuaishou; CC BY-SA 4.0; Gao et al., CIKM 2022','requested_users':args.users,'training_users':int(train.user_id.nunique()),'training_interactions':len(train),'training_like_events':len(train[train.is_like==1]),'test_timestamp_cutoff_ms':cutoff,'overlapping_test_events_excluded':overlap,'evaluated_users':len(prepared),'excluded_users':dict(excluded),'selection_seed':2026,'candidate_protocol':'Per-user up to 20 later liked and 20 later unliked videos; exclude all videos exposed in training. Test feedback is hidden from scoring. Cohort requires both labels. This balanced sampled pool is not the full catalog.'}
 if not prepared:raise ValueError('No evaluable users')
 (out/'prepared.json').write_text(json.dumps({'metadata':report,'videos':metadata,'users':prepared}),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
