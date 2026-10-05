# Story Compass prototype

Static local prototype. Serve only `dist`, never the repository root: the root contains personal Takeout data.

Run `python website/serve_local.py --port 8081` from the repository root, then open http://127.0.0.1:8081. Stop the old simple HTTP server first. Personal catalog data is served through a loopback-only endpoint from research/local-page-catalog.json, outside dist. Run `python fit_preferences.py` first to create research/behavior-signals.json; the server merges those behavior signals into /__private/catalog and serves fitted weights at /__private/model. Without that file the site still works on content signals alone.

Public discovery-catalog.json contains general story metadata from official YouTube playlists. It includes no history membership or favorite flags. A clean checkout shows curated suggestions. To prepare personal data, run analyze_history.py, supply the local preferences and catalog-review.json, then run curate_discoveries.py and prepare_test_catalog.py. Discovery candidates are absent from the supplied export, which does not prove the user has never heard them. The 30 local records were manually reviewed for title-based tags; mood and audio quality remain unknown.

Ranking uses Beta attribute beliefs (dist/recommendations.js). Confirmed favorites contribute 3 units, likes 2, saves 1, and explicit dislikes 2 negative units. Direct dislikes suppress all positive evidence from that story, including stale saves and returns. Explicit feedback suppresses its inferred behavior term; favorites retain a score floor of 0.95, likes 0.85, and dislikes a ceiling of 0.05. These are heuristic score bounds, not validated enjoyment probabilities.

Without explicit feedback, openings on distinct days provide weak evidence of 0.1 per day, capped at 0.5. The optional v2 model uses only return days and recency; its contribution is capped at ±0.25. Gap-derived completion, skips and pairwise preferences are uncertain diagnostics and do not influence ranking. Legacy behavior logits and skip-derived entity weights are ignored. Attribute contributions remain weighted by series, author, genre and channel with inverse document frequency. Discovery exploration and diversity are retained.

Series detection checks title segments separately from author segments. For example, Abhik Arjun Dutta is an author; it does not identify the Arjun detective series. JavaScript and the Python fitting pipeline use the same rule.

Duration filtering excludes unknown durations and is disabled if none are verified. Playlist duration does not establish current playback availability. History supports Show more; feedback restores focus to the same button or to Collection when a card disappears.

Deploy only the ZIP produced by `python website/package_deploy.py`. The packager rejects every unapproved file and catalog field. It never packages the private endpoint or local profile. Do not upload the repository root. Public deployment intentionally has no personal history profile.

Checks: `node website/test_recommendations.cjs` and `python website/test_deploy.py`. No live AI, accounts or embedded playback yet.
