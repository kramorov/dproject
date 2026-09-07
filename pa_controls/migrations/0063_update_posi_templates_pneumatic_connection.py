from django.db import migrations


def update_templates(apps, schema_editor):
    """Заменяем в шаблонах серий два плейсхолдера пневмоподключения одним.

    После объединения полей thread_in/thread_out в единое pneumatic_thread
    в data_dict остался один плейсхолдер {pneumatic_connection} — обновляем
    шаблоны названий/описаний серий позиционеров.
    """
    PosiModelLine = apps.get_model('pa_controls', 'PosiModelLine')

    # Фрагмент вида «Пневмоприсоединия: вх: {pneumatic_connection_in},
    # вых:{pneumatic_connection_out};» → единое пневмоприсоединение.
    old_fragment = 'Пневмоприсоединия: вх: {pneumatic_connection_in}, вых:{pneumatic_connection_out};'
    new_fragment = 'Пневмоприсоединение: {pneumatic_connection};'

    fields = ('name_template', 'description_template', 'model_item_code_template')
    for ml in PosiModelLine.objects.all():
        changed_fields = []
        for field_name in fields:
            value = getattr(ml, field_name) or ''
            new_value = value.replace(old_fragment, new_fragment)
            # Страховка: одиночные плейсхолдеры вне фрагмента
            new_value = new_value.replace('{pneumatic_connection_in}', '{pneumatic_connection}')
            new_value = new_value.replace('{pneumatic_connection_out}', '{pneumatic_connection}')
            if new_value != value:
                setattr(ml, field_name, new_value)
                changed_fields.append(field_name)
        if changed_fields:
            ml.save(update_fields=changed_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('pa_controls', '0062_posi_body_connections_single_pneumatic_thread'),
    ]

    operations = [
        migrations.RunPython(
            update_templates,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
