#!/usr/bin/env python3
"""Перевод китайских строк в data.json (справочники) на русский.

Рекурсивно заменяет строки (и ключи словарей) по словарю translate_data.json.
Данные-ключи (model, action, priceModel и т.п.) не трогаются — они в словаре не числятся.

Использование (любая версия Python 3):
    python translate_data.py <data.json> <translate_data.json> <data_ru.json>

Пример:
    python translate_data.py "_internal/data.json" translate_data.json data_ru.json
"""

import json
import sys


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)

    data_path, mapping_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stats = {'keys': 0, 'values': 0}

    def translate(obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                new_k = k
                if isinstance(k, str) and k in mapping:
                    new_k = mapping[k]
                    stats['keys'] += 1
                out[new_k] = translate(v)
            return out
        if isinstance(obj, list):
            return [translate(v) for v in obj]
        if isinstance(obj, str) and obj in mapping:
            stats['values'] += 1
            return mapping[obj]
        return obj

    result = translate(data)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

    print('Переведено ключей:', stats['keys'])
    print('Переведено значений:', stats['values'])
    print('Результат:', out_path)


if __name__ == '__main__':
    main()
