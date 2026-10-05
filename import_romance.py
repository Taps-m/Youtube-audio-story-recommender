"""Import manually reviewed romance picks from official public video metadata."""
import json,re,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parent
PICKS=['IGuYKCiLxc4','piYSiRnd9KA','6sn1U8NZJno','RD9DiE-GqI4']

def main():
    public_path=ROOT/'website/dist/discovery-catalog.json'
    public={r['video_id']:r for r in json.loads(public_path.read_text(encoding='utf-8'))}
    added=[]
    for video_id in PICKS:
        url='https://www.youtube.com/watch?v='+video_id
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        html=urllib.request.urlopen(request,timeout=25).read().decode('utf-8')
        match=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',html)
        if not match:raise ValueError('Missing player metadata: '+video_id)
        player,_=json.JSONDecoder().raw_decode(html[match.end():])
        details=player.get('videoDetails',{})
        if details.get('videoId')!=video_id or details.get('author')!='Mirchi Bangla':raise ValueError('Unexpected video or channel')
        seconds=int(details.get('lengthSeconds',0))
        if seconds<=0 or details.get('isLiveContent'):raise ValueError('Unverified duration')
        record={'video_id':video_id,'title':details['title'],'channel':details['author'],'duration_minutes':seconds/60,'metadata_source':url,'metadata_checked_at':datetime.now(timezone.utc).isoformat()}
        public[video_id]=record;added.append(record)
    history=ROOT/'history/Takeout/YouTube and YouTube Music/history/watch-history.json'
    seen={parse_qs(urlparse(r.get('titleUrl','')).query).get('v',[''])[0] for r in json.loads(history.read_text(encoding='utf-8'))}
    local=[dict(r,eligible_as_new_discovery=r['video_id'] not in seen,history_status='Previously opened' if r['video_id'] in seen else 'Not found in supplied history',confirmed_favorite=False) for r in added]
    public_path.write_text(json.dumps(list(public.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'research/romance-candidates.json').write_text(json.dumps(local,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Verified romance entries:',len(added),'Absent from history:',sum(r['eligible_as_new_discovery'] for r in local))
if __name__=='__main__':main()
