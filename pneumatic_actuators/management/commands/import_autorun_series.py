"""
Заведение новых серий пневмоприводов BTS и NRT:
- серия (PneumaticActuatorModelLine) + дефолтные опции серии;
- таблица корпусов (PneumaticActuatorBodyTable);
- корпуса (PneumaticActuatorBody);
- модели (PneumaticActuatorModelLineItem);
- опции уровня модели: пружины (PneumaticSpringsQtyOption) и положение
  безопасности (PneumaticSafetyPositionOption, для SR).

Источники:
- Данные системы расчёта.json (состав моделей/пружинных комплектов);
- T.NTR.26.1.pdf (физика корпусов NRT — встроена в команду);
- BTS: физика корпусов — минимум (давление/угол), остальное дописывает
  пользователь в админке.

Идемпотентно: update_or_create по code (повторный запуск ничего не дублирует).
"""
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
from params.models import (
    StemShapes, StemSize, MountingPlateTypes, ThreadSize, PneumaticConnection,
    SafetyPositionOption, ActuatorGearboxOutputType,
)

# ── NRT: 18 корпусов; физика из T.NTR.26.1.pdf ──────────────────────────────
NRT_SIZES = ['032', '040', '052', '063', '075', '083', '092', '105', '125',
             '140', '160', '190', '210', '240', '270', '300', '350', '400']

# масса DA/SR (кг) и расход откр/закр (л/цикл), T.NTR.26.1 «РАСХОД И ВЕС»
NRT_MASS_AIR = {
    '032': (0.6, None, 0.04, 0.05), '040': (1.0, None, 0.08, 0.11),
    '052': (1.3, 1.42, 0.12, 0.16), '063': (2.1, 2.25, 0.21, 0.23),
    '075': (2.5, 2.75, 0.30, 0.34), '083': (3.1, 3.45, 0.43, 0.47),
    '092': (4.2, 4.80, 0.64, 0.47), '105': (5.7, 6.40, 0.95, 0.88),
    '125': (8.4, 9.55, 1.60, 1.40), '140': (13.1, 15.10, 2.50, 2.20),
    '160': (19.0, 22.00, 3.40, 3.20), '190': (30.4, 34.75, 5.90, 5.40),
    '210': (44.0, 52.00, 7.50, 7.50), '240': (55.0, 66.00, 11.00, 9.00),
    '270': (80.5, 98.00, 17.00, 14.00), '300': (108.0, 138.00, 23.80, 29.70),
    '350': (164.0, 202.00, 35.10, 46.30), '400': (206.0, 251.00, 52.60, 56.00),
}

# габариты T.NTR.26.1 (16 размеров 52..400): ISO, квадрат штока Q, резьба воздуха Z
NRT_DIMS_SIZES = ['52', '63', '75', '83', '092', '105', '125', '140', '160',
                  '190', '210', '240', '270', '300', '350', '400']
NRT_ISO = ['F03/F05', 'F05/F07', 'F05/F07', 'F05/F07', 'F05/F07', 'F07/F10',
           'F07/F10', 'F10/F12', 'F10/F12', 'F14', 'F14', 'F16', 'F16', 'F16',
           'F16/F25', 'F16/F25']
NRT_STEM_Q = ['11', '14', '14', '17', '17', '17', '22', '27', '27', '36', '36',
              '46', '46', '46', '46', '55']
NRT_AIR_Z = ['G-1_4'] * 11 + ['G-1_2'] * 5

# пружинные комплекты SR по размеру (из Данные системы расчёта.json)
NRT_SR_SPRINGS = {
    '052': list(range(5, 13)), '063': list(range(5, 13)), '075': list(range(5, 13)),
    '083': list(range(5, 13)), '092': list(range(5, 13)), '105': list(range(5, 13)),
    '125': list(range(5, 13)), '140': list(range(5, 13)), '160': list(range(5, 13)),
    '190': list(range(5, 13)), '210': list(range(5, 13)), '240': list(range(5, 13)),
    '270': list(range(5, 13)), '300': list(range(5, 12)), '350': list(range(6, 13)),
    '400': list(range(8, 17)),
}

