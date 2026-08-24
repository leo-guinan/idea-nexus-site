#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
required = [ROOT/'public/index.html', ROOT/'public/products/index.html', ROOT/'public/transform/index.html', ROOT/'public/transform/ai-audit/index.html', ROOT/'public/research/index.html', ROOT/'public/styles.css']
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    print('missing:', ', '.join(missing)); sys.exit(1)
for p in required:
    text = p.read_text()
    if p.suffix == '.html' and ('<title>' not in text or 'IDEA NEXUS' not in text):
        print('invalid html:', p); sys.exit(1)
print(f'passed: {len(required)} required artifacts present and branded')
