import json, glob

for f in sorted(glob.glob('_sample_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    resp = d.get('response', '')
    lines = resp.split('\n')

    status_line = ''
    positions = 0
    components = 0
    needs_info = False
    has_json = '```json' in resp

    for l in lines:
        ls = l.strip()
        if 'СТАТУС' in ls and '===' in ls:
            status_line = ls
        if ls.startswith('needs_info') or ls.startswith('completed'):
            needs_info = 'needs_info' in ls
        if ls.startswith('--- ПОЗИЦИЯ'):
            positions += 1
        if ls.startswith('[') and (']:' in ls or '|' in ls):
            components += 1

    print(f"#{d['id']} | p={d.get('prompt_tokens','?')} c={d.get('completion_tokens','?')} | {d.get('latency_ms','?')}ms | needs_info={needs_info} | pos={positions} comp={components}")
    # Show first meaningful lines
    for l in lines[:6]:
        if l.strip():
            print(f"    {l.strip()[:120]}")
    print()
