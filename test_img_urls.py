import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoProject1.settings'
django.setup()
from django.conf import settings
print("MEDIA_SERVE_MODE:", settings.MEDIA_SERVE_MODE)
print("MEDIA_PUBLIC_BASE_URL:", settings.MEDIA_PUBLIC_BASE_URL)

from gearbox.models import GearBox
g = GearBox.objects.select_related('model_line__brand').first()
print("\nGearBox:", g.code if g else 'NONE', g.name if g else '')
print("model_line:", g.model_line.name if g and g.model_line else None)
print("model_line.images count:", g.model_line.images.count() if g and g.model_line else 0)
print("item.images count:", g.images.count() if g else 0)

# Проверяем URL картинок
if g and g.model_line:
    imgs = g._get_images_section()
    print("\n_get_images_section:")
    for i in imgs[:3]:
        print(f"  url: {i['url']}")
        print(f"  preview_url: {i['preview_url']}")

# Проверяем public_url (только у MediaLibraryItem, не у GearBox)
if g:
    print("\npublic_url:", getattr(g, 'public_url', 'N/A (GearBox не имеет public_url)'))

# Проверяем get_serve_url на первой картинке
if g and g.model_line:
    img = g.model_line.images.first()
    if img:
        print("\nget_serve_url('direct'):", img.get_serve_url('direct'))
        print("public_url:", img.public_url)
        print("media_file:", img.media_file)
        print("media_file.url:", img.media_file.url if img.media_file else None)
    else:
        print("\nНЕТ КАРТИНОК у model_line!")
