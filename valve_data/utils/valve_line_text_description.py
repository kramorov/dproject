# valve_data/utils/valve_line_text_description.py
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from valve_data.models import ValveLineModelData


def get_field_value_with_fallback(valve_line , field_name , show_data_source=False , recursion_level=0 ,
                                  max_recursion=5) :
    """
    Рекурсивно получает значение поля с учетом original_valve_line
    """
    if show_data_source:
        print(f"DEBUG: get_field_value_with_fallback, valve_line:{valve_line.name}, field:{field_name}")
    if recursion_level >= max_recursion :
        if show_data_source :
            return {
                'value' : None ,
                'source' : None ,
                'comment' : f"Достигнут максимальный уровень рекурсии ({max_recursion})"
            }
        return None

    # Получаем значение из текущей модели
    current_value = getattr(valve_line , field_name , None)
    if show_data_source:
        print(f"DEBUG: get_field_value_with_fallback, current_value:{current_value}")
    # Проверяем, является ли значение "пустым" в зависимости от типа
    is_empty = False
    if current_value is None :
        is_empty = True
    elif isinstance(current_value , str) and current_value.strip() == '' :
        is_empty = True
    elif isinstance(current_value , (int , float)) and current_value == 0 :
        # Для числовых полей 0 может быть валидным значением, но в вашем случае 0 считается пустым
        is_empty = True
    elif hasattr(current_value , 'pk') and not current_value.pk :  # Для ForeignKey
        is_empty = True

    # Если значение есть и оно не пустое, возвращаем его
    if not is_empty :
        if show_data_source :
            print(f"DEBUG: get_field_value_with_fallback, значения найдено, current_value:{current_value}")
        if show_data_source :
            return {
                'value' : current_value ,
                'source' : valve_line ,
                'comment' : f"Значение из модели: {valve_line.name}"
            }
        else :
            return current_value

    # Если значения нет, проверяем original_valve_line

    original_line = getattr(valve_line , 'original_valve_line' , None)
    if show_data_source:
        print(f"DEBUG: get_field_value_with_fallback, значения нет, проверяем original_valve_line:{original_line}")
    if original_line :
        fallback_result = get_field_value_with_fallback(
            original_line , field_name , show_data_source , recursion_level + 1 , max_recursion
        )

        if fallback_result :
            if show_data_source :
                print(
                    f"DEBUG: get_field_value_with_fallback, fallback_result не пустой, fallback_result[value]:{fallback_result['value']}")
                if fallback_result['value'] is not None :
                    fallback_result[
                        'comment'] = f"Значение унаследовано из: {original_line.name} (уровень {recursion_level + 1})"
                return fallback_result
            else :
                return fallback_result

    # Если ничего не найдено
    if show_data_source :
        print(f"DEBUG: get_field_value_with_fallback, fallback_result ПУСТОЙ, Так ничего и не нашли")
        return {
            'value' : None ,
            'source' : None ,
            'comment' : "Значение не найдено"
        }
    return None


def get_valve_line_full_data(valve_line , show_data_source=False) :
    """
    Получает полную информацию о ValveLine с учетом original_valve_line
    """
    data = {
        'basic_info' : get_basic_info(valve_line , show_data_source=False) ,
        'technical_specs' : get_technical_specs(valve_line , show_data_source) ,
        'body_colors' : get_body_colors_info(valve_line , show_data_source) ,
        'sealing_materials' : get_sealing_materials_info(valve_line , show_data_source) ,
        'valve_actuations' : get_valve_actuations_info(valve_line , show_data_source) ,
        'descriptions' : get_descriptions_info(valve_line , show_data_source) ,
        'service_life' : get_service_life_info(valve_line , show_data_source) ,
        'status' : get_status_info(valve_line , show_data_source) ,
    }

    if show_data_source :
        data['data_source_info'] = {
            'current_model' : valve_line.name ,
            'has_original' : bool(getattr(valve_line , 'original_valve_line' , None)) ,
            'original_model' : getattr(getattr(valve_line , 'original_valve_line' , None) , 'name' , None)
        }

    return data


