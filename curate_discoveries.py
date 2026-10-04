"""Read first-page metadata from public official YouTube playlists; no media download."""
import json,re,urllib.request
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from datetime import datetime,timezone
R=Path(__file__).parent
PLAYLISTS=['PLq71IJk8mCV7wu6haZBFgoCauLDYPyMZX','PLq71IJk8mCV5z1vvLnRcQSLKJnAuwmohf']
def walk(node):
 if isinstance(node,dict):
  if 'playlistVideoRenderer' in node: yield node['playlistVideoRenderer']
  v=node.get('lockupViewModel',{})
  if v.get('contentType')=='LOCKUP_CONTENT_TYPE_VIDEO':
   meta=v.get('metadata',{}).get('lockupMetadataViewModel',{})
   rows=meta.get('metadata',{}).get('contentMetadataViewModel',{}).get('metadataRows',[])
   channel=rows[0]['metadataParts'][0]['text']['content'] if rows else ''
   overlays=v.get('contentImage',{}).get('thumbnailViewModel',{}).get('overlays',[])
   badges=[b for o in overlays for b in o.get('thumbnailBottomOverlayViewModel',{}).get('badges',[])]
   length=next((b['thumbnailBadgeViewModel'].get('text','') for b in badges if 'thumbnailBadgeViewModel' in b),'')
   yield {'videoId':v.get('contentId',''),'title':{'simpleText':meta.get('title',{}).get('content','')},'shortBylineText':{'simpleText':channel},'lengthText':{'simpleText':length}}
  for value in node.values():yield from walk(value)
 elif isinstance(node,list):
  for value in node:yield from walk(value)
def text(node):return node.get('simpleText') or ''.join(x.get('text','') for x in node.get('runs',[]))
def metadata(playlist):
 url='https://www.youtube.com/playlist?list='+playlist
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 html=urllib.request.urlopen(req,timeout=25).read().decode('utf-8')
 match=re.search(r'var ytInitialData = (.*?);</script>',html)
 if not match:raise RuntimeError('No playlist metadata; use manual curation or YouTube API instead.')
 for v in walk(json.loads(match.group(1))):
  title=text(v.get('title',{}));channel=text(v.get('shortBylineText',{}))
  if channel!='Mirchi Bangla':continue
  length=text(v.get('lengthText',{}));duration=None
  if re.fullmatch(r'\d+(?::\d{2}){1,2}',length):
   sec=0
   for part in length.split(':'):sec=sec*60+int(part)
   duration=sec/60
  yield {'video_id':v['videoId'],'title':title,'channel':channel,'duration_minutes':duration,'metadata_source':url,'metadata_checked_at':datetime.now(timezone.utc).isoformat()}
history=R/'history/Takeout/YouTube and YouTube Music/history/watch-history.json'
seen={parse_qs(urlparse(x.get('titleUrl','')).query).get('v',[''])[0] for x in json.loads(history.read_text(encoding='utf-8'))}
all_records={}
for playlist in PLAYLISTS:
 for record in metadata(playlist):all_records[record['video_id']]=record
# Exclude mixed compilations containing a story already present in the seed.
# ID absence alone cannot make a reupload or a compilation a fresh story.
new=[x for x in all_records.values() if x['video_id'] not in seen and not re.search(r'uposanghar\s*[-–]|achin pakhi\s*[-–]',x['title'],re.I)]
# Public catalog does not contain favorites, timestamps, history membership or feedback.
public=list(all_records.values())
if not new:raise RuntimeError('No unseen records found; existing catalog files were not replaced.')
(R/'website/dist/discovery-catalog.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'research/discovery-candidates.json').write_text(json.dumps(new[:20],ensure_ascii=False,indent=2),encoding='utf-8')
print('Public curated records:',len(public),'Unseen IDs in supplied export:',len(new),'Selected:',min(20,len(new)))
for x in new[:20]:print(x['video_id'],x['title'])
