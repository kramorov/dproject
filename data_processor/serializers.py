# text_processor/serializers.py
from rest_framework import serializers
import re

# Справочник для типов арматуры
ARMATURE_TYPES = {
    "ЗК" : "Задвижка клиновая" ,
    "ЗКв" : "Задвижка вентилируемая" ,
    "ЗКс" : "Задвижка сальниковая" ,
    # Добавьте другие типы арматуры по необходимости
}
# Справочник Тип присоединения к трубопроводу:
VALVES_CONNECTION_TYPES_TO_PIPE = {
    "Ф" : "Фланцевое присоединение с ответными фланцами, прокладками и крепежом" ,
    "ФП" : "Фланцевое присоединение (с ответными фланцами с приварными катушками имеющие внутреннее заводское "
           "антикоррозионное покрытие под приварку к трубопроводу, прокладками и крепежом)" ,
    "С" : "С концами под приварку" ,
    "СП" : "Под приварку к трубопроводу, имеющие внутреннее заводское антикоррозионное покрытие под приварку к трубопроводу" ,
    "МG" : "Муфтовый c G – трубной цилиндрической резьбой по ГОСТ 6357" ,
    "MRc" : "Rc – конической резьбой по ГОСТ 6211" ,
    "MK" : "К – конической дюймовой резьбой по ГОСТ 6111" ,
    "Ф0" : "Без ответных фланцев и крепежа" ,
    "ФЗ" : "Фланцевое присоединение с ответными фланцами, прокладками, крепежом и заглушкой поворотной (для установки с "
           "одной стороны)" ,
}