def get_basic_info(valve_line , show_data_source=False) :
    """Получает основную информацию с учетом наследования"""

    def get_field(field_name) :
        return get_field_value_with_fallback(valve_line , field_name , show_data_source)

    basic_info = {
        'name' : get_field('name') ,
        'code' : get_field('code') ,
        'producer' : get_field('valve_producer') ,
        'brand' : get_field('valve_brand') ,
        'valve_variety' : get_field('valve_variety') ,
        'function' : get_field('valve_function') ,
    }

    # Если показываем источники данных, сохраняем полную информацию
    if show_data_source :
        # Не извлекаем только значения, а сохраняем всю структуру с комментариями
        basic_info_with_sources = {}
        for key , value in basic_info.items() :
            if value and isinstance(value , dict) :
                basic_info_with_sources[key] = {
                    'value' : value['value'] ,
                    'comment' : value.get('comment' , '') ,
                    'source' : getattr(value.get('source') , 'name' , 'Неизвестно') if value.get(
                        'source') else 'Текущая модель'
                }
            else :
                basic_info_with_sources[key] = {
                    'value' : value ,
                    'comment' : 'Значение из текущей модели' ,
                    'source' : valve_line.name
                }
        return basic_info_with_sources
    else :
        # Если не показываем источники, извлекаем только значения
        for key , value in basic_info.items() :
            if value and isinstance(value , dict) :
                basic_info[key] = value['value']
        return basic_info


def get_technical_specs(valve_line , show_data_source=False) :
    """Получает технические характеристики с учетом наследования"""
    specs = []

    fields_mapping = [
        ('valve_sealing_class' , 'Класс герметичности') ,
        ('body_material' , 'Материал корпуса (тип)') ,
        ('body_material_specified' , 'Материал корпуса (марка)') ,
        ('shut_element_material' , 'Материал запорного элемента (тип)') ,
        ('shut_element_material_specified' , 'Материал запорного элемента (марка)') ,
        ('port_qty' , 'Количество портов') ,
        ('construction_variety' , 'Тип конструкции') ,
        ('pipe_connection' , 'Присоединение к трубе') ,
    ]

    for field_name , label in fields_mapping :
        field_value = get_field_value_with_fallback(valve_line , field_name , show_data_source)

        if show_data_source :
            if field_value and field_value['value'] not in [None , '' , 0] :
                specs.append({
                    'label' : label ,
                    'value' : field_value['value'] ,
                    'source_comment' : field_value.get('comment' , '')
                })
        else :
            if field_value not in [None , '' , 0] :
                specs.append({'label' : label , 'value' : field_value})

    return specs


def get_body_colors_info(valve_line , show_data_source=False) :
    """Получает информацию о цветах корпуса"""
    # Для связанных данных через M2M используем только текущую модель
    body_colors = valve_line.valve_line_body_colors.select_related(
        'body_color' , 'option_variety'
    ).filter(is_available=True).order_by('option_variety__sorting_order' , 'sorting_order')

    colors_data = []
    for color in body_colors :
        color_info = {
            'color_name' : color.body_color.name ,
            'option_type' : color.option_variety.name ,
            'additional_cost' : float(color.additional_cost) ,
            'lead_time_days' : color.lead_time_days ,
            'option_code' : color.option_code_template ,
            'source_comment' : f"Цвет из текущей модели: {valve_line.name}" if show_data_source else None
        }
        colors_data.append(color_info)

    # Если в текущей модели нет цветов, проверяем original_valve_line
    if not colors_data and getattr(valve_line , 'original_valve_line' , None) :
        return get_body_colors_info(valve_line.original_valve_line , show_data_source)

    return colors_data


def get_sealing_materials_info(valve_line , show_data_source=False) :
    """Получает информацию о материалах уплотнения"""
    sealing_materials = valve_line.valve_line_sealing_material.select_related(
        'sealing_element_material' , 'option_variety' , 'allowed_dn_table'
    ).filter(is_available=True).order_by('option_variety__sorting_order' , 'sorting_order')

    result = []
    for sealing in sealing_materials :
        model_data = []
        model_data_table = get_field_value_with_fallback(valve_line , 'valve_model_data_table' , False)

        if model_data_table and sealing.allowed_dn_table :
            model_data_queryset = get_valve_model_data_for_dn_template(
                model_data_table ,
                sealing.allowed_dn_table
            )
            model_data = [
                {
                    'dn' : data.valve_model_dn.name ,
                    'pn' : data.valve_model_pn.name ,
                    'torque_open' : data.valve_model_torque_to_open or 0 ,
                    'torque_close' : data.valve_model_torque_to_close or 0 ,
                    'thrust_close' : data.valve_model_thrust_to_close or 0 ,
                    'rotations' : data.valve_model_rotations_to_open or 0 ,
                }
                for data in model_data_queryset
            ]

        sealing_info = {
            'material_name' : sealing.sealing_element_material.name ,
            'option_type' : sealing.option_variety.name ,
            'temp_min' : sealing.work_temp_min ,
            'temp_max' : sealing.work_temp_max ,
            'additional_cost' : float(sealing.additional_cost) ,
            'lead_time_days' : sealing.lead_time_days ,
            'option_code' : sealing.option_code_template ,
            'model_data' : model_data ,
            'source_comment' : f"Материал уплотнения из текущей модели: {valve_line.name}" if show_data_source else None
        }
        result.append(sealing_info)

    # Если в текущей модели нет материалов уплотнения, проверяем original_valve_line
    if not result and getattr(valve_line , 'original_valve_line' , None) :
        return get_sealing_materials_info(valve_line.original_valve_line , show_data_source)

    return result


