"""
Заливка матрицы сигналов ЭП из таблицы `available-options-ea-AOX.xlsx` (фаза 5,
пакет 13.2 плана).

Синхронизация — по первой колонке («Model», пользовательские названия):
точное совпадение с `ElectricActuatorModelLineItem.name`, затем с нормализацией
(удаление точек: «AR11E.005» → «AR11E005»).

Строки матрицы создаются на уровне **корпуса** (`body`): модели общего корпуса
(в т.ч. QUI-варианты) разделяют опции — это же решает привязку схем по корпусу.
Если у модели нет корпуса — скоуп model_line_item.

Покрытие (v2, после согласования 2026-10-18):
- пары контактов (End/Way/Torque SPDT/DPDT) — **две строки OPEN+CLOSE** с общим
  `bundle` (атомарный выбор), bundle-код уникален на корпус;
- позиционная ОС (4-20 акт/пас; навесной трансмиттер 19–20/49–51) —
  слот POSITION_FEEDBACK, device=TRANSMITTER_4_20;
- OverHeat (21/23 Basic, 55/57 INT) — слот THERMAL_SENSOR, FB_OVERHEAT_NC/SPDT,
  device=THERMAL_RELAY;
- обогрев БУ (83–88, INT) — слот HEATER_CONTROL_UNIT: separate wire →
  SEPARATE_LINE, from actuator → CU_CIRCUIT; «No heater…» — строки нет;
- обогрев ПРИВОДА (73–76) — НЕ строка матрицы (живёт в температурной опции);
- `availability='std'` → `is_default=True`;
- маркеры: 'st'/'√'+статус → std; 'opt?'/'√'/'Customizable' → opt; '×'/'/'/
  'no' → строки нет; 'No heater…' → строк нет.

Напряжение: таблица не кодирует напряжение — заливается 220-AC; 380-AC/24-DC
добавляются через Excel-каркас выгрузки (ea_matrix_io).

Идемпотентность: перед заливкой удаляются ВСЕ строки со скоупом body=<корпуса
обрабатываемых моделей> — команда пересоздаёт AOX-строки целиком.

Использование:
    python manage.py load_ea_aox_matrix [--xlsx путь]
"""
from django.core.management.base import BaseCommand

from electric_actuators.models import (
    EaSignalSlot, EaFeedbackSignal, EaFeedbackDevice, EaSignalMatrixEntry,
    EaSlotOption, ElectricActuatorModelLineItem,
)
from params.models import ControlUnitInstalledOption, PowerSupplies, ActuatorHeaterSupply

# Пары контактов: колонка → (слот, пара). Пара раскрывается в две строки
# FB_*_OPEN_* + FB_*_CLOSE_* с общим bundle.
BASIC_PAIRS = {
    7: ('LIMIT_SWITCHES', 'END_SPDT'),
    8: ('LIMIT_SWITCHES', 'END_SPDT'),
    9: ('LIMIT_SWITCHES', 'END_DPDT'),
    10: ('LIMIT_SWITCHES', 'END_DPDT'),
    11: ('WAY_SWITCHES', 'WAY_SPDT'),
    12: ('WAY_SWITCHES', 'WAY_SPDT'),
    13: ('WAY_SWITCHES', 'WAY_DPDT'),
    14: ('WAY_SWITCHES', 'WAY_DPDT'),
    15: ('TORQUE_SWITCHES', 'TORQUE_SPDT'),
    16: ('TORQUE_SWITCHES', 'TORQUE_SPDT'),
    17: ('TORQUE_SWITCHES', 'TORQUE_DPDT'),
    18: ('TORQUE_SWITCHES', 'TORQUE_DPDT'),
}
BASIC_MODE = {c: ('modulating' if c % 2 == 0 else 'on_off')
              for c in BASIC_PAIRS}
BASIC_MODE.update({3: 'on_off', 4: 'modulating', 5: 'on_off', 6: 'modulating',
                   19: 'on_off', 20: 'modulating', 21: 'on_off',
                   23: 'modulating'})