# ── BTS: 42 корпуса (подсерия → размеры) ────────────────────────────────────
BTS_BASES = {
    1: ['200', '250', '300', '350'],
    2: ['250', '300', '350', '400'],
    3: ['300', '350', '400', '450', '500'],
    4: ['400', '450', '500', '550', '600'],
    5: ['500', '550', '600', '650', '700', '750', '800'],
    6: ['600', '650', '700', '750', '800', '900'],
    7: ['700', '750', '800', '900', '1000', '1100'],
    8: ['800', '900', '1000', '1100', '1200'],
}

# SR-варианты: (подсерия, размер) → размеры пружинного цилиндра (классы 1..4)
# (8, '1200') — только SR-исполнение, DA-модель не создаём
BTS_SR_ONLY = {(8, '1200')}
BTS_K_SETS = {
    (1, '250'): [2, 3, 4], (1, '300'): [1, 2, 3, 4], (1, '350'): [1, 2, 3, 4],
    (2, '300'): [1, 2, 3, 4], (2, '350'): [1, 2, 3, 4], (2, '400'): [1, 2, 3, 4],
    (3, '300'): [3, 4], (3, '350'): [2, 3, 4], (3, '400'): [1, 2, 3, 4],
    (3, '450'): [1, 2, 3, 4], (3, '500'): [1, 2, 3, 4],
    (4, '400'): [3, 4], (4, '450'): [1, 2, 3, 4], (4, '500'): [1, 2, 3, 4],
    (4, '550'): [1, 2, 3, 4], (4, '600'): [1, 2, 3, 4],
    (5, '500'): [3, 4], (5, '550'): [2, 3, 4], (5, '600'): [1, 2, 3, 4],
    (5, '650'): [1, 2, 3, 4], (5, '700'): [1, 2, 3, 4], (5, '750'): [1, 2, 3, 4],
    (5, '800'): [1, 2, 3, 4],
    (6, '600'): [3, 4], (6, '650'): [2, 3, 4], (6, '700'): [1, 2, 3, 4],
    (6, '750'): [1, 2, 3, 4], (6, '800'): [1, 2, 3, 4], (6, '900'): [1, 2, 3, 4],
    (7, '700'): [3], (7, '750'): [2, 3], (7, '800'): [2, 3], (7, '900'): [1, 2, 3],
    (7, '1000'): [1, 2, 3], (7, '1100'): [1, 2],
    (8, '800'): [3], (8, '900'): [2, 3], (8, '1000'): [1, 2, 3],
    (8, '1100'): [1, 2, 3], (8, '1200'): [1, 2],
}