def get_valve_actuations_info(valve_line , show_data_source=False) :
    """Получает информацию о механизмах управления"""
    actuations = valve_line.valve_line_valve_actuation.select_related(
        'valve_actuation' , 'option_variety' , 'allowed_dn_table'
    ).filter(is_available=True).order_by('option_variety__sorting_order' , 'sorting_order')

    result = []
    for actuation in actuations :
        model_data = []
        model_data_table = get_field_value_with_fallback(valve_line , 'valve_model_data_table' , False)

        if model_data_table and actuation.allowed_dn_table :
            model_data_queryset = get_valve_model_data_for_dn_template(
                model_data_table ,
                actuation.allowed_dn_table
            )
            model_data = [
                {
                    'dn' : data.valve_model_dn.name ,
                    'pn' : data.valve_model_pn.name ,
                    'torque_open' : data.valve_model_torque_to_open or 0 ,
                    'torque_close' : data.valve_model_torque_to_close or 0 ,
                    'construction_length' : data.valve_model_construction_length or 0 ,
                }
                for data in model_data_queryset
            ]

        actuation_info = {
            'actuation_name' : actuation.valve_actuation.name ,
            'option_type' : actuation.option_variety.name ,
            'additional_cost' : float(actuation.additional_cost) ,
            'lead_time_days' : actuation.lead_time_days ,
            'option_code' : actuation.option_code_template ,
            'model_data' : model_data ,
            'source_comment' : f"Механизм управления из текущей модели: {valve_line.name}" if show_data_source else None
        }
        result.append(actuation_info)

    # Если в текущей модели нет механизмов управления, проверяем original_valve_line
    if not result and getattr(valve_line , 'original_valve_line' , None) :
        return get_valve_actuations_info(valve_line.original_valve_line , show_data_source)

    return result


def get_descriptions_info(valve_line , show_data_source=False) :
    """Получает описания с учетом наследования"""

    def get_field(field_name) :
        return get_field_value_with_fallback(valve_line , field_name , show_data_source)

    descriptions = {
        'description' : get_field('description') ,
        'features' : get_field('features_text') ,
        'application' : get_field('application_text') ,
    }

    # Если показываем источники данных, извлекаем только значения
    if show_data_source :
        for key , value in descriptions.items() :
            if value and isinstance(value , dict) :
                descriptions[key] = value['value']

    return descriptions


