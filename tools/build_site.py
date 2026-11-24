#!/usr/bin/env python3
"""Static offline site generator for the Python -> Interview Ready study course.

Usage:  .venv/bin/python tools/build_site.py [--open]

Reads the course folders (markdown, .py, .sql), writes a fully offline site into
site/ (works from file://, relative links only, data passed via <script src>).
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import posixpath
import re
import shutil
import sys
import time
import webbrowser
from html.parser import HTMLParser
from urllib.parse import unquote

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, SqlLexer, TextLexer

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
SITE = os.path.join(ROOT, "site")
ASSETS_SRC = os.path.join(TOOLS, "site_assets")
MANIFEST = os.path.join(TOOLS, "site_manifest.json")

SKIP_DIRS = {".venv", "venv", "site", "tools", "__pycache__", ".pytest_cache", "node_modules"}
CODE_EXTS = {".py": PythonLexer, ".sql": SqlLexer}
SEARCH_LIMIT = 6000

# rank of well-known filenames inside a folder (lower first)
FILE_RANK = {
    "README.md": 0, "lesson.md": 1, "interview-qa.md": 2, "cheatsheet.md": 3, "labs.md": 4,
    "rapid-fire.md": 6, "mock-interview.md": 7,
    "exercises.py": 8, "test_exercises.py": 9, "schema.py": 10, "setup.sql": 11, "practice.sql": 12,
}
LABELS = {
    "lesson.md": "Lesson", "interview-qa.md": "Interview Q&A", "cheatsheet.md": "Cheatsheet",
    "labs.md": "Labs", "exercises.py": "Exercises (code)", "test_exercises.py": "Tests (code)",
    "setup.sql": "setup.sql (code)", "practice.sql": "practice.sql (code)",
}


# ---------------------------------------------------------------- helpers
def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def prettify(name: str) -> str:
    base = os.path.splitext(name)[0] if re.search(r"\.\w+$", name) else name
    m = re.match(r"^(week|project|problem|chapter|lab)-0*(\d+)-(.*)$", base, re.I)
    if m:
        return f"{m.group(1).capitalize()} {m.group(2)}: {m.group(3).replace('-', ' ').capitalize()}"
    m = re.match(r"^0*(\d+)-(.*)$", base)
    if m:
        return f"{m.group(1)}. {m.group(2).replace('-', ' ').capitalize()}"
    return base.replace("-", " ").replace("_", " ").capitalize()


def track_default_title(folder: str) -> str:
    m = re.match(r"^\d+-(.*)$", folder)
    return (m.group(1) if m else folder).replace("-", " ").title()


def json_js(obj) -> str:
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")


def relpath(target: str, from_dir: str) -> str:
    return posixpath.relpath(target, from_dir or ".")


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, d):
        self.parts.append(d)


def plain_text(h: str) -> str:
    p = _Text()
    p.feed(h)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def strip_tags(h: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


# ---------------------------------------------------------------- model
class Page:
    def __init__(self, rel: str):
        self.rel = rel  # posix path relative to project root
        self.ext = posixpath.splitext(rel)[1]
        self.is_code = self.ext in CODE_EXTS
        if self.is_code:
            self.id = rel
            self.out = rel + ".html"
        else:
            self.id = rel[: -len(self.ext)]
            self.out = self.id + ".html"
        self.dir = posixpath.dirname(rel)
        self.out_dir = posixpath.dirname(self.out)
        self.root = "../" * (self.out.count("/"))
        self.name = posixpath.basename(rel)
        self.title = self.name       # contextual title (pager / search)
        self.nav_title = self.name
        self.h1 = self.name
        self.body = ""
        self.text = ""
        self.section = ""
        self.manifest_title = None
        self.blurb = None
        self.plain = False


class Node:
    """Directory node in the content tree."""

    def __init__(self, rel: str):
        self.rel = rel
        self.name = posixpath.basename(rel)
        self.title = prettify(self.name) if rel else ""
        self.meta = {}
        self.dirs: list[Node] = []
        self.pages: list[Page] = []
        self.children: list = []  # ordered mix of Node / Page

    def all_pages(self):
        for c in self.children:
            if isinstance(c, Page):
                yield c
            else:
                yield from c.all_pages()


def file_sort_key(name: str):
    return (FILE_RANK.get(name, 5), natural_key(name))


def scan(abs_dir: str, rel: str, is_root=False) -> Node:
    node = Node(rel)
    entries = sorted(os.listdir(abs_dir), key=natural_key)
    subdirs, files = [], []
    for e in entries:
        full = os.path.join(abs_dir, e)
        if os.path.isdir(full):
            if e.startswith(".") or e in SKIP_DIRS:
                continue
            sub = scan(full, posixpath.join(rel, e) if rel else e)
            if any(True for _ in sub.all_pages()):
                subdirs.append(sub)
        else:
            if e.startswith("."):
                continue
            ext = os.path.splitext(e)[1]
            if ext not in (".md", *CODE_EXTS):
                continue
            if is_root and e != "PROGRESS.md":
                continue
            files.append(e)
    files.sort(key=file_sort_key)
    readme = [f for f in files if f == "README.md"]
    rest = [f for f in files if f != "README.md"]
    pg = lambda f: Page(posixpath.join(rel, f) if rel else f)
    node.children = [pg(f) for f in readme] + subdirs + [pg(f) for f in rest]
    node.dirs = subdirs
    return node


def apply_meta(node: Node, entry: dict, is_track=False):
    """Apply a manifest entry (titles, blurbs, ordering) to a directory node, recursively."""
    node.meta = entry or {}
    if not entry:
        return
    if entry.get("title") and not is_track:
        node.title = entry["title"]
    kids = {c.name: c for c in node.children}
    listed, seen = [], set()

    def take(name):
        c = kids.get(name)
        if c is not None and name not in seen:
            seen.add(name)
            return c
        return None

    for w in entry.get("weeks", []) or []:
        if not isinstance(w, dict):
            continue
        if "folder" in w:
            c = take(w["folder"])
            if isinstance(c, Node):
                apply_meta(c, w)
                listed.append(c)
        elif "file" in w:
            c = take(w["file"])
            if isinstance(c, Page):
                c.manifest_title, c.blurb, c.plain = w.get("title"), w.get("blurb"), is_track
                listed.append(c)
    for w in entry.get("files", []) or []:
        c = take(w.get("file", "")) if isinstance(w, dict) else None
        if isinstance(c, Page):
            c.manifest_title, c.blurb = w.get("title"), w.get("blurb")
            listed.append(c)
    head, tail = [], []
    for w in entry.get("root_files", []) or []:
        c = take(w.get("file", "")) if isinstance(w, dict) else None
        if isinstance(c, Page):
            c.manifest_title = w.get("title")
            (head if c.name == "README.md" else tail).append(c)
    # unlisted README (no manifest entry) stays first
    unlisted = [c for c in node.children if c.name not in seen]
    readme = [c for c in unlisted if isinstance(c, Page) and c.name == "README.md"]
    unlisted = [c for c in unlisted if c not in readme]
    node.children = head + readme + listed + unlisted + tail
    node.dirs = [c for c in node.children if isinstance(c, Node)]


# ---------------------------------------------------------------- markdown
MERMAID_RE = re.compile(r"^([ \t]*)```mermaid[ \t]*\n(.*?)\n[ \t]*```[ \t]*$", re.S | re.M)


LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def fix_list_spacing(src: str) -> str:
    """python-markdown needs a blank line before a list; many lessons omit it."""
    out, in_fence, prev = [], False, ""
    for line in src.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        elif (not in_fence and LIST_ITEM_RE.match(line) and prev.strip()
              and not LIST_ITEM_RE.match(prev) and not prev.startswith((" ", "\t", ">", "|", "#"))):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def render_md(src: str) -> str:
    src = fix_list_spacing(src)
    stash = []

    def grab(m):
        stash.append(m.group(2))
        return f"\n\nMERMAIDSTASHTOKEN{len(stash) - 1}X\n\n"

    src = MERMAID_RE.sub(grab, src)
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists", "attr_list", "md_in_html", "codehilite"],
        extension_configs={"codehilite": {"css_class": "highlight", "guess_lang": False},
                           "toc": {"permalink": False}},
    )
    out = md.convert(src)
    for i, code in enumerate(stash):
        out = out.replace(f"<p>MERMAIDSTASHTOKEN{i}X</p>",
                          f'<pre class="mermaid">{html.escape(code, quote=False)}</pre>')
    return out


A_RE = re.compile(r'<a\b([^>]*?)\bhref="([^"]*)"([^>]*)>')
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


class Linker:
    def __init__(self, by_rel: dict, dir_first: dict):
        self.by_rel = by_rel
        self.dir_first = dir_first
        self.broken = []

    def resolve(self, src_rel_dir: str, path: str):
        full = posixpath.normpath(posixpath.join(src_rel_dir, path))
        if full.startswith("..") or full.startswith("/"):
            return None, False
        if full == ".":
            full = ""
        if full in self.by_rel:
            return self.by_rel[full], True
        for cand in (posixpath.join(full, "README.md"),):
            if cand in self.by_rel:
                return self.by_rel[cand], True
        if full in self.dir_first:
            return self.dir_first[full], True
        return None, os.path.exists(os.path.join(ROOT, full))

    def rewrite(self, h: str, src_rel: str, src_dir: str, out_dir: str) -> str:
        def sub(m):
            pre, href, post = m.group(1), m.group(2), m.group(3)
            raw = html.unescape(href)
            if raw.startswith("#") or raw == "":
                return m.group(0)
            if raw.startswith("//") or SCHEME_RE.match(raw):
                if re.match(r"https?:", raw, re.I) and "target=" not in pre + post:
                    post += ' target="_blank" rel="noopener"'
                return f'<a{pre}href="{href}"{post}>'
            path, _, frag = raw.partition("#")
            path = unquote(path.split("?")[0])
            target, exists = self.resolve(src_dir, path)
            if target is None:
                if not exists:
                    self.broken.append((src_rel, raw))
                return m.group(0)
            new = relpath(target.out, out_dir)
            if frag:
                new += "#" + frag
            return f'<a{pre}href="{html.escape(new)}"{post}>'
        return A_RE.sub(sub, h)


# ---------------------------------------------------------------- pygments css
def write_pygments_css(path: str):
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs('[data-theme="dark"] .highlight')
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* light */\n" + light + "\n/* dark */\n" + dark + "\n")


# ---------------------------------------------------------------- html shell
def shell(title, root, pid, ptype, inner, prev=None, nxt=None, meta=""):
    def pg(cls, p, arrow):
        if not p:
            return ""
        t = html.escape(p.title)
        href = html.escape(root + p.out)
        txt = f"← {t}" if arrow == "prev" else f"{t} →"
        return f'<a class="{cls}" href="{href}">{txt}</a>'
    pager = pg("prev", prev, "prev") + pg("next", nxt, "next")
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)} | Study Hub</title>"
        f'<link rel="stylesheet" href="{root}assets/style.css">'
        f'<link rel="stylesheet" href="{root}assets/pygments.css"></head>\n'
        f'<body data-root="{root}" data-page-id="{html.escape(pid)}" data-page-type="{ptype}">\n'
        '<header id="topbar"><button id="menu-toggle" aria-label="Toggle menu">☰</button>'
        f'<a class="brand" href="{root}index.html">Study Hub</a>'
        '<input id="search" type="search" placeholder="Search (press /)" autocomplete="off">'
        '<div id="search-results" hidden></div>'
        '<button id="theme-toggle" aria-label="Toggle theme">◐</button></header>\n'
        '<div id="layout"><nav id="sidebar"><div id="nav-tree"></div></nav>'
        f'<main id="content">{meta}<article class="doc">\n{inner}\n</article>'
        f'<div class="pager">{pager}</div></main><aside id="toc"></aside></div>\n'
        f'<script src="{root}assets/data.js"></script><script src="{root}assets/app.js"></script>'
        "</body></html>\n"
    )


# ---------------------------------------------------------------- main build
def load_manifest():
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa
            print(f"WARNING: could not read manifest: {e}")
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open site/index.html afterwards")
    args = ap.parse_args()
    t0 = time.time()

    manifest = load_manifest()
    mtracks = {t.get("folder"): t for t in manifest.get("tracks", []) if isinstance(t, dict)}

    root_node = scan(ROOT, "", is_root=True)
    # split top-level into tracks and root pages
    track_nodes = [c for c in root_node.children if isinstance(c, Node)]
    root_pages = [c for c in root_node.children if isinstance(c, Page)]

    rec = manifest.get("recommended_order") or []

    def track_order(n: Node):
        mt = mtracks.get(n.name, {})
        m = re.match(r"^(\d+)", n.name)
        fallback = int(m.group(1)) if m else 999
        if n.name in rec:
            return (0, rec.index(n.name), natural_key(n.name))
        return (1, mt.get("order", fallback), natural_key(n.name))
    track_nodes.sort(key=track_order)

    for t in track_nodes:
        mt = mtracks.get(t.name, {})
        t.title = mt.get("title") or track_default_title(t.name)
        apply_meta(t, mt, is_track=True)

    # collect pages & titles; render
    all_pages: list[Page] = []
    for t in track_nodes:
        all_pages.extend(t.all_pages())
    all_pages.extend(root_pages)
    by_rel = {p.rel: p for p in all_pages}
    dir_first = {}

    def reg_dirs(n: Node):
        for c in n.children:
            if isinstance(c, Node):
                dir_first[c.rel] = next(iter(c.all_pages()))
                reg_dirs(c)
    reg_dirs(root_node)

    # titles that need folder context
    def assign(n: Node, section: str, parent_title: str):
        for c in n.children:
            if isinstance(c, Node):
                assign(c, section, c.title)
            else:
                c.section = section
                c._parent_title = parent_title

    for t in track_nodes:
        assign(t, t.title, t.title)

    linker = Linker(by_rel, dir_first)
    for p in all_pages:
        with open(os.path.join(ROOT, p.rel), encoding="utf-8", errors="replace") as f:
            src = f.read().replace(ROOT, "<project-root>")
        if p.is_code:
            lexer = CODE_EXTS[p.ext]()
            code = highlight(src, lexer, HtmlFormatter(cssclass="highlight"))
            p.h1 = p.name
            p.body = (f'<h1>{html.escape(p.name)}</h1>'
                      f'<p class="code-path"><code>{html.escape(p.rel)}</code></p>\n{code}')
            p.text = ""
        else:
            body = render_md(src)
            body = linker.rewrite(body, p.rel, p.dir, p.out_dir)
            m = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", body, re.S)
            if m:
                p.h1 = strip_tags(m.group(1))
            else:
                p.h1 = prettify(p.name)
                body = f"<h1>{html.escape(p.h1)}</h1>\n" + body
            p.body = body
            p.text = plain_text(body)[:SEARCH_LIMIT]
        # titles
        parent = getattr(p, "_parent_title", "")
        if p.name == "PROGRESS.md":
            p.nav_title = p.title = "Progress notes"
            p.section = "Notes"
        elif p.manifest_title:
            p.nav_title = p.manifest_title
            p.title = p.nav_title if (p.plain or not parent) else f"{parent}: {p.nav_title}"
        elif p.name in LABELS:
            p.nav_title = LABELS[p.name]
            p.title = f"{parent}: {LABELS[p.name]}" if parent else LABELS[p.name]
        elif p.is_code:
            p.nav_title = p.name
            p.title = f"{parent}: {p.name}" if parent else p.name
        else:
            p.nav_title = p.title = p.h1

    # ordered flat list
    flat = all_pages  # already ordered: tracks in order then root pages
    index_of = {p.id: i for i, p in enumerate(flat)}

    # NAV
    def nav_page(p: Page):
        d = {"title": p.nav_title, "id": p.id, "path": p.out, "children": [],
             "track": p.rel.split("/")[0] if "/" in p.rel else ""}
        if p.blurb:
            d["blurb"] = p.blurb
        return d

    def nav_node(n: Node, track: str):
        d = {"title": n.title, "id": n.rel, "path": "", "children": [], "track": track}
        if n.meta.get("blurb"):
            d["blurb"] = n.meta["blurb"]
        for c in n.children:
            d["children"].append(nav_node(c, track) if isinstance(c, Node) else
                                 dict(nav_page(c), track=track))
        return d

    nav = []
    for t in track_nodes:
        d = nav_node(t, t.name)
        for k in ("description", "hours", "kind", "stage"):
            if t.meta.get(k):
                d[k] = t.meta[k]
        nav.append(d)
    for p in root_pages:
        nav.append(nav_page(p))

    # write site
    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    os.makedirs(os.path.join(SITE, "assets"))
    if os.path.isdir(ASSETS_SRC):
        for name in os.listdir(ASSETS_SRC):
            s = os.path.join(ASSETS_SRC, name)
            d = os.path.join(SITE, "assets", name)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    else:
        print("note: tools/site_assets not found; style.css/app.js not copied")
    write_pygments_css(os.path.join(SITE, "assets", "pygments.css"))

    # breadcrumb
    def breadcrumb(p: Page):
        parts = [f'<a href="{p.root}index.html">Home</a>']
        segs = p.rel.split("/")[:-1]
        acc = ""
        for s in segs:
            acc = f"{acc}/{s}" if acc else s
            tgt = dir_first.get(acc)
            title = next((n.title for n in _iter_nodes(track_nodes) if n.rel == acc), prettify(s))
            if tgt:
                parts.append(f'<a href="{html.escape(p.root + tgt.out)}">{html.escape(title)}</a>')
            else:
                parts.append(html.escape(title))
        parts.append(f"<span>{html.escape(p.nav_title if p.name in LABELS else p.h1)}</span>")
        return '<nav class="breadcrumb">' + " / ".join(parts) + "</nav>"

    def _iter_nodes(nodes):
        for n in nodes:
            yield n
            yield from _iter_nodes([c for c in n.children if isinstance(c, Node)])

    for p in all_pages:
        i = index_of[p.id]
        prev = flat[i - 1] if i > 0 else None
        nxt = flat[i + 1] if i + 1 < len(flat) else None
        meta = (f'<div class="page-meta">{breadcrumb(p)}'
                f'<button id="mark-done" data-id="{html.escape(p.id)}">Mark as done</button></div>')
        page_html = shell(p.h1, p.root, p.id, "code" if p.is_code else "doc", p.body, prev, nxt, meta)
        out = os.path.join(SITE, p.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(page_html)

    # index
    cards = []
    for t in track_nodes:
        pages = list(t.all_pages())
        mt = t.meta
        desc = html.escape(mt.get("description", ""))
        hours = html.escape(str(mt.get("hours", "")))
        kind = html.escape(mt.get("kind", ""))
        cards.append(
            f'<a class="track-card" data-track="{html.escape(t.name)}" data-kind="{kind}" '
            f'href="{html.escape(pages[0].out)}"><h3>{html.escape(t.title)}</h3>'
            f'<p class="desc">{desc}</p>'
            f'<p class="meta"><span class="hours">{hours}</span> '
            f'<span class="count">{len(pages)} pages</span></p>'
            '<div class="progress"><span style="width:0%"></span></div></a>')
    roadmap = ""
    sched = by_rel.get("09-behavioral-career/06-master-study-schedule.md")
    if sched:
        rb = render_md(open(os.path.join(ROOT, sched.rel), encoding="utf-8").read().replace(ROOT, "<project-root>"))
        rb = re.sub(r"<h1[^>]*>.*?</h1>", "", rb, count=1, flags=re.S)
        rb = linker.rewrite(rb, sched.rel, sched.dir, "")
        roadmap = f'<section id="roadmap"><h2>Study roadmap</h2>\n{rb}\n</section>'
    home = (
        '<section class="hero"><h1>Python → Interview Ready Study Hub</h1>'
        '<p>Offline study course: lessons, interview Q&amp;A, cheatsheets, labs and exercises. '
        'Your progress is stored in this browser.</p></section>\n'
        '<div id="continue"></div>\n'
        f'<section id="tracks"><h2>Tracks</h2><div class="track-grid">\n' + "\n".join(cards) +
        f'\n</div></section>\n{roadmap}')
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(shell("Python → Interview Ready Study Hub", "", "index", "home", home,
                      None, flat[0] if flat else None))

    # data.js
    counts = {"pages": len(all_pages), "tracks": len(track_nodes),
              "doc": sum(1 for p in all_pages if not p.is_code),
              "code": sum(1 for p in all_pages if p.is_code)}
    search = [{"id": p.id, "title": p.title, "path": p.out,
               "section": p.section, "text": p.text} for p in all_pages]
    pages_flat = [{"id": p.id, "title": p.title, "path": p.out} for p in all_pages]
    meta = {"generated": datetime.date.today().isoformat(), "counts": counts}
    with open(os.path.join(SITE, "assets", "data.js"), "w", encoding="utf-8") as f:
        f.write(f"window.NAV={json_js(nav)};\nwindow.SEARCH_INDEX={json_js(search)};\n"
                f"window.PAGES_FLAT={json_js(pages_flat)};\nwindow.SITE_META={json_js(meta)};\n")

    # summary
    broken = sorted(set(linker.broken))
    print(f"Built {len(all_pages)} pages ({counts['doc']} docs, {counts['code']} code) "
          f"in {len(track_nodes)} tracks -> {SITE}")
    print(f"Broken internal links: {len(broken)}")
    for src, href in broken[:60]:
        print(f"  {src}: {href}")
    if len(broken) > 60:
        print(f"  ... {len(broken) - 60} more")
    print(f"Done in {time.time() - t0:.2f}s")
    if args.open:
        webbrowser.open("file://" + os.path.join(SITE, "index.html"))


if __name__ == "__main__":
    sys.exit(main())
