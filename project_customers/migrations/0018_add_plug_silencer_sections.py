# Data migration: добавить разделы «Заглушки пневматические» и «Глушители пневматические».

# В 0015_split_site_sections эти два каталога не попали в сплит «catalog»:
# маршруты фронта требуют section-коды catalog_plug / catalog_sil (meta.section),
# а их нет в SiteSection → анонимных и пользователей редиректит на /login.
# Здесь создаём разделы и выдаём их всем, у кого есть catalog_pf (та же семья).

from django.db import migrations


NEW_SECTIONS = [
    ('catalog_plug', 'Заглушки пневматические'),
    ('catalog_sil', 'Глушители пневматические'),
]


def add_sections(apps, schema_editor):
    SiteSection = apps.get_model('project_customers', 'SiteSection')
    Role = apps.get_model('project_customers', 'Role')
    ProjectCustomer = apps.get_model('project_customers', 'ProjectCustomer')

    created_sections = []
    for i, (code, name) in enumerate(NEW_SECTIONS):
        section, _ = SiteSection.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'is_active': True,
                'sorting_order': 20 + i,
                'category': 'catalog',
            },
        )
        if not section.is_active:
            section.is_active = True
            section.save()
        created_sections.append(section)

    # Выдать тем же ролям, что имеют catalog_pf (фитинги — та же семья каталогов)
    try:
        fitting_section = SiteSection.objects.get(code='catalog_pf')
    except SiteSection.DoesNotExist:
        fitting_section = None
    if fitting_section is not None:
        for role in Role.objects.filter(section_permissions=fitting_section).distinct():
            role.section_permissions.add(*created_sections)
        for customer in ProjectCustomer.objects.filter(visible_sections=fitting_section).distinct():
            customer.visible_sections.add(*created_sections)


def remove_sections(apps, schema_editor):
    SiteSection = apps.get_model('project_customers', 'SiteSection')
    SiteSection.objects.filter(code__in=[code for code, _ in NEW_SECTIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('project_customers', '0017_remove_role_django_user'),
    ]

    operations = [
        migrations.RunPython(add_sections, remove_sections),
    ]