def get_service_life_info(valve_line , show_data_source=False) :
    """Получает информацию о сроках службы с учетом наследования"""
    service_info = []

    # Гарантийный срок мин
    warranty_min = get_field_value_with_fallback(valve_line , 'warranty_period_min' , show_data_source)
    warranty_min_variety = get_field_value_with_fallback(valve_line , 'warranty_period_min_variety' , show_data_source)

    if warranty_min and warranty_min not in [None , '' , 0] :
        warranty_min_text = f"{warranty_min['value'] if show_data_source else warranty_min} мес."
        if warranty_min_variety and warranty_min_variety not in [None , '' , 0] :
            variety_text = warranty_min_variety['value'] if show_data_source else warranty_min_variety
            warranty_min_text += f" ({variety_text})"

        service_info.append({
            'label' : 'Гарантийный срок мин' ,
            'value' : warranty_min_text ,
            'source_comment' : warranty_min.get('comment' , '') if show_data_source else None
        })

    # Гарантийный срок макс
    warranty_max = get_field_value_with_fallback(valve_line , 'warranty_period_max' , show_data_source)
    warranty_max_variety = get_field_value_with_fallback(valve_line , 'warranty_period_max_variety' , show_data_source)

    if warranty_max and warranty_max not in [None , '' , 0] :
        warranty_max_text = f"{warranty_max['value'] if show_data_source else warranty_max} мес."
        if warranty_max_variety and warranty_max_variety not in [None , '' , 0] :
            variety_text = warranty_max_variety['value'] if show_data_source else warranty_max_variety
            warranty_max_text += f" ({variety_text})"

        service_info.append({
            'label' : 'Гарантийный срок макс' ,
            'value' : warranty_max_text ,
            'source_comment' : warranty_max.get('comment' , '') if show_data_source else None
        })

    # Срок эксплуатации
    service_years = get_field_value_with_fallback(valve_line , 'valve_in_service_years' , show_data_source)
    service_years_comment = get_field_value_with_fallback(valve_line , 'valve_in_service_years_comment' ,
                                                          show_data_source)

    if service_years and service_years not in [None , '' , 0] :
        years_text = f"{service_years['value'] if show_data_source else service_years} лет"
        if service_years_comment and service_years_comment not in [None , '' , 0] :
            comment_text = service_years_comment['value'] if show_data_source else service_years_comment
            years_text += f" ({comment_text})"

        service_info.append({
            'label' : 'Срок эксплуатации' ,
            'value' : years_text ,
            'source_comment' : service_years.get('comment' , '') if show_data_source else None
        })

    # Количество циклов
    service_cycles = get_field_value_with_fallback(valve_line , 'valve_in_service_cycles' , show_data_source)
    service_cycles_comment = get_field_value_with_fallback(valve_line , 'valve_in_service_cycles_comment' ,
                                                           show_data_source)

    if service_cycles and service_cycles not in [None , '' , 0] :
        cycles_text = f"{service_cycles['value'] if show_data_source else service_cycles} циклов"
        if service_cycles_comment and service_cycles_comment not in [None , '' , 0] :
            comment_text = service_cycles_comment['value'] if show_data_source else service_cycles_comment
            cycles_text += f" ({comment_text})"

        service_info.append({
            'label' : 'Количество циклов' ,
            'value' : cycles_text ,
            'source_comment' : service_cycles.get('comment' , '') if show_data_source else None
        })

    return service_info


def get_status_info(valve_line , show_data_source=False) :
    """Получает информацию о статусах"""
    is_active = get_field_value_with_fallback(valve_line , 'is_active' , show_data_source)
    is_approved = get_field_value_with_fallback(valve_line , 'is_approved' , show_data_source)

    if show_data_source :
        is_active = is_active['value'] if is_active else False
        is_approved = is_approved['value'] if is_approved else False

    return {
        'active' : "Активна" if is_active else "Не активна" ,
        'approved' : "Проверена" if is_approved else "Не проверена" ,
    }


