"""
Заведение линейной серии BTL (Autorun):
- серия (PneumaticActuatorModelLine) + дефолтные опции серии;
- таблица корпусов (PneumaticActuatorBodyTable);
- корпуса (PneumaticActuatorBody) — 30 типоразмеров BTL125…BTL1000
  (номер модели = диаметр цилиндра, мм);
- модели (PneumaticActuatorModelLineItem) — DA + SR на каждый типоразмер;
- опции уровня модели: пружина 'DA' / встроенный модуль 'S' (SR),
  положение безопасности НЗ (стандарт, K) + НО (B);
- прайс типовых ходов — в extra_params каждой модели
  ('stroke_prices': {ход: цена}, 'stroke_min'/'stroke_max').

Физика тел: только давление 0.3–0.6 и диаметр поршня (каталог BTL не даёт
масс/габаритов/расхода — допишет пользователь в админке).

Источник: Данные системы расчёта.json (linear + linearPrices).

Идемпотентно: update_or_create по code (повторный запуск ничего не дублирует).
"""
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from pneumatic_actuators.models import (
    PneumaticActuatorModelLine,
    PneumaticActuatorBodyTable,
    PneumaticActuatorBody,
    PneumaticActuatorModelLineItem,
    PneumaticActuatorVariety,
    PneumaticActuatorConstructionVariety,
    PneumaticActuatorSpringsQty,
)
from pneumatic_actuators.models.pa_options import (
    PneumaticSpringsQtyOption,
    PneumaticSafetyPositionOption,
)
from producers.models import Brands
from core.models import EquipmentType
from params.models import SafetyPositionOption, ActuatorGearboxOutputType

SOURCE_JSON = r'E:\work\Контроль\Проект_приводы\AutoRun\报价系统261119\报价系统261119\Данные системы расчёта.json'

BTL_SIZES = [
    '125', '140', '160', '180', '200', '220', '250', '280', '300', '320',
    '350', '380', '400', '420', '450', '480', '500', '520', '550', '580',
    '600', '620', '650', '680', '700', '750', '800', '850', '900', '1000',
]


