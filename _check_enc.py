"""Check md files for mojibake / encoding issues."""
import os

MARKERS = ['Р В', 'РЎвЂ', 'вЂ', 'Р С', 'РІвЂ', 'Р в„']

files = ['SESSION.md', 'configurator.md', 'ai-assistant.md', 'ARCHITECTURE_PLAN.md', 'introspector.md']

for f in files:
    if not os.path.exists(f):
        print(f"{f:25s} — MISSING")
        continue
    try:
        b = open(f, 'rb').read()
        t = b.decode('utf-8')
        moji = any(m in t for m in MARKERS)
        # также проверяем не читается ли как cp1251 с потерей
        status = 'MOJIBAKE' if moji else 'OK'
        print(f"{f:25s} — utf8 {status}")
    except UnicodeDecodeError:
        print(f"{f:25s} — NOT UTF-8 (probably cp1251 or other)")
