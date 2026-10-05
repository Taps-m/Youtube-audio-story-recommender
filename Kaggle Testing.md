# Synthetic 100-user benchmark

Source: [Kaggle YouTube Recommendation Data](https://www.kaggle.com/datasets/iitanshravan/youtube-recommendation-data-for-cleaning-and-ml). The publisher describes these as generated interactions, not actual YouTube activity. License: CC0.

Run from the project root:

```powershell
python prepare_kaggle_test.py
node website/test_kaggle.cjs
```

The preparation script caches the downloaded archive, rejects missing/invalid identifiers, categories and like labels, normalizes yes/no to 1/0, and removes repeated user/video rows. It selects 100 users with at least eight unique interactions, three likes and three unliked records, using seed 2026. Each user's randomly selected liked/unliked test pair is excluded from training. An unliked record is not treated as an explicit dislike.

Raw data, selected records and reports stay under ignored `research/kaggle/`, outside the website and GitHub. No synthetic videos are added to the real story catalog.

The benchmark tests the current base scorer using categories and training likes. Compare pair accuracy with training-only category popularity and the random expectation of 50%; ties count as half a correct pair. Candidate categories are available at scoring time, while test feedback remains hidden. This random split does not test temporal generalization. The cohort selection requires enough positive/negative examples, so it is not representative of every user.

Initial run: 1,000,000 source rows; 3,055 invalid rows and 103 duplicate user/video rows rejected; 51,764 eligible users; 100 selected users; 993 training interactions; 200 test interactions. Model pair accuracy: **48.5%**, popularity: **46.5%**, random expectation: **50%**, with 41 model ties. This does not demonstrate useful preference learning or statistically significant improvement. Broad categories and synthetic signals are insufficient to validate Bengali story recommendations.

This benchmark does not train an LLM or evaluate semantic embeddings/LLM reranking; those require meaningful candidate descriptions and appropriate preference labels. Real listener evaluation remains necessary.
