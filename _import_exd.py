import json, sqlite3

with open('exd_dump.json') as f:
    rows = json.load(f)

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

inserted = 0
for r in rows:
    try:
        c.execute(
            'INSERT INTO pa_controls_limitswitchbox_exd (id, limitswitchbox_id, exdoption_id) VALUES (?, ?, ?)',
            (r['id'], r['limitswitchbox_id'], r['exdoption_id'])
        )
        inserted += 1
    except sqlite3.IntegrityError:
        pass  # пропускаем дубликаты

conn.commit()
print(f'Imported {inserted}/{len(rows)} rows')
