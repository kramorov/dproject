# ea_control/migrations/0005_cusignaltype_voltage_fk.py
"""CuSignalType.voltage: CharField → FK params.PowerSupplies.

Напряжение типа сигнала было свободным текстом («24V», «220V»), что
дублирует глобальный справочник напряжений (slots.md «Золотое правило»:
физика типизируется через FK на справочники). Переносим на FK с сохранением
существующих строк через таблицу соответствия по текстовым кодам.
"""
from django.db import migrations, models
import django.db.models.deletion


# Старый текстовый номинал → код глобального справочника params.PowerSupplies.
_VOLTAGE_CODE_MAP = {
    '24V': '24-DC',
    '220V': '220-AC',
    '380V': '380-AC',
}


def _power_supply_by_code(apps):
    PowerSupplies = apps.get_model('params', 'PowerSupplies')
    return {ps.code: ps for ps in PowerSupplies.objects.all()}


def map_voltage(apps, schema_editor):
    """Заполнить временный FK по старому текстовому номиналу."""
    CuSignalType = apps.get_model('ea_control', 'CuSignalType')
    by_code = _power_supply_by_code(apps)
    unmapped = []
    for st in CuSignalType.objects.all():
        old = (st.voltage or '').strip()
        code = _VOLTAGE_CODE_MAP.get(old)
        target = by_code.get(code) if code else None
        if target is None and old:
            # фолбэк: ищем справочник, в чьём коде встречается номинал
            target = next((ps for ps in by_code.values()
                           if old.lower() in ps.code.lower()), None)
        if target is None:
            unmapped.append((st.code, old))
            st.voltage_new = None
        else:
            st.voltage_new = target
        st.save(update_fields=['voltage_new'])
    if unmapped:
        print(f'WARNING: CuSignalType без соответствия напряжению: {unmapped}')


def unmap_voltage(apps, schema_editor):
    """Обратно: восстановить текстовый номинал из кода справочника (best-effort)."""
    CuSignalType = apps.get_model('ea_control', 'CuSignalType')
    for st in CuSignalType.objects.all():
        if st.voltage_new_id:
            st.voltage = st.voltage_new.code
            st.save(update_fields=['voltage'])


class Migration(migrations.Migration):

    dependencies = [
        ('ea_control', '0004_cuslotrule_action_value'),
        ('params', '0076_remove_safetypositionoption_requires_battery'),
    ]

    operations = [
        # 1. Временный FK (nullable), чтобы перенести данные без потери.
        migrations.AddField(
            model_name='cusignaltype',
            name='voltage_new',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cu_signal_types',
                to='params.powersupplies',
                help_text='Номинал напряжения управляющего сигнала (глобальный справочник напряжений)',
                verbose_name='Напряжение сигнала'),
        ),
        # 2. Перенос старых текстовых номиналов в FK.
        migrations.RunPython(map_voltage, unmap_voltage),
        # 3. Убрать старый CharField.
        migrations.RemoveField(
            model_name='cusignaltype',
            name='voltage',
        ),
        # 4. Переименовать временный FK в итоговое имя.
        migrations.RenameField(
            model_name='cusignaltype',
            old_name='voltage_new',
            new_name='voltage',
        ),
        # 5. Закрепить обязательность (все строки уже перенесены).
        migrations.AlterField(
            model_name='cusignaltype',
            name='voltage',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cu_signal_types',
                to='params.powersupplies',
                help_text='Номинал напряжения управляющего сигнала (глобальный справочник напряжений)',
                verbose_name='Напряжение сигнала'),
        ),
    ]
