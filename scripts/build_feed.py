#!/usr/bin/env python3
"""Build the Daycrest Gazette site + RSS feeds from articles/*.md.

Standard library only, so it runs anywhere (GitHub Actions, a cloud run, a Mac).

Article format (articles/YYYY-MM-DD-slug.md):

    ---
    title: Headline here
    date: 2026-11-16 06:17
    section: Followed          # Front Page, Faith, Wildcats, Followed, Nature, ...
    summary: One-line dek shown in lists.
    brief: First takeaway | Second takeaway | Third   # optional "In brief" box
    source: The Holy Post      # optional
    source_url: https://...    # optional, "Read/watch the original" link
    issue: 1                   # optional Gazette issue number
    ---
    Markdown body...

Output goes to _site/:
    feed.xml               every section, newest 80 articles, full text
    feeds/<section>.xml    one feed per section
    index.html             front page listing
    a/<slug>.html          one page per article (the feed's permalinks)
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
STATIC = ROOT / "static"
OUT = ROOT / "_site"
CONFIG = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
FEED_LIMIT = int(CONFIG.get("feed_limit", 80))
ET = timezone(timedelta(hours=-5))  # dates in front matter are Eastern; DST nuance is harmless here


def base_url() -> str:
    """https://<owner>.github.io/<repo>/ derived from the Actions env, or site.json override."""
    if CONFIG.get("base_url"):
        return CONFIG["base_url"].rstrip("/") + "/"
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        if name.lower() == f"{owner.lower()}.github.io":
            return f"https://{owner.lower()}.github.io/"
        return f"https://{owner.lower()}.github.io/{name}/"
    return "http://localhost:8000/"


# ---------------------------------------------------------------- markdown
def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", text)
    return text


