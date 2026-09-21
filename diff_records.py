import sqlite3, sys
from collections import Counter

A = sys.argv[1] if len(sys.argv) > 1 else 'db.sqlite3'
B = sys.argv[2] if len(sys.argv) > 2 else 'db_head_4f00d76.sqlite3'
REPORT = 'db_diff_report.txt'

def fmt(v, limit=120):
    s = repr(v)
    return s if len(s) <= limit else s[:limit] + '...(%d chars)' % len(s)

def table_meta(con):
    cur = con.cursor()
    rows = cur.execute(
        "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name").fetchall()
    meta = {}
    for (name,) in rows:
        cols = cur.execute('pragma table_info("%s")' % name).fetchall()
        pk = [c[1] for c in cols if c[5] > 0]
        pk = pk[0] if len(pk) == 1 else None
        meta[name] = (cols, pk)
    return meta

def load(con, name, cols, pk):
    cur = con.cursor()
    cur.execute('select * from "%s"' % name)
    if pk is not None:
        d = {}
        for row in cur:
            d[row[0]] = row
        return d, pk
    return Counter(repr(r) for r in cur), None

con_a = sqlite3.connect('file:%s?mode=ro' % A, uri=True)
con_b = sqlite3.connect('file:%s?mode=ro' % B, uri=True)
meta_a = table_meta(con_a)
meta_b = table_meta(con_b)

lines = []
summary = []
for name in sorted(set(meta_a) | set(meta_b)):
    if name not in meta_a or name not in meta_b:
        summary.append('%-55s table exists only in %s' % (name, A if name in meta_a else B))
        continue
    cols, pk = meta_a[name]
    da, _ = load(con_a, name, cols, pk)
    db_, _ = load(con_b, name, cols, pk)
    if da == db_:
        continue
    added = removed = changed = 0
    details = []
    if pk is not None:
        ka, kb = set(da), set(db_)
        for k in sorted(ka - kb, key=repr):
            added += 1
            details.append(('+', 'pk=%s %s' % (fmt(k), ' | '.join('%s=%s' % (c[1], fmt(v, 80)) for c, v in zip(cols, da[k])))))
        for k in sorted(kb - ka, key=repr):
            removed += 1
            details.append(('-', 'pk=%s %s' % (fmt(k), ' | '.join('%s=%s' % (c[1], fmt(v, 80)) for c, v in zip(cols, db_[k])))))
        for k in sorted(ka & kb, key=repr):
            if da[k] != db_[k]:
                changed += 1
                diff = []
                for c, va, vb in zip(cols, da[k], db_[k]):
                    if va != vb:
                        diff.append('%s: %s -> %s' % (c[1], fmt(va, 60), fmt(vb, 60)))
                details.append(('~', 'pk=%s | %s' % (fmt(k), ' | '.join(diff))))
    else:
        ca, cb = Counter(k for k in da if isinstance(k, str)), Counter(k for k in db_ if isinstance(k, str))
        for k in sorted(ca - cb):
            added += ca[k]
            details.append(('+', fmt(k, 200)))
        for k in sorted(cb - ca):
            removed += cb[k]
            details.append(('-', fmt(k, 200)))
    summary.append('%-55s +%d -%d ~%d' % (name, added, removed, changed))
    lines.append('=== %s (+%d added, -%d removed, ~%d changed) ===' % (name, added, removed, changed))
    for sign, d in details:
        lines.append('  %s %s' % (sign, d))
    lines.append('')

print('Tables with differences (A=%s vs B=%s):' % (A, B))
for s in summary:
    print(s)
with open(REPORT, 'w', encoding='utf-8') as f:
    f.write('Record-level diff: %s (local working db) vs %s (committed HEAD db)\n\n' % (A, B))
    f.write('\n'.join(summary))
    f.write('\n\n' + '\n'.join(lines))
print('\nFull record details written to %s (%d lines)' % (REPORT, len(lines)))
