import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

root = sys.argv[1] if len(sys.argv) > 1 else '.'
terms = sys.argv[2:]
for dp, dn, fn in os.walk(root):
    if '__pycache__' in dp or 'migrations' in dp or '.git' in dp:
        continue
    for f in fn:
        if not f.endswith('.py'):
            continue
        p = os.path.join(dp, f)
        try:
            s = open(p, encoding='utf-8').read()
        except Exception:
            continue
        for i, l in enumerate(s.splitlines(), 1):
            for t in terms:
                if t in l:
                    print(f'{p}:{i}: {l.strip()[:200]}')
                    break
