import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
django.setup()

from django.conf import settings
from storage_manager.storage_backends.cloudru import CloudRuStorage

store = CloudRuStorage()

# Тестовый файл — первый попавшийся
from media_library.models import MediaLibraryItem
item = MediaLibraryItem.objects.filter(media_file__isnull=False).first()
if item:
    key = item.media_file.name
    print(f"Key: {key}")
    url = store.url(key)
    print(f"\nPresigned URL ({len(url)} chars):")
    print(url)
    print()
    
    # Извлекаем tenant_id из credential
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(url).query)
    cred = qs.get('X-Amz-Credential', [''])[0]
    print(f"X-Amz-Credential: {cred}")
    if ':' in cred:
        tenant = cred.split(':')[0]
        print(f"Extracted tenant: {tenant}")
    
    # Проверяем через curl
    print(f"\nTest with curl:")
    print(f'curl -I "{url}"')
else:
    print("No media item found")
