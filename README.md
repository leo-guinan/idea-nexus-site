# Idea Nexus Ventures

The public site for Idea Nexus Ventures: HumAIn products, organizational AI transformation, and network-informed market intelligence.

## Local development

```bash
python3 scripts/build.py
python3 -m http.server 4173 --directory public
```

Open http://localhost:4173.

## Chroma Cloud page index

Public Markdown pages are synced idempotently to the `inv_public_site_pages` Chroma Cloud collection. The sync uses stable route/chunk IDs, local ONNX embeddings, page metadata, stale-record cleanup, and a semantic verification query.

```bash
python3 scripts/sync_chroma_cloud.py
```

The script reads `INV_CHROMA_API_KEY`, `INV_CHROMA_TENANT`, and `INV_CHROMA_DATABASE` from the environment or `~/.hermes/.env`. It never prints or writes credentials. The GitHub workflow `.github/workflows/chroma-sync.yml` runs on page changes and expects those same names in GitHub Secrets. The public browser never receives Chroma credentials; runtime retrieval must remain server-side.

## Content architecture

- `site/pages/*.md` — source content; one page per Markdown file
- `site/data/coverage.json` — editorial coverage model and page-gap queue
- `scripts/build.py` — deterministic Markdown-to-static-HTML build
- `scripts/content_gaps.py` — reports missing or thin coverage
- `.github/workflows/content-gaps.yml` — scheduled/manual gap report
- `.github/workflows/propose-page.yml` — creates a proposal branch from an approved gap; it never publishes directly

Agent-generated content is proposal-only until a human reviews and merges it. The market has enough autonomous publishing already.
