"""
Анализ бэкапа Cloud.ru: что занимает место, какие preview-файлы можно удалить.

Использование:
    python manage.py shell < analyze_backup.py
    или просто скопировать в Django shell.
"""
import json
import os
from collections import defaultdict


def _fmt_size(size_bytes: int) -> str:
    for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.1f} ПБ'


MANIFEST_PATH = 'backups/cloudru/2026-06-01/manifest.json'

with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

files = manifest['files']
print(f'Всего файлов: {len(files)}')
print(f'Общий размер: {_fmt_size(sum(f["size"] for f in files))}')
print()

# ── Группировка по префиксу ──
by_prefix = defaultdict(lambda: {'count': 0, 'size': 0, 'exts': defaultdict(lambda: {'count': 0, 'size': 0})})
by_ext = defaultdict(lambda: {'count': 0, 'size': 0})

for obj in files:
    key = obj['key']
    size = obj['size']

    # Определяем префикс (первые 2-3 сегмента)
    parts = key.split('/')
    if len(parts) >= 3:
        prefix = '/'.join(parts[:3])
    elif len(parts) >= 2:
        prefix = '/'.join(parts[:2])
    else:
        prefix = parts[0]

    by_prefix[prefix]['count'] += 1
    by_prefix[prefix]['size'] += size

    ext = os.path.splitext(key)[1].lower() or '(none)'
    by_ext[ext]['count'] += 1
    by_ext[ext]['size'] += size
    by_prefix[prefix]['exts'][ext]['count'] += 1
    by_prefix[prefix]['exts'][ext]['size'] += size

# ── По префиксам ──
print('=== ПО ПРЕФИКСАМ ===')
for prefix in sorted(by_prefix.keys(), key=lambda p: -by_prefix[p]['size']):
    info = by_prefix[prefix]
    pct = info['size'] / manifest['total_size_bytes'] * 100
    print(f'\n{prefix}/')
    print(f'  Файлов: {info["count"]}, Размер: {_fmt_size(info["size"])} ({pct:.1f}%)')
    # Топ расширений
    for ext in sorted(info['exts'].keys(), key=lambda e: -info['exts'][e]['size'])[:5]:
        ei = info['exts'][ext]
        print(f'    {ext}: {ei["count"]} шт, {_fmt_size(ei["size"])}')

# ── По расширениям ──
print('\n=== ПО РАСШИРЕНИЯМ ===')
for ext in sorted(by_ext.keys(), key=lambda e: -by_ext[e]['size']):
    info = by_ext[ext]
    pct = info['size'] / manifest['total_size_bytes'] * 100
    print(f'  {ext:12s}  {info["count"]:5d} шт  {_fmt_size(info["size"]):>10s}  ({pct:5.1f}%)')

# ── Preview-файлы ──
print('\n=== PREVIEW-ФАЙЛЫ (media_library_previews/) ===')
preview_files = [f for f in files if f['key'].startswith('media_library_previews/')]
if preview_files:
    preview_size = sum(f['size'] for f in preview_files)
    print(f'  Файлов: {len(preview_files)}, Размер: {_fmt_size(preview_size)} ({preview_size / manifest["total_size_bytes"] * 100:.1f}%)')
    print(f'  Примеры:')
    for f in preview_files[:10]:
        print(f'    {f["key"]} ({_fmt_size(f["size"])})')
else:
    print('  Нет preview-файлов')

# ── Старые варианты (до MediaVariant) ──
print('\n=== VARIANTS (media_library/variants/) ===')
variant_files = [f for f in files if f['key'].startswith('media_library/variants/')]
if variant_files:
    var_size = sum(f['size'] for f in variant_files)
    print(f'  Файлов: {len(variant_files)}, Размер: {_fmt_size(var_size)} ({var_size / manifest["total_size_bytes"] * 100:.1f}%)')
else:
    print('  Нет variant-файлов')

# ── Категории по имени файла ──
print('\n=== ПО ТИПУ СОДЕРЖИМОГО (оценка по имени) ===')
cats = defaultdict(lambda: {'count': 0, 'size': 0})
for obj in files:
    key = obj['key'].lower()
    size = obj['size']
    if 'cert' in key or 'certif' in key or 'сертиф' in key:
        cats['certificates']['count'] += 1
        cats['certificates']['size'] += size
    elif 'schema' in key or 'схем' in key or 'drawing' in key or 'чертеж' in key:
        cats['drawings']['count'] += 1
        cats['drawings']['size'] += size
    elif 'manual' in key or 'инструкц' in key or 'руковод' in key:
        cats['manuals']['count'] += 1
        cats['manuals']['size'] += size
    elif 'tech' in key or 'тех' in key:
        cats['tech_docs']['count'] += 1
        cats['tech_docs']['size'] += size
    elif 'photo' in key or 'product' in key or 'gallery' in key or 'фото' in key or 'banner' in key:
        cats['images_gallery']['count'] += 1
        cats['images_gallery']['size'] += size
    elif 'variant' in key or 'preview' in key or '_sm.' in key or '_md.' in key or '_lg.' in key or 'icon_' in key or 'thumb_' in key or 'card_' in key:
        cats['variants_previews']['count'] += 1
        cats['variants_previews']['size'] += size
    elif 'image_processor' in key:
        cats['crop_sessions']['count'] += 1
        cats['crop_sessions']['size'] += size
    else:
        cats['other']['count'] += 1
        cats['other']['size'] += size

for cat in sorted(cats.keys(), key=lambda c: -cats[c]['size']):
    info = cats[cat]
    pct = info['size'] / manifest['total_size_bytes'] * 100
    print(f'  {cat:20s}  {info["count"]:4d} шт  {_fmt_size(info["size"]):>10s}  ({pct:5.1f}%)')

# ── Топ-20 самых больших файлов ──
print('\n=== ТОП-20 САМЫХ БОЛЬШИХ ФАЙЛОВ ===')
for f in sorted(files, key=lambda x: -x['size'])[:20]:
    print(f'  {_fmt_size(f["size"]):>10s}  {f["key"]}')
