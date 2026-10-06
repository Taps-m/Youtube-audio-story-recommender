# Colab: test the existing scorer on real KuaiRand interactions

Use the downloaded and extracted KuaiRand-1K data. No GPU, API key or LLM fine-tuning is required.

For a local run, `python download_kuairand.py` downloads resumable segments, checks the official MD5 and extracts only the four required input files into the ignored research folder. Then run:

```text
python prepare_kuairand_test.py --data research/kuairand/KuaiRand-1K/data
node website/test_kuairand.cjs
```

In the existing Colab notebook, add one cell:

```python
import os, subprocess
from pathlib import Path

repo = Path('/content/Youtube-audio-story-recommender')
os.chdir(repo)
subprocess.run(['git', 'pull', '--ff-only'], check=True)
subprocess.run(['python', 'prepare_kuairand_test.py', '--data', 'KuaiRand-1K/data'], check=True)
subprocess.run(['node', 'website/test_kuairand.cjs'], check=True)
```

The scripts independently reproduce the seeded selection of 100 users and report how many can be evaluated; the earlier notebook's `train_data` variable is not required. Users without training likes or both test labels are excluded and counted.

Training log: April 8–21, 2022. Test log: April 22–May 8, 2022. Actual timestamps slightly overlap despite the date labels, so test events at or before the latest training timestamp are excluded. All previously exposed video IDs are excluded from candidate pools. Up to 20 later liked and 20 later unliked videos are sampled for each eligible user. This balanced sample does not measure full-catalog performance. No recorded like is not an explicit dislike.

The production `website/dist/recommendations.js` scorer receives creator IDs and category tags from video basic metadata. Only training likes shape the preference profile. Statistical video features averaged across the full collection period are deliberately excluded. Baseline popularity uses training likes only. Outputs: macro AUC (random expectation 0.5) and Recall@10 in the sampled pools, plus per-user results in `research/kuairand/test/results.json`. Recall@10 accounts for ties by expected hits rather than arbitrary CSV ordering. A seeded bootstrap over users supplies 95% intervals for model AUC and its paired improvement over popularity; these intervals do not cover candidate-sampling uncertainty or domain differences.

This evaluates base ranking, not embeddings or LLM reranking, and does not prove quality for Bengali YouTube stories.

## Completed local run — October 6, 2026

The official archive passed its MD5 check. The real-data run selected 100 users: 99 had earlier interactions, seven had no training likes (including the absent user), and three lacked an evaluable later liked/unliked pair. The benchmark evaluated **90 users** using **495,484 earlier interactions** and **8,253 earlier like events**. It excluded **11 overlapping test events**. The adapter also passed the controlled fixture check.

| Metric | Existing scorer | Training category popularity | Random expectation |
| --- | ---: | ---: | ---: |
| Macro AUC | 0.5848 | 0.5962 | 0.5000 |
| Macro Recall@10 in sampled candidate pools | 38.84% | 38.17% | 30.63% |

Model AUC bootstrap 95% interval: 0.5557–0.6148. Paired model-minus-popularity AUC difference: -0.0114, interval -0.0470–0.0228. This run supports above-chance discrimination in this restricted benchmark but **does not establish improvement over the popularity baseline**. The higher Recall@10 point estimate is small and is not evidence of a statistically reliable advantage. No model weights were tuned on the held-out test.

These results were produced locally, not in Colab. Direct computer access to the Colab session failed. Per-user outputs remain in ignored `research/kuairand/test/results.json`; only aggregate results and reproducible code are published.

Dataset: [KuaiRand](https://github.com/chongminggao/KuaiRand), Gao et al., CIKM 2022, CC BY-SA 4.0. Keep downloaded data and result records out of the public story catalog; generated files under `research/kuairand/` are ignored by Git.
