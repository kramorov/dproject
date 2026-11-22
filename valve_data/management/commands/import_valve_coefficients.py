"""
Импорт коэффициентов момента арматуры (6 точек) из Данные системы расчёта.json
в valve_data.TorqueThrustCharacteristics + ValveTorqueCoefficient (длинный формат).

Источник: массив 'coefficients' экспорта (8 типов арматуры с factors /
minimumFactors / values). Создаёт набор «ротационный 6 точек» и по одной строке
на точку для каждого типа арматуры.
Идемпотентно (update_or_create по составному ключу).
"""
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from valve_data.models import (
    TorqueThrustCharacteristics, ValveTorqueCoefficient,
    TorquePoint, SealType, ValveSupportType,
)
from valve_data.models.torque_characteristics import TORQUE_POINTS
from params.models import ValveTypes
from pa_controls.models import ActingType

SOURCE_JSON = r'E:\work\Контроль\Проект_приводы\AutoRun\报价系统261119\报价系统261119\Данные системы расчёта.json'

# Имя из экспорта → (valve_type_code, support_code, seal_type_code)
COEFFICIENT_TARGETS = [
    ('Плавающий шаровой кран, мягкое уплотнение', 'ball-valve', 'floating', 'soft'),
    ('Плавающий шаровой кран, жёсткое уплотнение', 'ball-valve', 'floating', 'hard'),
    ('Шаровой кран с цапфами, мягкое уплотнение', 'ball-valve', 'trunnion', 'soft'),
    ('Шаровой кран с цапфами, жёсткое уплотнение', 'ball-valve', 'trunnion', 'hard'),
    ('Дисковый затвор, мягкое уплотнение', 'butterfly-valve', None, 'soft'),
    ('Дисковый затвор, жёсткое уплотнение', 'butterfly-valve', None, 'hard'),
    ('Пробковый кран', 'plug-valve', None, None),
    ('Высокопроизводительный дисковый затвор PTFE', 'butterfly-valve', None, 'ptfe'),
]


class Command(BaseCommand):
    help = 'Импорт коэффициентов момента арматуры (6 точек) из экспорта.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Только печать, без записи в БД')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        with open(SOURCE_JSON, encoding='utf-8') as f:
            data = json.load(f)

        rotary = ActingType.objects.get(code='ROTARY')
        char, made = TorqueThrustCharacteristics.objects.get_or_create(
            code='rotary-6',
            defaults=dict(name='Ротационный (6 точек)', motion_type=rotary,
                          sorting_order=0, is_active=True))
        if made:
            self.stdout.write('создан набор характеристик rotary-6')
        for code in TORQUE_POINTS:
            char.points.add(TorquePoint.objects.get(code=code))

        points = {p.code: p for p in TorquePoint.objects.all()}
        valve_types = {v.code: v for v in ValveTypes.objects.all()}
        supports = {s.code: s for s in ValveSupportType.objects.all()}
        seals = {s.code: s for s in SealType.objects.all()}

        created = updated = 0
        for entry in data['coefficients']:
            target = next((t for t in COEFFICIENT_TARGETS if t[0] == entry['name']), None)
            if target is None:
                self.stdout.write(self.style.WARNING(f'не найдено соответствие: {entry["name"]}'))
                continue
            _, vt_code, sup_code, seal_code = target
            valve_type = valve_types[vt_code]
            support = supports[sup_code] if sup_code else None
            seal = seals[seal_code] if seal_code else None
            factors = entry.get('factors') or entry.get('values')
            mins = entry.get('minimumFactors') or []
            displays = entry.get('values') or []

            for i, code in enumerate(TORQUE_POINTS):
                factor = factors[i] if i < len(factors) else None
                if factor is None:
                    continue
                min_factor = mins[i] if i < len(mins) else None
                display = str(displays[i]) if i < len(displays) else ''
                _, made = ValveTorqueCoefficient.objects.update_or_create(
                    characteristics=char, valve_type=valve_type,
                    support=support, seal_type=seal, point=points[code],
                    defaults=dict(factor=factor, min_factor=min_factor,
                                  display=display, source='AUTORUN 报价系统',
                                  is_active=True, sorting_order=0))
                if made:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            'Итог (%s): создано=%s, обновлено=%s' % ('dry-run' if dry else 'применено', created, updated)))
        if dry:
            transaction.set_rollback(True)
