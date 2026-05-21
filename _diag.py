import urllib.request, json, os

url = 'http://localhost:8000/api/core/?model=media_library.MediaLibraryItem&fmt=compact'
data = json.loads(urllib.request.urlopen(url).read())['data']
media_root = r'C:\Users\kramo\PycharmProjects\djangoProject1\media'

missing_orig = 0
missing_prev = 0
ok = 0

for i in data:
    fn = i.get('file_name', '')
    if not fn:
        continue
    orig = os.path.join(media_root, fn)
    orig_ok = os.path.exists(orig)
    
    # preview path
    prev_fn = fn.replace('media_library/', 'media_library_previews/')
    if '.' in prev_fn:
        prev_fn = prev_fn.rsplit('.', 1)[0] + '.jpg'
    prev = os.path.join(media_root, prev_fn)
    prev_ok = os.path.exists(prev)
    
    if orig_ok:
        ok += 1
    else:
        missing_orig += 1
    if not prev_ok:
        missing_prev += 1

print(f"Total items: {len(data)}")
print(f"Original files present: {ok}")
print(f"Original files MISSING: {missing_orig}")
print(f"Preview files MISSING: {missing_prev}")
print(f"\nSample MISSING originals (first 5):")
count = 0
for i in data:
    fn = i.get('file_name', '')
    if fn:
        orig = os.path.join(media_root, fn)
        if not os.path.exists(orig):
            print(f"  id={i['id']} file={fn}")
            count += 1
            if count >= 5:
                break
