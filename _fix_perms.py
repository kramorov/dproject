import re, os

# Files to protect with admin_section
ADMIN_FILES = [
    r'media_library\views\admin_upload.py',
    r'media_library\views\admin_detail.py',
    r'media_library\views\admin_variants.py',
    r'media_library\views\admin_regenerate_variants.py',
    r'media_library\views\admin_recreate_preview.py',
    r'media_library\views\admin_copy.py',
    r'cert_doc\views\admin_create.py',
    r'cert_doc\views\admin_detail.py',
    r'cert_doc\views\admin_copy.py',
    r'cert_doc\views\admin_media_upload.py',
    r'price\views\document_journal.py',
    r'price\views\document_detail.py',
    r'price\views\price_catalog.py',
    r'price\views\price_snapshot.py',
    r'price\views\ea_configurator.py',
    r'sku\views.py',
]

# Files to protect with configurator
CONFIGURATOR_FILES = [
    r'pneumatic_actuators\api\views_constructor.py',
    r'electric_actuators\api\views_constructor.py',
    r'electric_actuators\api\views_admin.py',
    r'electric_actuators\api\views_admin_items.py',
]

def process_file(filepath, section):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check which import pattern is used
    if 'from rest_framework.permissions import AllowAny' in content:
        content = content.replace(
            'from rest_framework.permissions import AllowAny',
            'from project_customers.permissions import SectionAccessPermission')
    else:
        print(f'  SKIP {filepath} — no AllowAny import found')
        return

    # Replace permission_classes = [AllowAny] + add required_section
    old = 'permission_classes = [AllowAny]'
    new = f'permission_classes = [SectionAccessPermission]\n    required_section = {section!r}'
    if old in content:
        content = content.replace(old, new)
    else:
        # Try with TODO comment
        old2 = 'permission_classes = [AllowAny]  # TODO'
        if old2 in content:
            content = content.replace(old2, new)
        else:
            print(f'  WARN {filepath} — no permission_classes = [AllowAny] found')
            return

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  OK {filepath}')

print('=== Admin section ===')
for f in ADMIN_FILES:
    if os.path.exists(f):
        process_file(f, 'admin_section')
    else:
        print(f'  MISS {f}')

print('\n=== Configurator section ===')
for f in CONFIGURATOR_FILES:
    if os.path.exists(f):
        process_file(f, 'configurator')
    else:
        print(f'  MISS {f}')

print('\nDone.')
