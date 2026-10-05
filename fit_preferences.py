#!/usr/bin/env python3
"""Fit a Bayesian logistic preference model from local YouTube Takeout history.

Reads private data under history/ and research/ and writes research/preference-model.json
(git-ignored). Takeout records only when a video was opened, so listening time is inferred
from the gap to the next YouTube event and treated as censored where it is ambiguous.
"""
import json, re, math, collections
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np

ROOT = Path(__file__).parent
TK = ROOT / 'history/Takeout/YouTube and YouTube Music'
IST = timezone(timedelta(hours=5, minutes=30))
STRONG = re.compile(r'sunday suspense|bengali audio story|bangla audio story|audio story|audiostory|goyenda golpo', re.I)
EXCL = re.compile(r'short film|trailer|reaction|review|#shorts', re.I)
SKIP_WINDOW = 5      # min: another story opened this soon = deliberate skip
AMBIG_WINDOW = 5     # min: non-story event this soon = ambiguous (other device, navigation)
CHAIN_HOURS = 48     # reopens within this window are one listening attempt
KAPPA = 4.0          # shrinkage strength toward the parent group
PU_WEIGHT = 0.1      # weight of unlabeled stories treated as weak negatives
WATCH_LATER_WEIGHT = 0.5
PRIORS = {  # name: (mean, sd) on standardized features
    'intercept': (-0.85, 1.0), 'completion': (1.0, 0.5), 'return_days': (0.8, 0.5),
    'bt_preference': (1.0, 0.5), 'skip_rate': (-0.7, 0.5), 'recency': (0.3, 0.3)}
FEATURES = list(PRIORS)[1:]

SERIES = [('Byomkesh', r'byomkesh|ব্যোমকেশ', 'detective mystery', 'Saradindu Bandyopadhyay'),
          ('Feluda', r'feluda|ফেলুদা', 'detective mystery', 'Satyajit Ray'),
          ('Professor Shonku', r'sh[oa]nku|শঙ্কু|শংকু', 'science fiction', 'Satyajit Ray'),
          ('Arjun', r'\barjun\b|অর্জুন', 'detective mystery', 'Samaresh Majumdar'),
          ('Dipkaku O Jhinuk', r'dipkaku|দীপকাকু', 'detective mystery', 'Sukanta Gangopadhyay'),
          ('Riju', r'riju series', 'spy thriller', 'Saswati Chowdhury'),
          ('Chanakya', r'chanakya|চাণক্য', None, 'Abhigyan Ganguly')]
AUTHORS = [('Saradindu Bandyopadhyay', r's[ah]*radindu|শরদিন্দু'), ('Satyajit Ray', r'satyajit (?:ray|roy)|সত্যজিৎ'),
           ('Samaresh Majumdar', r'samaresh majumdar|সমরেশ'), ('Abhik Arjun Dutta', r'abhik arjun dutta')]
GENRES = [('detective mystery', r'detective|goyenda|গোয়েন্দা|গোয়েন্দা'), ('mystery', r'\bmystery\b|rahasya|রহস্য'),
          ('horror', r'horror|ভৌতিক|bhuter|supernatural'), ('suspense', r'\bsuspense\b|thriller'),
          ('science fiction', r'sci.fi|science fiction'), ('romance', r'romantic|premer|love story')]

def vid(u):
    m = re.search(r'v=([\w-]{11})', u or ''); return m.group(1) if m else None
def title(x): return re.sub(r'^Watched\s+', '', x.get('title', ''))
def channel(x): return (x.get('subtitles') or [{}])[0].get('name', 'Unknown').strip()
def ts(x): return datetime.fromisoformat(x['time'].replace('Z', '+00:00'))
def is_story(x):
    t = title(x); return bool(STRONG.search(t)) and not EXCL.search(t) and bool(vid(x.get('titleUrl')))
def sigmoid(z): return 1 / (1 + np.exp(-z))
def logit(p): return math.log(p / (1 - p))

def enrich(v, t, ch, review):
    clean = re.sub(r'(?:best of )?sunday suspense(?: classics)?', '', t, flags=re.I)
    r = review.get(v, {})
    series, authors, genres = set(r.get('series', [])), set(r.get('authors', [])), set(r.get('tags', []))
    for name, rx, g, a in SERIES:
        if re.search(rx, clean, re.I): series.add(name); authors.add(a); g and genres.add(g)
    for name, rx in AUTHORS:
        if re.search(rx, clean, re.I): authors.add(name)
    if not r.get('tags'):
        for g, rx in GENRES:
            if re.search(rx, clean, re.I): genres.add(g)
    return {'series': sorted(series), 'authors': sorted(authors), 'genres': sorted(genres), 'channel': ch}

