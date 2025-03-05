import re
from rest_framework import serializers
from django.db.models import Q

from params.serializers import IpOptionSerializer , ExdOptionSerializer , PowerSuppliesSerializer
from .models import EttDocument, MtrType, DnType, PnType, EttActuatorType, EttClimaticOption, EttSeismicOption,\
    EttStatusSignal, EttControlSignal, EttFeedbackSignal, EttControlUnitHeater, EttControlUnitType,\
    EttControlUnitDisplayType, EttCableGlandType, EttElectricOptionsCombination, EttControlOptionsCombination,\
    EttOtherOptionsCombination, EttOpenTime

from django.core.exceptions import ObjectDoesNotExist

class EttDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttDocument
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор

class EttClimaticOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttClimaticOption
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор

class EttControlSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttControlSignal
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttStatusSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttStatusSignal
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttFeedbackSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttFeedbackSignal
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttControlUnitHeaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttControlUnitHeater
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttControlUnitLocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttControlUnitType
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttControlUnitDisplayTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttControlUnitDisplayType
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttCableGlandTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttCableGlandType
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
class EttSeismicOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EttSeismicOption
        fields = '__all__'  # Это включит все поля модели EttDocument в сериализатор
def find_records_by_symbolic_code(model_name , symbolic_code_value) :
    try :
        # Проверка, является ли модель моделью Django
        model = globals().get(model_name)
        if model is None :
            raise ValueError(f"Модель с именем {model_name} не найдена.")

        # Поиск всех записей, у которых symbolic_code совпадает с заданным значением
        records = model.objects.filter(symbolic_code=symbolic_code_value)
        # Поиск первой записи по symbolic_code в указанной модели
        record = model.objects.get(symbolic_code=symbolic_code_value)
        if records.exists() :
            return True, list(records)  # Возвращаем список найденных записей
        else :
            return False, f"Записи {model_name} со значением {symbolic_code_value} не найдены."

    except ValueError as e :
        return False, f"Ошибка: {str(e)}. Модель с именем {model_name} не найдена." # Возвращаем сообщение об ошибке, если модель не найдена


# Пример использования:
# Допустим, мы ищем записи по модели "MtrType" и значению symbolic_code = "ЗКв1000"
# result = find_records_by_symbolic_code('MtrType' , 'ЗКв1000')
# if result:
#     for record in result:
#         print(record)  # Выводим все найденные записи
# else:
#     print("Записи не найдены.")

def split_string_by_first_digit(input_string) :
    # Регулярное выражение для поиска первой цифры и разделения
    match = re.match(r"([^\d]+)(\d.*)" , input_string)
# ([^\d]+) — это группа, которая захватывает все символы до первой цифры. [^\d] означает "любой символ, который не является цифрой", а + указывает на то, что таких символов может быть несколько.
# (\d.*) — это группа, которая захватывает первую цифру и все последующие символы (то есть, начиная с первой цифры и до конца строки). \d означает "цифра", а .* означает "любое количество любых символов".
    if match:
        # Если регулярное выражение находит совпадение, возвращаем список с двумя частями
        return match.group(1), match.group(2)
    else:
        # Если цифр нет, возвращаем список с исходной строкой и пустой строкой
        return input_string, ""


# Пример использования:
# input_string = "ЗКв1000"
# result = split_string_by_first_digit(input_string)
#
# print(result)  # Вывод: ('ЗКв', '1000')

def split_ett_string_to_groups(str):
    pattern = r"([^\*\-,/]+)"
    groups = re.findall(pattern , str)
    return groups


def search_ett_open_time(dn_criteria, mtr_type_criteria, actuator_speed_criteria):
    """
    This function filters the EttOpenTime model based on the given criteria.

    Parameters:
    - dn_criteria: The DN (diameter) value to search for
    - mtr_type_criteria: The type of MtrType to search for
    - actuator_speed_criteria: The actuator speed criteria to search for

    Returns:
    - A queryset of EttOpenTime instances that match the given criteria
    """
    # Ensure that `mtr_type_criteria` is a valid MtrType instance, not an ID
    mtr_type_instance = MtrType.objects.get(id=mtr_type_criteria.id)

    # Filtering based on the given criteria
    results = EttOpenTime.objects.filter(
        actuator_speed=actuator_speed_criteria,
        mtr_type=mtr_type_instance
    ).filter(
        Q(dn_from__lt=dn_criteria) & Q(dn_up_to__gte=dn_criteria)
    )

    return results
