"""Prepare 100 synthetic users with held-out positive/negative video pairs."""
import csv,io,json,random,urllib.request,zipfile
from pathlib import Path
from collections import defaultdict,Counter

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'research/kaggle'
URL='https://www.kaggle.com/api/v1/datasets/download/iitanshravan/youtube-recommendation-data-for-cleaning-and-ml'

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 archive=OUT/'source.zip'
 if not archive.exists():
  print('Downloading public synthetic dataset...',flush=True)
  with urllib.request.urlopen(URL,timeout=90) as response:archive.write_bytes(response.read())
 groups=defaultdict(dict);counts=Counter()
 with zipfile.ZipFile(archive) as zipped:
  name=next(n for n in zipped.namelist() if n.endswith('.csv'))
  for row in csv.DictReader(io.TextIOWrapper(zipped.open(name),encoding='utf-8-sig')):
   counts['source_rows']+=1
   user=row.get('user_id','').strip();video=row.get('video_id','').strip();category=row.get('category','').strip()
   liked={'0':False,'1':True,'yes':True,'no':False}.get(row.get('liked','').strip().lower())
   if not user.isdigit() or not video or video.lower() in {'null','nan'} or not category or category.lower() in {'null','nan'} or liked is None:
    counts['invalid_rows']+=1;continue
   if video in groups[user]:counts['duplicate_user_video_rows']+=1;continue
   groups[user][video]={'video_id':video,'category':category,'liked':liked}
 eligible=[]
 for user,records in groups.items():
  rows=list(records.values())
  if len(rows)>=8 and sum(r['liked'] for r in rows)>=3 and sum(not r['liked'] for r in rows)>=3:eligible.append(user)
 if len(eligible)<100:raise ValueError('Not enough eligible users')
 selected=random.Random(2026).sample(sorted(eligible),100);users=[]
 for user in selected:
  rows=list(groups[user].values());rng=random.Random('2026:'+user)
  positive=rng.choice([r for r in rows if r['liked']]);negative=rng.choice([r for r in rows if not r['liked']])
  train=[r for r in rows if r['video_id'] not in {positive['video_id'],negative['video_id']}]
  users.append({'user_id':user,'train':train,'test':[positive,negative]})
 report={'source':'https://www.kaggle.com/datasets/iitanshravan/youtube-recommendation-data-for-cleaning-and-ml','synthetic':True,'seed':2026,**counts,'eligible_users':len(eligible),'selected_users':len(users),'train_interactions':sum(len(u['train']) for u in users),'test_interactions':200,'split':'Random held-out liked/unliked pair per user, disjoint video IDs. Unliked is absence of a like, not an explicit dislike.','scope':'Synthetic pipeline benchmark; no real YouTube preference validation or LLM training.'}
 (OUT/'users-100.json').write_text(json.dumps({'metadata':report,'users':users},indent=2),encoding='utf-8')
 (OUT/'preparation-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
