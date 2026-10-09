"""Перенос pressure/temp с позиций на серии.

- Серии (model line) получают значения pressure_min/pressure_max/temp_min/temp_max
  из своих позиций. Для pressure_max берётся наиболее частое значение (default),
  остальные позиции глушителей сохраняют свой override.
- У глушителей позиция-переопределение остаётся в ``pressure_max``; позиции,
  совпадающие с дефолтом серии, обнуляются (0/null → берём из серии).
"""

from django.db import migrations


def _mode(values):
    """Наиболее частое значение (None игнорируется). При равенстве — первое встреченное."""
    counts = {}
    for value in values:
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


# (item_model, line_model, has_pressure_max_override)
_PAIRS = [
    ('PneumaticFitting', 'PneumaticFittingModelLine', False),
    ('PneumaticPlug', 'PneumaticPlugModelLine', False),
    ('PneumaticSilencer', 'PneumaticSilencerModelLine', True),
]


def populate_model_lines(apps, schema_editor):
    for item_name, line_name, has_override in _PAIRS:
        Item = apps.get_model('pneumatic_fittings', item_name)
        Line = apps.get_model('pneumatic_fittings', line_name)

        for line in Line.objects.all():
            items = list(Item.objects.filter(model_line_id=line.id))
            if not items:
                continue

            line.pressure_min = _mode([it.pressure_min for it in items])
            line.pressure_max = _mode([it.pressure_max for it in items])
            line.temp_min = _mode([it.temp_min for it in items])
            line.temp_max = _mode([it.temp_max for it in items])
            line.save(update_fields=['pressure_min', 'pressure_max', 'temp_min', 'temp_max'])

            if has_override:
                default_pmax = line.pressure_max
                for it in items:
                    # Совпадает с дефолтом серии — обнуляем (наследуется из серии).
                    if it.pressure_max == default_pmax:
                        it.pressure_max = None
                        it.save(update_fields=['pressure_max'])


def reverse_model_lines(apps, schema_editor):
    """Восстановить значения позиций из серий (override глушителей при этом теряется)."""
    for item_name, line_name, _has_override in _PAIRS:
        Item = apps.get_model('pneumatic_fittings', item_name)
        Line = apps.get_model('pneumatic_fittings', line_name)

        for line in Line.objects.all():
            Item.objects.filter(model_line_id=line.id).update(
                pressure_min=line.pressure_min,
                pressure_max=line.pressure_max,
                temp_min=line.temp_min,
                temp_max=line.temp_max,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('pneumatic_fittings', '0031_add_pressure_temp_to_model_line'),
    ]

    operations = [
        migrations.RunPython(populate_model_lines, reverse_model_lines),
    ]
