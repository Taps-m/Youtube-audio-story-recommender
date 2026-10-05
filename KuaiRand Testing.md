# Colab: test the existing scorer on real KuaiRand interactions

Use the downloaded and extracted KuaiRand-1K data. No GPU, API key or LLM fine-tuning is required.

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

Training: April 8–21, 2022. Testing: April 22–May 8, 2022. All previously exposed video IDs are excluded from candidate pools. Up to 20 later liked and 20 later unliked videos are sampled for each eligible user. This balanced sample does not measure full-catalog performance. No recorded like is not an explicit dislike.

The production `website/dist/recommendations.js` scorer receives creator IDs and category tags from video basic metadata. Only training likes shape the preference profile. Statistical video features averaged across the full collection period are deliberately excluded. Baseline popularity uses training likes only. Outputs: macro AUC (random expectation 0.5) and Recall@10 in the sampled pools, plus per-user results in `research/kuairand/test/results.json`.

This evaluates base ranking, not embeddings or LLM reranking, and does not prove quality for Bengali YouTube stories. The adapter has been checked with a controlled fixture; no actual KuaiRand performance result is claimed until this cell runs successfully.

Dataset: [KuaiRand](https://github.com/chongminggao/KuaiRand), Gao et al., CIKM 2022, CC BY-SA 4.0. Keep downloaded data and result records out of the public story catalog; generated files under `research/kuairand/` are ignored by Git.
