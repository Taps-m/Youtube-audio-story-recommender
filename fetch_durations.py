"""Fetch duration metadata from public YouTube watch pages without downloading media."""
import json,re,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
ROOT=Path(__file__).parent
CACHE=ROOT/'research/duration-cache.json'
def fetch(video_id):
 url='https://www.youtube.com/watch?v='+video_id
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  html=urllib.request.urlopen(req,timeout=25).read().decode('utf-8')
  match=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',html)
  if not match:raise ValueError('No public player metadata')
  player,_=json.JSONDecoder().raw_decode(html[match.end():])
  details=player.get('videoDetails',{})
  if details.get('videoId')!=video_id or details.get('isLiveContent'):raise ValueError('Unavailable or live content')
  seconds=int(details.get('lengthSeconds',0))
  if seconds<=0:raise ValueError('No positive duration')
  return video_id,{'duration_minutes':seconds/60,'source':url,'checked_at':datetime.now(timezone.utc).isoformat()},None
 except Exception as error:return video_id,None,str(error)
def main():
 cache=json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}
 paths=[ROOT/'research/local-page-catalog.json',ROOT/'website/dist/discovery-catalog.json']
 rows=[s for p in paths if p.exists() for s in json.loads(p.read_text(encoding='utf-8'))]
 missing=sorted({s['video_id'] for s in rows if not s.get('duration_minutes') and s['video_id'] not in cache})
 with ThreadPoolExecutor(max_workers=4) as pool:
  for vid,data,error in pool.map(fetch,missing):
   if data:cache[vid]=data
   else:print('Unresolved:',vid,error)
 CACHE.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
 for path in paths:
  if not path.exists():continue
  data=json.loads(path.read_text(encoding='utf-8'))
  for record in data:
   entry=cache.get(record['video_id'])
   if entry and not record.get('duration_minutes'):record['duration_minutes']=entry['duration_minutes']
  path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Requested:',len(missing),'Cached verified durations:',len(cache))
if __name__=='__main__':main()
