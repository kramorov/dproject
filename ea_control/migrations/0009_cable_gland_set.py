# ea_control/migrations/0009_cable_gland_set.py
"""Вводы БУ: вместо одиночной резьбы — набор резьбовых отверстий
(params.ThreadSizeSet: 1×1½" NPT + 2×¾" NPT и т.п.)."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ea_control', '0008_mechanical_technology'),
        ('params', '0076_remove_safetypositionoption_requires_battery'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cuslotoption',
            name='cable_gland_thread',
        ),
        migrations.AddField(
            model_name='cuslotoption',
            name='cable_gland_set',
            field=models.ForeignKey(blank=True, help_text='Для kind=cable_gland: набор резьбовых отверстий ввода кабелей БУ (глобальный справочник params.ThreadSizeSet — каждая резьба с количеством; слот CU_CABLE_GLANDS)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cu_slot_options', to='params.threadsizeset', verbose_name='Набор резьб кабельных вводов БУ'),
        ),
    ]
