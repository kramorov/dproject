"""Find exact mojibake lines in md files."""
import os

MARKERS = ['\u0420\u00a0\u0412', '\u0420\u040e\u0432\u0402', '\u0432\u0402', '\u0420\u00a0\u0421', '\u0420\u0406\u0432\u0402', '\u0420\u00a0\u0432\u201e']

for f in ['SESSION.md', 'configurator.md', 'ai-assistant.md', 'ARCHITECTURE_PLAN.md', 'introspector.md']:
    if not os.path.exists(f):
        continue
    c = open(f, encoding='utf-8').read()
    bad = []
    for i, l in enumerate(c.split('\n'), 1):
        if any(m in l for m in MARKERS):
            bad.append((i, l[:90]))
    if bad:
        print(f"\n=== {f}: {len(bad)} mojibake lines ===")
        for i, l in bad[:10]:
            print(f"  {i}: {l}")
    else:
        print(f"{f}: clean")
