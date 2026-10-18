# electric_actuators/services/ea_matrix_io.py
"""
Экспорт/импорт матрицы сигналов серии ЭП в Excel (xlsx).

Строка файла = одна опция: модель × БУ × напряжение × режим × слот × сигнал
(или питание обогрева) × форма × доступность. В файл пишутся КОДЫ опций
(control_unit.code, power_supply.code, slot.code, signal.code / heater_supply.code,
form.code, body.code, item.code) — по ним выполняется обратный импорт (upsert
строк матрицы на уровне корпуса).

Экспорт собирает для каждого model_line_item серии:
- эффективные строки (std/opt) — через резолвер по парам БУ×напряжение×режим,
  существующим в матрице корпуса;
- строки-запреты (na) из сырых строк бренда/серии/корпуса.
"""
from django.db.models import Q

from electric_actuators.models import (
    EaSignalMatrixEntry, ElectricActuatorModelLine,
    ElectricActuatorBody, ElectricActuatorModelLineItem,
)
from electric_actuators.services.ea_signal_resolver import resolve_matrix

FIELDS = ['series_code', 'item_code', 'body_code', 'control_unit',
          'power_supply', 'mode', 'slot', 'kind', 'signal_code', 'form_code',
          'heater_supply', 'availability', 'is_default', 'bundle',
          'device', 'encoding', 'ext_encoding']


def _row_dict(series_code, item_code, body_code, entry):
    """Матричная строка/слот-строка → dict для xlsx."""
    return {
        'series_code': series_code,
        'item_code': item_code,
        'body_code': body_code,
        'control_unit': entry['control_unit'],
        'power_supply': entry['power_supply'],
        'mode': entry['mode'],
        'slot': entry['slot'],
        'kind': entry['kind'],
        'signal_code': entry.get('signal_code') or '',
        'form_code': entry.get('form_code') or '',
        'heater_supply': entry.get('heater_supply') or '',
        'availability': entry['availability'],
        'is_default': entry.get('is_default', False),
        'bundle': entry.get('bundle') or '',
        'device': entry.get('device') or '',
        'encoding': entry.get('encoding') or '',
        'ext_encoding': entry.get('ext_encoding') or '',
    }


def export_series_rows(model_line_code):
    """Все строки матрицы серии (эффективные + na) в виде списка dict."""
    line = ElectricActuatorModelLine.objects.get(code=model_line_code)
    rows = []
    for item in ElectricActuatorModelLineItem.objects.filter(
            model_line=line).select_related('body'):
        body = item.body
        # пары БУ×напряжение×режим, существующие в матрице корпуса/серии/бренда
        pairs = (EaSignalMatrixEntry.objects.filter(
            Q(body=body) | Q(model_line=line) | Q(brand=line.brand))
            .values('control_unit__code', 'power_supply__code', 'mode')
            .distinct())
        for pair in pairs:
            from params.models import ControlUnitInstalledOption, PowerSupplies
            cu = ControlUnitInstalledOption.objects.get(
                code=pair['control_unit__code'])
            ps = PowerSupplies.objects.get(code=pair['power_supply__code'])
            res = resolve_matrix(item, cu, ps, pair['mode'])
            for slot in res['slots']:
                for srow in slot['rows']:
                    entry = EaSignalMatrixEntry.objects.get(pk=srow['id'])
                    kind = ('signal'
                            if entry.feedback_signal_id or entry.control_signal_id
                            else 'protocol' if entry.protocol_id
                            else 'heater')
                    rows.append(_row_dict(
                        line.code, item.code or item.name,
                        body.code if body and getattr(body, 'code', None)
                        else (body.name if body else ''),
                        {
                            'control_unit': pair['control_unit__code'],
                            'power_supply': pair['power_supply__code'],
                            'mode': pair['mode'],
                            'slot': slot['code'],
                            'kind': kind,
                            'signal_code': (
                                entry.feedback_signal.code
                                if entry.feedback_signal_id
                                else entry.control_signal.code
                                if entry.control_signal_id else ''),
                            'form_code': (
                                entry.feedback_signal.form.code
                                if entry.feedback_signal_id
                                else entry.control_signal.form.code
                                if entry.control_signal_id else ''),
                            'heater_supply': (entry.heater_supply.code
                                              if entry.heater_supply_id else ''),
                            'availability': srow['availability'],
                            'is_default': srow['is_default'],
                            'bundle': srow['bundle'],
                            'device': (entry.device.code
                                       if entry.device_id else ''),
                            'encoding': entry.encoding,
                            'ext_encoding': entry.ext_encoding,
                        }))
        # na-запреты (сырые строки скоупов, относящихся к модели)
        for entry in EaSignalMatrixEntry.objects.filter(
                availability='na').filter(
                Q(body=body) | Q(model_line=line) | Q(brand=line.brand)):
            rows.append(_row_dict(
                line.code, item.code or item.name,
                body.code if body and getattr(body, 'code', None)
                else (body.name if body else ''),
                {
                    'control_unit': entry.control_unit.code,
                    'power_supply': entry.power_supply.code,
                    'mode': entry.mode,
                    'slot': entry.slot.code,
                    'kind': ('signal' if entry.feedback_signal_id
                             or entry.control_signal_id
                             else 'protocol' if entry.protocol_id
                             else 'heater'),
                    'signal_code': (entry.feedback_signal.code
                                    if entry.feedback_signal_id
                                    else entry.control_signal.code
                                    if entry.control_signal_id
                                    else entry.protocol.code
                                    if entry.protocol_id else ''),
                    'form_code': (entry.feedback_signal.form.code
                                  if entry.feedback_signal_id
                                  else entry.control_signal.form.code
                                  if entry.control_signal_id else ''),
                    'heater_supply': (entry.heater_supply.code
                                      if entry.heater_supply_id else ''),
                    'availability': 'na',
                    'is_default': False,
                    'bundle': entry.bundle,
                    'device': entry.device.code if entry.device_id else '',
                    'encoding': entry.encoding,
                    'ext_encoding': entry.ext_encoding,
                }))
    return rows


