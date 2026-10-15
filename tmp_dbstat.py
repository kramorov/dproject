import sqlite3

conn = sqlite3.connect('db.sqlite3')
rows = conn.execute(
    'SELECT name, SUM(pgsize) AS bytes FROM dbstat GROUP BY name ORDER BY bytes DESC LIMIT 15'
).fetchall()
for name, b in rows:
    print('%-55s %8.2f MB' % (name, b / 1024 / 1024))
tot = conn.execute('SELECT SUM(pgsize) FROM dbstat').fetchone()[0]
print('%-55s %8.2f MB' % ('TOTAL', tot / 1024 / 1024))
conn.close()
