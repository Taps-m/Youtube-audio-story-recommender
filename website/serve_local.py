"""Loopback-only server; personal test data lives outside the public directory."""
import argparse,json
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
ROOT=Path(__file__).resolve().parent
PRIVATE=ROOT.parent/'research/local-page-catalog.json'
SIGNALS=ROOT.parent/'research/behavior-signals.json'
def signals():
 try:return json.loads(SIGNALS.read_text(encoding='utf-8'))
 except (OSError,ValueError):return {}
def private_catalog():
 rows=json.loads(PRIVATE.read_text(encoding='utf-8'));stories=signals().get('stories',{})
 for row in rows:
  if row.get('video_id') in stories:row['behavior']=stories[row['video_id']]
 return rows
class Handler(SimpleHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Cache-Control','no-store')
  super().end_headers()
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
 def send_json(self,value):
  data=json.dumps(value,ensure_ascii=False).encode('utf-8');self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if self.path.split('?')[0]=='/__private/catalog':
   if not PRIVATE.exists():self.send_error(404,'Local catalog not prepared');return
   self.send_json(private_catalog());return
  if self.path.split('?')[0]=='/__private/model':
   data=signals()
   if not data:self.send_error(404,'Run fit_preferences.py first');return
   self.send_json({'model':data.get('model',{}),'entity_theta':data.get('entity_theta',{})});return
  if self.path.split('?')[0].startswith('/__private/') or self.path.split('?')[0] in ['/catalog.js','/local-test-catalog.json']:
   self.send_error(404);return
  super().do_GET()
parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8081);args=parser.parse_args()
print(f'Local preview http://127.0.0.1:{args.port}',flush=True)
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
