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
- Verified facts.
- **Link the full source, always.** `source_url` must be the exact article/post/episode page, never a homepage or section page. Any extra fact or brief from another outlet gets its own inline link to that exact page. If you can't find the exact page, leave the item out.
- Sections: `Almanac`, `Front Page`, `Nation & World`, `Faith`, `Wildcats`, `Weather`, `Around Town`, `Creek Report`, `Kentucky Voices`, `Turntable`, `Nature`, `Sky`, `Farm & Garden`, `Creed & Controversy`, `Ideas`, `Crossword`, `Followed`.

## Photos: real pictures first
Clay prefers **real photographs** over generated art. Use a real photo whenever one exists under a free license; draw a diagram/chart only to explain something a photo can't.
- Allowed sources: Wikimedia Commons (every file there is freely licensed), U.S. federal public-domain images (NASA, NOAA, NPS, USFWS, USDA, USGS, Library of Congress "no known restrictions"), Smithsonian Open Access (CC0), Unsplash, Flickr images marked CC0/CC BY/CC BY-SA.
- Never: news-outlet, AP/Reuters/Getty or team/athletics photos, photos lifted from a creator's video/thumbnail, or pictures of real people's faces (public figures included) — show the subject instead (the place, the ship, the bird, the book).
- Embed on its own line, then a credit line right under it:
  `![What to notice in the photo](https://commons.wikimedia.org/wiki/Special:FilePath/<File_name.jpg>?width=1000)`
  `*Photo: <Author>, [<license> via Wikimedia Commons](https://commons.wikimedia.org/wiki/File:<File_name.jpg>)*`
  (If the shell can download images, you may save a ≤1000-px JPEG to `static/img/` instead and keep the same credit line.)
- One lead photo per article is plenty; add a second only if it shows something new.

## Explainer format (every article that's more than a brief)
Modeled on AI "visual explainer" daily briefs: understand it in two minutes, go deeper if you want.
1. `brief:` in front matter: 3 takeaways separated by `|` (renders as an **In brief** box at the top).
2. A real photo (see above) and/or one simple diagram when a picture beats prose: a timeline, a flow of an argument, a comparison, a map sketch, a "before vs after". Write it as a small hand-made SVG (grayscale, Georgia serif, viewBox 400 wide (tall rather than wide), text 15px+, readable on a phone) saved as `static/img/YYYY-MM-DD-slug.svg`, and put it on its own line: `![Caption that says what to notice](img/YYYY-MM-DD-slug.svg)`. No diagram rather than a decorative one. Public-domain photos/plates are fine too (credited in the caption).
3. Short `##` sections in plain words; define any term the first time it appears.
4. End with `## Why it matters` (2–4 sentences), then the source link (from `source_url`).
5. Followed write-ups also get `## Worth watching?`: one honest line on whether the full video/episode adds much beyond the write-up, and which minutes to jump to if so.

## Recurring features (all public-safe; nothing about Clay, his family, work or school)
| When | Section | What |
|---|---|---|
| Every issue | `Almanac` | One short article: Lexington, KY sunrise/sunset and day length, moon phase (compute in Python with standard formulas), the day in the church year (RCL Year A; season, feast or commemoration), and **On this day in Kentucky** — one verified event, linked to its source (Kentucky Historical Society, ExploreKYHistory, KET, etc.). |
| Every issue | `Nature` | Species of the Day (list in the task prompt), with a real photo. |
| Mon | `Sky` | **This Week's Sky** for Central Kentucky: what to look for and when (planets, Moon, meteor showers, bright stars), from Sky & Telescope's "This Week's Sky at a Glance" and NASA's "What's Up". Include a simple sky chart (SVG: horizon, direction, time) plus a NASA/Commons photo of the object when one exists. |
| Tue | `Farm & Garden` | **Task of the week** for a Central Kentucky homestead/acre: one seasonal job (soil test, cover crop, pruning, seed-starting, pasture, orchard, tool care) grounded in a UK Cooperative Extension publication or county-agent article, linked. Steps + "why now". |
| Wed | `Creed & Controversy` | One heresy or one debate between Christian traditions, explained fairly in its own best terms, then measured against the Nicene Creed / Chalcedon / the seven ecumenical councils. Timeline or "who said what" diagram; photo of a relevant icon, manuscript, church or council site from Commons. Link primary texts (e.g., CCEL, New Advent's Fathers). |
| Thu | `Ideas` | **Idea of the week** from 1000-Word Philosophy or the Stanford Encyclopedia of Philosophy: the idea, the best objection, a question to sit with. Link the entry. |
| Fri | `Crossword` | **Saturday Crossword** (posted Friday, since there's no weekend issue): an ORIGINAL 11×11 or 13×13 American-style puzzle (symmetric, all words checked, original clues, family-friendly, a light Kentucky/faith/outdoors theme now and then). Publish it as a self-contained playable page `static/puzzles/YYYY-MM-DD.html` (tap a square, type, arrows, check/reveal buttons, answers stored lightly obfuscated) and an article in the feed that links to it. Verify every across/down entry is a real word and the grid fill matches the clues before publishing. |

Plus the weekday features already in the task (Around Town Mon/Thu, Creek Report Tue/Fri, Kentucky Voices + Turntable Wed).

## Followed (creators in `sources.json`)
- Check each creator's feed for anything new since the last run (weekends roll into Monday).
- One article per new video/episode/post, roughly 300–600 words: what it covers, the main ideas and why they matter, then the link. A write-up that points back to the original, never a replacement for it.
- `prefer: writing` → work from their own essay/newsletter first. `video` → transcript/description. `show-notes` → episode notes.
- `stance: disagree` → state their view fairly and in its strongest form, then note where it departs from historic orthodoxy (Nicene Creed, ecumenical councils) or where other traditions differ. Respectful, never mocking.
- Fill in a creator's `feed` the first time it's found; leave `null` if not found and try again next run.
- Don't repeat a piece already in `articles/` (check `source_url`).

## Publishing
Commit to `main`; the Actions workflow builds `_site/` and deploys. Feed: `https://<owner>.github.io/<repo>/feed.xml`.
