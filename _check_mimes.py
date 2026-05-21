import urllib.request, json
data = json.loads(urllib.request.urlopen('http://localhost:5173/api/core/?model=media_library.MediaLibraryItem&fmt=compact').read())['data']
mimes = set(i.get('mime_type', 'NULL') for i in data)
print("Unique mime_types:", mimes)
for i in data[:5]:
    print(f"  id={i['id']} mime_type={repr(i.get('mime_type'))} has_file={i.get('has_file')}")
