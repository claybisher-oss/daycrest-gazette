# The Daycrest Gazette

*Plant, read, rest, repeat.*

A weekday paper for one reader, published as full-text RSS for NetNewsWire.

- **Feed:** `https://<owner>.github.io/daycrest-gazette/feed.xml`
- **One post per day:** each day's articles are combined into a single issue.
- **Articles:** `articles/*.md` (see `WRITING.md` for format and rules)
- **Followed creators:** `sources.json`
- **Build:** `python3 scripts/build_feed.py` → `_site/` (standard library only). GitHub Actions builds and deploys on every push to `main`.

One-time setup: **Settings → Pages → Build and deployment → Source: GitHub Actions.**
