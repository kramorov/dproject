from django.db.models import Model
from collections import namedtuple

from electric_actuators.models import ModelLine, ElectricActuatorData, ActualActuator
from params.models import IpOption, ExdOption, PowerSupplies, DigitalProtocolsSupportOption, ControlUnitInstalledOption, \
    EnvTempParameters

SearchResult = namedtuple('SearchResult', ['record', 'text_description'])


def find_record_by_fields(model: Model, search_criteria: dict, return_field: str):
    """
    Универсальная функция для поиска записи в базе данных по указанным полям и значениям,
    с возвратом указанного поля.

    :param model: Модель, в которой нужно искать запись.
    :param search_criteria: Словарь с полями и значениями для фильтрации.
    :param return_field: Название поля, значение которого нужно вернуть.
    :return: Именованный кортеж с записью и значением указанного поля.
    search_criteria = {
    "symbolic_code": "IP68",
    "ip_rank": 5}
    """
    try:
        record = model.objects.get(**search_criteria)
        text_description = getattr(record, return_field, 'Ошибка!')
        if not text_description:
            text_description = 'Н/Д'
        return SearchResult(record=record, text_description=text_description)
    except model.DoesNotExist:
        return SearchResult(record=float('nan'), text_description='Ошибка!')


def process_model_name(model_string):
    result_table = [
        {"parameter_name": "Название параметра", "parameter_value": "Значение параметра"},
    ]
    model_line = ''
    model_suffix = ''
    model = ''
    speed = ''
    qui = ''
    lt = ''
    ip = ''
    cu = ''
    dp = ''
    voltage = ''
    ex = ''
    # model_string = 'Ar21E007.s45.LT.IP68.INT/N.380/50.Ex'
    model_string_upper = model_string.upper()
    if model_string_upper[:2] != 'AR':
        result_table.extend([
            {"parameter_name": "Ошибка",
             "parameter_value": "Это не название модели привода Архимед! Начинается не с AR"}
        ])
        return result_table

    lines = model_string_upper.split('.')
    model = lines[0]
    model_line = model.split('E')[0] + 'E'
    model_line_result = find_record_by_fields(ModelLine, {'name': model_line}, 'name')
    if model_line_result.text_description == 'Ошибка!':
        model_line = 'Серия приводов с названием = ' + model_line + ' не найдена.'
        result_table.extend([
            {"parameter_name": "Ошибка", "parameter_value": model_line}
        ])
        return result_table
    else:
        model_line = model_line_result.text_description
    dp_list = list(DigitalProtocolsSupportOption.objects.values_list('symbolic_code', flat=True))
    cu_list = list(ControlUnitInstalledOption.objects.values_list('encoding', flat=True))
    for i in range(1, len(lines)):
        cur_str = lines[i]
        # print(lines[i])
        if 'S' in cur_str:
            model_suffix = cur_str
            continue
        if 'QUI' in cur_str:
            model_suffix = cur_str
            continue
        if 'EX' in cur_str:
            ex = cur_str
            continue
        if 'LT' in cur_str:
            lt = cur_str
            lt_result = find_record_by_fields(EnvTempParameters, {'symbolic_code': cur_str}, 'text_description')
            lt = lt_result.text_description
            continue
        if ('380' in cur_str) or ('220' in cur_str) or ('24/DC' in cur_str):
            voltage = cur_str
            continue
        if 'IP' in cur_str:
            ip_result = find_record_by_fields(IpOption, {'symbolic_code': cur_str}, 'text_description')
            if ip_result.text_description == 'Ошибка!':
                ip = 'Запись с параметром =' + cur_str + ' не найдена.'
            else:
                ip = ip_result.text_description
        if cur_str in cu_list:
            cu_result = find_record_by_fields(ControlUnitInstalledOption, {'encoding': cur_str}, 'text_description')
            cu = cu_result.text_description
            continue
        if cur_str in dp_list:
            dp_result = find_record_by_fields(DigitalProtocolsSupportOption, {'symbolic_code': cur_str},
                                              'text_description')
            dp = dp_result.text_description
            continue
    if len(model_suffix) > 0:
        model = model + '.' + model_suffix
    voltage_result = find_record_by_fields(PowerSupplies, {'symbolic_code': voltage}, 'text_description')
    if voltage_result.text_description == 'Ошибка!':
        voltage = 'Модель привода с напряжением = ' + voltage + ' не найдена.'
        result_table.extend([
            {"parameter_name": "Ошибка", "parameter_value": voltage}
        ])
        return result_table
    else:
        voltage = voltage_result.text_description

    model_result = find_record_by_fields(ElectricActuatorData, {'name': model, 'voltage': voltage_result.record},
                                         'name')
    if model_result.text_description == 'Ошибка!':
        model = 'Модель привода с названием = ' + model + ' не найдена.'
        result_table.extend([
            {"parameter_name": "Ошибка", "parameter_value": model}
        ])
        return result_table
    else:
        model = model_result.text_description
    if len(dp) > 0 and cu_result.record.encoding != 'INT/N':
        result_table.extend([
            {"parameter_name": "Ошибка", "parameter_value": 'Поддержка цифровых протоколов возможна только с блоком '
                                                            'INT/N!' + dp + '=>' + cu_result.record.encoding}
        ])
        return result_table
    # Заполняем данными реальную модель привода
    actual_actuator = ActualActuator.objects.create(actual_model=model_result.record)
    actual_actuator.init()
    if len(ex) == 0:
        exd_no_result = find_record_by_fields(ExdOption, {'symbolic_code': 'NONE'},
                                              'exd_full_code')
        ex = model_line_result.record.default_exd.exd_full_code
    else:
        ex = 'Общепромышленное исполнение'

    # model_result = find_record_by_field(ElectricActuatorData, 'name', model, 'name')
    # if model_result.record is float('nan'):
    #     model = 'Модель привода с названием = ' + model + ' не найдена.'
    #     result_table.extend([
    #         {"parameter_name": "Ошибка", "parameter_value": model}
    #     ])
    #     return result_table
    result_table.extend([
        {"parameter_name": 'Серия приводов', "parameter_value": model_line},
        {"parameter_name": 'Модель', "parameter_value": model},
        {"parameter_name": 'qui', "parameter_value": qui},
        {"parameter_name": 'lt', "parameter_value": lt},
        {"parameter_name": 'ip', "parameter_value": ip},
        {"parameter_name": 'Блок управления', "parameter_value": cu},
        {"parameter_name": 'Поддержка цифровых протоколов', "parameter_value": dp},
        {"parameter_name": 'voltage', "parameter_value": voltage},
        {"parameter_name": 'Взрывозащита', "parameter_value": ex}
    ])

    return result_table
