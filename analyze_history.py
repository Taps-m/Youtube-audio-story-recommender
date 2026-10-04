import json,re
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).parent
src=ROOT/'history/Takeout/YouTube and YouTube Music/history'
w=json.loads((src/'watch-history.json').read_text(encoding='utf-8'))
s=json.loads((src/'search-history.json').read_text(encoding='utf-8'))
terms=r'sunday suspense|midnight horror|goyenda|golpo|গল্প|রহস্য|ভৌতিক|feluda|ফেলুদা|byomkesh|ব্যোমকেশ|bengali audio|bangla audio|audio story|audiostory|গোয়েন্দা|গোয়েন্দা|thriller land|romanch|রোমাঞ্চ'
pattern=re.compile(terms,re.I)
def title(x): return re.sub(r'^(Watched|Searched for)\s+','',x.get('title',''))
def channel(x): return (x.get('subtitles') or [{}])[0].get('name','Unknown').strip()
stories=[x for x in w if pattern.search(title(x)+' '+channel(x)) and x.get('titleUrl','').startswith('https://www.youtube.com/watch?')]
strong=re.compile(r'sunday suspense|bengali audio story|bangla audio story|audio story|audiostory|goyenda golpo',re.I)
confirmed=[x for x in stories if strong.search(title(x)) and not re.search(r'short film|trailer|reaction|review',title(x),re.I)]
searches=[x for x in s if pattern.search(title(x))]
counts=Counter(x['titleUrl'] for x in stories)
unique={}
for x in sorted(stories,key=lambda x:x.get('time',''),reverse=True):
 unique.setdefault(x['titleUrl'],{'title':title(x),'url':x['titleUrl'],'channel':channel(x),'last_seen':x.get('time'),'watch_events':counts[x['titleUrl']],'classification':'Keyword candidate; human review needed'})
out=ROOT/'research'; out.mkdir(exist_ok=True)
(out/'story-history-candidates.json').write_text(json.dumps(list(unique.values()),ensure_ascii=False,indent=2),encoding='utf-8')
channels=Counter(channel(x) for x in stories)
q=Counter(title(x).strip() for x in searches)
times=[x['time'] for x in w if x.get('time')]
summary={'watch_events':len(w),'search_events':len(s),'watch_date_range_utc':[min(times),max(times)],'story_candidate_events':len(stories),'unique_story_candidates':len(unique),'story_search_events':len(searches),'top_story_channels':channels.most_common(12),'top_story_searches':q.most_common(15),'repeated_candidates':sorted(unique.values(),key=lambda x:x['watch_events'],reverse=True)[:8],'recent_candidates':list(unique.values())[:10]}
summary['strong_title_match_events']=len(confirmed)
summary['strong_title_match_unique_videos']=len(set(x['titleUrl'] for x in confirmed))
summary['strong_title_match_channels']=Counter(channel(x) for x in confirmed).most_common(8)
seed=[]; seen=set()
for x in sorted(confirmed,key=lambda x:(counts[x['titleUrl']],x.get('time','')),reverse=True):
 if x['titleUrl'] in seen: continue
 seen.add(x['titleUrl']); seed.append(unique[x['titleUrl']])
 if len(seed)==30: break
(out/'test-catalog-seed.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'history-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
