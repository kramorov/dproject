"""Расшифровка кода ЕТТ (Единые технические требования).

Формат входной строки (10 полей, разделители ``*``, ``-``, ``/``)::

    ЗКв1000*16-ФЛ1Л-Х-313-12-н/ЭПДА1/Н/С0

Порядок полей (по документам владельца ЕТТ):
  0. Вид МТР + DN (буквы + цифры в одном поле)
  1. PN, кгс/см²
  2. Тип присоединения к трубопроводу (не расшифровывается)
  3. Климатическое исполнение
  4. Материальное исполнение (не расшифровывается)
  5. Толщина стенки трубопровода (не расшифровывается)
  6. Класс прочности трубопровода (не расшифровывается)
  7. Тип привода + комбинации ЭП (электро/управление/опции)
  8. Температура рабочей среды (не расшифровывается)
  9. Исполнение по сейсмостойкости
"""

import re

from .models import (
    MtrType,
    DnType,
    PnType,
    EttActuatorType,
    EttClimaticOption,
    EttOpenTime,
    EttElectricOptionsCombination,
    EttControlOptionsCombination,
    EttOtherOptionsCombination,
    EttSeismicOption,
)

# Разделители полей ЕТТ: * - , /
_SPLIT_RE = re.compile(r'[^*\-,/]+')
# Первая цифра делит поле «Вид МТР + DN» на буквенную и цифровую части.
_FIRST_DIGIT_RE = re.compile(r'([^\d]+)(\d.*)')


def _split_code(code):
    parts = _SPLIT_RE.findall(code or '')
    if len(parts) != 10:
        raise ValueError(
            'Неверный формат кода ЕТТ: ожидается 10 полей, получено {n}.'.format(n=len(parts))
        )
    return parts


def _split_first_digit(value):
    m = _FIRST_DIGIT_RE.match(value)
    if m:
        return m.group(1), m.group(2)
    return value, ''


def _get(model, code, label):
    obj = model.objects.filter(symbolic_code=code).first()
    if obj is None:
        raise ValueError('В справочнике не найдено «{label}» со значением «{code}».'.format(
            label=label, code=code))
    return obj


def _display(instance, attr='name'):
    """Человекочитаемое значение справочной записи (или «—» для пустой)."""
    if instance is None:
        return '—'
    value = getattr(instance, attr, None) or getattr(instance, 'name', '') or ''
    value = str(value).strip()
    return value or '—'


def _open_time(dn_value, mtr_type, actuator_speed):
    row = EttOpenTime.objects.filter(
        actuator_speed=actuator_speed,
        mtr_type=mtr_type,
        dn_from__lt=dn_value,
        dn_up_to__gte=dn_value,
    ).first()
    if row is None:
        raise ValueError(
            'Не найдено время открытия/закрытия для DN={dn} и скорости привода '
            '«{speed}».'.format(dn=dn_value, speed=actuator_speed)
        )
    return row