def format_valve_line_text(valve_line , show_data_source=False) :
    """Форматирует информацию о ValveLine в текстовом виде"""
    data = get_valve_line_full_data(valve_line , show_data_source)
    lines = []

    # Основная информация
    if show_data_source :
        lines.append(f"СЕРИЯ АРМАТУРЫ: {data['basic_info']['name']['value']}")
        lines.append(f"Код серии: {data['basic_info']['code']['value']}")
        lines.append(f"Источник имени: {data['basic_info']['name']['comment']}")
        lines.append(f"Источник кода: {data['basic_info']['code']['comment']}")
    else :
        lines.append(f"СЕРИЯ АРМАТУРЫ: {data['basic_info']['name']}")
        lines.append(f"Код серии: {data['basic_info']['code']}")

    if show_data_source and data.get('data_source_info') :
        lines.append(f"Текущая модель: {data['data_source_info']['current_model']}")
        if data['data_source_info']['has_original'] :
            lines.append(f"Наследует из: {data['data_source_info']['original_model']}")

    lines.append("=" * 50)

    # Производитель и тип
    if show_data_source :
        for field in ['producer' , 'brand' , 'valve_variety' , 'function'] :
            if data['basic_info'].get(field) and data['basic_info'][field]['value'] :
                field_data = data['basic_info'][field]
                lines.append(f"{field.capitalize()}: {field_data['value']} [{field_data['comment']}]")
    else :
        for field in ['producer' , 'brand' , 'valve_variety' , 'function'] :
            if data['basic_info'].get(field) :
                lines.append(f"{field.capitalize()}: {data['basic_info'][field]}")

    lines.append("")

    # Технические характеристики
    lines.append("ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:")
    lines.append("-" * 30)

    for spec in data['technical_specs'] :
        line = f"{spec['label']}: {spec['value']}"
        if show_data_source and spec.get('source_comment') :
            line += f" [{spec['source_comment']}]"
        lines.append(line)

    lines.append("")

    # Цвета корпуса
    lines.append("ДОСТУПНЫЕ ЦВЕТА КОРПУСА:")
    lines.append("-" * 25)

    if data['body_colors'] :
        for color in data['body_colors'] :
            color_info = f"  • {color['color_name']} ({color['option_type']})"
            if color['additional_cost'] > 0 :
                color_info += f" +{color['additional_cost']} руб."
            if color['lead_time_days'] > 0 :
                color_info += f" +{color['lead_time_days']} дн."
            if color['option_code'] :
                color_info += f" [код: {color['option_code']}]"
            if show_data_source and color.get('source_comment') :
                color_info += f" [{color['source_comment']}]"
            lines.append(color_info)
    else :
        lines.append("  Не указаны")
    lines.append("")

    # Материалы уплотнения
    lines.append("МАТЕРИАЛЫ УПЛОТНЕНИЯ:")
    lines.append("-" * 25)

    if data['sealing_materials'] :
        for sealing in data['sealing_materials'] :
            lines.append(f"  {sealing['material_name']} ({sealing['option_type']}):")
            lines.append(f"    Температура: {sealing['temp_min']}°C ... {sealing['temp_max']}°C")
            if sealing['additional_cost'] > 0 :
                lines.append(f"    Доп. стоимость: +{sealing['additional_cost']} руб.")
            if sealing['lead_time_days'] > 0 :
                lines.append(f"    Доп. срок: +{sealing['lead_time_days']} дн.")
            if sealing['option_code'] :
                lines.append(f"    Код опции: {sealing['option_code']}")
            if show_data_source and sealing.get('source_comment') :
                lines.append(f"    Источник: {sealing['source_comment']}")

            # Таблица данных
            if sealing['model_data'] :
                lines.append("    Доступные размеры:")
                lines.append("      Dn   |  Pn   | Момент откр | Момент закр | Усилие закр | Обороты")
                lines.append("      " + "-" * 65)
                for model in sealing['model_data'] :
                    lines.append(f"      {model['dn']:4} | {model['pn']:5} | "
                                 f"{model['torque_open']:11} | {model['torque_close']:11} | "
                                 f"{model['thrust_close']:10} | {model['rotations']:8}")
            lines.append("")
    else :
        lines.append("  Не указаны")
    lines.append("")

    # Механизмы управления
    lines.append("ТИПЫ МЕХАНИЗМОВ УПРАВЛЕНИЯ:")
    lines.append("-" * 30)

    if data['valve_actuations'] :
        for actuation in data['valve_actuations'] :
            lines.append(f"  {actuation['actuation_name']} ({actuation['option_type']}):")
            if actuation['additional_cost'] > 0 :
                lines.append(f"    Доп. стоимость: +{actuation['additional_cost']} руб.")
            if actuation['lead_time_days'] > 0 :
                lines.append(f"    Доп. срок: +{actuation['lead_time_days']} дн.")
            if actuation['option_code'] :
                lines.append(f"    Код опции: {actuation['option_code']}")
            if show_data_source and actuation.get('source_comment') :
                lines.append(f"    Источник: {actuation['source_comment']}")

            # Таблица данных
            if actuation['model_data'] :
                lines.append("    Доступные размеры:")
                lines.append("      Dn   |  Pn   | Момент откр | Момент закр | Строит.длина")
                lines.append("      " + "-" * 55)
                for model in actuation['model_data'] :
                    lines.append(f"      {model['dn']:4} | {model['pn']:5} | "
                                 f"{model['torque_open']:11} | {model['torque_close']:11} | "
                                 f"{model['construction_length']:12}")
            lines.append("")
    else :
        lines.append("  Не указаны")
    lines.append("")

    # Описания
    for desc_type in ['description' , 'features' , 'application'] :
        if data['descriptions'].get(desc_type) :
            label = desc_type.capitalize().replace('_' , ' ')
            lines.append(f"{label.upper()}:")
            lines.append("-" * 15)
            lines.append(data['descriptions'][desc_type])
            lines.append("")

    # Сроки службы
    lines.append("СРОКИ СЛУЖБЫ:")
    lines.append("-" * 15)

    for service in data['service_life'] :
        line = f"{service['label']}: {service['value']}"
        if show_data_source and service.get('source_comment') :
            line += f" [{service['source_comment']}]"
        lines.append(line)

    lines.append("")

    # Статусы
    lines.append(f"СТАТУС: {data['status']['active']}, {data['status']['approved']}")

    return "\n".join(lines)


