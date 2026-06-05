import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
django.setup()

from solenoid_valves.models import DirectionValve

dv = DirectionValve.objects.filter(code='RPA10A512GL.24DC').first()
section = dv._get_images_section()
for i, s in enumerate(section[:2]):
    print(f'img[{i}]:')
    for key in ('preview_url', 'url', 'thumb_url'):
        val = s.get(key, '')
        # show just the file path part
        path = val.split('media-storage/')[-1].split('?')[0] if 'media-storage/' in val else val[-80:]
        print(f'  {key}: ...{path}')
    print()
