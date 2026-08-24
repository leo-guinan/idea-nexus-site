#!/usr/bin/env python3
"""Build Idea Nexus static pages from Markdown source."""
from html import escape
from pathlib import Path
import re, shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site" / "pages"
OUT = ROOT / "public"


def parse_page(path):
    text = path.read_text()
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip('"')
    return meta, body.strip()


def inline(text):
    text = escape(text, quote=False)
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def markdown(body):
    lines, out, i = body.splitlines(), [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("> "):
            out.append(f"<blockquote>{inline(line[2:])}</blockquote>")
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>"); i += 1
            out.append("<ul>" + "".join(items) + "</ul>"); continue
        elif re.match(r"^\d+ — ", line):
            out.append(f'<p class="method-step">{inline(line)}</p>')
        elif line.startswith("[") and "](" in line:
            out.append(f'<p class="text-link">{inline(line)}</p>')
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i+1].strip() and not re.match(r"^(#|###|##|> |- |\d+ — |\[)", lines[i+1]):
                i += 1; paragraph.append(lines[i])
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
        i += 1
    return "\n".join(out)


def nav(active):
    links = [("Build", "/products/", "product"), ("Transform", "/transform/", "transform"), ("Understand", "/research/", "research"), ("Field notes", "/field-notes/", "index")]
    return "".join(f'<a class="{"active" if active == key else ""}" href="{href}">{label}</a>' for label, href, key in links)


def layout(meta, content):
    title = escape(meta.get("title", "Idea Nexus Ventures"))
    kind = meta.get("kind", "page")
    accent = meta.get("accent", "")
    active = "transform" if kind in {"transform", "offer"} else kind if kind in {"product", "research"} else "index" if kind == "index" else ""
    description = escape(meta.get("summary", "Idea Nexus Ventures builds and studies systems that increase the productive power of human networks."))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Idea Nexus Ventures</title><meta name="description" content="{description}">
<link rel="stylesheet" href="/styles.css"></head><body class="accent-{escape(accent)}">
<header class="site-header"><a class="wordmark" href="/">IDEA NEXUS <span>VENTURES</span></a><nav>{nav(active)}</nav><a class="header-cta" href="/transform/ai-audit/">Start with the audit</a></header>
<main class="page-shell"><div class="page-kind">{escape(kind.upper())}</div><article class="content">{content}</article></main>
<footer class="site-footer"><div><a class="wordmark" href="/">IDEA NEXUS <span>VENTURES</span></a><p>Systems for more capable human networks.</p></div><div class="footer-links"><a href="/products/">HumAIn products</a><a href="/transform/">Organizational transformation</a><a href="/research/">Market intelligence</a><a href="/principles/">Principles</a><a href="/contact/">Contact</a></div><div class="footer-note">All the leverage. None of the hype.</div></footer>
</body></html>'''


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    count = 0
    for path in sorted(SOURCE.glob("*.md")):
        meta, body = parse_page(path)
        slug = meta.get("slug", path.stem)
        target = OUT / "index.html" if slug == "index" else OUT / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(layout(meta, markdown(body)))
        count += 1
    shutil.copy(ROOT / "site" / "styles.css", OUT / "styles.css")
    print(f"built {count} pages into {OUT}")

if __name__ == "__main__":
    main()
