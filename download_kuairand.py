"""Download and verify KuaiRand-1K; extract only the four benchmark inputs."""
from pathlib import Path
import concurrent.futures,hashlib,shutil,tarfile,time,urllib.request
ROOT=Path(__file__).resolve().parent/'research/kuairand'
URL='https://zenodo.org/records/10439422/files/KuaiRand-1K.tar.gz?download=1'
SIZE=1135436720
MD5='6b0b9c8222d67fcd4c676218edca3f1f'
CHUNK=16*1024*1024
FILES={'user_features_1k.csv','video_features_basic_1k.csv','log_standard_4_08_to_4_21_1k.csv','log_standard_4_22_to_5_08_1k.csv'}

def checksum(path):
 h=hashlib.md5()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def main():
 ROOT.mkdir(parents=True,exist_ok=True);parts=ROOT/'download-parts';parts.mkdir(exist_ok=True)
 archive=ROOT/'KuaiRand-1K.tar.gz'
 if not archive.exists() or archive.stat().st_size!=SIZE:
  def fetch(i):
   start=i*CHUNK;end=min(SIZE,start+CHUNK)-1;target=parts/f'{i:03}.part'
   if target.exists() and target.stat().st_size==end-start+1:return
   for attempt in range(4):
    try:
     offset=target.stat().st_size if target.exists() else 0
     if offset==end-start+1:return
     if offset>end-start+1:raise ValueError('Oversized partial segment')
     resume=start+offset
     request=urllib.request.Request(URL+f'&transfer={time.time_ns()}&segment={i}',headers={'Range':f'bytes={resume}-{end}'})
     with urllib.request.urlopen(request,timeout=60) as response:
      if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {resume}-{end}/{SIZE}':raise ValueError('Range not honored')
      with target.open('ab') as f:shutil.copyfileobj(response,f,256*1024)
     if target.stat().st_size!=end-start+1:raise ValueError('Incomplete range')
     return
    except Exception as error:
     print(f'Retrying segment {i}: {type(error).__name__}',flush=True)
     if attempt==3:raise
     time.sleep(2*(attempt+1))
  n=(SIZE+CHUNK-1)//CHUNK
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   for i,_ in enumerate(pool.map(fetch,range(n)),1):
    if i%4==0 or i==n:print(f'Downloaded {i}/{n} chunks',flush=True)
  with archive.open('wb') as dest:
   for i in range(n):
    with (parts/f'{i:03}.part').open('rb') as source:shutil.copyfileobj(source,dest,4*1024*1024)
 if checksum(archive)!=MD5:raise ValueError('Archive checksum mismatch; do not use this data')
 print('Official archive MD5 verified.',flush=True)
 data=ROOT/'KuaiRand-1K/data';data.mkdir(parents=True,exist_ok=True)
 found=set()
 with tarfile.open(archive,'r|gz') as tar:
  for member in tar:
   name=Path(member.name).name
   if name not in FILES or member.name!='KuaiRand-1K/data/'+name:continue
   if not member.isfile():raise ValueError('Unexpected archive member')
   target=data/name
   if not target.exists() or target.stat().st_size!=member.size:
    with tar.extractfile(member) as source,target.open('wb') as dest:shutil.copyfileobj(source,dest,4*1024*1024)
    print('Extracted:',name,flush=True)
   found.add(name)
   if found==FILES:break
 if found!=FILES:raise ValueError('Archive is missing benchmark inputs')
 print('Benchmark files ready:',data,flush=True)
if __name__=='__main__':main()
