#!/usr/bin/env python3
"""Дамп китайских строк из извлечённых .pyc-файлов PyInstaller.

Использование (Python 3.11, под которой собран exe):
    python extract_strings.py <каталог_с_pyc> <выходной_json>

Пример:
    C:\\Python311\\python.exe extract_strings.py app.exe_extracted dump_strings.json
"""

import collections
import json
import os
import sys

import pyc_strings


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)

    root = sys.argv[1]
    out_path = sys.argv[2]

    # текст -> {locations: [файл:объект]}
    result = {}
    per_file = collections.Counter()

    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith('.pyc'):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            try:
                code = pyc_strings.read_code(path)
            except Exception:
                continue

            found = collections.defaultdict(list)
            for text, obj_name in pyc_strings.iter_string_consts(code):
                if pyc_strings.is_cjk(text):
                    found[text].append(obj_name)

            if found:
                per_file[rel] = len(found)
                for text, locations in found.items():
                    entry = result.setdefault(text, {'locations': []})
                    for loc in locations:
                        entry['locations'].append(f'{rel}:{loc}')

    strings = [
        {'text': text, 'locations': info['locations']}
        for text, info in sorted(result.items())
    ]

    dump = {
        'python': '3.11',
        'total_unique': len(strings),
        'per_file': dict(sorted(per_file.items(), key=lambda kv: -kv[1])),
        'strings': strings,
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dump, f, ensure_ascii=False, indent=2)

    print(f'Уникальных китайских строк: {len(strings)}')
    for rel, count in dump['per_file'].items():
        print(f'  {rel}: {count}')
    print(f'Сохранено: {out_path}')


if __name__ == '__main__':
    main()
