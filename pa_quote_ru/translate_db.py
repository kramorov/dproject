#!/usr/bin/env python3
"""Переводит локальную БД quotation.db (записи, импортированные из data.json).

Приложение хранит импортированные справочники в SQLite
%LOCALAPPDATA%/QuotationSystem/quotation.db (таблица `records`).
Этот скрипт применяет тот же словарь translate_data.json к полям
record_key и payload, а source_sha256 обновляет под переведённый data.json.
"""

import hashlib
import json
import sqlite3
import sys


def translate(obj, mapping):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nk = mapping.get(k, k) if isinstance(k, str) else k
            out[nk] = translate(v, mapping)
        return out
    if isinstance(obj, list):
        return [translate(v, mapping) for v in obj]
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    return obj


def main():
    db_path = sys.argv[1]
    mapping_path = sys.argv[2]
    data_json_path = sys.argv[3]

    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    with open(data_json_path, 'rb') as f:
        data_sha = hashlib.sha256(f.read()).hexdigest()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute('SELECT rowid, category, record_key, payload FROM records')
    rows = cur.fetchall()

    n_key = 0
    n_payload = 0
    for rowid, category, record_key, payload in rows:
        new_key = mapping.get(record_key, record_key)
        if new_key != record_key:
            n_key += 1

        new_payload = payload
        try:
            obj = json.loads(payload)
            obj = translate(obj, mapping)
            new_payload = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
            if new_payload != payload:
                n_payload += 1
        except Exception:
            new_payload = mapping.get(payload, payload)
            if new_payload != payload:
                n_payload += 1

        cur.execute(
            'UPDATE records SET record_key=?, payload=? WHERE rowid=?',
            (new_key, new_payload, rowid),
        )

    cur.execute(
        "UPDATE metadata SET value=? WHERE key='source_sha256'", (data_sha,))
    conn.commit()
    conn.close()

    print('Переведено record_key:', n_key)
    print('Переведено payload:', n_payload)
    print('source_sha256 обновлён на:', data_sha)


if __name__ == '__main__':
    main()
