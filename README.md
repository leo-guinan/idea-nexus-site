# Idea Nexus Ventures

The public site for Idea Nexus Ventures: HumAIn products, organizational AI transformation, and network-informed market intelligence.

## Local development

```bash
python3 scripts/build.py
python3 -m http.server 4173 --directory public
```

Open http://localhost:4173.

## Content architecture

- `site/pages/*.md` — source content; one page per Markdown file
- `site/data/coverage.json` — editorial coverage model and page-gap queue
- `scripts/build.py` — deterministic Markdown-to-static-HTML build
- `scripts/content_gaps.py` — reports missing or thin coverage
- `.github/workflows/content-gaps.yml` — scheduled/manual gap report
- `.github/workflows/propose-page.yml` — creates a proposal branch from an approved gap; it never publishes directly

Agent-generated content is proposal-only until a human reviews and merges it. The market has enough autonomous publishing already.
