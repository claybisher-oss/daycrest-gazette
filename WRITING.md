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
- Sections: `Front Page`, `NPR`, `Faith`, `Wildcats`, `Weather`, `Around Town`, `Creek Report`, `Kentucky Voices`, `Turntable`, `Nature` (Species of the Day), `Followed`.

## Followed (creators in `sources.json`)
- Check each creator's feed for anything new since the last run (weekends roll into Monday).
- One article per new video/episode/post, roughly 300–600 words: what it covers, the main ideas and why they matter, then the link. A write-up that points back to the original, never a replacement for it.
- `prefer: writing` → work from their own essay/newsletter first. `video` → transcript/description. `show-notes` → episode notes.
- `stance: disagree` → state their view fairly and in its strongest form, then note where it departs from historic orthodoxy (Nicene Creed, ecumenical councils) or where other traditions differ. Respectful, never mocking.
- Fill in a creator's `feed` the first time it's found; leave `null` if not found and try again next run.
- Don't repeat a piece already in `articles/` (check `source_url`).

## Publishing
Commit to `main`; the Actions workflow builds `_site/` and deploys. Feed: `https://<owner>.github.io/<repo>/feed.xml`.