# Справочник для DN значений Ряд DN задвижки клиновой в зависимости от наружного диаметра трубопровода:
VALVES_DN = {
    "10" : {"pipe_dn" : 16 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "15" : {"pipe_dn" : 20 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "20" : {"pipe_dn" : 26 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "25" : {"pipe_dn" : 32 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "32" : {"pipe_dn" : 42 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "40" : {"pipe_dn" : 45 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "50" : {"pipe_dn" : 57 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "65" : {"pipe_dn" : 76 , "comment" : "При новом проектировании не применять." , "time_to_open_min_std" : 0 ,
            "time_to_open_max_std" : 60 , "time_to_open_max_fast" : 15} ,
    "80" : {"pipe_dn" : 89 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 60 ,
            "time_to_open_max_fast" : 15} ,
    "100" : {"pipe_dn" : 114 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 100 ,
             "time_to_open_max_fast" : 22} ,
    "125" : {"pipe_dn" : 133 , "comment" : "При новом проектировании не применять." , "time_to_open_min_std" : 0 ,
             "time_to_open_max_std" : 100 , "time_to_open_max_fast" : 22} ,
    "150" : {"pipe_dn" : 159 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 100 ,
             "time_to_open_max_fast" : 22} ,
    "150а" : {"pipe_dn" : 168 , "comment" : "" , "time_to_open_min_std" : 0 , "time_to_open_max_std" : 100 ,
              "time_to_open_max_fast" : 22} ,
    "200" : {"pipe_dn" : 219 , "comment" : "" , "time_to_open_min_std" : 100 , "time_to_open_max_std" : 180 ,
             "time_to_open_max_fast" : 35} ,
    "250" : {"pipe_dn" : 273 , "comment" : "" , "time_to_open_min_std" : 100 , "time_to_open_max_std" : 180 ,
             "time_to_open_max_fast" : 35} ,
    "300" : {"pipe_dn" : 325 , "comment" : "" , "time_to_open_min_std" : 100 , "time_to_open_max_std" : 180 ,
             "time_to_open_max_fast" : 35} ,
    "350" : {"pipe_dn" : 377 , "comment" : "При новом проектировании не применять." , "time_to_open_min_std" : 120 ,
             "time_to_open_max_std" : 240 , "time_to_open_max_fast" : 40} ,
    "400" : {"pipe_dn" : 426 , "comment" : "" , "time_to_open_min_std" : 120 , "time_to_open_max_std" : 240 ,
             "time_to_open_max_fast" : 40} ,
    "450" : {"pipe_dn" : 450 , "comment" : "При новом проектировании не применять." , "time_to_open_min_std" : 120 ,
             "time_to_open_max_std" : 240 , "time_to_open_max_fast" : 40} ,
    "500" : {"pipe_dn" : 530 , "comment" : "" , "time_to_open_min_std" : 120 , "time_to_open_max_std" : 240 ,
             "time_to_open_max_fast" : 40} ,
    "600" : {"pipe_dn" : 630 , "comment" : "" , "time_to_open_min_std" : 180 , "time_to_open_max_std" : 320 ,
             "time_to_open_max_fast" : 45} ,
    "700" : {"pipe_dn" : 720 , "comment" : "" , "time_to_open_min_std" : 180 , "time_to_open_max_std" : 320 ,
             "time_to_open_max_fast" : 45} ,
    "800" : {"pipe_dn" : 820 , "comment" : "" , "time_to_open_min_std" : 180 , "time_to_open_max_std" : 320 ,
             "time_to_open_max_fast" : 45} ,
    "1000" : {"pipe_dn" : 1020 , "comment" : "" , "time_to_open_min_std" : 300 , "time_to_open_max_std" : 420 ,
              "time_to_open_max_fast" : 55} ,
    "1200" : {"pipe_dn" : 1220 , "comment" : "" , "time_to_open_min_std" : 300 , "time_to_open_max_std" : 420 ,
              "time_to_open_max_fast" : 55} ,
    "1400" : {"pipe_dn" : 1420 , "comment" : "" , "time_to_open_min_std" : 300 , "time_to_open_max_std" : 420 ,
              "time_to_open_max_fast" : 60} ,

}
# Ряд номинальных давлений
VALVES_PN = {"16" : 16 , "25" : 25 , "40" : 40 , "63" : 63 , "100" : 100 , "160" : 100 , "200" : 200 , "250" : 250 ,
             "320" : 320}
# Климатическое исполнение
TEMPERATURE_OPTION = {"Х" : {"name" : "Х - Холодный климат" , "temp_min" : -45 , "temp_max" : 45} ,
                      "У" : {"name" : "У - Умеренный климат" , "temp_min" : -45 , "temp_max" : 45}}
# Типы приводов
ACTUATOR_TYPES = {
    "РР" : {"name" : "Ручной редуктор (в соответствии с Таблицей 23 настоящих Единых технических требований)" ,
            "type" : "none"} ,
    "РМ" : {"name" : "Ручной маховик (в соответствии с Таблицей 23" , "type" : "none"} ,
    "УШ1" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 450…700" , "type" : "none"} ,
    "УШ2" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 650…1100" , "type" : "none"} ,
    "УШ3" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 1100…1700" , "type" : "none"} ,
    "УШ4" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 1700…2300" , "type" : "none"} ,
    "УШ5" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 2300…2900" , "type" : "none"} ,
    "УШ6" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 2900…5250" , "type" : "none"} ,
    "УШ7" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 5250…7000" , "type" : "none"} ,
    "УШ8" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 7000…7750" , "type" : "none"} ,
    "УШ9" : {"name" : "Ручной маховик (с удлинителем штока), Длина штока, мм 7750…8500" , "type" : "none"} ,
    "УШа" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 1000" , "type" : "none"} ,
    "УШб" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 1500" , "type" : "none"} ,
    "УШв" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 2000" , "type" : "none"} ,
    "УШг" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 2500" , "type" : "none"} ,
    "УШд" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 3000" , "type" : "none"} ,
    "УШе" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 3500" , "type" : "none"} ,
    "УШж" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 4000" , "type" : "none"} ,
    "УШз" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 4500" , "type" : "none"} ,
    "УШи" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 5000" , "type" : "none"} ,
    "УШк" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 5500" , "type" : "none"} ,
    "УШл" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 6000" , "type" : "none"} ,
    "УШм" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 6500" , "type" : "none"} ,
    "УШн" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 7000" , "type" : "none"} ,
    "УШо" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 7500" , "type" : "none"} ,
    "УШп" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 8000" , "type" : "none"} ,
    "УШр" : {"name" : "Ручной маховик с УФ и глубиной установки ЗК, мм: 8500" , "type" : "none"} ,

    "ЭПХХХ" : {
        "name" : "Стандартный ЭП со временем перекрытия арматуры, приведенным в Таблице 28, и с обозначением модификации "
                 "в соответствии с Приложением 1 настоящих Единых технических требований" , "type" : "standart"} ,
    "ЭБХХХ" : {
        "name" : "Быстродействующий ЭП со временем перекрытия арматуры, приведенным в Таблице 28, и с обозначением "
                 "модификации в соответствии с Приложением 1 настоящих Единых технических требований" ,
        "type" : "fast"} ,
    "ЭБПХХХ" : {"name" : "Быстродействующий ЭП для СПАЗ, со временем перекрытия арматуры, приведенным в Таблице 28, "
                         "и с обозначением модификации в соответствии с Приложением 1 настоящих Единых технических "
                         "требований" , "type" : "fast"} ,
    "ЭГХХХХ" : {"name" : "Стандартный ЭГП со временем перекрытия арматуры, приведенным в Таблице 20, и с обозначением "
                         "модификации в соответствии с Таблицей 39 настоящих Единых технических требований" ,
                "type" : "standart"} ,
    "ЭБГХХХХ" : {
        "name" : "Быстродействующий ЭГП для СПАЗ, со временем перекрытия арматуры, приведенным в Таблице 20, "
                 "и с обозначением модификации в соответствии с Таблицей 39 настоящих Единых технических требований" ,
        "type" : "fast"} ,
    "ППХХХХ" : {
        "name" : "Стандартный ПП со временем перекрытия арматуры, приведенным в Таблице 20, и с обозначением "
                 "модификации в соответствии с Таблицей 36 настоящих Единых технических требований" ,
        "type" : "standart"} ,
    "ПБПХХХХ" : {
        "name" : "Быстродействующий ПП для СПАЗ, со временем перекрытия арматуры, приведенным в Таблице 20, "
                 "и с обозначением модификации в соответствии с Таблицей 36 настоящих Единых технических требований" ,
        "type" : "fast"} ,
    "ПГХХХХ" : {
        "name" : "Стандартный ПГП со временем перекрытия арматуры, приведенным в Таблице 20, и с обозначением "
                 "модификации в соответствии с Таблицей 42 настоящих Единых технических требований" ,
        "type" : "standart"} ,
    "ПБГХХХХ" : {
        "name" : "Быстродействующий ПГП для СПАЗ, со временем перекрытия арматуры, приведенным в Таблице 20, "
                 "и с обозначением модификации в соответствии с Таблицей 42 настоящих Единых технических требований" ,
        "type" : "fast"} ,
}
# Температура рабочей среды
WORKING_MEDIUM_TEMP = {
    "А" : "Для температуры до 100оС*" ,
    "Н" : "Для температуры до 200 0С" ,
    "К" : "Для температуры до 250 0С" ,
    "Л" : "Для температуры до 425оС" ,
    "О" : "Для температуры до 475оС" ,
    "В" : "Для высокой температуры до 5650С" ,
    "Т" : "Для температуры до 650оС" ,
    "Ф" : "Для температуры до 900оС" ,
}
# Сейсмичность района размещения
SEISMIC_CONDITIONS = {
    "С0" : "Не сейсмостойкое" ,
    "С" : "Сейсмостойкое" ,
    "ПС" : "Повышенной сейсмостойкости" ,
}
# ЭЛЕКТРОТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ - комбинации
ELECTRIC_OPTIONS_COMBINATIONS = {
    "А" : {"option_exd" : "ExdIIB" , "option_ip" : "IP54" , "actuator_voltage" : "220/50"} ,
    "Б" : {"option_exd" : "ExdIIB" , "option_ip" : "IP65" , "actuator_voltage" : "220/50"} ,
    "В" : {"option_exd" : "ExdIIB" , "option_ip" : "IP54" , "actuator_voltage" : "380/50"} ,
    "Г" : {"option_exd" : "ExdIIB" , "option_ip" : "IP65" , "actuator_voltage" : "380/50"} ,
    "Д" : {"option_exd" : "Общепром." , "option_ip" : "IP54" , "actuator_voltage" : "220/50"} ,
    "Е" : {"option_exd" : "Общепром." , "option_ip" : "IP65" , "actuator_voltage" : "220/50"} ,
    "Ж" : {"option_exd" : "Общепром." , "option_ip" : "IP54" , "actuator_voltage" : "380/50"} ,
    "З" : {"option_exd" : "Общепром." , "option_ip" : "IP65" , "actuator_voltage" : "380/50"},
    "И" : {"option_exd" : "ExdIIC" , "option_ip" : "IP54" , "actuator_voltage" : "220/50"} ,
    "К" : {"option_exd" : "ExdIIC" , "option_ip" : "IP65" , "actuator_voltage" : "220/50"} ,
    "Л" : {"option_exd" : "ExdIIC" , "option_ip" : "IP54" , "actuator_voltage" : "380/50"} ,
    "М" : {"option_exd" : "ExdIIC" , "option_ip" : "IP65" , "actuator_voltage" : "380/50"} ,
}
# КОНТРОЛЬ И УПРАВЛЕНИЕ - комбинации
# ОБОЗНАЧЕНИЕ КОМБИНАЦИИ (Х)
# СИГНАЛ СОСТОЯНИЯ, ОТКРЫТО/ЗАКРЫТО/АВАРИЯ/ДИСТАНЦИОННЫЙ РЕЖИМ
# СИГНАЛ УПРАВЛЕНИЯ, ОТКРЫТЬ/ ЗАКРЫТЬ/СТОП
# ПРОТОКОЛ ПЕРЕДАЧИ
CU_OPTIONS_COMBINATIONS = {
    "А" : {"cu_voltage" : "24 с.к." , "control_and_feedback" : "24 В" , "digital_protocol" : "–"} ,
    "Б" : {"cu_voltage" : "24 с.к." , "control_and_feedback" : "24 В" , "digital_protocol" : "Fieldbus"} ,
    "В" : {"cu_voltage" : "24 с.к." , "control_and_feedback" : "24 В" , "digital_protocol" : "Modbus"} ,
    "Г" : {"cu_voltage" : "220 с.к." , "control_and_feedback" : "220 В" , "digital_protocol" : "–"} ,
    "Д" : {"cu_voltage" : "220 с.к." , "control_and_feedback" : "220 В" , "digital_protocol" : "Fieldbus"} ,
    "Е" : {"cu_voltage" : "220 с.к." , "control_and_feedback" : "220 В" , "digital_protocol" : "Modbus"} ,
    "Ж" : {"cu_voltage" : "24 с.к." , "control_and_feedback" : "4-20 мА + HART" , "digital_protocol" : "–"} ,
    "З" : {"cu_voltage" : "24 с.к." , "control_and_feedback" : "4-20 мА + HART" , "digital_protocol" : "Fieldbus"} ,
    "И" : {"cu_voltage" : "24 с.к." , "control_and_feedback" : "4-20 мА + HART" , "digital_protocol" : "Modbus"} ,
    "К" : {"cu_voltage" : "220 с.к." , "control_and_feedback" : "4-20 мА + HART" , "digital_protocol" : "–"} ,
    "Л" : {"cu_voltage" : "220 с.к." , "control_and_feedback" : "4-20 мА + HART" , "digital_protocol" : "Fieldbus"} ,
    "М" : {"cu_voltage" : "220 с.к." , "control_and_feedback" : "4-20 мА + HART" , "digital_protocol" : "Modbus"}
}
# ОПЦИИ/КОМПЛЕКТУЮЩИЕ - комбинации
# ОБОЗНАЧЕНИЕ КОМБИНАЦИИ
# РАСПОЛОЖЕНИЕ БЛОКА УПРАВЛЕНИЯ
# КВ1, КАБЕЛЬНЫЙ ВВОД БРОНИРОВАННЫЙ НЕ БРОНИРОВАННЫЙ
# ГРАФИЧЕСКИЙ ЖК -ДИСПЛЕЙ
OTHER_OPTIONS_COMBINATIONS = {
    "1" : {"cu_location" : "На Электроприводе" , "armored_cable" : "Бронированный" , "display_type" : "С дисплеем"} ,
    "2" : {"cu_location" : "На Электроприводе" , "armored_cable" : "Небронированный с фитингом под металлорукав" ,
           "display_type" : "С дисплеем"} ,
    "3" : {"cu_location" : "На Электроприводе" , "armored_cable" : "Бронированный" , "display_type" : "Без дисплея"} ,
    "4" : {"cu_location" : "На Электроприводе" , "armored_cable" : "Небронированный с фитингом под металлорукав" ,
           "display_type" : "Без дисплея"} ,
    "5" : {"cu_location" : "Выносной блок" , "armored_cable" : "Бронированный" , "display_type" : "С дисплеем"} ,
    "6" : {"cu_location" : "Выносной блок" , "armored_cable" : "Небронированный с фитингом под металлорукав" ,
           "display_type" : "С дисплеем"} ,
    "7" : {"cu_location" : "Выносной блок" , "armored_cable" : "Бронированный" , "display_type" : "Без дисплея"} ,
    "8" : {"cu_location" : "Выносной блок" , "armored_cable" : "Небронированный с фитингом под металлорукав" ,
           "display_type" : "Без дисплея"} ,
}




def check_and_split(input_string , patterns) :
    # Перебираем все шаблоны
    for pattern in patterns :
        # Определяем количество фиксированных символов (можно вычислить длину фиксированной части, не включая 'Х')
        fixed_part_length = len(pattern) - pattern.count('Х')

        # Строим регулярное выражение: фиксированная часть + любые символы для оставшихся символов
        regex = re.compile(
            f"^{pattern[:fixed_part_length]}.{len(pattern) - fixed_part_length}$")  # .{X} для оставшихся символов

        # 1. Проверяем, совпадает ли строка с шаблоном
        match = regex.match(input_string)

        if match :
            # 2. Разделяем строку на фиксированную и переменную части
            fixed_part = pattern[:fixed_part_length]  # Фиксированная часть
            variable_part = input_string[fixed_part_length :]  # Переменная часть

            return {
                'match' : True ,
                'fixed_part' : fixed_part ,
                'variable_part' : variable_part
            }

    # Если не найдено совпадений
    return {'match' : False}


# Пример использования
patterns = ['ЭБХХХ' , 'ЭБГХХХХ' , 'ППХХХХ' , 'ПБПХХХХ']  # Пример шаблонов
input_string = 'ЭБ1234'  # Пример строки для проверки

result = check_and_split(input_string , patterns)

# if result['match'] :
#     print('Совпадает!')
#     print('Фиксированная часть:' , result['fixed_part'])
#     print('Переменная часть:' , result['variable_part'])
# else :
#     print('Строка не соответствует шаблонам.')


# Функция для разделения строки
def get_valve_type_dn(field_value) :
    # Регулярное выражение для поиска типа арматуры и DN
    match = re.match(r"([А-Яа-я]+)(\d+[а-я]*)" , field_value)

    if match :
        armature_type = match.group(1)  # Тип арматуры (например, "ЗК")
        dn_value = match.group(2)  # Значение DN (например, "150а")

        # Проверка на существование типа арматуры в справочнике
        if armature_type in ARMATURE_TYPES :
            armature_name = ARMATURE_TYPES[armature_type]
        else :
            raise ValueError(f"Тип арматуры '{armature_type}' не найден в справочнике.")

        # Проверка на существование DN в справочнике
        if dn_value in VALVES_DN :
            diameter = VALVES_DN[dn_value]['pipe_dn']
            comment = VALVES_DN[dn_value]['comment']
            time_to_open_max_fast = VALVES_DN[dn_value]['time_to_open_max_fast']
            time_to_open_min_std = VALVES_DN[dn_value]['time_to_open_min_std']
            time_to_open_max_std = VALVES_DN[dn_value]['time_to_open_max_std']

        else :
            raise ValueError(f"DN '{dn_value}' не найдено в справочнике.")

        return armature_name , dn_value , diameter , comment , time_to_open_min_std , time_to_open_max_std , time_to_open_max_fast
    else :
        raise ValueError(f"Не удалось разобрать строку: '{field_value}'")


# {
#   "input_string": "ЗК500*16-ФП-Х-К0/8-К48/РР/Н/С0"
# }
class ETTSerializer(serializers.Serializer) :
    # Определяем поля, которые мы будем извлекать из строки
    valve_type = serializers.CharField()
    valve_dn = serializers.IntegerField()
    valve_pipe_dn = serializers.IntegerField()
    valve_dn_comment = serializers.CharField()
    valve_pn = serializers.IntegerField()
    time_to_open_min = serializers.IntegerField()
    time_to_open_max = serializers.IntegerField()
    option_exd = serializers.CharField()
    option_ip = serializers.CharField()
    actuator_voltage = serializers.CharField()
    cu_location = serializers.CharField()
    armored_cable = serializers.CharField()
    display_type = serializers.CharField()
    cu_voltage = serializers.CharField()
    control_and_feedback = serializers.CharField()
    digital_protocol = serializers.CharField()
    temperature_option = serializers.CharField()
    temperature_option_temp_min = serializers.IntegerField()
    temperature_option_temp_max = serializers.IntegerField()
    actuator_type = serializers.CharField()
    working_medium_temp = serializers.CharField()
    seismic_conditions = serializers.CharField()
    valve_connection_type_to_pipe = serializers.CharField()

    def validate_input_string(self , value) :
        # Метод для валидации исходной строки и разбивки её на части
        # input_string_value = self.split_input_string(value)
        input_string_value = value
        parts = input_string_value.replace('*' , '-').replace('/' , '-').split('-')
        if len(parts) != 8 :
            raise serializers.ValidationError("Неверный формат входной строки. Число полей не равно 8.")
        return value

    # Когда вы вызываете serializer.is_valid() или при явном вызове serializer.save(), DRF автоматически вызывает
    # to_internal_value() для преобразования данных запроса в формат, с которым будет работать сериализатор.
    def to_internal_value(self , data) :
        # Метод для конвертации данных в правильные форматы
        desc_table = []
        input_string_value = data.get('input_string' , '')
        parts = input_string_value.replace('*' , '-').replace('/' , '-').split('-')
        # обрабатываем поле 0 - тип арматуры и Дн
        # valve_type , valve_dn , valve_pipe_dn , valve_dn_comment, time_to_open_min_std, time_to_open_max_std, time_to_open_max_fast = get_valve_type_dn(parts[0])
        armature_name , dn_value , valve_pipe_dn , valve_dn_comment , time_to_open_min_std , time_to_open_max_std , time_to_open_max_fast = get_valve_type_dn(
            parts[0])
        valve_dn = re.sub(r'\D' , '' , dn_value)
        desc_table.extend([{'param_name' : 'Тип:' , 'param_value' : armature_name} ,
                           {'param_name' : 'DN:' , 'param_value' : valve_dn} ,
                           {'param_name' : 'Наружный диаметр  трубопровода:' , 'param_value' : valve_pipe_dn} ,
                           {'param_name' : 'Примечание:' , 'param_value' : valve_dn_comment}])
        # обрабатываем поле 1 - Pn
        if parts[1] in VALVES_PN :
            valve_pn = VALVES_PN[parts[1]]
            desc_table.extend([{'param_name' : 'Номинальное давление PN, кгс/см²:' , 'param_value' : valve_pn}])
        else :
            raise ValueError(f"PN '{parts[1]}' не найдено в справочнике.")
        # обрабатываем поле 2 - Тип присоединения к трубопроводу
        if parts[2] in VALVES_CONNECTION_TYPES_TO_PIPE :
            valve_connection_type_to_pipe = VALVES_CONNECTION_TYPES_TO_PIPE[parts[2]]
            desc_table.extend([
                {'param_name' : 'Тип присоединения к трубопроводу' , 'param_value' : valve_connection_type_to_pipe}])
        else :
            raise ValueError(f"Тип присоединения к трубопроводу '{parts[2]}' не найден в справочнике.")
        # обрабатываем поле 4 - Климатическое исполнение
        if parts[3] in TEMPERATURE_OPTION :
            temperature_option = TEMPERATURE_OPTION[parts[3]]['name']
            temperature_option_temp_min = TEMPERATURE_OPTION[parts[3]]['temp_min']
            temperature_option_temp_max = TEMPERATURE_OPTION[parts[3]]['temp_max']
            desc_str = f"{temperature_option}  от {temperature_option_temp_min} до {temperature_option_temp_max}"
            desc_table.extend([{'param_name' : 'Климатическое исполнение по ГОСТ 15150 категория размещения 1:' ,
                                'param_value' : desc_str}])
        else :
            raise ValueError(f"Климатическое исполнение '{parts[3]}' не найдено в справочнике.")
        # обрабатываем поле 5 - Тип привода
        actuator_block_string = parts[7]
        actuator_block_string_len = len(actuator_block_string)
        time_to_open_min = 0
        time_to_open_max = 0
        if actuator_block_string_len > 3 :  # Это не ручной, это электропривод
            other_option_combination_symbol = actuator_block_string[actuator_block_string_len - 2]
            cu_option_combination_symbol = actuator_block_string[actuator_block_string_len - 3]
            electric_option_combination_symbol = actuator_block_string[actuator_block_string_len - 4]
            actuator_type_symbol = actuator_block_string[:actuator_block_string_len - 5]
            if ACTUATOR_TYPES[actuator_type_symbol]['type'] == 'fast' :
                time_to_open_min = 0
                time_to_open_max = VALVES_DN[dn_value]['time_to_open_max_fast']
            elif ACTUATOR_TYPES[actuator_type_symbol]['type'] == 'standart' :
                time_to_open_min = VALVES_DN[dn_value]['time_to_open_min_std']
                time_to_open_max = VALVES_DN[dn_value]['time_to_open_max_std']
            desc_table.extend([{'param_name' : 'Тип привода:' ,
                                'param_value' : ACTUATOR_TYPES[actuator_type_symbol]['name']} ,
                               {'param_name' : 'Время открытия мин, сек:' , 'param_value' : time_to_open_min} ,
                               {'param_name' : 'Время открытия макс, сек:' , 'param_value' : time_to_open_max}
                               ])

            if electric_option_combination_symbol in ELECTRIC_OPTIONS_COMBINATIONS :
                option_exd = ELECTRIC_OPTIONS_COMBINATIONS[electric_option_combination_symbol]['cu_location']
                option_ip = ELECTRIC_OPTIONS_COMBINATIONS[electric_option_combination_symbol]['option_ip']
                actuator_voltage = ELECTRIC_OPTIONS_COMBINATIONS[electric_option_combination_symbol]['actuator_voltage']
                desc_table.extend([{'param_name' : 'Исполнение по взрывозащите:' ,
                                    'param_value' : option_exd} ,
                                   {'param_name' : 'Исполнение по пылевлагозащите, не ниже:' ,
                                    'param_value' : option_ip} ,
                                   {'param_name' : 'Напряжение питания, U питания, В:' ,
                                    'param_value' : actuator_voltage} ,
                                   ])
            else :
                raise ValueError(
                    f"Символ для *Электротехнические характеристики* '{electric_option_combination_symbol}' не "
                    f"найдено в справочнике. Блок '{actuator_block_string} {actuator_block_string_len}'  ")

            if cu_option_combination_symbol in CU_OPTIONS_COMBINATIONS :
                cu_voltage = CU_OPTIONS_COMBINATIONS[cu_option_combination_symbol]['cu_voltage']
                control_and_feedback = CU_OPTIONS_COMBINATIONS[cu_option_combination_symbol]['control_and_feedback']
                digital_protocol = CU_OPTIONS_COMBINATIONS[cu_option_combination_symbol]['digital_protocol']
                desc_table.extend([{'param_name' : 'Сигнализация состояния Открыто/ЗакрытоАвария/Дистанционный режим:' ,
                                    'param_value' : cu_voltage} ,
                                   {'param_name' : 'Сигнал управления Открыть/Закрыть/Стоп:' ,
                                    'param_value' : control_and_feedback} ,
                                   {'param_name' : 'Протокол передачи данных:' ,
                                    'param_value' : digital_protocol} ,
                                   ])
            else :
                raise ValueError(
                    f"Символ для *Контроль и управление* '{cu_option_combination_symbol}' не найдено в справочнике.")

            if other_option_combination_symbol in OTHER_OPTIONS_COMBINATIONS :
                cu_location = OTHER_OPTIONS_COMBINATIONS[other_option_combination_symbol]['cu_location']
                armored_cable = OTHER_OPTIONS_COMBINATIONS[other_option_combination_symbol]['armored_cable']
                display_type = OTHER_OPTIONS_COMBINATIONS[other_option_combination_symbol]['display_type']
                desc_table.extend([{'param_name' : 'Расположение блока управления:' ,
                                    'param_value' : cu_location} ,
                                   {'param_name' : 'Кабельный ввод КВ1 для силового кабеля:' ,
                                    'param_value' : armored_cable} ,
                                   {'param_name' : 'Графический ЖК-дисплей:' ,
                                    'param_value' : display_type} ,
                                   ])
            else :
                raise ValueError(
                    f"Символ для *Опции и комплектующие* '{other_option_combination_symbol}' не найдено в справочнике.")

        else :  # Это ручной редуктор или маховик, это не электропривод
            actuator_type_symbol = actuator_block_string
            option_exd = "NONE"
            option_ip = "NONE"
            actuator_voltage = "NONE"
            cu_voltage = "NONE"
            control_and_feedback = "NONE"
            digital_protocol = "NONE"
            cu_location = "NONE"
            armored_cable = "NONE"
            display_type = "NONE"
        if actuator_type_symbol in ACTUATOR_TYPES :
            actuator_type = ACTUATOR_TYPES[actuator_type_symbol]
            desc_table.extend(
                [{'param_name' : 'Тип привода:' , 'param_value' : ACTUATOR_TYPES[actuator_type_symbol]['name']}])
        else :
            raise ValueError(f"Тип привода '{actuator_type_symbol}' не найден в справочнике.")
        # обрабатываем поле 6 - Температура рабочей среды
        if parts[8] in WORKING_MEDIUM_TEMP :
            working_medium_temp = WORKING_MEDIUM_TEMP[parts[8]]
            desc_table.extend([{'param_name' : 'Температура рабочей среды:' , 'param_value' : working_medium_temp}])
        else :
            raise ValueError(f"Температура рабочей среды '{parts[8]}' не найден в справочнике.")

        # обрабатываем поле 7 - Сейсмичность района размещения
        if parts[9] in SEISMIC_CONDITIONS :
            seismic_conditions = SEISMIC_CONDITIONS[parts[9]]
            desc_table.extend([{'param_name' : 'Сейсмичность района размещения:' , 'param_value' : seismic_conditions}])
        else :
            raise ValueError(f"Сейсмичность района размещения '{parts[9]}' не найдена в справочнике.")

        # Сохраняем данные в формате, соответствующем полям
        return {
            'valve_type' : armature_name ,
            'valve_dn' : int(valve_dn) ,
            'valve_pipe_dn' : int(valve_pipe_dn) ,
            'valve_dn_comment' : valve_dn_comment ,
            'valve_pn' : int(valve_pn) ,
            'time_to_open_min' : int(time_to_open_min) ,
            'time_to_open_max' : int(time_to_open_max) ,
            'valve_connection_type_to_pipe' : valve_connection_type_to_pipe ,
            'temperature_option' : temperature_option ,
            'temperature_option_temp_min' : temperature_option_temp_min ,
            'temperature_option_temp_max' : temperature_option_temp_max ,
            'actuator_type' : actuator_type ,
            'working_medium_temp' : working_medium_temp ,
            'seismic_conditions' : seismic_conditions ,
            'option_ip' : option_ip ,
            'option_exd' : option_exd ,
            'actuator_voltage' : actuator_voltage ,
            'cu_location' : cu_location ,
            'armored_cable' : armored_cable ,
            'display_type' : display_type ,
            'cu_voltage' : cu_voltage ,
            'control_and_feedback' : control_and_feedback ,
            'digital_protocol' : digital_protocol ,
            'desc_table' : desc_table ,
        }

    # Метод to_representation() вызывается при преобразовании внутреннего формата данных в формат,
    # пригодный для отправки в ответе API, например, в JSON. Этот метод используется для представления данных в виде,
    # который будет возвращен клиенту (обычно JSON).
    # Он вызывается, когда вы хотите вернуть сериализованный ответ, например, через Response(serializer.data).
    def to_representation(self , instance) :
        # Метод для сериализации данных в словарь (для ответа API)
        return {
            'valve_type' : instance['valve_type'] ,
            'valve_dn' : instance['valve_dn'] ,
            'valve_pipe_dn' : instance['valve_pipe_dn'] ,
            'valve_dn_comment' : instance['valve_dn_comment'] ,
            'valve_pn' : instance['valve_pn'] ,
            'time_to_open_min' : instance['time_to_open_min'] ,
            'time_to_open_max' : instance['time_to_open_max'] ,
            'valve_connection_type_to_pipe' : instance['valve_connection_type_to_pipe'] ,
            'temperature_option' : instance['temperature_option'] ,
            'temperature_option_temp_min' : instance['temperature_option_temp_min'] ,
            'temperature_option_temp_max' : instance['temperature_option_temp_max'] ,
            'actuator_type' : instance['actuator_type'] ,
            'option_ip' : instance['option_ip'] ,
            'option_exd' : instance['option_exd'] ,
            'actuator_voltage' : instance['actuator_voltage'] ,
            'cu_location' : instance['cu_location'] ,
            'armored_cable' : instance['armored_cable'] ,
            'display_type' : instance['display_type'] ,
            'cu_voltage' : instance['cu_voltage'] ,
            'control_and_feedback' : instance['control_and_feedback'] ,
            'digital_protocol' : instance['digital_protocol'] ,
            'working_medium_temp' : instance['working_medium_temp'] ,
            'seismic_conditions' : instance['seismic_conditions'] ,
            'desc_table' : instance['desc_table'] ,
        }


class TextInputSerializer(serializers.Serializer) :
    input_text = serializers.CharField()
