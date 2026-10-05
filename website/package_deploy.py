"""Validate the entire public directory before packaging a Cloudflare Pages upload."""
from pathlib import Path
import json,zipfile
ROOT=Path(__file__).resolve().parent
ALLOWED={'index.html','about.html','style.css','app.js','recommendations.js','discovery-catalog.json'}
def validate(directory):
 files=[p for p in directory.rglob('*') if p.is_file()]
 if any(p.is_symlink() for p in directory.rglob('*')):raise ValueError('Symlinks are not allowed in deployment.')
 found={p.relative_to(directory).as_posix() for p in files}
 if found!=ALLOWED:raise ValueError('Unexpected or missing deployment files: '+str(found.symmetric_difference(ALLOWED)))
 rows=json.loads((directory/'discovery-catalog.json').read_text(encoding='utf-8'))
 permitted={'video_id','title','channel','duration_minutes','metadata_source','metadata_checked_at'}
 for row in rows:
  if set(row)-permitted:raise ValueError('Personal or unknown catalog fields found.')
 return files
if __name__=='__main__':
 files=validate(ROOT/'dist');out=ROOT/'release';out.mkdir(exist_ok=True)
 with zipfile.ZipFile(out/'cloudflare-pages.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.name)
 print('Validated public-only package:',out/'cloudflare-pages.zip')
