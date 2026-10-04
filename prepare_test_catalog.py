import json,csv,re
from pathlib import Path
R=Path(__file__).parent
research=R/'research'
base=R/'history/Takeout/YouTube and YouTube Music'
prefs=json.loads((research/'confirmed-preferences.json').read_text(encoding='utf-8'))
favorites={x['video_id'] for x in prefs['favorites']}
with (base/'playlists/Watch later-videos.csv').open(encoding='utf-8-sig',newline='') as f:
 saved={x['Video ID'].strip() for x in csv.DictReader(f)}
with (base/'subscriptions/subscriptions.csv').open(encoding='utf-8-sig',newline='') as f:
 subs={x['Channel Title'].strip().casefold() for x in csv.DictReader(f)}
seed=json.loads((research/'test-catalog-seed.json').read_text(encoding='utf-8'))
records=[]
for x in seed:
 vid=x['url'].split('v=')[-1].split('&')[0]
 name=x['title']; tags=[]
 for tag,pat in [('detective mystery',r'byomkesh|ব্যোমকেশ|feluda|ফেলুদা|goyenda'),('horror',r'horror|ভৌতিক|bhuter'),('suspense',r'thriller|suspense'),('science fiction',r'sci.fi|science fiction'),('romance',r'romantic|premer|love story')]:
  if re.search(pat,name,re.I): tags.append(tag)
 records.append({'video_id':vid,'title':name,'channel':x['channel'],'url':x['url'],'history_status':'previously opened','confirmed_favorite':vid in favorites,'saved_watch_later':vid in saved,'subscribed_channel':x['channel'].casefold() in subs,'title_keyword_tags':tags,'tag_source':'title keywords; not AI reviewed','duration_minutes':None,'availability_checked':False,'eligible_as_new_discovery':False})
(research/'working-test-catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
assert len(records)==30
assert sum(x['confirmed_favorite'] for x in records)==3
assert not any(x['eligible_as_new_discovery'] for x in records)
print('Prepared 30 records; all 3 confirmed favorites retained; no opened story classified as new.')
print('Watch later matches:',sum(x['saved_watch_later'] for x in records))
print('Subscribed channel matches:',sum(x['subscribed_channel'] for x in records))
