# Generated manually 2026-09-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_actuators', '0038_alter_pneumaticexdoption_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pneumaticactuatormodelline',
            name='spec_template',
            field=models.JSONField(blank=True, default=dict, help_text='JSON: {группа: {подпись: ключ_поля}}. Пусто — берётся из типа оборудования.', verbose_name='Шаблон спецификации'),
        ),
    ]
