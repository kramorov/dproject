"""
Diagnostic script: Power Supply Option matrix for an EA model line.

Usage:
    python diag_ea_power_supply.py AR01E

Outputs a Pandas DataFrame to console:
    - Rows: model_line_items (models)
    - Columns: power supply options (voltages)
    - Values:  ✓ есть  |  ✗ есть (неакт)  |  — нет

Purpose: verify whether missing voltage options are a DB issue (no through-record,
is_active=False) or a code issue (filters, query logic).
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import pandas as pd
from electric_actuators.models import (
    ElectricActuatorModelLine,
    ElectricActuatorModelLineItem,
)
from electric_actuators.models.ea_model_line_item_options import ElectricPowerSupplyOption


def build_diag_table(model_line_name: str):
    """Build and print Pandas table."""

    # 1. Найти серию
    try:
        ml = ElectricActuatorModelLine.objects.get(name__iexact=model_line_name, is_active=True)
    except ElectricActuatorModelLine.DoesNotExist:
        print(f"ERROR: Series '{model_line_name}' not found or not active.")
        candidates = ElectricActuatorModelLine.objects.filter(
            name__icontains=model_line_name
        ).values_list('name', flat=True)
        print(f"  Available: {list(candidates)}")
        return

    print(f"\n=== {ml.name} (id={ml.id}, brand={ml.brand}) ===\n")

    # 2. Модели серии
    mli_list = list(ElectricActuatorModelLineItem.objects.filter(
        model_line=ml
    ).order_by('sorting_order'))

    # 3. Все through-записи для этой серии (активные и неактивные)
    all_records = list(ElectricPowerSupplyOption.objects.filter(
        model_line_item__model_line=ml
    ).select_related('power_supply', 'model_line_item'))

    # Уникальные напряжения
    ps_ids = sorted(set(r.power_supply_id for r in all_records))
    from params.models import PowerSupplies
    ps_map = {ps.id: ps for ps in PowerSupplies.objects.filter(id__in=ps_ids)}
    ps_sorted = sorted(ps_map.values(), key=lambda x: (x.sorting_order or 0, x.name or ''))

    # 4. Индекс: (mli_id, ps_id) → запись
    record_index = {}
    for r in all_records:
        record_index[(r.model_line_item_id, r.power_supply_id)] = r

    # 5. Строим DataFrame
    data = {}
    col_names = [str(ps.name) for ps in ps_sorted]

    for mli in mli_list:
        row_vals = {}
        for ps in ps_sorted:
            rec = record_index.get((mli.id, ps.id))
            if rec is None:
                row_vals[str(ps.name)] = '—'
            elif not rec.is_active:
                row_vals[str(ps.name)] = '✗'
            else:
                row_vals[str(ps.name)] = '✓'
        data[mli.name] = row_vals

    df = pd.DataFrame.from_dict(data, orient='index', columns=col_names)
    df.index.name = 'Модель'

    # 6. Итого
    totals = {}
    for col in col_names:
        yes = (df[col] == '✓').sum()
        inactive = (df[col] == '✗').sum()
        no = (df[col] == '—').sum()
        totals[col] = f"✓{yes} ✗{inactive} —{no}"
    totals_row = pd.DataFrame([totals], index=['ИТОГО'])
    df = pd.concat([df, totals_row])

    # 7. Вывод
    pd.set_option('display.max_columns', 20)
    pd.set_option('display.width', 200)
    pd.set_option('display.max_rows', 200)
    print(df.to_string())
    print(f"\nЛегенда:  ✓ = есть (активно)  |  ✗ = есть (НЕактивно)  |  — = нет в БД\n")

    # Также сохраняем в Excel для удобства
    xlsx_path = f'ea_power_supply_diag_{model_line_name}.xlsx'
    df.to_excel(xlsx_path, sheet_name='Питание')
    print(f"📎 Сохранено в {xlsx_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('series', nargs='?', default='AR01E')
    args = parser.parse_args()
    build_diag_table(args.series)
