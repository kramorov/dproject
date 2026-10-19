# electric_actuators/migrations/0076_electricactuatormodelline_description_template.py
"""Добавляет шаблон описания на уровне серии (переопределение EquipmentType)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('electric_actuators', '0075_allowedcontrolunitoption_is_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='electricactuatormodelline',
            name='description_template',
            field=models.TextField(blank=True, default='', help_text='Шаблон описания серии (пусто — берётся из EquipmentType)', verbose_name='Шаблон описания'),
        ),
        migrations.AddField(
            model_name='electricactuatormodelline',
            name='description_template_i18n',
            field=models.JSONField(blank=True, default=dict, help_text='JSON: {"ru": ..., "en": ..., "cn": ...}', verbose_name='Переводы шаблона описания (ru/en/cn)'),
        ),
    ]