def decode_ett(code):
    """Возвращает словарь с ``desc_table`` и разобранными полями.

    При нераспознанном/неполном коде бросает ``ValueError`` с текстом ошибки.
    """
    code = (code or '').strip()
    if not code:
        raise ValueError('Код ЕТТ не может быть пустым.')

    parts = _split_code(code)
    desc_table = []

    # 0 — Вид МТР + DN
    valve_type_str, valve_dn_str = _split_first_digit(parts[0])
    if not valve_type_str or not valve_dn_str:
        raise ValueError(
            'Первое поле «{p}» должно состоять из буквенного кода вида МТР и '
            'цифрового DN.'.format(p=parts[0])
        )
    valve_type = _get(MtrType, valve_type_str, 'Вид МТР')
    valve_dn = _get(DnType, valve_dn_str, 'DN')
    desc_table.append({'param_name': 'Вид МТР', 'param_value': valve_type.text_description})
    desc_table.append({'param_name': 'DN, мм', 'param_value': valve_dn.valve_dn_value})

    # 1 — PN
    valve_pn = _get(PnType, parts[1], 'PN')
    desc_table.append({
        'param_name': 'Номинальное давление PN, кгс/см²',
        'param_value': valve_pn.valve_pn_value,
    })

    # 3 — Климатическое исполнение
    climatic = _get(EttClimaticOption, parts[3], 'Климатическое исполнение')
    desc_table.append({
        'param_name': 'Климатическое исполнение по ГОСТ 15150, категория размещения 1',
        'param_value': '{desc} от {tmin} до {tmax}'.format(
            desc=climatic.text_description,
            tmin=climatic.work_temp_min,
            tmax=climatic.work_temp_max,
        ),
    })

    # 7 — Тип привода + комбинации ЭП (последние 3 символа — комбинации).
    actuator_block = parts[7]
    time_to_open_min = None
    time_to_open_max = None
    option_ip = '—'
    option_exd = '—'
    actuator_voltage = '—'
    status_signal = '—'
    control_signal = '—'
    feedback_signal = '—'
    cu_location = '—'
    cu_heater = '—'
    display_type = '—'
    cg1_type = '—'
    cg23_type = '—'

    # Код типа привода — отделяем от трёх символов комбинаций ЭП.
    if len(actuator_block) > 3:
        actuator_type_symbol = actuator_block[:-3]
    else:
        # Ручной привод (редуктор/маховик) — комбинаций ЭП нет.
        actuator_type_symbol = actuator_block

    actuator_type_obj = _get(EttActuatorType, actuator_type_symbol, 'Тип привода')

    if len(actuator_block) > 3:
        # Электропривод: последние три символа — комбинации «опции/управление/электро».
        other_symbol = actuator_block[-1]
        control_symbol = actuator_block[-2]
        electric_symbol = actuator_block[-3]

        open_time = _open_time(valve_dn.valve_dn_value, valve_type, actuator_type_obj.actuator_speed)
        time_to_open_min = open_time.time_to_open_min
        time_to_open_max = open_time.time_to_open_max
        desc_table.append({'param_name': 'Время открытия мин, с', 'param_value': time_to_open_min})
        desc_table.append({'param_name': 'Время открытия макс, с', 'param_value': time_to_open_max})

        electric = _get(EttElectricOptionsCombination, electric_symbol, 'Электротехнические характеристики')
        option_exd = _display(electric.exd_choice)
        option_ip = _display(electric.ip_choice)
        actuator_voltage = _display(electric.power_choice)
        desc_table.append({'param_name': 'Исполнение по взрывозащите', 'param_value': option_exd})
        desc_table.append({'param_name': 'Исполнение по пылевлагозащите, не ниже', 'param_value': option_ip})
        desc_table.append({'param_name': 'Напряжение питания, В', 'param_value': actuator_voltage})

        control = _get(EttControlOptionsCombination, control_symbol, 'Контроль и управление')
        status_signal = _display(control.status_signal_choice, 'text_description')
        control_signal = _display(control.control_signal_choice, 'text_description')
        feedback_signal = _display(control.feedback_signal_choice, 'text_description')
        desc_table.append({
            'param_name': 'Сигнализация состояния Открыто/Закрыто/Стоп/Авария/Дистанционный режим',
            'param_value': status_signal,
        })
        desc_table.append({
            'param_name': 'Сигнал управления Открыть/Закрыть/Стоп',
            'param_value': control_signal,
        })
        desc_table.append({
            'param_name': 'Сигнал обратной связи / Протокол',
            'param_value': feedback_signal,
        })

        other = _get(EttOtherOptionsCombination, other_symbol, 'Опции/комплектующие')
        cu_location = _display(other.cu_location_choice, 'text_description')
        cu_heater = _display(other.cu_heater_choice, 'text_description')
        display_type = _display(other.display_choice, 'text_description')
        cg1_type = _display(other.cg1_choice, 'text_description')
        cg23_type = _display(other.cg23_choice, 'text_description')
        desc_table.append({
            'param_name': 'Наличие и расположение блока управления',
            'param_value': cu_location,
        })
        desc_table.append({
            'param_name': 'Наличие встроенного электрообогрева блока управления',
            'param_value': cu_heater,
        })
        desc_table.append({'param_name': 'Графический дисплей', 'param_value': display_type})
        desc_table.append({'param_name': 'Кабельный ввод КВ1 для силового кабеля', 'param_value': cg1_type})
        desc_table.append({
            'param_name': 'Кабельный ввод КВ2/КВ3 для контрольного и интерфейсного кабелей',
            'param_value': cg23_type,
        })

    # 9 — Сейсмостойкость
    seismic = _get(EttSeismicOption, parts[9], 'Сейсмостойкость')
    desc_table.append({'param_name': 'Сейсмичность района размещения', 'param_value': seismic.text_description})
    desc_table.append({'param_name': 'Тип привода', 'param_value': actuator_type_obj.text_description})

    return {
        'desc_table': desc_table,
        'valve_type': valve_type.text_description,
        'valve_dn': valve_dn.valve_dn_value,
        'valve_pn': valve_pn.valve_pn_value,
        'actuator_type': actuator_type_obj.text_description,
        'time_to_open_min': time_to_open_min,
        'time_to_open_max': time_to_open_max,
        'option_ip': option_ip,
        'option_exd': option_exd,
        'actuator_voltage': actuator_voltage,
        'cu_location': cu_location,
        'cu_heater': cu_heater,
        'display_type': display_type,
        'cg1_type': cg1_type,
        'cg23_type': cg23_type,
        'control_signal': control_signal,
        'status_signal': status_signal,
        'feedback_signal': feedback_signal,
    }
