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
    flush_para(); flush_list(); flush_quote()
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
        body += (f'\n<p class="source">Original: <a href="{html.escape(meta["source_url"])}">'
                 f"{label}</a></p>")
    return {
        "slug": slug, "title": meta["title"], "date": when, "section": section,
        "summary": meta.get("summary", ""), "issue": meta.get("issue", ""),
        "source_url": meta.get("source_url", ""), "html": body,
        "minutes": max(1, round(words / 230)),
    }


def section_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ---------------------------------------------------------------- output
def absolutize(body: str, base: str) -> str:
    """Feed readers need absolute URLs for images and in-site links."""
    return re.sub(r'(src|href)="(?!https?:|mailto:|#)/?([^"]+)"', rf'\1="{base}\2"', body)


def rss(items: list[dict], title: str, desc: str, self_url: str, base: str) -> str:
    now = format_datetime(datetime.now(timezone.utc))
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{html.escape(title)}</title>",
        f"<link>{base}</link>",
        f"<description>{html.escape(desc)}</description>",
        "<language>en-us</language>",
        f"<lastBuildDate>{now}</lastBuildDate>",
        f'<atom:link href="{self_url}" rel="self" type="application/rss+xml"/>',
        f"<image><url>{base}icon.png</url><title>{html.escape(title)}</title><link>{base}</link></image>",
    ]
    for a in items:
        link = f"{base}a/{a['slug']}.html"
        body = absolutize(a["html"], base).replace("]]>", "]]]]><![CDATA[>")
        parts += [
            "<item>",
            f"<title>{html.escape(a['title'])}</title>",
            f"<link>{link}</link>",
            f'<guid isPermaLink="true">{link}</guid>',
            f"<pubDate>{format_datetime(a['date'])}</pubDate>",
            f"<category>{html.escape(a['section'])}</category>",
            f"<description>{html.escape(a['summary'] or a['title'])}</description>",
            f"<content:encoded><![CDATA[{body}]]></content:encoded>",
            "</item>",
        ]
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
</head><body>
<header class="mast"><a href="{base}">{name}</a><div class="motto">{html.escape(CONFIG.get('motto', ''))}</div></header>
<main>{inner}</main>
<footer>Written for one reader. Summaries are in our own words; follow the links to support the original creators.</footer>
</body></html>
"""


def main() -> None:
    base = base_url()
    arts = [a for p in sorted(ARTICLES.glob("*.md")) if (a := parse_article(p))]
    arts.sort(key=lambda a: a["date"], reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "a").mkdir(parents=True)
    (OUT / "feeds").mkdir()
    if STATIC.exists():
        for f in STATIC.iterdir():
            if f.is_file():
                shutil.copy2(f, OUT / f.name)
            elif f.is_dir():
                shutil.copytree(f, OUT / f.name)

    title, desc = CONFIG["title"], CONFIG.get("description", "")
    (OUT / "feed.xml").write_text(rss(arts[:FEED_LIMIT], title, desc, f"{base}feed.xml", base), encoding="utf-8")

    sections: dict[str, list[dict]] = {}
    for a in arts:
        sections.setdefault(a["section"], []).append(a)
    for name, items in sections.items():
        s = section_slug(name)
        (OUT / "feeds" / f"{s}.xml").write_text(
            rss(items[:FEED_LIMIT], f"{title} — {name}", desc, f"{base}feeds/{s}.xml", base),
            encoding="utf-8")

    for a in arts:
        meta = f"{a['section']} · {a['date'].strftime('%a %b %-d, %Y')} · {a['minutes']} min read"
        if a["issue"]:
            meta += f" · No. {a['issue']}"
        inner = (f'<article><div class="kicker">{html.escape(meta)}</div>'
                 f"<h1>{html.escape(a['title'])}</h1>{absolutize(a['html'], base)}</article>")
        (OUT / "a" / f"{a['slug']}.html").write_text(page(a["title"], inner, base), encoding="utf-8")

    rows, last_day = [], None
    for a in arts[:FEED_LIMIT]:
        day = a["date"].strftime("%A, %B %-d, %Y")
        if day != last_day:
            rows.append(f"<h2 class='day'>{day}</h2>")
            last_day = day
        rows.append(f"<p class='row'><span class='sec'>{html.escape(a['section'])}</span> "
                    f"<a href='{base}a/{a['slug']}.html'>{html.escape(a['title'])}</a>"
                    + (f"<br><span class='dek'>{html.escape(a['summary'])}</span>" if a["summary"] else "")
                    + "</p>")
    feeds = " · ".join(f"<a href='{base}feeds/{section_slug(n)}.xml'>{html.escape(n)}</a>"
                       for n in sorted(sections))
    inner = (f"<p class='subscribe'>Subscribe in NetNewsWire: <a href='{base}feed.xml'>{base}feed.xml</a>"
             f"<br>Section feeds: {feeds or '—'}</p>" + "\n".join(rows))
    (OUT / "index.html").write_text(page(title, inner, base), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built {len(arts)} articles, {len(sections)} sections → {OUT} (base {base})")


if __name__ == "__main__":
    main()
