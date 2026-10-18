"""
Заливка матрицы сигналов ЭП из таблицы `available-options-ea-AOX.xlsx` (фаза 5).

Синхронизация — по первой колонке («Model», пользовательские названия):
точное совпадение с `ElectricActuatorModelLineItem.name`, затем с нормализацией
(удаление точек: «AR11E.005» → «AR11E005»).

Строки матрицы создаются на уровне **корпуса** (`body`): модели общего корпуса
(в т.ч. QUI-варианты) разделяют опции — это же решает привязку схем по корпусу.
Если у модели нет корпуса — скоуп model_line_item.

Покрытие (v1) — блоки с однозначной семантикой:
- переключатели Basic/INT (End/Way/Torque, SPDT/DPDT) — слоты LIMIT/WAY/TORQUE;
- позиционная ОС (4-20 акт/пас; навесной трансмиттер 19–20/49–51) —
  слот POSITION_FEEDBACK;
- обогрев привода/БУ (separate wire / from actuator, 73–76/83–88) — слоты HEATER_*.

Известные упрощения v1 (выводятся в отчёт):
- концевые/путевые/моментные — пара контактов (Откр/Закр) представляется одной
  строкой слота (сигнал-представитель FB_*_OPEN_*); разложение на два сигнала —
  вместе с генератором схем;
- Basic-строки заливаются для напряжения 220AC (таблица не кодирует напряжение
  в маркерах); 24DC/380VAC — после уточнения по примечаниям;
- команды (61–88 Control), перегрев, индикатор, счётчик, S2/стартер,
  позиционер (89–92) — пропускаются до уточнения семантики;
- маркеры: 'st'/статус колонки 'st' → std; 'opt?'/'√' → opt; '×'/'/'/статус 'no' →
  строки нет (статусы колонок — строка 5, чётная наследует нечётную, INT-тройки —
  первая колонка тройки).

Идемпотентность: перед заливкой удаляются ВСЕ строки со скоупом body=<корпуса
обрабатываемых моделей> — команда пересоздаёт AOX-строки целиком.

Использование:
    python manage.py load_ea_aox_matrix [--xlsx путь]
"""
from django.core.management.base import BaseCommand

from electric_actuators.models import (
    EaSignalSlot, EaFeedbackSignal, EaFeedbackDevice, EaSignalMatrixEntry,
    ElectricActuatorModelLineItem,
)
from params.models import ControlUnitInstalledOption, PowerSupplies, ActuatorHeaterSupply

# Basic FB: колонка → (слот, сигнал); режим — BASIC_MODE
BASIC_FB = {
    3: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE'),
    4: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE'),
    5: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    6: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    7: ('LIMIT_SWITCHES', 'FB_END_OPEN_SPDT'),
    8: ('LIMIT_SWITCHES', 'FB_END_OPEN_SPDT'),
    9: ('LIMIT_SWITCHES', 'FB_END_OPEN_DPDT'),
    10: ('LIMIT_SWITCHES', 'FB_END_OPEN_DPDT'),
    11: ('WAY_SWITCHES', 'FB_WAY_OPEN_SPDT'),
    12: ('WAY_SWITCHES', 'FB_WAY_OPEN_SPDT'),
    13: ('WAY_SWITCHES', 'FB_WAY_OPEN_DPDT'),
    14: ('WAY_SWITCHES', 'FB_WAY_OPEN_DPDT'),
    15: ('TORQUE_SWITCHES', 'FB_TORQUE_OPEN_SPDT'),
    16: ('TORQUE_SWITCHES', 'FB_TORQUE_OPEN_SPDT'),
    17: ('TORQUE_SWITCHES', 'FB_TORQUE_OPEN_DPDT'),
    18: ('TORQUE_SWITCHES', 'FB_TORQUE_OPEN_DPDT'),
    19: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
    20: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
}
BASIC_MODE = {c: ('modulating' if c % 2 == 0 else 'on_off')
              for c in BASIC_FB}
BASIC_MODE.update({73: 'on_off', 74: 'modulating', 75: 'on_off', 76: 'modulating'})

# INT FB: колонка → (слот, сигнал); БУ — INT_CU
INT_FB = {}
for _col, (_slot, _sig) in {
        25: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_ACTIVE'),
        28: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
        31: ('LIMIT_SWITCHES', 'FB_END_OPEN_SPDT'),
        34: ('LIMIT_SWITCHES', 'FB_END_OPEN_DPDT'),
        37: ('WAY_SWITCHES', 'FB_WAY_OPEN_SPDT'),
        40: ('WAY_SWITCHES', 'FB_WAY_OPEN_DPDT'),
        43: ('TORQUE_SWITCHES', 'FB_TORQUE_OPEN_SPDT'),
        46: ('TORQUE_SWITCHES', 'FB_TORQUE_OPEN_DPDT'),
        49: ('POSITION_FEEDBACK', 'FB_POS_4_20MA_PASSIVE'),
}.items():
    for offset in range(3):
        INT_FB[_col + offset] = (_slot, _sig)
INT_CU = {}
for _col in INT_FB:
    INT_CU[_col] = {0: 'int-o', 1: 'int-l', 2: 'int-n'}[(_col - 25) % 3]

