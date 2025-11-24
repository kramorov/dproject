import re
from django.utils.html import format_html


class ValveLineUtilsMixin:
    """Миксин для утилитарных методов"""

    def parse_item_code_template(self, template_string, dn=None, pn=None):
        """Парсит шаблон формирования артикула с переменными в формате {%VARIABLE}"""
        if not template_string:
            return ""

        variables = {
            'BRAND': self.effective_valve_brand or "",
            'VALVELINE': self.effective_name or "",
            'CODE': self.effective_code or "",
            'DN': dn or "",
            'PN': pn or "",
            'PRODUCER': self.effective_valve_producer or "",
            'VARIETY': self.effective_valve_variety or "",
        }

        def replace_variable(match):
            variable_name = match.group(1)
            return variables.get(variable_name, "")

        try:
            result = re.sub(r'{%(\w+)}', replace_variable, template_string)
            return result.strip()
        except Exception as e:
            print(f"Error parsing item_code template: {e}")
            return ""

    def format_text_info(self, show_data_source=False):
        """Форматирует информацию о ValveLine в текстовом виде"""
        data = self.get_full_data(show_data_source)
        lines = []

        lines.append(f"СЕРИЯ АРМАТУРЫ: {self.effective_name or 'Не указано'}")
        lines.append(f"Код серии: {self.effective_code or 'Не указан'}")

        if show_data_source and data.get('data_source_info'):
            lines.append(f"Текущая модель: {data['data_source_info']['current_model']}")
            if data['data_source_info']['has_original']:
                lines.append(f"Наследует из: {data['data_source_info']['original_model']}")

        lines.append("=" * 50)

        # Основная информация
        if data['basic_info']:
            lines.append("ОСНОВНАЯ ИНФОРМАЦИЯ:")
            lines.append("-" * 20)
            for item in data['basic_info']:
                lines.append(f"{item['label']}: {item['value']}")
            lines.append("")

        # Технические характеристики
        if data['technical_specs']:
            lines.append("ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:")
            lines.append("-" * 30)
            for spec in data['technical_specs']:
                lines.append(f"{spec['label']}: {spec['value']}")
            lines.append("")

        # Температурные характеристики
        if data['temperature_info']:
            lines.append("ТЕМПЕРАТУРНЫЕ ХАРАКТЕРИСТИКИ:")
            lines.append("-" * 30)
            for temp in data['temperature_info']:
                lines.append(f"{temp['label']}: {temp['value']}°C")
            lines.append("")

        # Цвета корпуса
        if data['body_colors']:
            lines.append("ДОСТУПНЫЕ ЦВЕТА КОРПУСА:")
            lines.append("-" * 25)
            for color in data['body_colors']:
                color_info = f"  • {color['color_name']} ({color['option_type']})"
                if color['additional_cost'] > 0:
                    color_info += f" +{color['additional_cost']} руб."
                if color['lead_time_days'] > 0:
                    color_info += f" +{color['lead_time_days']} дн."
                if color['option_code']:
                    color_info += f" [код: {color['option_code']}]"
                lines.append(color_info)
            lines.append("")

        # Таблица модельных данных
        if data['model_data']['has_data']:
            lines.append("ТАБЛИЦА МОДЕЛЬНЫХ ДАННЫХ (DN/PN):")
            lines.append("-" * 35)

            lines.append(
                "  DN   |  PN   | Момент откр | Момент закр | Усилие закр | Обороты | Площадка | Шток | Высота штока | Строит.длина")
            lines.append("  " + "-" * 110)

            for model in data['model_data']['model_data']:
                line = f"  {model['dn']:4} | {model['pn']:5} | " \
                       f"{model['torque_open']:11} | {model['torque_close']:11} | " \
                       f"{model['thrust_close']:10} | {model['rotations']:8} | " \
                       f"{model['mounting_plate']:9} | {model['stem_size']:5} | " \
                       f"{model['stem_height']:11} | {model['construction_length']:12}"
                lines.append(line)
            lines.append("")

        # Таблица Kv данных
        if data['kv_data']['has_data']:
            lines.append("ТАБЛИЦА ДАННЫХ KV:")
            lines.append("-" * 20)

            lines.append("  DN   |  PN   | Угол откр. | Kv, м³/час")
            lines.append("  " + "-" * 40)

            for kv_entry in data['kv_data']['kv_data']:
                line = f"  {kv_entry['dn']:4} | {kv_entry['pn']:5} | " \
                       f"{kv_entry['opening_angle']:10}° | {kv_entry['kv_value']:10.2f}"
                lines.append(line)
            lines.append("")

        # Сводка по Kv данным
        if data['kv_summary']['has_data']:
            lines.append("СВОДКА ПО KV ДАННЫМ:")
            lines.append("-" * 20)
            lines.append(f"Всего записей: {data['kv_summary']['total_entries']}")
            lines.append(f"Диапазон DN: {', '.join(data['kv_summary']['dn_range'])}")
            lines.append(f"Диапазон PN: {', '.join(data['kv_summary']['pn_range'])}")
            lines.append(f"Углы открытия: {', '.join(map(str, data['kv_summary']['angle_range']))}°")
            lines.append("")

        # Описания
        if data['descriptions']:
            lines.append("ОПИСАНИЯ:")
            lines.append("-" * 15)
            for desc in data['descriptions']:
                if desc['value']:
                    lines.append(f"{desc['label'].upper()}:")
                    lines.append("-" * len(desc['label']) + "-")
                    lines.append(desc['value'])
                    lines.append("")

        # Сроки службы
        if data['service_life']:
            lines.append("СРОКИ СЛУЖБЫ:")
            lines.append("-" * 15)
            for service in data['service_life']:
                lines.append(f"{service['label']}: {service['value']}")
            lines.append("")

        # Статусы
        lines.append(f"СТАТУС: {data['status']['active']}, {data['status']['approved']}")

        return "\n".join(lines)

    def format_html_info(self, show_data_source=False):
        """Форматирует информацию о ValveLine в HTML виде для админки"""
        text_content = self.format_text_info(show_data_source)
        return format_html(f"<pre>{text_content}</pre>")

    def get_available_dn_pn_combinations(self):
        """Возвращает все доступные комбинации DN/PN"""
        model_data_table = self.effective_valve_model_data_table
        if not model_data_table:
            return []

        from ..valve_line_model_data import ValveLineModelData
        combinations = ValveLineModelData.objects.filter(
            valve_model_data_table=model_data_table
        ).values_list('valve_model_dn__name', 'valve_model_pn__name').distinct()

        return [f"{dn}/{pn}" for dn, pn in combinations]