class Command(BaseCommand):
    help = 'Завести серии BTS и NRT: серии, корпуса, модели, опции (идемпотентно).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Только печать, без записи в БД')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        created = {'series': 0, 'tables': 0, 'bodies': 0, 'mlis': 0,
                   'springs_opts': 0, 'safety_opts': 0}

        variety_rp = PneumaticActuatorConstructionVariety.objects.get(code='RP')
        variety_sy = PneumaticActuatorConstructionVariety.objects.get(code='SY')
        var_da = PneumaticActuatorVariety.objects.get(code='DA')
        var_sr = PneumaticActuatorVariety.objects.get(code='SR')
        brand = Brands.objects.get(code='AUTORUN')
        et = EquipmentType.objects.get(id=3)
        out_type = ActuatorGearboxOutputType.objects.get(id=1)

        stem_sq = StemShapes.objects.get(code='sq')
        conns = list(PneumaticConnection.objects.filter(code__in=['pipe', 'namur-1']))
        sp_nc = SafetyPositionOption.objects.get(code='nc')
        sp_no = SafetyPositionOption.objects.get(code='no')

        rt = PneumaticActuatorModelLine.objects.get(code='RT')
        air_sy = PneumaticActuatorModelLine.objects.get(code='AIR-SY')

        # ================= NRT =================
        ml_nrt, made = PneumaticActuatorModelLine.objects.get_or_create(
            code='NRT',
            defaults=dict(
                name='NRT', brand=brand, equipment_type=et,
                pneumatic_actuator_construction_variety=variety_rp,
                default_output_type=out_type,
                model_item_code_template=rt.model_item_code_template,
                ext_encoding_template=rt.ext_encoding_template,
                sorting_order=20, is_active=True,
            ))
        if made:
            created['series'] += 1
            if not dry:
                ml_nrt.ensure_all_default_options_exist()

        table_nrt, made = PneumaticActuatorBodyTable.objects.get_or_create(
            code='NRT', defaults=dict(name='NRT', sorting_order=20, is_active=True))
        if made:
            created['tables'] += 1

        for idx, size in enumerate(NRT_SIZES):
            mass_da, mass_sr, air_o, air_c = NRT_MASS_AIR[size]
            dims = {}
            if size in NRT_DIMS_SIZES:
                j = NRT_DIMS_SIZES.index(size)
                dims = dict(iso=NRT_ISO[j], q=NRT_STEM_Q[j], z=NRT_AIR_Z[j])
            body, made = PneumaticActuatorBody.objects.get_or_create(
                code=f'NRT{size}',
                defaults=dict(
                    name=f'NRT{size}', body_table=table_nrt,
                    stem_shape=stem_sq,
                    min_pressure_bar='2.0', max_pressure_bar='8.0',
                    air_usage_open=str(air_o), air_usage_close=str(air_c),
                    piston_diameter=str(int(size)),
                    turn_angle='0-90°',
                    sorting_order=idx, is_active=True,
                ))
            if made:
                created['bodies'] += 1
                if dims:
                    body.stem_size = StemSize.objects.filter(code=f'SQ{dims["q"]}').first()
                    for iso in dims['iso'].split('/'):
                        plate = MountingPlateTypes.objects.filter(code=iso).first()
                        if plate:
                            body.mounting_plate.add(plate)
                    thr = ThreadSize.objects.filter(code=dims['z']).first()
                    if thr:
                        body.thread_in = thr
                        body.thread_out = thr
                    body.pneumatic_connection.add(*conns)
                    body.save()

        # MLI NRT: DA + SR
        mlis_sr = {}
        for idx, size in enumerate(NRT_SIZES):
            mli_da, made = PneumaticActuatorModelLineItem.objects.get_or_create(
                model_line=ml_nrt, code=f'NRT{size}D',
                defaults=dict(name=f'NRT{size}D', body=PneumaticActuatorBody.objects.get(code=f'NRT{size}'),
                              pneumatic_actuator_variety=var_da, sorting_order=idx * 10, is_active=True))
            if made:
                created['mlis'] += 1
            if size in NRT_SR_SPRINGS:
                mli_sr, made = PneumaticActuatorModelLineItem.objects.get_or_create(
                    model_line=ml_nrt, code=f'NRT{size}SR',
                    defaults=dict(name=f'NRT{size}SR', body=PneumaticActuatorBody.objects.get(code=f'NRT{size}'),
                                  pneumatic_actuator_variety=var_sr, sorting_order=idx * 10 + 1, is_active=True))
                if made:
                    created['mlis'] += 1
                mlis_sr[size] = mli_sr

        # опции пружин: DA + комплекты SR
        sq_da = PneumaticActuatorSpringsQty.objects.get(code='DA')
        for size in NRT_SIZES:
            mli_da = PneumaticActuatorModelLineItem.objects.get(model_line=ml_nrt, code=f'NRT{size}D')
            _, made = PneumaticSpringsQtyOption.objects.get_or_create(
                model_line_item=mli_da, springs_qty=sq_da,
                defaults=dict(encoding='', is_default=True, is_active=True, sorting_order=0))
            if made:
                created['springs_opts'] += 1
        for size, mli in mlis_sr.items():
            for n in NRT_SR_SPRINGS[size]:
                sq = PneumaticActuatorSpringsQty.objects.get(code=f'{n:02d}')
                _, made = PneumaticSpringsQtyOption.objects.get_or_create(
                    model_line_item=mli, springs_qty=sq,
                    defaults=dict(encoding=f'{n:02d}', is_default=False, is_active=True,
                                  sorting_order=n))
                if made:
                    created['springs_opts'] += 1
            # положение безопасности SR: НЗ (стандарт) + НО
            for sp, enc, is_def in ((sp_nc, 'NC', True), (sp_no, 'NO', False)):
                _, made = PneumaticSafetyPositionOption.objects.get_or_create(
                    model_line_item=mli, safety_position=sp,
                    defaults=dict(encoding=enc, is_default=is_def, is_active=True,
                                  sorting_order=0 if is_def else 1))
                if made:
                    created['safety_opts'] += 1

        # ================= BTS =================
        ml_bts, made = PneumaticActuatorModelLine.objects.get_or_create(
            code='BTS',
            defaults=dict(
                name='BTS', brand=brand, equipment_type=et,
                pneumatic_actuator_construction_variety=variety_sy,
                default_output_type=out_type,
                model_item_code_template=air_sy.model_item_code_template,
                ext_encoding_template=air_sy.ext_encoding_template,
                sorting_order=21, is_active=True,
            ))
        if made:
            created['series'] += 1
            if not dry:
                ml_bts.ensure_all_default_options_exist()

        table_bts, made = PneumaticActuatorBodyTable.objects.get_or_create(
            code='BTS', defaults=dict(name='BTS', sorting_order=21, is_active=True))
        if made:
            created['tables'] += 1

        bts_bodies = []
        for sub in sorted(BTS_BASES):
            for size in BTS_BASES[sub]:
                code = f'BTS{sub}-{size}'
                body, made = PneumaticActuatorBody.objects.get_or_create(
                    code=code,
                    defaults=dict(
                        name=code, body_table=table_bts,
                        min_pressure_bar='3.0', max_pressure_bar='6.0',
                        piston_diameter=str(int(size)),
                        turn_angle='0-90°',
                        sorting_order=len(bts_bodies), is_active=True,
                    ))
                if made:
                    created['bodies'] += 1
                bts_bodies.append((sub, size, body))

        # MLI BTS: DA базы + SR (по одному на корпус, пружинные блоки — опциями)
        mli_map = {}
        for idx, (sub, size, body) in enumerate(bts_bodies):
            if (sub, size) in BTS_SR_ONLY:
                continue  # только SR-исполнение (например, BTS8-1200)
            mli_da, made = PneumaticActuatorModelLineItem.objects.get_or_create(
                model_line=ml_bts, code=f'BTS{sub}-{size}',
                defaults=dict(name=f'BTS{sub}-{size}', body=body,
                              pneumatic_actuator_variety=var_da,
                              sorting_order=idx * 10, is_active=True))
            if made:
                created['mlis'] += 1
            if (sub, size) in BTS_K_SETS:
                mli_sr, made = PneumaticActuatorModelLineItem.objects.get_or_create(
                    model_line=ml_bts, code=f'BTS{sub}-{size}SR',
                    defaults=dict(name=f'BTS{sub}-{size}SR', body=body,
                                  pneumatic_actuator_variety=var_sr,
                                  sorting_order=idx * 10 + 1, is_active=True))
                if made:
                    created['mlis'] += 1
                mli_map[(sub, size)] = mli_sr

        # опции пружин BTS: DA + блоки S1..S4
        for sub, size, body in bts_bodies:
            if (sub, size) in BTS_SR_ONLY:
                continue
            mli_da = PneumaticActuatorModelLineItem.objects.get(model_line=ml_bts, code=f'BTS{sub}-{size}')
            _, made = PneumaticSpringsQtyOption.objects.get_or_create(
                model_line_item=mli_da, springs_qty=sq_da,
                defaults=dict(encoding='', is_default=True, is_active=True, sorting_order=0))
            if made:
                created['springs_opts'] += 1
        for (sub, size), mli in mli_map.items():
            for k in BTS_K_SETS[(sub, size)]:
                sq = PneumaticActuatorSpringsQty.objects.get(code=f'S{k}')
                _, made = PneumaticSpringsQtyOption.objects.get_or_create(
                    model_line_item=mli, springs_qty=sq,
                    defaults=dict(encoding=f'S{k}', is_default=False, is_active=True,
                                  sorting_order=k))
                if made:
                    created['springs_opts'] += 1
            for sp, enc, is_def in ((sp_nc, 'NC', True), (sp_no, 'NO', False)):
                _, made = PneumaticSafetyPositionOption.objects.get_or_create(
                    model_line_item=mli, safety_position=sp,
                    defaults=dict(encoding=enc, is_default=is_def, is_active=True,
                                  sorting_order=0 if is_def else 1))
                if made:
                    created['safety_opts'] += 1

        self.stdout.write(self.style.SUCCESS(
            'Итог (%s): %s' % ('dry-run' if dry else 'применено', created)))
        if dry:
            transaction.set_rollback(True)  # ничего не пишем
        else:
            self.stdout.write('Серии: NRT (id=%s), BTS (id=%s)' % (ml_nrt.pk, ml_bts.pk))
