# Story Compass prototype

Static local prototype. Serve only `dist`, never the repository root: the root contains personal Takeout data.

Use the bundled Python runtime to run `python -m http.server 8080 --bind 127.0.0.1 --directory dist` from this directory, then open http://127.0.0.1:8080.

The ignored local-test-catalog.json contains personal testing selections and loads only on loopback hostnames. Copy research/working-test-catalog.json to dist/local-test-catalog.json for local testing. A clean checkout has an empty catalog. Before any deployment, remove the private file from the upload directory and add a reviewed anonymous catalog through a separate public data source. Raw Takeout files are never needed by the website.

Implemented: responsive homepage, confirmed favorites, title-derived genre filters, local feedback and queue, reset, direct YouTube links. Duration filters return an honest empty state until duration is verified. New discoveries are an empty state. No live AI, API credentials, accounts or embedded playback.
