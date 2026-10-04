# Story Compass prototype

Static local prototype. Serve only `dist`, never the repository root: the root contains personal Takeout data.

Run `python website/serve_local.py --port 8081` from the repository root, then open http://127.0.0.1:8081. Stop the old simple HTTP server first. Personal catalog data is served through a loopback-only endpoint from research/local-page-catalog.json, outside dist.

Public discovery-catalog.json contains general story metadata from official YouTube playlists. It includes no history membership or favorite flags. A clean checkout shows curated suggestions. To prepare personal data, run analyze_history.py, supply the local preferences and catalog-review.json, then run curate_discoveries.py and prepare_test_catalog.py. Discovery candidates are absent from the supplied export, which does not prove the user has never heard them. The 30 local records were manually reviewed for title-based tags; mood and audio quality remain unknown.

Ranking uses confirmed favorites at triple the weight of explicit likes. Series matches weigh 9, authors 7, specific genres 3 and generic suspense 0.5, multiplied by accumulated affinity. Saved stories get +2; likes get +6; heard stories get -1000 and always sort after unheard choices. Hidden stories stop contributing to the profile and can be restored. Explanations reflect the highest contributing match.

Duration filtering excludes unknown durations and is disabled if none are verified. Playlist duration does not establish current playback availability. History supports Show more; feedback restores focus to the same button or to Collection when a card disappears.

Deploy only the ZIP produced by `python website/package_deploy.py`. The packager rejects every unapproved file and catalog field. It never packages the private endpoint or local profile. Do not upload the repository root. Public deployment intentionally has no personal history profile.

Checks: `node website/test_recommendations.cjs` and `python website/test_deploy.py`. No live AI, accounts or embedded playback yet.
