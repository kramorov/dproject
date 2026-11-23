"""
Импорт коэффициентов момента арматуры (6 точек) из Данные системы расчёта.json
в valve_data.ValveTorqueCoefficient.

Источник: массив 'coefficients' экспорта (8 типов арматуры с factors).
Создаёт 8 записей-таблиц (одна запись = тип арматуры × опора × уплотнение
с 6 значениями BTO…ETC). Идемпотентно (update_or_create по code).
"""
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from valve_data.models import (
    ValveTorqueCoefficient, SealType, ValveSupportType,
)
from valve_data.models.torque_characteristics import TORQUE_POINTS
from params.models import ValveTypes

SOURCE_JSON = r'E:\work\Контроль\Проект_приводы\AutoRun\报价系统261119\报价系统261119\Данные системы расчёта.json'

# Имя из экспорта → (valve_type_code, support_code, seal_type_code, code, name)
COEFFICIENT_TARGETS = [
    ('Плавающий шаровой кран, мягкое уплотнение', 'ball-valve', 'floating', 'soft',
     'ball-floating-soft', 'Шаровой кран, плавающий, мягкое'),
    ('Плавающий шаровой кран, жёсткое уплотнение', 'ball-valve', 'floating', 'hard',
     'ball-floating-hard', 'Шаровой кран, плавающий, жёсткое'),
    ('Шаровой кран с цапфами, мягкое уплотнение', 'ball-valve', 'trunnion', 'soft',
     'ball-trunnion-soft', 'Шаровой кран, на цапфах, мягкое'),
    ('Шаровой кран с цапфами, жёсткое уплотнение', 'ball-valve', 'trunnion', 'hard',
     'ball-trunnion-hard', 'Шаровой кран, на цапфах, жёсткое'),
    ('Дисковый затвор, мягкое уплотнение', 'butterfly-valve', None, 'soft',
     'butterfly-soft', 'Дисковый затвор, мягкое'),
    ('Дисковый затвор, жёсткое уплотнение', 'butterfly-valve', None, 'hard',
     'butterfly-hard', 'Дисковый затвор, жёсткое'),
    ('Пробковый кран', 'plug-valve', None, None,
     'plug', 'Пробковый кран'),
    ('Высокопроизводительный дисковый затвор PTFE', 'butterfly-valve', None, 'ptfe',
     'butterfly-ptfe', 'Дисковый затвор PTFE'),
]


class Command(BaseCommand):
    help = 'Импорт таблиц коэффициентов момента арматуры (6 точек) из экспорта.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Только печать, без записи в БД')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        with open(SOURCE_JSON, encoding='utf-8') as f:
            data = json.load(f)

        valve_types = {v.code: v for v in ValveTypes.objects.all()}
        supports = {s.code: s for s in ValveSupportType.objects.all()}
        seals = {s.code: s for s in SealType.objects.all()}
        created = updated = 0
        for entry in data['coefficients']:
            target = next((t for t in COEFFICIENT_TARGETS if t[0] == entry['name']), None)
            if target is None:
                self.stdout.write(self.style.WARNING(f'не найдено соответствие: {entry["name"]}'))
                continue
            _, vt_code, sup_code, seal_code, code, name = target
            valve_type = valve_types[vt_code]
            support = supports[sup_code] if sup_code else None
            seal = seals[seal_code] if seal_code else None
            factors = entry.get('factors') or []

            values = {}
            for i, pcode in enumerate(TORQUE_POINTS):
                if i < len(factors) and factors[i] is not None:
                    values[pcode] = factors[i]
            if not values:
                self.stdout.write(self.style.WARNING(f'нет факторов: {entry["name"]}'))
                continue
            _, made = ValveTorqueCoefficient.objects.update_or_create(
                code=code,
                defaults=dict(name=name, valve_type=valve_type, support=support,
                              seal_type=seal, source='AUTORUN 报价系统',
                              is_active=True, sorting_order=0, **values))
            if made:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            'Итог (%s): создано=%s, обновлено=%s' % ('dry-run' if dry else 'применено', created, updated)))
        if dry:
            transaction.set_rollback(True)