class Command(BaseCommand):
    help = 'Завести линейную серию BTL: серия, корпуса, модели, опции, прайс ходов (идемпотентно).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Только печать, без записи в БД')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        created = {'series': 0, 'tables': 0, 'bodies': 0, 'mlis': 0,
                   'springs_opts': 0, 'safety_opts': 0}

        variety_ln = PneumaticActuatorConstructionVariety.objects.get(code='LN')
        var_da = PneumaticActuatorVariety.objects.get(code='DA')
        var_sr = PneumaticActuatorVariety.objects.get(code='SR')
        brand = Brands.objects.get(code='AUTORUN')
        et = EquipmentType.objects.get(id=3)
        out_type_linear = ActuatorGearboxOutputType.objects.get(id=3)

        sq_da = PneumaticActuatorSpringsQty.objects.get(code='DA')
        sq_module = PneumaticActuatorSpringsQty.objects.get(code='S')
        sp_nc = SafetyPositionOption.objects.get(code='nc')
        sp_no = SafetyPositionOption.objects.get(code='no')

        with open(SOURCE_JSON, encoding='utf-8') as f:
            data = json.load(f)
        prices = data.get('linearPrices', {})

        def stroke_data(model, action):
            """Прайс ходов конкретной модели: {ход: цена}."""
            out = {}
            for key, rec in prices.items():
                if not key.startswith(f'{action}:{model}:'):
                    continue
                out[int(rec['stroke'])] = rec['price']
            return out

        # ================= серия =================
        ml, made = PneumaticActuatorModelLine.objects.get_or_create(
            code='BTL',
            defaults=dict(
                name='BTL', brand=brand, equipment_type=et,
                pneumatic_actuator_construction_variety=variety_ln,
                default_output_type=out_type_linear,
                model_item_code_template='{model_code}-W{stroke}.{temperature}.{safety_position}.{manual_override}',
                ext_encoding_template='{shaft_material}',
                sorting_order=22, is_active=True,
            ))
        if made:
            created['series'] += 1
            if not dry:
                ml.ensure_all_default_options_exist()

        table, made = PneumaticActuatorBodyTable.objects.get_or_create(
            code='BTL', defaults=dict(name='BTL', sorting_order=22, is_active=True))
        if made:
            created['tables'] += 1

        # ================= тела =================
        for idx, size in enumerate(BTL_SIZES):
            body, made = PneumaticActuatorBody.objects.get_or_create(
                code=f'BTL{size}',
                defaults=dict(
                    name=f'BTL{size}', body_table=table,
                    min_pressure_bar='3.0', max_pressure_bar='6.0',
                    piston_diameter=str(int(size)),
                    turn_angle=None,  # линейный привод — угла поворота нет
                    sorting_order=idx, is_active=True,
                ))
            if made:
                created['bodies'] += 1

        # ================= модели (MLI) =================
        for idx, size in enumerate(BTL_SIZES):
            body = PneumaticActuatorBody.objects.get(code=f'BTL{size}')
            sd_da = stroke_data(f'BTL{size}', 'double')
            sd_sr = stroke_data(f'BTL{size}', 'single')

            mli_da, made = PneumaticActuatorModelLineItem.objects.get_or_create(
                model_line=ml, code=f'BTL{size}D',
                defaults=dict(
                    name=f'BTL{size}D', body=body,
                    pneumatic_actuator_variety=var_da,
                    sorting_order=idx * 10, is_active=True,
                    extra_params={
                        'stroke_prices': sd_da,
                        'stroke_min': min(sd_da) if sd_da else None,
                        'stroke_max': max(sd_da) if sd_da else None,
                    }))
            if made:
                created['mlis'] += 1
            else:
                # перезаписываем прайс ходов при повторном запуске
                if not dry:
                    mli_da.extra_params = {
                        'stroke_prices': sd_da,
                        'stroke_min': min(sd_da) if sd_da else None,
                        'stroke_max': max(sd_da) if sd_da else None,
                    }
                    mli_da.save(update_fields=['extra_params'])

            mli_sr, made = PneumaticActuatorModelLineItem.objects.get_or_create(
                model_line=ml, code=f'BTL{size}SR',
                defaults=dict(
                    name=f'BTL{size}SR', body=body,
                    pneumatic_actuator_variety=var_sr,
                    sorting_order=idx * 10 + 1, is_active=True,
                    extra_params={
                        'stroke_prices': sd_sr,
                        'stroke_min': min(sd_sr) if sd_sr else None,
                        'stroke_max': max(sd_sr) if sd_sr else None,
                    }))
            if made:
                created['mlis'] += 1
            else:
                if not dry:
                    mli_sr.extra_params = {
                        'stroke_prices': sd_sr,
                        'stroke_min': min(sd_sr) if sd_sr else None,
                        'stroke_max': max(sd_sr) if sd_sr else None,
                    }
                    mli_sr.save(update_fields=['extra_params'])

            # опции уровня модели
            _, made = PneumaticSpringsQtyOption.objects.get_or_create(
                model_line_item=mli_da, springs_qty=sq_da,
                defaults=dict(encoding='', is_default=True, is_active=True, sorting_order=0))
            if made:
                created['springs_opts'] += 1
            _, made = PneumaticSpringsQtyOption.objects.get_or_create(
                model_line_item=mli_sr, springs_qty=sq_module,
                defaults=dict(encoding='', is_default=True, is_active=True, sorting_order=0))
            if made:
                created['springs_opts'] += 1

            # положение безопасности SR: НЗ (K, стандарт) + НО (B)
            for sp, enc, is_def in ((sp_nc, 'NC', True), (sp_no, 'NO', False)):
                _, made = PneumaticSafetyPositionOption.objects.get_or_create(
                    model_line_item=mli_sr, safety_position=sp,
                    defaults=dict(encoding=enc, is_default=is_def, is_active=True,
                                  sorting_order=0 if is_def else 1))
                if made:
                    created['safety_opts'] += 1

        self.stdout.write(self.style.SUCCESS(
            'Итог (%s): %s' % ('dry-run' if dry else 'применено', created)))
        if dry:
            transaction.set_rollback(True)
        else:
            self.stdout.write('Серия BTL (id=%s)' % ml.pk)
