"""
Diagnostic: show ElectricControlUnitOption / ElectricSafetyPositionOption for a series.

Usage: python diag_ea_control_units.py AR01E
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import pandas as pd
from electric_actuators.models import ElectricActuatorModelLine, ElectricActuatorModelLineItem
from electric_actuators.models.ea_model_line_item_options import (
    ElectricPowerSupplyOption, ElectricControlUnitOption, ElectricSafetyPositionOption
)
from params.models import PowerSupplies


def diag(series_name: str):
    ml = ElectricActuatorModelLine.objects.get(name__iexact=series_name, is_active=True)
    print(f"\n=== {ml.name} ===\n")

    # Все напряжения серии
    ps_records = ElectricPowerSupplyOption.objects.filter(
        model_line_item__model_line=ml
    ).select_related('power_supply', 'model_line_item')

    # Группируем по (model, voltage)
    ps_by_mli = {}
    for r in ps_records:
        ps_by_mli.setdefault(r.model_line_item_id, {})[r.power_supply_id] = r

    models = ElectricActuatorModelLineItem.objects.filter(
        model_line=ml, is_active=True
    ).order_by('sorting_order')

    ps_ids = sorted(set(r.power_supply_id for r in ps_records))
    power_supplies = {ps.id: ps for ps in PowerSupplies.objects.filter(id__in=ps_ids)}

    for mli in models:
        print(f"--- {mli.name} ---")
        for ps_id in sorted(ps_ids):
            ps_rec = ps_by_mli.get(mli.id, {}).get(ps_id)
            if not ps_rec:
                print(f"  {power_supplies[ps_id].name}: НЕТ записи")
                continue

            status = 'АКТИВНА' if ps_rec.is_active else 'НЕАКТИВНА'
            print(f"  {power_supplies[ps_id].name} (id={ps_rec.id}, {status}):")

            # Control units
            cus = ElectricControlUnitOption.objects.filter(
                power_supply_option=ps_rec
            ).select_related('control_unit').order_by('sorting_order')
            if cus:
                for cu in cus:
                    d = ' [default]' if cu.is_default else ''
                    print(f"    CU: {cu.control_unit.name} enc={cu.encoding}{d}")
            else:
                print(f"    CU: — нет —")

            # Safety positions
            sps = ElectricSafetyPositionOption.objects.filter(
                power_supply_option=ps_rec
            ).select_related('safety_position').order_by('sorting_order')
            if sps:
                for sp in sps:
                    d = ' [default]' if sp.is_default else ''
                    print(f"    SP: {sp.safety_position.name} enc={sp.encoding}{d}")
            else:
                print(f"    SP: — нет —")
        print()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('series', nargs='?', default='AR01E')
    args = parser.parse_args()
    diag(args.series)