def load_durations():
    d = {}
    for f in ['research/local-page-catalog.json', 'research/working-test-catalog.json', 'research/discovery-candidates.json', 'website/dist/discovery-catalog.json']:
        p = ROOT / f
        if not p.exists(): continue
        data = json.loads(p.read_text(encoding='utf-8'))
        for s in (data if isinstance(data, list) else data.values() if isinstance(data, dict) else []):
            if isinstance(s, dict) and s.get('video_id') and s.get('duration_minutes'): d[s['video_id']] = float(s['duration_minutes'])
    return d

def km(rows, points=(0.1, 0.25, 0.5, 0.85)):
    """Kaplan-Meier survival of listening fraction. rows = (fraction, event_happened)."""
    rows = sorted((min(f, 1.0), e) for f, e in rows); S, n, i, curve = 1.0, len(rows), 0, []
    while i < len(rows):
        t = rows[i][0]; same = [e for f, e in rows[i:] if f == t]; d = sum(same)
        if d: S *= 1 - d / n
        curve.append((t, S)); n -= len(same); i += len(same)
    return {str(p): round(next((s for t, s in reversed(curve) if t <= p), 1.0), 3) for p in points}

def fit(X, y, w, m, s):
    b = m.copy()
    for _ in range(100):
        p = sigmoid(X @ b)
        g = X.T @ (w * (p - y)) + (b - m) / s**2
        H = (X.T * (w * p * (1 - p))) @ X + np.diag(1 / s**2)
        step = np.linalg.solve(H, g); b -= step
        if np.abs(step).max() < 1e-9: break
    return b, np.linalg.inv(H)

