import sqlite3
c = sqlite3.connect('db.sqlite3').cursor()
c.execute('SELECT COUNT(*) FROM pa_controls_limitswitchbox_exd')
print('Rows:', c.fetchone()[0])
c.execute('SELECT * FROM pa_controls_limitswitchbox_exd LIMIT 3')
for r in c.fetchall():
    print(r)