# Basic FB: колонка → (слот, сигнал); 19-20 — навесной трансмиттер
BASIC_FB = {
    3: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE'),
    4: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE'),
    5: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    6: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    19: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    20: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
}

# OverHeat: колонка → сигнал (слот THERMAL_SENSOR, device=THERMAL_RELAY)
BASIC_OVERHEAT = {21: 'FB_OVERHEAT_NC', 23: 'FB_OVERHEAT_SPDT'}

# INT-пары: базовая колонка тройки → (слот, пара); тройка = ICU/SRCU/LCU
INT_PAIRS = {
    31: ('LIMIT_SWITCHES', 'END_SPDT'),
    34: ('LIMIT_SWITCHES', 'END_DPDT'),
    37: ('WAY_SWITCHES', 'WAY_SPDT'),
    40: ('WAY_SWITCHES', 'WAY_DPDT'),
    43: ('TORQUE_SWITCHES', 'TORQUE_SPDT'),
    46: ('TORQUE_SWITCHES', 'TORQUE_DPDT'),
}
INT_FB = {
    25: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE'),
    28: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    49: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
}
INT_OVERHEAT = {55: 'FB_OVERHEAT_NC', 57: 'FB_OVERHEAT_SPDT'}
INT_CU_OFFSET = {0: 'int-o', 1: 'int-l', 2: 'int-n'}

# Обогрев БУ (INT): базовая колонка тройки → heater_supply
HEATER_INT = {
    83: ('HEATER_CONTROL_UNIT', 'SEPARATE_LINE'),
    86: ('HEATER_CONTROL_UNIT', 'CU_CIRCUIT'),
}

PS_220 = '220-AC'


def _triple_cols(base):
    return {base + offset for offset in range(3)}


