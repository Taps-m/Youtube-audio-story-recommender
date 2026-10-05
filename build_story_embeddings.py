#!/usr/bin/env python3
"""Stage-1 plot/mood similarity: fetch story descriptions and build text embeddings.

Run on your own PC (needs YouTube and Hugging Face access):
    pip install -r requirements-research.txt
    python build_story_embeddings.py            # fetch (cached) + embed + spot-check
    python build_story_embeddings.py --check    # spot-check only

Writes research/story-text.json and research/story-neighbors.json (both git-ignored).
"""
import argparse, json, re, time
from pathlib import Path

ROOT = Path(__file__).parent
R = ROOT / 'research'
TEXT, NEIGH = R / 'story-text.json', R / 'story-neighbors.json'
MODEL = 'intfloat/multilingual-e5-base'   # multilingual, handles Bengali script
K = 10
URLS = re.compile(r'https?://\S+|www\.\S+|[#@]\S+')
NOISE = re.compile(r'subscribe|follow us|facebook|instagram|whatsapp|telegram|copyright|all rights reserved|'
                   r'download|google play|app store|credits?|voice|sound design|music|narrat|presented by|'
                   r'produced by|cast\b|editor|mix(ing)?\b|sponsor|business enquir|email|contact', re.I)

def load(p, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError): return default

def story_ids():
    """Catalog stories plus every history story the behavior model knows about."""
    ids = {}
    for f in [R / 'local-page-catalog.json', ROOT / 'website/dist/discovery-catalog.json']:
        for s in load(f, []): ids.setdefault(s['video_id'], s.get('title', ''))
    for v in load(R / 'behavior-signals.json', {}).get('stories', {}): ids.setdefault(v, '')
    return ids

def story_text(rec):
    """Title + plot-bearing description lines + tags; credits, links and promo lines removed."""
    lines = [URLS.sub('', l).strip() for l in (rec.get('description') or '').splitlines()]
    body = ' '.join(l for l in lines if len(l) > 3 and not NOISE.search(l))[:1200]
    tags = ', '.join((rec.get('tags') or [])[:15])
    return '. '.join(x for x in [rec.get('title', ''), body, tags] if x)

def fetch(ids, extract=None, pause=1.0):
    cache = load(TEXT, {})
    todo = [v for v in ids if v not in cache or cache[v].get('error')]
    if todo and extract is None:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True, 'no_warnings': True})
        extract = lambda v: ydl.extract_info('https://www.youtube.com/watch?v=' + v, download=False)
    for n, v in enumerate(todo, 1):
        try:
            info = extract(v)
            cache[v] = {'title': info.get('title') or ids[v], 'description': info.get('description') or '',
                        'tags': info.get('tags') or [], 'channel': info.get('channel') or '',
                        'duration_minutes': round(info['duration'] / 60, 1) if info.get('duration') else None}
        except Exception as e:  # unavailable, private or region-blocked videos: keep the title, retry next run
            cache[v] = {'title': ids[v], 'description': '', 'tags': [], 'error': str(e)[:200]}
        if n % 10 == 0 or n == len(todo):
            TEXT.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
            print(f'fetched {n}/{len(todo)}', flush=True)
        time.sleep(pause)
    return cache

def embed(cache, encode=None):
    import numpy as np
    vids = [v for v in cache if cache[v].get('title')]
    texts = ['passage: ' + story_text(cache[v]) for v in vids]   # E5 expects the "passage:" prefix
    if encode is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL)
        encode = lambda t: model.encode(t, normalize_embeddings=True, batch_size=16, show_progress_bar=True)
    V = np.asarray(encode(texts), dtype=float)
    V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-12
    S = V @ V.T
    off = S[~np.eye(len(vids), dtype=bool)]
    baseline = float(np.median(off)) if off.size else 0.0   # E5 cosines bunch high; weights use cos - baseline
    np.fill_diagonal(S, -np.inf)
    neighbors = {v: [[vids[j], round(float(S[i, j]), 4)] for j in np.argsort(-S[i]) if j != i][:K] for i, v in enumerate(vids)}
    doc = {'note': 'Private: built from personal history. Do not publish.', 'model': MODEL, 'k': K,
           'baseline': round(baseline, 4), 'with_description': sum(bool(cache[v].get('description')) for v in vids),
           'neighbors': neighbors}
    NEIGH.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    return doc

def check(cache, doc):
    favs = [f['video_id'] for f in load(R / 'confirmed-preferences.json', {}).get('favorites', [])]
    print(f"\nModel {doc['model']} | {len(doc['neighbors'])} stories | {doc['with_description']} with descriptions | baseline cosine {doc['baseline']}")
    for v in favs:
        if v not in doc['neighbors']: continue
        print('\n' + cache[v]['title'][:80])
        for j, c in doc['neighbors'][v]:
            print(f'  {c:.3f}  {cache.get(j, {}).get("title", j)[:75]}')
    print('\nDo these neighbors look right? If mostly unrelated, the embedding term should not be used.')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); a = ap.parse_args()
    if a.check: check(load(TEXT, {}), load(NEIGH, {}))
    else:
        cache = fetch(story_ids()); check(cache, embed(cache))