def markdown_to_html(md: str) -> str:
    out: list[str] = []
    para: list[str] = []
    list_tag: str | None = None
    quote: list[str] = []
    table: list[str] = []

    def flush_table():
        if not table:
            return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table]
        rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
        head, body = rows[0], rows[1:]
        out.append('<table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                   + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
                   + "</tbody></table>")
        table.clear()

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    def flush_quote():
        if quote:
            out.append("<blockquote>" + markdown_to_html("\n".join(quote)) + "</blockquote>")
            quote.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("|"):
            flush_para(); flush_list(); flush_quote()
            table.append(line)
            continue
        flush_table()
        if line.startswith(">"):
            flush_para(); flush_list()
            quote.append(line[1:].lstrip())
            continue
        flush_quote()
        if not line.strip():
            flush_para(); flush_list()
            continue
        if m := re.match(r"^(#{1,4})\s+(.*)", line):
            flush_para(); flush_list()
            lvl = min(len(m.group(1)) + 1, 5)  # # -> h2 (h1 is the title)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^(-{3,}|\*{3,})$", line.strip()):
            flush_para(); flush_list()
            out.append("<hr>")
            continue
        if m := re.match(r"^\s*([-*]|\d+\.)\s+(.*)", line):
            flush_para()
            tag = "ol" if m.group(1)[0].isdigit() else "ul"
            if list_tag != tag:
                flush_list()
                out.append(f"<{tag}>")
                list_tag = tag
            out.append(f"<li>{inline(m.group(2))}</li>")
            continue
        if m := re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", line.strip()):
            flush_para(); flush_list()
            cap = inline(m.group(1))
            out.append(f'<figure><img src="{html.escape(m.group(2))}" alt="{cap}">'
                       + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")
            continue
        flush_list()
        para.append(line.strip())
    flush_para(); flush_list(); flush_quote(); flush_table()
    return "\n".join(out)


# ---------------------------------------------------------------- articles
def parse_article(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        print(f"skip (no front matter): {path.name}", file=sys.stderr)
        return None
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = re.sub(r"\s+#.*$", "", line)
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            meta[k.strip().lower()] = v
    if meta.get("draft", "").lower() in ("true", "yes"):
        return None
    for key in ("title", "date"):
        if not meta.get(key):
            print(f"skip (missing {key}): {path.name}", file=sys.stderr)
            return None
    when = None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            when = datetime.strptime(meta["date"], fmt).replace(tzinfo=ET)
            break
        except ValueError:
            pass
    if when is None:
        print(f"skip (bad date): {path.name}", file=sys.stderr)
        return None
    slug = path.stem
    section = meta.get("section", "Front Page")
    words = len(re.findall(r"\w+", m.group(2)))
    body = markdown_to_html(m.group(2).strip())
    brief = [b.strip() for b in meta.get("brief", "").split("|") if b.strip()]
    if brief:
        body = ('<div class="brief"><p><strong>In brief</strong></p><ul>'
                + "".join(f"<li>{inline(b)}</li>" for b in brief) + "</ul></div>\n" + body)
    if meta.get("source_url"):
        label = html.escape(meta.get("source") or "the original")
        body += (f'\n<p class="source">Read the full story: <a href="{html.escape(meta["source_url"])}">'
                 f"{label}</a></p>")
    return {
        "slug": slug, "title": meta["title"], "date": when, "section": section,
        "summary": meta.get("summary", ""), "issue": meta.get("issue", ""),
        "source_url": meta.get("source_url", ""), "html": body,
        "minutes": max(1, round(words / 230)),
        "words": words,
        "edition": meta.get("edition", "").strip().title(),
    }


def section_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ---------------------------------------------------------------- output
# One feed item per issue: all of a day's articles combined into a single post.
# An article may set `edition: Breakfast|Lunch|Dinner` to split a day into at most three posts.
SECTION_ORDER = ["Almanac", "Weather", "Front Page", "Nation & World", "Faith", "Wildcats",
                 "Around Town", "Creek Report", "Kentucky Voices", "Turntable", "Sky",
                 "Farm & Garden", "Creed & Controversy", "Ideas", "Crossword", "Followed", "Nature"]
EDITION_ORDER = {"Breakfast": 0, "": 1, "Lunch": 1, "Dinner": 2}


def absolutize(body: str, base: str) -> str:
    """Feed readers need absolute URLs for images and in-site links."""
    return re.sub(r'(src|href)="(?!https?:|mailto:|#)/?([^"]+)"', rf'\1="{base}\2"', body)


def build_issues(arts: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for a in arts:
        groups.setdefault((a["date"].date(), a["edition"]), []).append(a)
    issues = []
    for (day, ed), items in groups.items():
        items.sort(key=lambda a: (SECTION_ORDER.index(a["section"]) if a["section"] in SECTION_ORDER
                                  else len(SECTION_ORDER), a["date"]))
        nums = [a["issue"] for a in items if a["issue"]]
        slug = day.isoformat() + (f"-{ed.lower()}" if ed else "")
        when = max(a["date"] for a in items)
        title = f"{CONFIG['title']} — {day.strftime('%a, %b %-d, %Y')}" + (f" · {ed}" if ed else "")
        toc = "".join(f"<li><a href='#{a['slug']}'>{html.escape(a['title'])}</a> "
                      f"<span class='sec'>{html.escape(a['section'])}</span></li>" for a in items)
        parts = [f"<nav class='toc'><p><strong>In this issue</strong> · "
                 f"{max(1, round(sum(a['words'] for a in items) / 230))} min read</p><ol>{toc}</ol></nav>"]
        for a in items:
            parts.append(f"<section class='story' id='{a['slug']}'><div class='kicker'>{html.escape(a['section'])}"
                         f" · {a['minutes']} min</div><h2>{html.escape(a['title'])}</h2>{a['html']}"
                         f"<p class='back'><a href='#top'>↑ Contents</a></p></section>")
        summary = " · ".join(a["title"] for a in items[:4]) + (" …" if len(items) > 4 else "")
        issues.append({"slug": slug, "title": title, "date": when, "edition": ed,
                       "number": nums[0] if nums else "", "summary": summary, "items": items,
                       "html": "\n<hr>\n".join(parts)})
    issues.sort(key=lambda i: (i["date"].date(), EDITION_ORDER.get(i["edition"], 1)), reverse=True)
    return issues


def rss(issues: list[dict], base: str) -> str:
    now = format_datetime(datetime.now(timezone.utc))
    t = html.escape(CONFIG["title"])
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>", f"<title>{t}</title>", f"<link>{base}</link>",
        f"<description>{html.escape(CONFIG.get('description', ''))}</description>",
        "<language>en-us</language>", f"<lastBuildDate>{now}</lastBuildDate>",
        f'<atom:link href="{base}feed.xml" rel="self" type="application/rss+xml"/>',
        f"<image><url>{base}icon.png</url><title>{t}</title><link>{base}</link></image>",
    ]
    for i in issues:
        link = f"{base}a/{i['slug']}.html"
        body = absolutize(i["html"], base).replace("]]>", "]]]]><![CDATA[>")
        body = body.replace("href='#", f"href='{link}#")
        parts += ["<item>", f"<title>{html.escape(i['title'])}</title>", f"<link>{link}</link>",
                  f'<guid isPermaLink="true">{link}</guid>', f"<pubDate>{format_datetime(i['date'])}</pubDate>",
                  f"<description>{html.escape(i['summary'])}</description>",
                  f"<content:encoded><![CDATA[{body}]]></content:encoded>", "</item>"]
    parts += ["</channel>", "</rss>"]
    return "\n".join(parts) + "\n"


def page(title: str, inner: str, base: str) -> str:
    name = html.escape(CONFIG["title"])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(title)}</title>
<link rel="alternate" type="application/rss+xml" title="{name}" href="{base}feed.xml">
<link rel="icon" href="{base}icon.png">
<link rel="stylesheet" href="{base}style.css">
</head><body id="top">
<header class="mast"><a href="{base}">{name}</a><div class="motto">{html.escape(CONFIG.get('motto', ''))}</div></header>
<main>{inner}</main>
<footer>Written for one reader. Summaries are in our own words; follow the links to read the full stories and support the original creators.</footer>
</body></html>
"""


def main() -> None:
    base = base_url()
    arts = [a for p in sorted(ARTICLES.glob("*.md")) if (a := parse_article(p))]
    issues = build_issues(arts)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "a").mkdir(parents=True)
    if STATIC.exists():
        for f in STATIC.iterdir():
            if f.is_file():
                shutil.copy2(f, OUT / f.name)
            elif f.is_dir():
                shutil.copytree(f, OUT / f.name)

    (OUT / "feed.xml").write_text(rss(issues[:FEED_LIMIT], base), encoding="utf-8")
    for i in issues:
        meta = i["date"].strftime("%A, %B %-d, %Y") + (f" · {i['edition']}" if i["edition"] else "")
        if i["number"]:
            meta += f" · No. {i['number']}"
        inner = f"<article><div class='kicker'>{html.escape(meta)}</div>{absolutize(i['html'], base)}</article>"
        (OUT / "a" / f"{i['slug']}.html").write_text(page(i["title"], inner, base), encoding="utf-8")

    rows = [f"<p class='subscribe'>Subscribe in NetNewsWire: <a href='{base}feed.xml'>{base}feed.xml</a></p>"]
    for i in issues[:FEED_LIMIT]:
        rows.append(f"<h2 class='day'><a href='{base}a/{i['slug']}.html'>"
                    f"{html.escape(i['date'].strftime('%A, %B %-d, %Y'))}"
                    + (f" · {html.escape(i['edition'])}" if i["edition"] else "") + "</a></h2><ul class='issue'>"
                    + "".join(f"<li><span class='sec'>{html.escape(a['section'])}</span> "
                              f"<a href='{base}a/{i['slug']}.html#{a['slug']}'>{html.escape(a['title'])}</a></li>"
                              for a in i["items"]) + "</ul>")
    (OUT / "index.html").write_text(page(CONFIG["title"], "\n".join(rows), base), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built {len(arts)} articles into {len(issues)} issue(s) → {OUT} (base {base})")


if __name__ == "__main__":
    main()
