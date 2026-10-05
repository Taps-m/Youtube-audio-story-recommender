# Personalized audio story discovery

Story Compass is a static prototype for discovering YouTube audio stories through listener preferences and feedback. The website code is in website/dist. Homepage Content.md records messaging requirements; build_tracker.py creates the project tracker.

## Local development

Run `python website/serve_local.py --port 8081` from the repository root. The page has no build dependencies. The local server loads private data from outside dist. Review website/README.md for private test data setup and current feature limits.

## Research tools

analyze_history.py reads local Takeout exports and extracts keyword candidates. prepare_test_catalog.py prepares local testing records. Both expect the local folder structure documented in their source. They perform keyword processing, not AI inference. fit_preferences.py infers listening attempts from Takeout gaps (completed, quick skip or censored), estimates completion with hierarchical Beta shrinkage and head-to-head preferences with a Bradley-Terry model, fits a Bayesian logistic model with leave-one-out evaluation, and writes private outputs to research/ (git-ignored). Takeout records only when a video was opened, so listening time is inferred, not measured.

## Repository privacy

Raw history, derived JSON profiles, personal test catalog data and generated documents are excluded from Git. Do not force-add ignored files. Code, documentation and scripts belong in GitHub; private source data stays local. Remove private files from deployment directories before publishing, since ignore rules do not govern manual uploads.

## Planned architecture

Cloudflare Pages for static hosting; local browser storage for feedback; reviewed AI-assisted catalog enrichment during preparation; rule-based browser filtering and ranking. Live AI, accounts and cross-device sync are future work.
