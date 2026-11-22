"""
Импорт усилий линейной серии BTL в BodyThrustTorqueTable из
Данные системы расчёта.json (ключ linear).

Семантика источника: одно значение усилия на давление (усилие постоянно
по ходу — кривая плоская):
- DA: air → bto/rto/eto (все равны);
- SR (K = НЗ: воздух открывает, пружина закрывает):
  air → bto/rto/eto, spring → btc/rtc/etc (все равны внутри направления).

spring_qty: 'DA' для двусторонних, 'S' (встроенный пружинный модуль) для SR.

Идемпотентно: update_or_create по (body, pressure, spring_qty, point).
"""
import json

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

PRESSURE_CODE = {0.3: '3', 0.4: '4', 0.5: '5', 0.6: '6'}


class Command(BaseCommand):
    help = 'Импорт усилий BTL в BodyThrustTorqueTable (идемпотентно).'

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
            body_table__code='BTL')}

        created = updated = skipped = 0
        errors = []

        for rec in data['linear']:
            model = rec['model']
            body = bodies.get(model)
            if body is None:
                errors.append((model, 'body missing'))
                continue
            if rec['pressure'] not in PRESSURE_CODE:
                skipped += 1
                continue
            pressure = pressures[PRESSURE_CODE[rec['pressure']]]

            is_da = rec['action'] == 'double'
            sq = springs['DA'] if is_da else springs.get('S')
            if sq is None:
                errors.append((model, 'spring_qty S missing'))
                continue

            air = rec.get('air')
            spring = rec.get('spring')
            rows = []
            if air is not None:
                rows.extend([('bto', float(air)), ('rto', float(air)), ('eto', float(air))])
            if spring is not None:
                rows.extend([('btc', float(spring)), ('rtc', float(spring)), ('etc', float(spring))])

            for point_code, val in rows:
                point = points.get(point_code)
                if point is None:
                    errors.append((model, point_code, 'point missing'))
                    continue
                _, made = BodyThrustTorqueTable.objects.update_or_create(
                    body=body, pressure=pressure, spring_qty=sq, point=point,
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
