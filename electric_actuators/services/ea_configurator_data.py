# electric_actuators/services/ea_configurator_data.py
"""
Данные конфигуратора ЭП из матрицы сигналов (фаза 6 плана).

Единая точка для фронта/селекторов: для выбранной модели × БУ × напряжение ×
режим (и температурной опции) возвращает слоты матрицы с локализованными
строками, предвыборы, пакеты, конфликты, предупреждения; при переданном наборе
выбранных строк — ошибки валидации, привязку схемы подключения («есть или
нет») и собранный ext-код заказа (сервис ea_ext_code).

Контекстные позиции ext (cu/cu_p/ps/mode) конфигуратор добавляет из своего
выбора через `context`; позиции слотов — из выбранных матричных строк
(option_position_code), temp — из температурной опции.
"""
from electric_actuators.models import EaSignalMatrixEntry
from electric_actuators.services.ea_signal_resolver import (
    resolve_matrix, validate_selection, find_diagram_binding,
)
from electric_actuators.services.ea_ext_code import (
    option_position_code, build_ext_code,
)


def _row_ext(entry):
    """Строка матрицы → 'позиция=код' (или '' — позиции в ext нет)."""
    if not entry.option_id:
        return ''
    pc = option_position_code(entry.option)
    return f'{pc[0]}={pc[1]}' if pc else ''


def configurator_signal_data(model_line_item, control_unit, power_supply, mode,
                             locale=None):
    """Слоты/строки матрицы для селекторов конфигуратора."""
    res = resolve_matrix(model_line_item, control_unit, power_supply, mode,
                         locale=locale)
    for slot in res['slots']:
        for row in slot['rows']:
            entry = EaSignalMatrixEntry.objects.get(pk=row['id'])
            row['ext'] = _row_ext(entry)
    return res


def selection_ext_code(model_line_item, selected_row_ids, temp_option=None,
                       context=None):
    """Ext-код из выбранных матричных строк (+ temp-опция и контекст).

    context — словарь контекстных позиций (cu/cu_p/ps/mode), которые не
    выражаются строками матрицы.
    """
    model_line = model_line_item.model_line
    selection = dict(context or {})
    for entry in EaSignalMatrixEntry.objects.filter(
            pk__in=selected_row_ids).select_related(
            'option__slot', 'feedback_signal', 'protocol', 'heater_supply'):
        if not entry.option_id:
            continue
        pc = option_position_code(entry.option)
        if pc:
            selection.setdefault(pc[0], pc[1])
    if temp_option is not None and getattr(temp_option, 'code', ''):
        from electric_actuators.services.ea_ext_code import TEMP_BASE
        base = TEMP_BASE.get(temp_option.code, '')
        if (base and temp_option.heater_supply_id
                and temp_option.heater_supply.code == 'MOTOR_CIRCUIT'):
            base += 'M'
        selection['temp'] = base
    return build_ext_code(model_line, selection)


def selection_validation(model_line_item, control_unit, power_supply, mode,
                         selected_row_ids, temp_option=None, context=None):
    """Итоговый блок конфигуратора: ошибки выбора, схема, ext-код."""
    res = configurator_signal_data(model_line_item, control_unit, power_supply,
                                   mode)
    out = {
        'errors': validate_selection(selected_row_ids, resolved=res),
        'diagram': find_diagram_binding(model_line_item, control_unit,
                                        power_supply, mode, selected_row_ids),
        'ext_code': selection_ext_code(model_line_item, selected_row_ids,
                                       temp_option=temp_option, context=context),
    }
    return out
