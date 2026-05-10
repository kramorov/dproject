import json, sqlite3
conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()
c.execute('SELECT id, limitswitchbox_id, exdoption_id FROM pa_controls_limitswitchbox_exd')
rows = [{'id': r[0], 'limitswitchbox_id': r[1], 'exdoption_id': r[2]} for r in c.fetchall()]
json.dump(rows, open('exd_dump.json', 'w'))
print(f'Saved {len(rows)} rows')
