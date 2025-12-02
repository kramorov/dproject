# core/utils/ts_utils.py
"""
Дополнительные утилиты для работы с TypeScript.
"""

import re
from typing import Dict , List


def typescript_to_django(value: str , field_type: str) -> any :
    """
    Конвертирует TypeScript значение в Python/Django значение.

    Args:
        value: Значение из TypeScript
        field_type: Тип поля Django

    Returns:
        Конвертированное значение
    """
    if value is None or value == 'null' or value == 'undefined' :
        return None

    if field_type in ['CharField' , 'TextField' , 'EmailField' , 'URLField'] :
        return str(value) if value else ''

    elif field_type in ['IntegerField' , 'FloatField' , 'DecimalField'] :
        try :
            return float(value) if '.' in str(value) else int(value)
        except (ValueError , TypeError) :
            return None

    elif field_type == 'BooleanField' :
        if isinstance(value , bool) :
            return value
        return str(value).lower() in ['true' , '1' , 'yes' , 'y']

    elif field_type in ['DateField' , 'DateTimeField'] :
        # Пытаемся распарсить дату из строки
        from datetime import datetime
        try :
            return datetime.fromisoformat(value.replace('Z' , '+00:00'))
        except (ValueError , TypeError) :
            return None

    return value


def validate_ts_interface(interface_str: str , model_class) -> List[str] :
    """
    Валидирует TypeScript интерфейс на соответствие Django модели.

    Args:
        interface_str: TypeScript код интерфейса
        model_class: Класс Django модели

    Returns:
        Список ошибок/предупреждений
    """
    errors = []

    # Извлекаем поля из TypeScript интерфейса
    ts_fields = _extract_ts_fields(interface_str)

    # Проверяем соответствие полям модели
    for field in model_class._meta.fields :
        if field.name not in ts_fields :
            errors.append(f"Поле {field.name} отсутствует в TypeScript интерфейсе")

    for ts_field in ts_fields :
        if not hasattr(model_class , ts_field) and ts_field not in ['id' , 'compact_data' , 'display_data' ,
                                                                    'full_data'] :
            errors.append(f"Поле {ts_field} есть в TypeScript, но отсутствует в модели")

    return errors


def _extract_ts_fields(interface_str: str) -> List[str] :
    """Извлекает имена полей из TypeScript интерфейса"""
    # Удаляем комментарии
    lines = interface_str.split('\n')
    clean_lines = []

    for line in lines :
        line = re.sub(r'//.*$' , '' , line)  # Удаляем однострочные комментарии
        line = re.sub(r'/\*.*?\*/' , '' , line , flags=re.DOTALL)  # Удаляем многострочные
        clean_lines.append(line.strip())

    # Ищем строки с полями
    fields = []
    for line in clean_lines :
        match = re.match(r'(\w+)\??:' , line)
        if match :
            fields.append(match.group(1))

    return fields