def main():
    w = [x for x in json.loads((TK / 'history/watch-history.json').read_text(encoding='utf-8')) if x.get('time')]
    w.sort(key=ts)
    review = json.loads((ROOT / 'research/catalog-review.json').read_text(encoding='utf-8')) if (ROOT / 'research/catalog-review.json').exists() else {}
    prefs = json.loads((ROOT / 'research/confirmed-preferences.json').read_text(encoding='utf-8'))
    favorites = {f['video_id'] for f in prefs.get('favorites', [])}
    watch_later = set()
    wl = TK / 'playlists/Watch later-videos.csv'
    if wl.exists():
        watch_later = {l.split(',')[0].strip() for l in wl.read_text(encoding='utf-8').splitlines()[1:] if l.strip()}
    dur = load_durations(); end_time = ts(w[-1])

    opens, meta = collections.defaultdict(list), {}
    for i, x in enumerate(w):
        if not is_story(x): continue
        v = vid(x['titleUrl']); meta.setdefault(v, (title(x), channel(x)))
        if i + 1 < len(w):
            n = w[i + 1]; nv = vid(n.get('titleUrl')); gap = (ts(n) - ts(x)).total_seconds() / 60
            kind = 'same' if nv == v else 'story' if is_story(n) else 'other'
        else: nv, gap, kind = None, None, 'end'
        opens[v].append({'t': ts(x), 'gap': gap, 'next': kind, 'next_vid': nv})

    stories, pairs, km_rows = {}, [], []
    outcome_counts = collections.Counter()
    for v, os_ in opens.items():
        D = dur.get(v); chains, cur = [], [os_[0]]
        for o in os_[1:]:
            if (o['t'] - cur[-1]['t']).total_seconds() > CHAIN_HOURS * 3600: chains.append(cur); cur = [o]
            else: cur.append(o)
        chains.append(cur)
        res = collections.Counter(); minutes = 0
        for ch in chains:
            covered = 0.0; last = ch[-1]
            for o in ch:
                g = o['gap']; cap = D or 240
                if g is None or (o['next'] == 'other' and g < AMBIG_WINDOW): continue
                if g <= 1.5 * cap and g <= 360: covered += min(g, cap)
            frac = covered / D if D else None
            skipped = last['next'] == 'story' and last['gap'] is not None and last['gap'] < SKIP_WINDOW and \
                      (covered < 0.5 * D if D else covered < 15)
            out = 'completed' if D and frac >= 0.85 else 'abandoned' if skipped else 'censored'
            res[out] += 1; outcome_counts[out] += 1; minutes += covered
            if out == 'abandoned' and last['next_vid']: pairs.append((last['next_vid'], v))
            if D: km_rows.append((frac, out == 'abandoned'))
        t, c = meta[v]
        stories[v] = {'video_id': v, 'title': t, **enrich(v, t, c, review), 'duration': D, 'attempts': len(chains),
                      'opens': len(os_), **{k: res[k] for k in ('completed', 'abandoned', 'censored')},
                      'minutes_inferred': round(minutes, 1),
                      'days': len({o['t'].astimezone(IST).date() for o in os_}),
                      'age_days': (end_time - os_[-1]['t']).total_seconds() / 86400}

    # Hierarchical Beta shrinkage: global -> channel -> author -> series -> story
    def hierarchy(succ_key, trial_fn):
        S = sum(s[succ_key] for s in stories.values()); N = sum(trial_fn(s) for s in stories.values())
        mu0 = (S + 1) / (N + 2); groups = collections.defaultdict(lambda: [0.0, 0.0])
        for s in stories.values():
            for k in ['c:' + s['channel']] + ['a:' + a for a in s['authors'][:1]] + ['s:' + x for x in s['series'][:1]]:
                groups[k][0] += s[succ_key]; groups[k][1] += trial_fn(s)
        out = {}
        for v, s in stories.items():
            mu = mu0
            for k in ['c:' + s['channel']] + ['a:' + a for a in s['authors'][:1]] + ['s:' + x for x in s['series'][:1]]:
                sg, ng = groups[k]; mu = (sg + KAPPA * mu) / (ng + KAPPA)
            out[v] = (s[succ_key] + KAPPA * mu) / (trial_fn(s) + KAPPA)
        return out
    p_complete = hierarchy('completed', lambda s: s['completed'] + s['abandoned'])
    skip_rate = hierarchy('abandoned', lambda s: s['attempts'])

    # Bradley-Terry over series / author / genre / channel entities from skip pairs
    def ents(v):
        s = stories.get(v)
        return [] if not s else ['series:' + x for x in s['series']] + ['author:' + x for x in s['authors']] + \
               ['genre:' + x for x in s['genres']] + ['channel:' + s['channel']]
    pairs = [(a, b) for a, b in pairs if a in stories and b in stories and a != b]
    theta = collections.defaultdict(float)
    for _ in range(800):
        grad = collections.defaultdict(float)
        for win, lose in pairs:
            d = sum(theta[e] for e in ents(win)) - sum(theta[e] for e in ents(lose))
            r = 1 - 1 / (1 + math.exp(-d))
            for e in ents(win): grad[e] += r
            for e in ents(lose): grad[e] -= r
        for e in set(grad) | set(theta): theta[e] += 0.05 * (grad[e] - theta[e])  # N(0,1) prior
    bt = {v: sum(theta[e] for e in ents(v)) for v in stories}

    ids = sorted(stories)
    raw = np.array([[logit(min(max(p_complete[v], 0.02), 0.98)), math.log1p(stories[v]['days']), bt[v],
                     skip_rate[v], math.exp(-stories[v]['age_days'] / 90)] for v in ids])
    mean, sd = raw.mean(0), raw.std(0); sd[sd == 0] = 1
    X = np.hstack([np.ones((len(ids), 1)), (raw - mean) / sd])
    y = np.array([1.0 if v in favorites or v in watch_later else 0.0 for v in ids])
    wt = np.array([1.0 if v in favorites else WATCH_LATER_WEIGHT if v in watch_later else PU_WEIGHT for v in ids])
    m = np.array([PRIORS[k][0] for k in PRIORS]); s = np.array([PRIORS[k][1] for k in PRIORS])
    beta, cov = fit(X, y, wt, m, s); se = np.sqrt(np.diag(cov))

    # Leave-one-out on every positive, compared with baselines
    pos = [i for i, v in enumerate(ids) if y[i] == 1]
    def handtuned(i_out):
        prof = collections.Counter()
        for i in pos:
            if i == i_out or ids[i] not in favorites: continue
            st = stories[ids[i]]
            for f in ('series', 'authors', 'genres'):
                for x in st[f]: prof[(f, x)] += 3
        def sc(v):
            st = stories[v]; return sum((9 if f == 'series' else 7 if f == 'authors' else (0.5 if x == 'suspense' else 3)) * prof[(f, x)]
                                        for f in ('series', 'authors', 'genres') for x in st[f])
        return np.array([sc(v) for v in ids])
    methods = {'fitted model': None, 'priors only (no fit)': lambda i: X @ m, 'open count': lambda i: np.array([stories[v]['opens'] for v in ids], float),
               'current hand-tuned weights': handtuned}
    loo = {}
    for name, fn in methods.items():
        ranks = []
        for i in pos:
            if fn is None:
                w2 = wt.copy(); w2[i] = 0; b2, _ = fit(X, y, w2, m, s); scores = X @ b2
            else: scores = fn(i)
            others = [j for j in range(len(ids)) if j == i or j not in pos]
            ranks.append(1 + sum(scores[j] > scores[i] for j in others) + 0.5 * sum(scores[j] == scores[i] for j in others if j != i))
        loo[name] = {'ranks': ranks, 'mrr': round(float(np.mean([1 / r for r in ranks])), 3),
                     'hit@10': round(float(np.mean([r <= 10 for r in ranks])), 2), 'median_rank': float(np.median(ranks))}

    probs = sigmoid(X @ beta); order = np.argsort(-probs)
    result = {
        'note': 'Private: derived from personal watch history. Do not publish.',
        'data': {'story_videos': len(ids), 'listening_attempts': sum(outcome_counts.values()), 'outcomes': dict(outcome_counts),
                 'with_known_duration': sum(1 for v in ids if stories[v]['duration']), 'skip_pairs': len(pairs),
                 'labels': {'favorites': int(sum(1 for v in ids if v in favorites)), 'watch_later': int(sum(1 for v in ids if v in watch_later and v not in favorites)),
                            'unlabeled_weak_negatives': int(sum(y == 0))}},
        'dropoff_survival_S(fraction)': km(km_rows),
        'parameters': {k: {'prior_mean': PRIORS[k][0], 'prior_sd': PRIORS[k][1], 'fitted': round(float(beta[j]), 3), 'se': round(float(se[j]), 3),
                           'moved_prior_sds': round(float((beta[j] - PRIORS[k][0]) / PRIORS[k][1]), 2)} for j, k in enumerate(PRIORS)},
        'feature_correlation': {f'{FEATURES[a]}~{FEATURES[b]}': round(float(np.corrcoef(raw[:, a], raw[:, b])[0, 1]), 2)
                                for a in range(5) for b in range(a + 1, 5)},
        'leave_one_out': loo,
        'favorites_check': {stories[v]['title'][:60]: {k: stories[v][k] for k in ('opens', 'days', 'completed', 'abandoned', 'censored', 'duration')} | {'p_enjoy': round(float(probs[ids.index(v)]), 3), 'rank': int(list(order).index(ids.index(v)) + 1)} for v in ids if v in favorites},
        'top_bt_entities': sorted(((e, round(t, 2)) for e, t in theta.items()), key=lambda x: -abs(x[1]))[:12],
        'top_predictions': [{'title': stories[ids[i]]['title'][:70], 'p_enjoy': round(float(probs[i]), 3), 'labelled': bool(y[i])} for i in order[:15]],
    }
    # Behavior signals consumed by the local site (served from research/, never from dist/)
    contrib = (X[:, 1:] * beta[1:])
    signals = {
        'note': 'Private: derived from personal watch history. Served only by website/serve_local.py.',
        'model': {'weights': {k: round(float(beta[j]), 4) for j, k in enumerate(PRIORS)},
                  'feature_mean': dict(zip(FEATURES, map(float, mean))), 'feature_sd': dict(zip(FEATURES, map(float, sd))),
                  'positive_labels': int(len(pos)), 'loo_mrr': loo['fitted model']['mrr'], 'baseline_open_count_mrr': loo['open count']['mrr']},
        'entity_theta': {e: round(t, 4) for e, t in theta.items() if abs(t) >= 0.01},
        'stories': {v: {'behavior_logit': round(float(contrib[i].sum()), 4), 'return_days': stories[v]['days'], 'opens': stories[v]['opens'],
                        'completed': stories[v]['completed'], 'skipped': stories[v]['abandoned'],
                        'p_complete': round(float(p_complete[v]), 3), 'skip_rate': round(float(skip_rate[v]), 3)}
                    for i, v in enumerate(ids)}}
    (ROOT / 'research/behavior-signals.json').write_text(json.dumps(signals, ensure_ascii=False, indent=1), encoding='utf-8')
    (ROOT / 'research/preference-model.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(json.dumps({k: result[k] for k in result if k != 'top_predictions'}, ensure_ascii=False, indent=1, default=str))
    print('top predictions:'); [print(' ', r['p_enjoy'], '*' if r['labelled'] else ' ', r['title']) for r in result['top_predictions']]

if __name__ == '__main__':
    main()
