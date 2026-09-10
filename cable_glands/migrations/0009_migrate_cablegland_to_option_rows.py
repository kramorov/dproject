# Generated manually — перенос FK thread/body_material в through-строки с сохранением данных.

from django.db import migrations


def _fill_encoding(model, opt, fallback_code):
    """Заполнить пустую кодировку значением по умолчанию (сохраняем прежний код)."""
    if not opt.encoding and fallback_code:
        model.objects.filter(pk=opt.pk).update(encoding=fallback_code)


def migrate_articles_to_options(apps, schema_editor):
    """Связывает артикулы с through-строками (создаёт недостающие, сохраняя данные).

    Используем QuerySet.update(), а не instance.save(), чтобы не запускать
    кастомный save() артикула (генерация name/code/SKU) внутри миграции.
    """
    CableGland = apps.get_model('cable_glands', 'CableGland')
    CableGlandThreadOption = apps.get_model('cable_glands', 'CableGlandThreadOption')
    CableGlandBodyMaterialOption = apps.get_model('cable_glands', 'CableGlandBodyMaterialOption')

    for g in CableGland.objects.all():
        updates = {}

        # body_material -> body_material_option (родитель — серия)
        if g.body_material_id and g.model_line_id:
            opt = CableGlandBodyMaterialOption.objects.filter(
                model_line_id=g.model_line_id,
                body_material_id=g.body_material_id,
            ).first()
            if opt is None:
                opt = CableGlandBodyMaterialOption.objects.create(
                    model_line_id=g.model_line_id,
                    body_material_id=g.body_material_id,
                    encoding='',
                    is_default=False,
                    is_active=True,
                    sorting_order=0,
                )
            _fill_encoding(CableGlandBodyMaterialOption, opt,
                           g.body_material.code if g.body_material else '')
            updates['body_material_option_id'] = opt.id

        # thread -> thread_option (родитель — корпус «модели в серии»)
        body_id = None
        if g.model_line_item_id:
            mli = g.model_line_item
            body_id = mli.body_id if mli else None
        if g.thread_id and body_id:
            opt = CableGlandThreadOption.objects.filter(
                cable_gland_body_id=body_id,
                thread_size_id=g.thread_id,
            ).first()
            if opt is None:
                opt = CableGlandThreadOption.objects.create(
                    cable_gland_body_id=body_id,
                    thread_size_id=g.thread_id,
                    encoding='',
                    is_default=False,
                    is_active=True,
                    sorting_order=0,
                )
            _fill_encoding(CableGlandThreadOption, opt,
                           g.thread.code if g.thread else '')
            updates['thread_option_id'] = opt.id

        if updates:
            CableGland.objects.filter(pk=g.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ('cable_glands', '0008_cablegland_body_material_option_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_articles_to_options, migrations.RunPython.noop),
    ]
