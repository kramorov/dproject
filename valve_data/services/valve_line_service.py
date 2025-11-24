import pandas as pd
from django.template.loader import render_to_string
# from weasyprint import HTML
import tempfile
import os


class ValveLineDataService:
    """Сервис для сложных операций с данными ValveLine"""

    def __init__(self, valve_line):
        self.valve_line = valve_line

    def export_to_excel(self, file_path=None):
        """Экспорт всех данных в Excel"""
        if file_path is None:
            file_path = f"valve_line_{self.valve_line.code}_{self.valve_line.id}.xlsx"

        data = self.valve_line.get_full_data()

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:

            # Основная информация
            if data['basic_info']:
                basic_df = pd.DataFrame(data['basic_info'])
                basic_df.to_excel(writer, sheet_name='Основная информация', index=False)

            # Технические характеристики
            if data['technical_specs']:
                tech_df = pd.DataFrame(data['technical_specs'])
                tech_df.to_excel(writer, sheet_name='Технические характеристики', index=False)

            # Температурные характеристики
            if data['temperature_info']:
                temp_df = pd.DataFrame(data['temperature_info'])
                temp_df.to_excel(writer, sheet_name='Температурные характеристики', index=False)

            # Модельные данные
            if data['model_data']['has_data']:
                model_df = pd.DataFrame(data['model_data']['model_data'])
                model_df.to_excel(writer, sheet_name='Модельные данные', index=False)

            # Kv данные
            if data['kv_data']['has_data']:
                kv_df = pd.DataFrame(data['kv_data']['kv_data'])
                kv_df.to_excel(writer, sheet_name='Kv данные', index=False)

            # Цвета корпуса
            if data['body_colors']:
                colors_df = pd.DataFrame(data['body_colors'])
                colors_df.to_excel(writer, sheet_name='Цвета корпуса', index=False)

        return file_path

    def validate_technical_data(self):
        """Валидация технических данных"""
        errors = []
        warnings = []

        # Проверка обязательных данных
        if not self.valve_line.effective_valve_model_data_table:
            errors.append("Не указана таблица модельных данных")

        if not self.valve_line.effective_allowed_dn_table:
            errors.append("Не указана таблица допустимых DN")

        # Проверка температурных диапазонов
        if (self.valve_line.effective_work_temp_min and
                self.valve_line.effective_work_temp_max and
                self.valve_line.effective_work_temp_min > self.valve_line.effective_work_temp_max):
            errors.append("Минимальная рабочая температура не может быть больше максимальной")

        # Проверка гарантийных сроков
        if (self.valve_line.effective_warranty_period_min and
                self.valve_line.effective_warranty_period_max and
                self.valve_line.effective_warranty_period_min > self.valve_line.effective_warranty_period_max):
            errors.append("Минимальный гарантийный срок не может быть больше максимального")

        # Предупреждения
        if not self.valve_line.effective_valve_model_kv_data_table:
            warnings.append("Не указана таблица Kv данных")

        if not self.valve_line.effective_body_colors_info():
            warnings.append("Не указаны цвета корпуса")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def compare_with_other_series(self, other_series):
        """Сравнение с другой серией"""
        current_data = self.valve_line.get_full_data()
        other_data = other_series.get_full_data()

        comparison = {
            'differences': [],
            'common_features': [],
            'unique_current': [],
            'unique_other': []
        }

        # Сравнение основных характеристик
        current_basic = {item['key']: item['value'] for item in current_data['basic_info']}
        other_basic = {item['key']: item['value'] for item in other_data['basic_info']}

        for key in set(current_basic.keys()) | set(other_basic.keys()):
            if key in current_basic and key in other_basic:
                if current_basic[key] != other_basic[key]:
                    comparison['differences'].append({
                        'feature': key,
                        'current': current_basic[key],
                        'other': other_basic[key]
                    })
                else:
                    comparison['common_features'].append({
                        'feature': key,
                        'value': current_basic[key]
                    })
            elif key in current_basic:
                comparison['unique_current'].append({
                    'feature': key,
                    'value': current_basic[key]
                })
            else:
                comparison['unique_other'].append({
                    'feature': key,
                    'value': other_basic[key]
                })

        return comparison

    def get_technical_specifications_summary(self):
        """Получение сводки технических характеристик для использования в коммерческих предложениях"""
        data = self.valve_line.get_full_data()

        summary = {
            'series_name': self.valve_line.effective_name,
            'brand': str(
                self.valve_line.effective_valve_brand) if self.valve_line.effective_valve_brand else 'Не указан',
            'producer': str(
                self.valve_line.effective_valve_producer) if self.valve_line.effective_valve_producer else 'Не указан',
            'valve_type': str(
                self.valve_line.effective_valve_variety) if self.valve_line.effective_valve_variety else 'Не указан',
            'temperature_range': f"{self.valve_line.effective_work_temp_min or 'N/A'}°C - {self.valve_line.effective_work_temp_max or 'N/A'}°C",
            'available_dn': ', '.join([f"DN{dn}" for dn in data['kv_summary']['dn_range']]) if data['kv_summary'][
                'has_data'] else 'Не указаны',
            'available_pn': ', '.join([f"PN{pn}" for pn in data['kv_summary']['pn_range']]) if data['kv_summary'][
                'has_data'] else 'Не указаны',
            'body_material': str(
                self.valve_line.effective_body_material_specified or self.valve_line.effective_body_material or 'Не указан'),
            'sealing_class': str(
                self.valve_line.effective_valve_sealing_class) if self.valve_line.effective_valve_sealing_class else 'Не указан',
            'connection_type': str(
                self.valve_line.effective_pipe_connection) if self.valve_line.effective_pipe_connection else 'Не указан',
        }

        return summary