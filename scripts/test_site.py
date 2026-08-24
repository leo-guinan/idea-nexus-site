#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
required = [ROOT/'public/index.html', ROOT/'public/products/index.html', ROOT/'public/humanpower/index.html', ROOT/'public/transform/index.html', ROOT/'public/transform/ai-audit/index.html', ROOT/'public/research/index.html', ROOT/'public/styles.css', ROOT/'public/marvin.js', ROOT/'public/marvin.json']
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    print('missing:', ', '.join(missing)); sys.exit(1)
for p in required:
    text = p.read_text()
    if p.suffix == '.html' and ('<title>' not in text or 'IDEA NEXUS' not in text):
        print('invalid html:', p); sys.exit(1)
    if p.suffix == '.html' and '####' in text:
        print('unrendered markdown heading:', p); sys.exit(1)
pages = list((ROOT/'public').rglob('*.html'))
marvin_js = (ROOT/'public/marvin.js').read_text()
if 'Conversation.startSession' not in marvin_js or 'elevenlabs-convai' in marvin_js or 'convai-widget-embed' in marvin_js:
    print('native ElevenLabs flow contract failed'); sys.exit(1)
for p in pages:
    text = p.read_text()
    if 'id="marvin-shell"' not in text or 'src="/marvin.js"' not in text or 'id="marvin-voice"' not in text:
        print('Marvin missing from:', p); sys.exit(1)
print(f'passed: {len(required)} required artifacts and Marvin on {len(pages)} pages')