def _column_statuses(ws):
    """Статус колонки из строки 5: чётная наследует нечётную;
    INT-тройки (ICU/SRCU/LCU) — статус первой колонки тройки."""
    status = {}
    all_cols = (set(BASIC_PAIRS) | set(BASIC_FB) | set(BASIC_OVERHEAT)
                | _triple_cols(31) | _triple_cols(34) | _triple_cols(37)
                | _triple_cols(40) | _triple_cols(43) | _triple_cols(46)
                | _triple_cols(25) | _triple_cols(28) | _triple_cols(49)
                | _triple_cols(55) | _triple_cols(57)
                | _triple_cols(83) | _triple_cols(86))
    for col in all_cols:
        if col <= 24:
            base = col if col % 2 == 1 else col - 1
        elif col <= 60:
            base = 25 + ((col - 25) // 3) * 3
        else:
            base = 83 + ((col - 83) // 3) * 3
        v = ws.cell(5, base).value
        status[col] = str(v).strip() if v else None
    return status


def availability_from(marker, status):
    """Маркер ячейки + статус колонки → availability (или None — строки нет).

    Положительные: 'st' → std; 'opt?' → opt; '√' → std при статусе 'st', иначе
    opt; 'Customizable' → opt (на заказ). '×'/'/'/None/'no' — строки нет;
    'No heater…' — строк нет.
    """
    if status == 'no':
        return None
    if marker is None:
        return None
    m = str(marker).strip().lower()
    if m in ('×', '/', ''):
        return None
    if m.startswith('no heater'):
        return None
    if m == 'st':
        return 'std'
    if m in ('opt?', 'customizable'):
        return 'opt'
    if m == '√':
        return 'std' if status == 'st' else 'opt'
    return None


class Command(BaseCommand):
    help = 'Заливка матрицы сигналов ЭП из available-options-ea-AOX.xlsx'

    def add_arguments(self, parser):
        parser.add_argument('--xlsx', type=str,
                            default='available-options-ea-AOX.xlsx')

    def handle(self, *args, **options):
        import openpyxl

        wb = openpyxl.load_workbook(options['xlsx'], data_only=True)
        ws = wb.active

        cu_none = ControlUnitInstalledOption.objects.get(code='none')
        cu_int = {code: ControlUnitInstalledOption.objects.get(code=code)
                  for code in ('int-o', 'int-l', 'int-n')}
        ps_220 = PowerSupplies.objects.get(code=PS_220)
        heater = {code: ActuatorHeaterSupply.objects.get(code=code)
                  for code in ('SEPARATE_LINE', 'CU_CIRCUIT')}
        slots = {s.code: s for s in EaSignalSlot.objects.all()}
        signals = {s.code: s for s in EaFeedbackSignal.objects.all()}
        opt_by_code = {o.code: o for o in EaSlotOption.objects.all()}
        transmitter = EaFeedbackDevice.objects.get(code='TRANSMITTER_4_20')
        thermal_relay = EaFeedbackDevice.objects.get(code='THERMAL_RELAY')
        col_status = _column_statuses(ws)

        matched, unmatched = [], []
        bodies_touched = set()
        excel_rows = []  # (ws_row, name, item, scope, scope_code)

        # Первый проход: матчинг + очистка строк затронутых корпусов
        for r in range(7, ws.max_row + 1):
            name = ws.cell(r, 1).value
            if not name or not isinstance(name, str):
                continue
            item = self._find_item(name)
            if item is None:
                unmatched.append(name)
                continue
            matched.append(name)
            scope = {'body': item.body} if item.body_id else {
                'model_line_item': item}
            scope_code = (item.body.code or item.body.name) if item.body_id \
                else item.code
            if item.body_id and item.body_id not in bodies_touched:
                bodies_touched.add(item.body_id)
                EaSignalMatrixEntry.objects.filter(body=item.body).delete()
            excel_rows.append((r, name, item, scope, scope_code))

        rows_created = 0
        batch = []

        def _add(**row_kwargs):
            batch.append(EaSignalMatrixEntry(**row_kwargs))

        def _bundle(pair, mode, scope_code):
            """Уникальный на корпус код пакета (атомарность пары Откр/Закр)."""
            return f'{pair}:{scope_code}:{mode}'

        def _pair_rows(col, marker, cu, mode, slot_code, pair, scope, scope_code):
            avail = availability_from(marker, col_status.get(col))
            if avail is None:
                return
            bundle = _bundle(pair, mode, scope_code)
            kind, contact = pair.split('_', 1)  # 'END', 'SPDT'
            option = opt_by_code.get(f'{slot_code}:{pair}')
            for pos in ('OPEN', 'CLOSE'):
                sig_code = f'FB_{kind}_{pos}_{contact}'
                _add(control_unit=cu, power_supply=ps_220, mode=mode,
                     slot=slots[slot_code], feedback_signal=signals[sig_code],
                     availability=avail, is_default=(avail == 'std'),
                     bundle=bundle, option=option, **scope)

        for r, name, item, scope, scope_code in excel_rows:
            # Basic FB (аналог + трансмиттер)
            for col, (slot_code, sig_code) in BASIC_FB.items():
                marker = ws.cell(r, col).value
                avail = availability_from(marker, col_status.get(col))
                if avail is None:
                    continue
                row_kwargs = dict(
                    control_unit=cu_none, power_supply=ps_220,
                    mode=BASIC_MODE[col], slot=slots[slot_code],
                    feedback_signal=signals[sig_code],
                    option=opt_by_code.get(f'{slot_code}:{sig_code}'),
                    availability=avail, is_default=(avail == 'std'),
                    **scope)
                if col in (19, 20):
                    row_kwargs['device'] = transmitter
                batch.append(EaSignalMatrixEntry(**row_kwargs))

            # Basic OverHeat (21/23)
            for col, sig_code in BASIC_OVERHEAT.items():
                marker = ws.cell(r, col).value
                avail = availability_from(marker, col_status.get(col))
                if avail is None:
                    continue
                batch.append(EaSignalMatrixEntry(
                    control_unit=cu_none, power_supply=ps_220,
                    mode=BASIC_MODE[col], slot=slots['THERMAL_SENSOR'],
                    feedback_signal=signals[sig_code],
                    device=thermal_relay,
                    option=opt_by_code.get(f'THERMAL_SENSOR:{sig_code}'),
                    availability=avail, is_default=(avail == 'std'),
                    **scope))

            # Basic пары контактов (OPEN+CLOSE, bundle)
            for col, (slot_code, pair) in BASIC_PAIRS.items():
                _pair_rows(col, ws.cell(r, col).value, cu_none, BASIC_MODE[col],
                           slot_code, pair, scope, scope_code)

            # INT FB (аналог, трансмиттер, пары, OverHeat)
            for base, (slot_code, sig_code) in INT_FB.items():
                for offset in range(3):
                    col = base + offset
                    marker = ws.cell(r, col).value
                    avail = availability_from(marker, col_status.get(col))
                    if avail is None:
                        continue
                    row_kwargs = dict(
                        control_unit=cu_int[INT_CU_OFFSET[offset]],
                        power_supply=ps_220, mode='both',
                        slot=slots[slot_code],
                        feedback_signal=signals[sig_code],
                        option=opt_by_code.get(f'{slot_code}:{sig_code}'),
                        availability=avail, is_default=(avail == 'std'),
                        **scope)
                    if base == 49:
                        row_kwargs['device'] = transmitter
                    batch.append(EaSignalMatrixEntry(**row_kwargs))

            for base, (slot_code, pair) in INT_PAIRS.items():
                for offset in range(3):
                    col = base + offset
                    _pair_rows(col, ws.cell(r, col).value,
                               cu_int[INT_CU_OFFSET[offset]], 'both',
                               slot_code, pair, scope, scope_code)

            for base, sig_code in INT_OVERHEAT.items():
                for offset in range(3):
                    col = base + offset
                    marker = ws.cell(r, col).value
                    avail = availability_from(marker, col_status.get(col))
                    if avail is None:
                        continue
                    batch.append(EaSignalMatrixEntry(
                        control_unit=cu_int[INT_CU_OFFSET[offset]],
                        power_supply=ps_220, mode='both',
                        slot=slots['THERMAL_SENSOR'],
                        feedback_signal=signals[sig_code],
                        device=thermal_relay,
                        option=opt_by_code.get(f'THERMAL_SENSOR:{sig_code}'),
                        availability=avail, is_default=(avail == 'std'),
                        **scope))

            # Обогрев БУ (INT 83–88): separate wire / from actuator
            for base, (slot_code, heater_code) in HEATER_INT.items():
                for offset in range(3):
                    col = base + offset
                    marker = ws.cell(r, col).value
                    avail = availability_from(marker, col_status.get(col))
                    if avail is None:
                        continue
                    batch.append(EaSignalMatrixEntry(
                        control_unit=cu_int[INT_CU_OFFSET[offset]],
                        power_supply=ps_220, mode='both',
                        slot=slots[slot_code],
                        heater_supply=heater[heater_code],
                        option=opt_by_code.get(f'{slot_code}:{heater_code}'),
                        availability=avail, is_default=(avail == 'std'),
                        **scope))

        # Пакетная вставка (bulk_create — на порядки быстрее построчных save)
        EaSignalMatrixEntry.objects.bulk_create(batch, batch_size=500)
        rows_created = len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Матчинг: найдено {len(matched)}, не найдено {len(unmatched)}'))
        if unmatched:
            self.stdout.write(self.style.WARNING(
                'Не найдены в БД: ' + ', '.join(unmatched)))
        self.stdout.write(f'Строк матрицы создано: {rows_created}')
        self.stdout.write(self.style.WARNING(
            'v2: пары Откр/Закр с bundle; OverHeat→THERMAL_SENSOR (термореле); '
            'обогрев БУ→HEATER_CONTROL_UNIT; обогрев привода — в температурных '
            'опциях; Customizable→opt; std→is_default; напряжение 220-AC '
            '(380/24 — через Excel-каркас).'))

    def _find_item(self, name):
        qs = ElectricActuatorModelLineItem.objects.filter(name=name)
        if qs.exists():
            return qs.first()
        normalized = name.replace('.', '')
        return ElectricActuatorModelLineItem.objects.filter(
            name=normalized).first()
