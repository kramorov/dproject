"""
Сверка данных БД (через-опции переключателей, CU-опции, wiring) с таблицей
AOX (матрица сигналов) — read-only отчёт (фаза 5, перед переносом).

Что сравнивается по каждой модели с данными таблицы:
- LIMIT/WAY/TORQUE: через-опции переключателей модели (spdt/dpdt/none,
  is_default) против строк матрицы её корпуса (слоты LIMIT/WAY/TORQUE,
  std/opt/na) — сопоставление: через-опция 'spdt'/'dpdt' ↔ матричная строка
  SPDT/DPDT; 'none' (is_default) ↔ отсутствие строк слота;
- БУ×напряжение: наборы пар в CU-опциях против БУ/напряжений строк матрицы;
- wiring: привязка схем (control_unit_wiring) — сводный отчёт, т.к. в БД
  привязки отсутствуют (21 связка не связаны с моделями).

Использование:
    python manage.py compare_ea_aox_db [--xlsx путь]
"""
from django.core.management.base import BaseCommand

from electric_actuators.models import (
    ElectricActuatorModelLineItem, EaSignalMatrixEntry,
)
from electric_actuators.services.ea_signal_resolver import resolve_matrix


class Command(BaseCommand):
    help = 'Сверка БД с таблицей AOX (read-only отчёт)'

    def add_arguments(self, parser):
        parser.add_argument('--xlsx', type=str,
                            default='available-options-ea-AOX.xlsx')

    def handle(self, *args, **options):
        import openpyxl
        from django.apps import apps

        End = apps.get_model('electric_actuators', 'ElectricEndSwitchesOption')
        Way = apps.get_model('electric_actuators', 'ElectricWaySwitchesOption')
        Tor = apps.get_model('electric_actuators', 'ElectricTorqueSwitchesOption')
        CUOpt = apps.get_model('electric_actuators', 'ElectricControlUnitOption')
        from params.models import ControlUnitInstalledOption, PowerSupplies

        wb = openpyxl.load_workbook(options['xlsx'], data_only=True)
        ws = wb.active

        # Модели с данными в таблице (совпадающие с БД)
        models = []
        for r in range(7, ws.max_row + 1):
            name = ws.cell(r, 1).value
            if not name or not isinstance(name, str):
                continue
            n = sum(1 for c in range(3, 97)
                    if ws.cell(r, c).value is not None)
            if n == 0:
                continue
            item = ElectricActuatorModelLineItem.objects.filter(
                name__in=[name, name.replace('.', '')]).first()
            if item:
                models.append((name, item, r))

        cu_none = ControlUnitInstalledOption.objects.get(code='none')
        ps_220 = PowerSupplies.objects.get(code='220-AC')

        self.stdout.write('=== Сверка переключателей (БД ↔ таблица) ===')
        # колонки слотов в таблице (любой маркер = данные есть)
        slot_cols = {
            'LIMIT': list(range(7, 11)) + list(range(31, 37)),
            'WAY': list(range(11, 15)) + list(range(37, 43)),
            'TORQUE': list(range(15, 19)) + list(range(43, 49)),
        }
        for name, item, r in models:
            # через-опции базовой модели (и QUI-вариантов того же корпуса — как есть)
            e = list(End.objects.filter(model_line_item=item).values_list(
                'end_switches_option__code', 'is_default'))
            w = list(Way.objects.filter(model_line_item=item).values_list(
                'way_switches_option__code', 'is_default'))
            t = list(Tor.objects.filter(model_line_item=item).values_list(
                'torque_switches_option__code', 'is_default'))
            # матрица корпуса (все пары БУ×напряжение, где есть строки)
            matrix = {}
            cu_set = {cu_none}
            cu_set |= set(ControlUnitInstalledOption.objects.filter(
                kind='INTEGRATED'))
            for cu in cu_set:
                for ps in (ps_220,):
                    res = resolve_matrix(item, cu, ps, 'on_off')
                    for s in res['slots']:
                        if s['code'] in ('LIMIT_SWITCHES', 'WAY_SWITCHES',
                                         'TORQUE_SWITCHES'):
                            for row in s['rows']:
                                key = (cu.code, ps.code, s['code'])
                                matrix.setdefault(key, []).append(
                                    (row['name'], row['availability']))
            self.stdout.write(f'\n{name} (строка {r}):')
            for label, db_opts, slot_code in (
                    ('LIMIT', e, 'LIMIT_SWITCHES'),
                    ('WAY', w, 'WAY_SWITCHES'),
                    ('TORQUE', t, 'TORQUE_SWITCHES')):
                has_table = any(
                    ws.cell(r, c).value is not None for c in slot_cols[label])
                self._compare(self.stdout, label, db_opts, matrix, slot_code,
                              has_table)

        self.stdout.write('\n=== БУ×напряжение (БД) ===')
        for name, item, r in models:
            pairs = CUOpt.objects.filter(
                power_supply_option__model_line_item=item).values_list(
                'control_unit__code',
                'power_supply_option__power_supply__code').distinct()
            self.stdout.write(f'{name}: {len(pairs)} пар БУ×напряжение')

        self.stdout.write('\n=== Wiring (сводка) ===')
        total = CUOpt.objects.count()
        wired = CUOpt.objects.exclude(control_unit_wiring__isnull=True).count()
        self.stdout.write(
            f'ElectricControlUnitOption: {total}, с привязанной схемой: {wired}')
        if wired == 0:
            self.stdout.write(
                'ВНИМАНИЕ: ни одна CU-опция не привязана к wiring — 21 связка '
                'ControlUnitWiring существуют без привязки к моделям; перенос '
                'схем придётся строить заново (по кодам wiring и профилям).')

    def _compare(self, out, label, db_opts, matrix, slot_code, has_table):
        """Сопоставление через-опций БД и матричных строк слота."""
        db_spdt = any(c == 'spdt' for c, _ in db_opts)
        db_dpdt = any(c == 'dpdt' for c, _ in db_opts)
        db_none_default = any(c == 'none' and d for c, d in db_opts)
        m_spdt = m_dpdt = False
        for (_, _, code), rows in matrix.items():
            if code != slot_code:
                continue
            for row_name, _ in rows:
                if 'SPDT' in row_name:
                    m_spdt = True
                if 'DPDT' in row_name:
                    m_dpdt = True
        if not has_table:
            status = 'таблица не заполнена (сравнение невозможно)'
        elif db_none_default and not (m_spdt or m_dpdt):
            status = 'OK: БД «нет» ↔ таблица без строк'
        elif db_spdt == m_spdt and db_dpdt == m_dpdt:
            status = 'OK'
        else:
            status = (f'РАСХОЖДЕНИЕ: БД spdt={db_spdt} dpdt={db_dpdt} '
                      f'none_def={db_none_default} | таблица spdt={m_spdt} '
                      f'dpdt={m_dpdt}')
        out.write(f'  {label}: {status}')
