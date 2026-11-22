"""
Импорт моментов NRT/BTS в BodyThrustTorqueTable из Данные системы расчёта.json.

Маппинг (проверен сверкой с каталогом T.NTR.26.1 / BTS PDF):
- DA: bto/rto/eto = air[0]/air[1]/air[2] (у NRT все равны; у BTS три разных).
- SR: строка pressure='spring' — пружина в ориентации хода открытия
  (bto=S(0°), rto=S(45°), eto=S(90°)); источник даёт пружину в ориентации
  закрытия (Старт=90°) → разворачиваем: bto=spring[2], rto=spring[1], eto=spring[0].
  Строки давлений — уже нетто «воздух − пружины», ориентация открытия: как в источнике.
- Коды пружин: NRT S{nn} → '05'…'16'; BTS -{k}K/B → 'S{k}'; DA → 'DA'.
Идемпотентно: update_or_create по (body, pressure, spring_qty).
"""
import re
import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from pneumatic_actuators.models import (
    PneumaticActuatorBody,
    PneumaticActuatorSpringsQty,
    BodyThrustTorqueTable,
)
from params.models import PneumaticAirSupplyPressure
from valve_data.models import TorquePoint

SOURCE_JSON = r'E:\work\Контроль\Проект_приводы\AutoRun\报价系统261119\报价系统261119\Данные системы расчёта.json'

PRESSURE_CODE = {
    0.2: '2', 0.25: '2.5', 0.3: '3', 0.35: '3.5', 0.4: '4',
    0.45: '4.5', 0.5: '5', 0.55: '5.5', 0.6: '6', 0.7: '7', 0.8: '8',
}


class Command(BaseCommand):
    help = 'Импорт моментов NRT/BTS в BodyThrustTorqueTable (идемпотентно).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Только печать, без записи в БД')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        with open(SOURCE_JSON, encoding='utf-8') as f:
            data = json.load(f)

        pressures = {p.code: p for p in PneumaticAirSupplyPressure.objects.all()}
        springs = {s.code: s for s in PneumaticActuatorSpringsQty.objects.all()}
        points = {p.code: p for p in TorquePoint.objects.all()}
        bodies = {b.code: b for b in PneumaticActuatorBody.objects.filter(
            body_table__code__in=['NRT', 'BTS'])}

        created = updated = skipped = 0
        errors = []
        spring_seen = set()

        for rec in data['rotary']:
            model = rec['model']
            m = re.match(r'NRT0?(\d+)([DS]\d*)$', model)
            if m:
                body_code = f'NRT{int(m.group(1)):03d}'
                kind = m.group(2)
                if kind == 'D':
                    sq_code = 'DA'
                else:
                    sq_code = f'{int(kind[1:]):02d}'
            else:
                m = re.match(r'BTS(\d+)-(\d+)(?:-90-(\d)K/B)?$', model)
                if not m:
                    skipped += 1
                    continue
                body_code = f'BTS{m.group(1)}-{m.group(2)}'
                sq_code = f'S{m.group(3)}' if m.group(3) else 'DA'

            body = bodies.get(body_code)
            sq = springs.get(sq_code)
            if body is None or sq is None:
                errors.append((model, body_code, sq_code, 'ref missing'))
                continue

            spring_row = None
            if rec.get('spring'):
                key = (body_code, sq_code)
                if key not in spring_seen:
                    spring_seen.add(key)
                    # пружина в ориентации закрытия (Старт=90°): BTC/RTC/ETC
                    spring_row = [
                        ('btc', float(rec['spring'][0])),
                        ('rtc', float(rec['spring'][1])),
                        ('etc', float(rec['spring'][2])),
                    ]

            rows = []
            if spring_row:
                rows.extend((body, pressures['spring'], sq, pc, v) for pc, v in spring_row)
            if rec.get('air') and rec.get('pressure') in PRESSURE_CODE:
                rows.extend([
                    (body, pressures[PRESSURE_CODE[rec['pressure']]], sq, 'bto', float(rec['air'][0])),
                    (body, pressures[PRESSURE_CODE[rec['pressure']]], sq, 'rto', float(rec['air'][1])),
                    (body, pressures[PRESSURE_CODE[rec['pressure']]], sq, 'eto', float(rec['air'][2])),
                ])

            for body_, pr, sq_, point_code, val in rows:
                point = points.get(point_code)
                if point is None:
                    errors.append((model, point_code, 'point missing'))
                    continue
                _, made = BodyThrustTorqueTable.objects.update_or_create(
                    body=body_, pressure=pr, spring_qty=sq_, point=point,
                    defaults=dict(value=val))
                if made:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            'Итог (%s): создано=%s, обновлено=%s, пропущено=%s, ошибок=%s' % (
                'dry-run' if dry else 'применено', created, updated, skipped, len(errors))))
        for e in errors[:20]:
            self.stdout.write('  ошибка: %s' % (e,))
        if dry:
            transaction.set_rollback(True)