def format_valve_line_html(valve_line , show_data_source=False) :
    """
    Форматирует информацию о ValveLine в HTML виде для админки
    """
    data = get_valve_line_full_data(valve_line , show_data_source)
    html_parts = []

    # Основная информация с указанием источников данных
    if show_data_source :
        # Для show_data_source=True данные должны быть структурированными
        name_value = data['basic_info']['name']['value'] if isinstance(data['basic_info']['name'] , dict) else \
        data['basic_info']['name']
        code_value = data['basic_info']['code']['value'] if isinstance(data['basic_info']['code'] , dict) else \
        data['basic_info']['code']

        html_parts.append(f"<h3>СЕРИЯ АРМАТУРЫ: {name_value}</h3>")
        html_parts.append(f"<p><strong>Код серии:</strong> {code_value}</p>")

        # Добавляем комментарии только если они есть и show_data_source=True
        if isinstance(data['basic_info']['name'] , dict) and data['basic_info']['name'].get('comment') :
            html_parts.append(f"<p><em>Источник имени:</em> {data['basic_info']['name']['comment']}</p>")
        if isinstance(data['basic_info']['code'] , dict) and data['basic_info']['code'].get('comment') :
            html_parts.append(f"<p><em>Источник кода:</em> {data['basic_info']['code']['comment']}</p>")
    else :
        # Для show_data_source=False данные могут быть обычными значениями
        name_value = str(data['basic_info']['name']) if data['basic_info']['name'] else 'Не указано'
        code_value = str(data['basic_info']['code']) if data['basic_info']['code'] else 'Не указан'

        html_parts.append(f"<h3>СЕРИЯ АРМАТУРЫ: {name_value}</h3>")
        html_parts.append(f"<p><strong>Код серии:</strong> {code_value}</p>")

    if show_data_source and data.get('data_source_info') :
        html_parts.append(f"<p><strong>Текущая модель:</strong> {data['data_source_info']['current_model']}</p>")
        if data['data_source_info']['has_original'] :
            html_parts.append(f"<p><strong>Наследует из:</strong> {data['data_source_info']['original_model']}</p>")

    html_parts.append("<hr>")

    # Производитель и тип с источниками
    info_html = []
    if show_data_source :
        for field in ['producer' , 'brand' , 'valve_variety' , 'function'] :
            field_data = data['basic_info'].get(field)
            if field_data :
                # Для show_data_source=True данные могут быть структурированными
                if isinstance(field_data , dict) :
                    field_value = field_data.get('value')
                    field_comment = field_data.get('comment' , '')
                else :
                    field_value = field_data
                    field_comment = 'Значение из текущей модели'

                if field_value :
                    label = field.capitalize().replace('_' , ' ')
                    info_html.append(
                        f"<strong>{label}:</strong> {field_value} <em style='color: #666;'>({field_comment})</em>")
    else :
        for field in ['producer' , 'brand' , 'valve_variety' , 'function'] :
            field_value = data['basic_info'].get(field)
            if field_value :
                # Преобразуем объекты моделей в строки
                field_value_str = str(field_value)
                label = field.capitalize().replace('_' , ' ')
                info_html.append(f"<strong>{label}:</strong> {field_value_str}")

    if info_html :
        html_parts.append("<p>" + " | ".join(info_html) + "</p>")

    # Технические характеристики
    html_parts.append("<h4>⚙️ Технические характеристики</h4>")
    if data['technical_specs'] :
        html_parts.append("<ul>")
        for spec in data['technical_specs'] :
            # Преобразуем значение в строку, если это объект модели
            spec_value = str(spec['value']) if hasattr(spec['value'] , '__str__') else spec['value']
            spec_html = f"<li><strong>{spec['label']}:</strong> {spec_value}"
            if show_data_source and spec.get('source_comment') :
                spec_html += f" <em style='color: #666; font-size: 0.9em;'>({spec['source_comment']})</em>"
            spec_html += "</li>"
            html_parts.append(spec_html)
        html_parts.append("</ul>")
    else :
        html_parts.append("<p>Технические характеристики не указаны</p>")

    # Цвета корпуса
    html_parts.append("<h4>🎨 Цвета корпуса</h4>")
    if data['body_colors'] :
        for color in data['body_colors'] :
            color_html = f"<div style='margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;'>"
            color_html += f"<strong>{color['color_name']} ({color['option_type']})</strong>"

            extras = []
            if color.get('additional_cost' , 0) > 0 :
                extras.append(f"+{color['additional_cost']} руб.")
            if color.get('lead_time_days' , 0) > 0 :
                extras.append(f"+{color['lead_time_days']} дн.")
            if color.get('option_code') :
                extras.append(f"код: {color['option_code']}")

            if extras :
                color_html += f"<br><span style='color: #666; font-size: 0.9em;'>{', '.join(extras)}</span>"

            if show_data_source and color.get('source_comment') :
                color_html += f"<br><em style='color: #888; font-size: 0.8em;'>{color['source_comment']}</em>"

            color_html += "</div>"
            html_parts.append(color_html)
    else :
        html_parts.append("<p>Цвета корпуса не указаны</p>")

    # Материалы уплотнения
    html_parts.append("<h4>🔧 Материалы уплотнения</h4>")
    if data['sealing_materials'] :
        for sealing in data['sealing_materials'] :
            sealing_html = f"<div style='margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px;'>"
            sealing_html += f"<h5 style='margin-top: 0;'>{sealing['material_name']} ({sealing['option_type']})</h5>"
            sealing_html += f"<p style='margin-bottom: 10px;'>Температурный диапазон: {sealing.get('temp_min' , '')}°C ... {sealing.get('temp_max' , '')}°C</p>"

            extras = []
            if sealing.get('additional_cost' , 0) > 0 :
                extras.append(f"Доп. стоимость: +{sealing['additional_cost']} руб.")
            if sealing.get('lead_time_days' , 0) > 0 :
                extras.append(f"Доп. срок: +{sealing['lead_time_days']} дн.")
            if sealing.get('option_code') :
                extras.append(f"Код опции: {sealing['option_code']}")

            if extras :
                sealing_html += f"<p style='margin-bottom: 10px;'>{', '.join(extras)}</p>"

            if show_data_source and sealing.get('source_comment') :
                sealing_html += f"<p style='color: #888; font-size: 0.9em; margin-bottom: 10px;'>{sealing['source_comment']}</p>"

            # Таблица данных
            if sealing.get('model_data') :
                sealing_html += "<div style='overflow-x: auto;'>"
                sealing_html += "<table style='width: 100%; border-collapse: collapse; font-size: 0.9em;'>"
                sealing_html += "<thead><tr style='background: #417690; color: white;'>"
                sealing_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Dn</th>"
                sealing_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Pn</th>"
                sealing_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Момент откр</th>"
                sealing_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Момент закр</th>"
                sealing_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Усилие закр</th>"
                sealing_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Обороты</th>"
                sealing_html += "</tr></thead><tbody>"

                for model in sealing['model_data'] :
                    sealing_html += "<tr style='background: white;'>"
                    sealing_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('dn' , '')}</td>"
                    sealing_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('pn' , '')}</td>"
                    sealing_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('torque_open' , 0)}</td>"
                    sealing_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('torque_close' , 0)}</td>"
                    sealing_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('thrust_close' , 0)}</td>"
                    sealing_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('rotations' , 0)}</td>"
                    sealing_html += "</tr>"

                sealing_html += "</tbody></table></div>"

            sealing_html += "</div>"
            html_parts.append(sealing_html)
    else :
        html_parts.append("<p>Материалы уплотнения не указаны</p>")

    # Механизмы управления
    html_parts.append("<h4>🎛️ Механизмы управления</h4>")
    if data['valve_actuations'] :
        for actuation in data['valve_actuations'] :
            actuation_html = f"<div style='margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px;'>"
            actuation_html += f"<h5 style='margin-top: 0;'>{actuation['actuation_name']} ({actuation['option_type']})</h5>"

            extras = []
            if actuation.get('additional_cost' , 0) > 0 :
                extras.append(f"Доп. стоимость: +{actuation['additional_cost']} руб.")
            if actuation.get('lead_time_days' , 0) > 0 :
                extras.append(f"Доп. срок: +{actuation['lead_time_days']} дн.")
            if actuation.get('option_code') :
                extras.append(f"Код опции: {actuation['option_code']}")

            if extras :
                actuation_html += f"<p style='margin-bottom: 10px;'>{', '.join(extras)}</p>"

            if show_data_source and actuation.get('source_comment') :
                actuation_html += f"<p style='color: #888; font-size: 0.9em; margin-bottom: 10px;'>{actuation['source_comment']}</p>"

            # Таблица данных
            if actuation.get('model_data') :
                actuation_html += "<div style='overflow-x: auto;'>"
                actuation_html += "<table style='width: 100%; border-collapse: collapse; font-size: 0.9em;'>"
                actuation_html += "<thead><tr style='background: #417690; color: white;'>"
                actuation_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Dn</th>"
                actuation_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Pn</th>"
                actuation_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Момент откр</th>"
                actuation_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Момент закр</th>"
                actuation_html += "<th style='padding: 8px; border: 1px solid #36657a;'>Строит.длина</th>"
                actuation_html += "</tr></thead><tbody>"

                for model in actuation['model_data'] :
                    actuation_html += "<tr style='background: white;'>"
                    actuation_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('dn' , '')}</td>"
                    actuation_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('pn' , '')}</td>"
                    actuation_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('torque_open' , 0)}</td>"
                    actuation_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('torque_close' , 0)}</td>"
                    actuation_html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{model.get('construction_length' , 0)}</td>"
                    actuation_html += "</tr>"

                actuation_html += "</tbody></table></div>"

            actuation_html += "</div>"
            html_parts.append(actuation_html)
    else :
        html_parts.append("<p>Механизмы управления не указаны</p>")

    # Описания
    html_parts.append("<h4>📝 Описания</h4>")
    has_descriptions = False

    description_text = data['descriptions'].get('description')
    if description_text :
        if isinstance(description_text , dict) :
            description_text = description_text.get('value' , '')
        if description_text :
            html_parts.append("<h5>Описание</h5>")
            html_parts.append(
                f"<div style='background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap;'>{description_text}</div>")
            has_descriptions = True

    features_text = data['descriptions'].get('features')
    if features_text :
        if isinstance(features_text , dict) :
            features_text = features_text.get('value' , '')
        if features_text :
            html_parts.append("<h5>Особенности</h5>")
            html_parts.append(
                f"<div style='background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap;'>{features_text}</div>")
            has_descriptions = True

    application_text = data['descriptions'].get('application')
    if application_text :
        if isinstance(application_text , dict) :
            application_text = application_text.get('value' , '')
        if application_text :
            html_parts.append("<h5>Применение</h5>")
            html_parts.append(
                f"<div style='background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap;'>{application_text}</div>")
            has_descriptions = True

    if not has_descriptions :
        html_parts.append("<p>Описания не указаны</p>")

    # Сроки службы
    html_parts.append("<h4>⏱️ Сроки службы</h4>")
    if data['service_life'] :
        html_parts.append(
            "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;'>")
        for service in data['service_life'] :
            service_html = f"<div style='background: white; padding: 12px; border: 1px solid #e0e0e0; border-radius: 5px;'>"
            service_html += f"<strong>{service['label']}</strong><br>"
            service_html += f"{service['value']}"
            if show_data_source and service.get('source_comment') :
                service_html += f"<br><em style='color: #666; font-size: 0.9em;'>{service['source_comment']}</em>"
            service_html += "</div>"
            html_parts.append(service_html)
        html_parts.append("</div>")
    else :
        html_parts.append("<p>Сроки службы не указаны</p>")

    # Статусы
    html_parts.append("<h4>📊 Статусы</h4>")
    html_parts.append(
        "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;'>")

    active_status = "Активна" if valve_line.is_active else "Не активна"
    approved_status = "Проверена" if valve_line.is_approved else "Не проверена"

    active_class = "background: #d4edda; color: #155724;" if valve_line.is_active else "background: #f8d7da; color: #721c24;"
    approved_class = "background: #d4edda; color: #155724;" if valve_line.is_approved else "background: #f8d7da; color: #721c24;"

    html_parts.append(f"<div style='padding: 12px; border-radius: 5px; {active_class}'>")
    html_parts.append(f"<strong>Активность:</strong><br>{active_status}")
    html_parts.append("</div>")

    html_parts.append(f"<div style='padding: 12px; border-radius: 5px; {approved_class}'>")
    html_parts.append(f"<strong>Проверка:</strong><br>{approved_status}")
    html_parts.append("</div>")

    html_parts.append("</div>")

    return format_html("".join(html_parts))


def get_valve_model_data_for_dn_template(valve_model_data_table , allowed_dn_template) :
    """Получает данные моделей арматуры для заданного шаблона допустимых Dn"""
    if not valve_model_data_table or not allowed_dn_template :
        return ValveLineModelData.objects.none()

    allowed_dn_ids = allowed_dn_template.dn.values_list('id' , flat=True)

    return ValveLineModelData.objects.filter(
        valve_model_data_table=valve_model_data_table ,
        valve_model_dn__id__in=allowed_dn_ids
    ).select_related('valve_model_dn' , 'valve_model_pn').order_by(
        'valve_model_dn__sorting_order' , 'valve_model_pn__sorting_order'
    )


def export_valve_lines_to_text(queryset , show_data_source=False) :
    """Экспортирует набор ValveLine в текстовом виде"""
    content = []
    for obj in queryset :
        content.append(format_valve_line_text(obj , show_data_source))
        content.append("\n" + "=" * 80 + "\n")

    return "\n".join(content)