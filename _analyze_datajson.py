import json, collections, re
data = json.load(open(sys.argv[1], encoding="utf-8"))
def has_cjk(s): return any('\u4e00' <= ch <= '\u9fff' for ch in s)
# collect Chinese strings: (path, is_key, text)
rows = []
def walk(obj, path, in_key=False):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and has_cjk(k):
                rows.append((path + "/<KEY>", True, k))
            walk(v, path + "/" + (k if isinstance(k,str) else "?"), False)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, path + f"[{i}]", False)
    elif isinstance(obj, str) and has_cjk(obj):
        rows.append((path, False, obj))
walk(data, "$")
print("total CJK strings (incl keys):", len(rows))
# group by top-level path
by_section = collections.Counter()
for path, is_key, text in rows:
    top = path.split("/")[1] if "/" in path else path
    by_section[top] += 1
print("by top-level section:")
for k, v in by_section.most_common():
    print(f"  {k}: {v}")
# unique texts
uniq = collections.OrderedDict()
for path, is_key, text in rows:
    uniq.setdefault(text, []).append((path, is_key))
print("\nunique texts:", len(uniq))
for text, locs in list(uniq.items()):
    # show field context (last meaningful key)
    print(repr(text), "->", len(locs), "locs; first:", locs[0])
