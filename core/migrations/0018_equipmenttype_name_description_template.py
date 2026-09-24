# Generated manually 2026-09-24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_set_pneumatic_actuator_spec_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmenttype',
            name='name_template',
            field=models.TextField(blank=True, help_text='Шаблон для generate_name(). Плейсхолдеры из _get_data_dict() модели-артикула (например {model_code}, {brand}). Пусто — фоллбэк на {model_code}.', null=True, verbose_name='Шаблон названия'),
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='description_template',
            field=models.TextField(blank=True, help_text='Шаблон для generate_description(). Плейсхолдеры из _get_data_dict() модели-артикула. Пусто — фоллбэк на {model_code}.', null=True, verbose_name='Шаблон описания'),
        ),
    ]