# {
#   "input_string": "ЗК500*16-ФП-Х-К0/8-К48/РР/Н/С0"
# }
class EttStringSerializer(serializers.Serializer) :
    # Определяем поля, которые мы будем извлекать из строки
    valve_type = serializers.CharField()
    valve_dn = serializers.IntegerField()
    valve_pn = serializers.IntegerField()
    time_to_open_min = serializers.IntegerField()
    time_to_open_max = serializers.IntegerField()
    temperature_option = serializers.CharField()
    temperature_option_temp_min = serializers.IntegerField()
    temperature_option_temp_max = serializers.IntegerField()
    actuator_type = serializers.CharField()
    seismic_conditions = serializers.CharField()
    option_ip = serializers.CharField()
    option_exd = serializers.CharField()
    actuator_voltage = serializers.CharField()
    cu_location = serializers.CharField()
    cu_heater = serializers.CharField()
    display_type = serializers.CharField()
    cg1_type = serializers.CharField()
    cg23_type = serializers.CharField()
    control_signal = serializers.CharField()
    status_signal = serializers.CharField()
    feedback_signal = serializers.CharField()

    def validate_input_string(self , value) :
        # Метод для валидации исходной строки и разбивки её на части
        parts = split_ett_string_to_groups(value) #Разбили строку на блоки кодов
        if len(parts) != 10 :
            raise serializers.ValidationError("Неверный формат входной строки. Число полей не равно 10.")
        # Проверим первый блок. Он должен состоять из двух частей - Первая часть из букв, вторая из цифр.from
        valve_type, valve_dn = split_string_by_first_digit(parts[0])
        if (len(valve_type)) == 0 or (len(valve_dn) == 0 ) :
            raise serializers.ValidationError(f"Неверный формат входной строки. Первое поле ({parts[0]}) состоит не из двух блоков - первая должна состоять из букв, вторая из цифр.")
        else:
            print(f'validate_input_string отработала нормально. Первое поле {parts[0]}')
            return value

    # Когда вы вызываете serializer.is_valid() или при явном вызове serializer.save(), DRF автоматически вызывает
    # to_internal_value() для преобразования данных запроса в формат, с которым будет работать сериализатор.
    def to_internal_value(self , data) :
        # Предполагаем, что validate_input_string уже отработала, и все норм.
        desc_table = []
        input_string_value = data.get('input_string' , '')
        parts = split_ett_string_to_groups(input_string_value) #Разбили строку на блоки кодов
        # обрабатываем поле 0 - тип арматуры и Дн
        valve_type_str , valve_dn_str = split_string_by_first_digit(parts[0])
        # Допустим, мы ищем записи по модели "MtrType" и значению symbolic_code = "ЗКв1000"
        result, result_value = find_records_by_symbolic_code('MtrType' , valve_type_str)
        if not result :
            print(result_value)
        valve_type = result_value[0]
        result, result_value = find_records_by_symbolic_code('DnType' , valve_dn_str)
        if not result :
            print(result_value)
        valve_dn = result_value[0]
        # valve_type , valve_dn , valve_pipe_dn , valve_dn_comment, time_to_open_min_std, time_to_open_max_std, time_to_open_max_fast = get_valve_type_dn(parts[0])
        # armature_name , dn_value , valve_pipe_dn , valve_dn_comment , time_to_open_min_std , time_to_open_max_std , time_to_open_max_fast = get_valve_type_dn(parts[0])
        print(valve_type)
        desc_table.extend([{'param_name' : 'Тип:' , 'param_value' : valve_type.text_description} ,
                           {'param_name' : 'DN:' , 'param_value' : valve_dn.valve_dn_value} ,])
        # обрабатываем поле 1 - Pn
        result, result_value = find_records_by_symbolic_code('PnType', parts[1])
        if not result :
            print(result_value)
            raise ValueError(f"Записи PnType со значением {parts[1]} не найдены.")
        else :
            valve_pn = result_value[0]
            desc_table.extend([{'param_name': 'Номинальное давление PN, кгс/см²:', 'param_value': valve_pn.valve_pn_value}])
        # обрабатываем поле 2 - Тип присоединения к трубопроводу

        # обрабатываем поле 4 - Климатическое исполнение
        result, result_value = find_records_by_symbolic_code('EttClimaticOption', parts[3])
        if not result :
            print(result_value)
            raise ValueError(f"Записи PnType со значением {parts[3]} не найдены.")
        else:
            temperature_option = result_value[0]

            temperature_option_temp_min = result_value[0].work_temp_min if result_value[0].work_temp_min<result_value[0].extremal_temp_min else result_value[0].extremal_temp_min
            temperature_option_temp_max = result_value[0].work_temp_max if result_value[0].work_temp_max>result_value[0].extremal_temp_max else result_value[0].extremal_temp_max
            desc_str = f"{temperature_option.text_description}  от {temperature_option_temp_min} до {temperature_option_temp_max}"
            desc_table.extend([{'param_name' : 'Климатическое исполнение по ГОСТ 15150 категория размещения 1:' ,
                                'param_value' : desc_str}])
            temperature_option = EttClimaticOptionSerializer(result_value[0] , read_only=True).data
        # обрабатываем поле 5 - Тип привода
        actuator_block_string = parts[7]
        actuator_block_string_len = len(actuator_block_string)
        time_to_open_min = 0
        time_to_open_max = 0
        if actuator_block_string_len > 3 :  # Это не ручной, это электропривод
            other_option_combination_symbol = actuator_block_string[actuator_block_string_len - 1]
            cu_option_combination_symbol = actuator_block_string[actuator_block_string_len - 2]
            electric_option_combination_symbol = actuator_block_string[actuator_block_string_len - 3]
            actuator_type_symbol = actuator_block_string[:actuator_block_string_len - 3]
            actuator_type_desc = result_value[0].text_description
            result , result_value  = find_records_by_symbolic_code('EttActuatorType' , actuator_type_symbol)
            if not result :
                print(result_value)
                raise ValueError(f"Записи EttActuatorType со значением {actuator_type_symbol} не найдены.")
            else :
                results = search_ett_open_time(valve_dn.valve_dn_value , valve_type , result_value[0].actuator_speed)
                if len(results)>0:
                    time_to_open_min = results[0].time_to_open_min
                    time_to_open_max = results[0].time_to_open_max
                    # time_to_open_max = VALVES_DN[dn_value]['time_to_open_max_fast']
                else: # Не нашли значения
                    time_to_open_min = 0
                    time_to_open_max = 0
                    raise ValueError(f"Записи EttOpenTime с Dn={valve_dn.valve_dn_value}, type={actuator_type_symbol}, "
                                     f"speed={result_value[0].actuator_speed} не найдены.")

                desc_table.extend([{'param_name' : 'Тип привода:' ,
                                    'param_value' : actuator_type_desc} ,
                                   {'param_name' : 'Время открытия мин, сек:' , 'param_value' : time_to_open_min} ,
                                   {'param_name' : 'Время открытия макс, сек:' , 'param_value' : time_to_open_max}
                                   ])

                result , result_value  = find_records_by_symbolic_code('EttElectricOptionsCombination' , electric_option_combination_symbol)
                if not result :
                    print(result_value)
                    raise ValueError(f"Записи EttElectricOptionsCombination со значением {electric_option_combination_symbol} не найдены.")
                else :

                    option_exd =    ExdOptionSerializer(result_value[0].exd_choice , read_only=True).data
                    option_ip =     IpOptionSerializer(result_value[0].ip_choice , read_only=True).data
                    actuator_voltage = PowerSuppliesSerializer(result_value[0].power_choice , read_only=True).data
                    desc_table.extend([{'param_name' : 'Исполнение по взрывозащите:' ,
                                        'param_value' : result_value[0].exd_choice.text_description} ,
                                       {'param_name' : 'Исполнение по пылевлагозащите, не ниже:' ,
                                        'param_value' : result_value[0].ip_choice} ,
                                       {'param_name' : 'Напряжение питания, U питания, В:' ,
                                        'param_value' : result_value[0].power_choice} ,
                                       ])

                result , result_value  = find_records_by_symbolic_code('EttControlOptionsCombination' , cu_option_combination_symbol)
                if not result :
                    print(result_value)
                    raise ValueError(
                        f"Записи EttControlOptionsCombination со значением {cu_option_combination_symbol} не найдены.")
                else :

                    status_signal = result_value[0].status_signal_choice.text_description
                    control_signal = result_value[0].control_signal_choice.text_description
                    feedback_signal = result_value[0].feedback_signal_choice.text_description
                    desc_table.extend([{'param_name' : 'Сигнализация состояния Открыто/ЗакрытоАвария/Дистанционный режим:' ,
                                        'param_value' : status_signal} ,
                                       {'param_name' : 'Сигнал управления Открыть/Закрыть/Стоп:' ,
                                        'param_value' : control_signal} ,
                                       {'param_name' : 'Протокол передачи данных:' ,
                                        'param_value' : feedback_signal} ,
                                       ])

                result , result_value   = find_records_by_symbolic_code('EttOtherOptionsCombination' , other_option_combination_symbol)
                if not result :
                    print(result_value)
                    raise ValueError(
                        f"Записи EttOtherOptionsCombination со значением {other_option_combination_symbol} не найдены.")
                else :
                    cu_location = EttControlUnitLocationTypeSerializer(result_value[0].cu_location_choice).data
                    cu_heater = result_value[0].cu_heater_choice.text_description
                    display_type = result_value[0].display_choice.text_description
                    # IpOptionSerializer(result_value[0].ip_choice , read_only=True).data
                    cg1_type = EttCableGlandTypeSerializer(result_value[0].cg1_choice).data
                    cg23_type = EttCableGlandTypeSerializer(result_value[0].cg23_choice).data
                    desc_table.extend([{'param_name' : 'Наличие и расположение блока управления:' ,
                                        'param_value' : result_value[0].cu_location_choice.text_description} ,
                                       {'param_name' : 'НАЛИЧИЕ ВСТРОЕННОГО ЭЛЕКТРООБОГРЕВА БЛОКА УПРАВЛЕНИЯ:' ,
                                        'param_value' : cu_heater} ,
                                       {'param_name' : 'ГРАФИЧЕСКИЙ ДИСПЛЕЙ:' ,
                                        'param_value' : display_type} ,
                                       {'param_name' : 'Кабельный ввод КВ1 для силового кабеля:' ,
                                        'param_value' : result_value[0].cg1_choice.text_description} ,
                                       {'param_name' : 'КАБЕЛЬНЫЙ ВВОД КВ2/КВ3 ДЛЯ КОНТРОЛЬНОГО И ИНТЕРФЕЙСНОГО КАБЕЛЕЙ:' ,
                                        'param_value' : result_value[0].cg23_choice.text_description} ,
                                       ])

        else :  # Это ручной редуктор или маховик, это не электропривод
            actuator_type_symbol = actuator_block_string
            actuator_voltage = "NONE"
            status_signal = "NONE"
            control_signal = "NONE"
            feedback_signal = "NONE"
            option_ip = "NONE"
            option_exd = "NONE"
            cu_location = "NONE"
            cu_heater = "NONE"
            display_type = "NONE"
            cg1_type = "NONE"
            cg23_type = "NONE"
        result , result_value = find_records_by_symbolic_code('EttActuatorType' , actuator_type_symbol)
        if not result :
            print(result_value)
            raise ValueError(f"Записи EttActuatorType со значением {actuator_type_symbol} не найдены.")
        else :
            actuator_type =result_value[0].text_description
            desc_table.extend(
                [{'param_name' : 'Тип привода:' , 'param_value' : actuator_type}])

        # обрабатываем поле 6 - Температура рабочей среды

        # обрабатываем поле 7 - Сейсмичность района размещения
        result , result_value  = find_records_by_symbolic_code('EttSeismicOption' , parts[9])
        if not result :
            print(result_value)
            raise ValueError(f"Записи EttSeismicOption со значением {parts[9]} не найдены.")
        else :
            seismic_conditions = result_value[0]
            desc_table.extend([{'param_name' : 'Сейсмичность района размещения:' , 'param_value' : seismic_conditions.text_description}])
        # Сохраняем данные в формате, соответствующем полям
        return {
            'valve_type' : valve_type.text_description ,
            'valve_dn' : int(valve_dn.valve_dn_value) ,
            'valve_pn' : int(valve_pn.valve_pn_value) ,
            'time_to_open_min' : int(time_to_open_min) ,
            'time_to_open_max' : int(time_to_open_max) ,
            'temperature_option' : temperature_option ,
            'temperature_option_temp_min' : temperature_option_temp_min ,
            'temperature_option_temp_max' : temperature_option_temp_max ,
            'actuator_type' : actuator_type ,
            'seismic_conditions' : seismic_conditions.text_description ,
            'option_ip' : option_ip ,
            'option_exd' : option_exd ,
            'actuator_voltage' : actuator_voltage ,
            'cu_location' : cu_location ,
            'cu_heater' : cu_heater ,
            'display_type' : display_type ,
            'cg1_type': cg1_type ,
            'cg23_type': cg23_type ,
            'control_signal' : control_signal ,
            'status_signal' : status_signal ,
            'feedback_signal' : feedback_signal ,
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
            'valve_pn' : instance['valve_pn'] ,
            'time_to_open_min' : instance['time_to_open_min'] ,
            'time_to_open_max' : instance['time_to_open_max'] ,
            'temperature_option' : instance['temperature_option'] ,
            'temperature_option_temp_min' : instance['temperature_option_temp_min'] ,
            'temperature_option_temp_max' : instance['temperature_option_temp_max'] ,
            'actuator_type' : instance['actuator_type'] ,
            'seismic_conditions' : instance['seismic_conditions'] ,
            'option_ip' : instance['option_ip'] ,
            'option_exd' : instance['option_exd'] ,
            'actuator_voltage' : instance['actuator_voltage'] ,
            'cu_location' : instance['cu_location'] ,
            'cu_heater' : instance['cu_heater'] ,
            'display_type' : instance['display_type'] ,
            'cg1_type' : instance['cg1_type'] ,
            'cg23_type' : instance['cg23_type'] ,
            'control_signal' : instance['control_signal'] ,
            'status_signal' : instance['status_signal'] ,
            'feedback_signal' : instance['feedback_signal'] ,
            'desc_table' : instance['desc_table'] ,
        }

