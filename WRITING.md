# How the Gazette is written (rules for every run)

This repo is **public** (GitHub Pages). Anyone with the link can read it.

## Never put in this repo
- Work anything: calendar items, meetings, clients, colleagues, the employer's name.
- Family names, ages, birthdays, the farm's location, home address, finances, budget, house fund.
- Workbook packets, coursework, grades, Canvas material, prayer requests, health.
- Anything from Clay's email, Todoist, Obsidian vault, or iCloud Library.

## Every article
- One file: `articles/YYYY-MM-DD-short-slug.md` with front matter (`title`, `date: YYYY-MM-DD HH:MM` Eastern, `section`, `summary`, optional `source`, `source_url`, `issue`).
- **Own words only.** No pasted article text, transcripts, lyrics or post-1928 poems. A quote is rare, under 15 words, one per source.
- Verified facts; link the original in `source_url`.
- Images: public-domain or openly licensed only, credited, saved under `static/img/`.
- Sections: `Front Page`, `Nation & World`, `Faith`, `Wildcats`, `Weather`, `Around Town`, `Creek Report`, `Kentucky Voices`, `Turntable`, `Nature` (Species of the Day), `Followed`.

## Explainer format (every article that's more than a brief)
Modeled on AI "visual explainer" daily briefs: understand it in two minutes, go deeper if you want.
1. `brief:` in front matter: 3 takeaways separated by `|` (renders as an **In brief** box at the top).
2. One simple diagram when a picture beats prose: a timeline, a flow of an argument, a comparison, a map sketch, a "before vs after". Write it as a small hand-made SVG (grayscale, Georgia serif, viewBox 400 wide (tall rather than wide), text 15px+, readable on a phone) saved as `static/img/YYYY-MM-DD-slug.svg`, and put it on its own line: `![Caption that says what to notice](img/YYYY-MM-DD-slug.svg)`. No diagram rather than a decorative one. Public-domain photos/plates are fine too (credited in the caption).
3. Short `##` sections in plain words; define any term the first time it appears.
4. End with `## Why it matters` (2–4 sentences), then the source link (from `source_url`).
5. Followed write-ups also get `## Worth watching?`: one honest line on whether the full video/episode adds much beyond the write-up, and which minutes to jump to if so.

## Followed (creators in `sources.json`)
- Check each creator's feed for anything new since the last run (weekends roll into Monday).
- One article per new video/episode/post, roughly 300–600 words: what it covers, the main ideas and why they matter, then the link. A write-up that points back to the original, never a replacement for it.
- `prefer: writing` → work from their own essay/newsletter first. `video` → transcript/description. `show-notes` → episode notes.
- `stance: disagree` → state their view fairly and in its strongest form, then note where it departs from historic orthodoxy (Nicene Creed, ecumenical councils) or where other traditions differ. Respectful, never mocking.
- Fill in a creator's `feed` the first time it's found; leave `null` if not found and try again next run.
- Don't repeat a piece already in `articles/` (check `source_url`).

## Publishing
Commit to `main`; the Actions workflow builds `_site/` and deploys. Feed: `https://<owner>.github.io/<repo>/feed.xml`.