# Обогрев: колонка → (слот, heater_supply)
HEATER = {
    73: ('HEATER_ACTUATOR', 'SEPARATE_LINE'),
    74: ('HEATER_ACTUATOR', 'SEPARATE_LINE'),
    75: ('HEATER_ACTUATOR', 'MOTOR_CIRCUIT'),
    76: ('HEATER_ACTUATOR', 'MOTOR_CIRCUIT'),
}
HEATER_INT = {}
for _col, (_slot, _hs) in {
        83: ('HEATER_CONTROL_UNIT', 'SEPARATE_LINE'),
        86: ('HEATER_CONTROL_UNIT', 'MOTOR_CIRCUIT'),
}.items():
    for offset in range(3):
        HEATER_INT[_col + offset] = (_slot, _hs)
INT_CU.update({83: 'int-o', 84: 'int-l', 85: 'int-n',
               86: 'int-o', 87: 'int-l', 88: 'int-n'})

PS_220 = '220-AC'


def _column_statuses(ws):
    """Статус колонки из строки 5 (st/opt?/no): чётная наследует нечётную;
    INT-тройки (ICU/SRCU/LCU) — статус первой колонки тройки."""
    status = {}
    for col in list(BASIC_FB) + list(INT_FB) + list(HEATER) + list(HEATER_INT):
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

    Положительные маркеры: 'st' → std; 'opt?' → opt; '√' → std при статусе
    колонки 'st', иначе opt. '×'/'/'/None/текст — строки нет; статус 'no' —
    строки нет.
    """
    if status == 'no':
        return None
    if marker == 'st':
        return 'std'
    if marker == 'opt?':
        return 'opt'
    if marker == '√':
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
                  for code in ('SEPARATE_LINE', 'MOTOR_CIRCUIT')}
        slots = {s.code: s for s in EaSignalSlot.objects.all()}
        signals = {s.code: s for s in EaFeedbackSignal.objects.all()}
        transmitter = EaFeedbackDevice.objects.get(code='TRANSMITTER_4_20')
        col_status = _column_statuses(ws)

        matched, unmatched = [], []
        bodies_touched = set()
        excel_rows = []  # (ws_row, name, item, scope)

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
            if item.body_id and item.body_id not in bodies_touched:
                bodies_touched.add(item.body_id)
                EaSignalMatrixEntry.objects.filter(body=item.body).delete()
            excel_rows.append((r, name, item, scope))

        rows_created = 0
        batch = []

        def _append(row):
            batch.append(row)

        for r, name, item, scope in excel_rows:
            # Basic FB
            for col, (slot_code, sig_code) in BASIC_FB.items():
                marker = ws.cell(r, col).value
                avail = availability_from(marker, col_status.get(col))
                if avail is None:
                    continue
                row = EaSignalMatrixEntry(
                    control_unit=cu_none, power_supply=ps_220,
                    mode=BASIC_MODE[col], slot=slots[slot_code],
                    feedback_signal=signals[sig_code],
                    availability=avail,
                    **scope)
                if col in (19, 20):
                    row.device = transmitter
                batch.append(row)

            # INT FB (БУ из колонки; режим both; 220AC)
            for col, (slot_code, sig_code) in INT_FB.items():
                marker = ws.cell(r, col).value
                avail = availability_from(marker, col_status.get(col))
                if avail is None:
                    continue
                row = EaSignalMatrixEntry(
                    control_unit=cu_int[INT_CU[col]], power_supply=ps_220,
                    mode='both', slot=slots[slot_code],
                    feedback_signal=signals[sig_code],
                    availability=avail,
                    **scope)
                if col in (49, 50, 51):
                    row.device = transmitter
                batch.append(row)

            # Обогрев Basic (режим из пары)
            for col, (slot_code, heater_code) in HEATER.items():
                marker = ws.cell(r, col).value
                avail = availability_from(marker, col_status.get(col))
                if avail is None:
                    continue
                batch.append(EaSignalMatrixEntry(
                    control_unit=cu_none, power_supply=ps_220,
                    mode=BASIC_MODE[col], slot=slots[slot_code],
                    heater_supply=heater[heater_code],
                    availability=avail,
                    **scope))

            # Обогрев INT (БУ из колонки)
            for col, (slot_code, heater_code) in HEATER_INT.items():
                marker = ws.cell(r, col).value
                avail = availability_from(marker, col_status.get(col))
                if avail is None:
                    continue
                batch.append(EaSignalMatrixEntry(
                    control_unit=cu_int[INT_CU[col]], power_supply=ps_220,
                    mode='both', slot=slots[slot_code],
                    heater_supply=heater[heater_code],
                    availability=avail,
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
            'Упрощения v1: пары контактов — одна строка-представитель; Basic — '
            'только 220AC; команды/перегрев/индикатор/счётчик/S2/позиционер — '
            'не залиты (см. docstring команды).'))

    def _find_item(self, name):
        qs = ElectricActuatorModelLineItem.objects.filter(name=name)
        if qs.exists():
            return qs.first()
        normalized = name.replace('.', '')
        return ElectricActuatorModelLineItem.objects.filter(
            name=normalized).first()