def write_xlsx(path, rows):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'ea_signal_matrix'
    ws.append(FIELDS)
    for row in rows:
        ws.append([row.get(f, '') for f in FIELDS])
    wb.save(path)
    return len(rows)


def read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = []
    for i, values in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        rec = dict(zip(FIELDS, values))
        if not rec.get('slot'):
            continue
        rows.append(rec)
    return rows


def apply_import(rows):
    """Upsert строк матрицы из файла (скоуп — корпус по body_code)."""
    from params.models import ControlUnitInstalledOption, PowerSupplies, \
        ActuatorHeaterSupply
    from electric_actuators.models import (EaSignalSlot, EaFeedbackSignal,
                                           EaControlSignal, EaFeedbackDevice)
    stats = {'created': 0, 'updated': 0, 'errors': []}
    for rec in rows:
        try:
            body = None
            if rec.get('body_code'):
                body = ElectricActuatorBody.objects.filter(
                    code=rec['body_code']).first() or \
                    ElectricActuatorBody.objects.filter(
                        name=rec['body_code']).first()
            item = ElectricActuatorModelLineItem.objects.filter(
                code=rec.get('item_code')).first()
            if body is None and item is not None:
                body = item.body
            cu = ControlUnitInstalledOption.objects.get(
                code=rec['control_unit'])
            ps = PowerSupplies.objects.get(code=rec['power_supply'])
            slot = EaSignalSlot.objects.get(code=rec['slot'])
            kw = dict(mode=rec['mode'], availability=rec['availability'] or 'opt',
                      is_default=rec.get('is_default') in (True, 'True', 1),
                      bundle=rec.get('bundle') or None,
                      encoding=rec.get('encoding') or '',
                      ext_encoding=rec.get('ext_encoding') or '')
            lookup = dict(control_unit=cu, power_supply=ps, mode=rec['mode'],
                          slot=slot)
            if body is not None:
                lookup['body'] = body
            elif item is not None:
                lookup['model_line_item'] = item
            else:
                raise ValueError('Нет body_code/item_code для строки')
            if rec.get('kind') == 'heater':
                hs = ActuatorHeaterSupply.objects.get(
                    code=rec['heater_supply'])
                lookup['heater_supply'] = hs
                obj, created = EaSignalMatrixEntry.objects.update_or_create(
                    defaults=kw, **lookup)
            else:
                sig = EaFeedbackSignal.objects.get(code=rec['signal_code']) \
                    if EaFeedbackSignal.objects.filter(
                        code=rec['signal_code']).exists() else \
                    EaControlSignal.objects.get(code=rec['signal_code'])
                device = EaFeedbackDevice.objects.filter(
                    code=rec.get('device')).first() if rec.get('device') else None
                kw['device'] = device
                lookup['feedback_signal' if EaFeedbackSignal.objects.filter(
                    code=rec['signal_code']).exists() else 'control_signal'] = sig
                obj, created = EaSignalMatrixEntry.objects.update_or_create(
                    defaults=kw, **lookup)
            stats['created' if created else 'updated'] += 1
        except Exception as e:  # noqa: BLE001 — отчёт по строкам
            stats['errors'].append(f'{rec.get("item_code")}/{rec.get("slot")}: {e}')
    return stats
