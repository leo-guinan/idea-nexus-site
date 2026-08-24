#!/usr/bin/env python3
"""Report editorial coverage gaps without publishing anything."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
coverage = json.loads((ROOT / 'site/data/coverage.json').read_text())
existing = []
for p in (ROOT / 'site/pages').glob('*.md'):
    text = p.read_text()
    m = re.search(r'^slug:\s*(.+)$', text, re.M)
    existing.append(m.group(1).strip() if m else p.stem)
missing = [x for x in coverage['required_topics'] if x['slug'] not in existing]
thin = []
for p in (ROOT / 'site/pages').glob('*.md'):
    body = p.read_text().split('---', 2)[-1]
    words = len(re.findall(r'\b\w+\b', body))
    if words < 180:
        thin.append({'file': str(p.relative_to(ROOT)), 'words': words})
print('# Content coverage report\n')
print(f'- Existing source pages: {len(existing)}')
print(f'- Required topic slots: {len(coverage["required_topics"])}')
print(f'- Missing topic slots: {len(missing)}')
print(f'- Thin pages (<180 words): {len(thin)}\n')
if missing:
    print('## Missing topics')
    for item in missing:
        print(f"- `{item['slug']}` — {item['title']} ({item['pillar']})")
if thin:
    print('\n## Thin pages')
    for item in thin:
        print(f"- `{item['file']}` — {item['words']} words")
if not missing and not thin:
    print('\nCoverage is currently complete against the declared model.')
