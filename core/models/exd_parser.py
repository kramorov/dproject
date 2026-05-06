#core/models/exd_parser.py

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from django.db import models


@dataclass
class ExdFilterData:
    """Результат парсинга строки взрывозащиты"""
    method_code: Optional[str] = None  # Код метода: d, e, i, m, p, t
    protection_type_code: Optional[str] = None  # Код типа: ia, ib, ic и т.д.
    level_code: Optional[str] = None  # Уровень: Ga, Gb, Gc, Da, Db, Dc
    temperature_code: Optional[str] = None  # Температурный класс: T1-T6
    group_code: Optional[str] = None  # Группа: IIA, IIB, IIC, IIIA, IIIB, IIIC
    has_x: Optional[bool] = False  # Суффикс X
    has_u: Optional[bool] = False  # Суффикс U

    # Для пыли
    dust_temperature: Optional[int] = None  # Температура для пыли (85, 95, 100)


class ExdStringParser:
    """
    Парсер строки взрывозащиты
    Примеры:
        - "Ex d IIC T6 Gb" -> взрывозащищенный, метод d, группа IIC, класс T6, уровень Gb
        - "Ex e" -> только метод e
        - "Ex ia IIB T4" -> метод ia, группа IIB, класс T4
        - "Ex tD A21" -> метод tD для пыли, уровень A21
    """

    # Регулярные выражения для компонентов
    EX_PREFIX = r'^Ex\s+'

    # Методы взрывозащиты
    METHODS = {
        'd', 'e', 'i', 'm', 'p', 'o', 'q', 'n', 't', 'ma', 'mb', 'mc',
        'ia', 'ib', 'ic', 'nA', 'nC', 'nR', 'nL'
    }

    # Уровни взрывозащиты (газ)
    GAS_LEVELS = {'Ga', 'Gb', 'Gc'}

    # Уровни взрывозащиты (пыль)
    DUST_LEVELS = {'Da', 'Db', 'Dc'}

    # Группы газа
    GAS_GROUPS = {'IIA', 'IIB', 'IIC'}

    # Группы пыли
    DUST_GROUPS = {'IIIA', 'IIIB', 'IIIC'}

    # Температурные классы
    TEMP_CLASSES = {f'T{i}' for i in range(1, 7)}

    @classmethod
    def parse(cls, exd_string: str) -> Optional[ExdFilterData]:
        """
        Парсит строку взрывозащиты и возвращает структурированные данные
        """
        if not exd_string or not exd_string.strip():
            return None

        # Убираем пробелы и приводим к стандартному виду
        exd_string = exd_string.strip()

        # Убираем префикс Ex если есть
        if exd_string.startswith('Ex'):
            exd_string = exd_string[2:].strip()
        elif exd_string.startswith('ex'):
            exd_string = exd_string[2:].strip()

        # Проверяем суффиксы
        has_x = False
        has_u = False

        if exd_string.endswith(' X'):
            has_x = True
            exd_string = exd_string[:-2].strip()
        elif exd_string.endswith('X'):
            has_x = True
            exd_string = exd_string[:-1].strip()

        if exd_string.endswith(' U'):
            has_u = True
            exd_string = exd_string[:-2].strip()
        elif exd_string.endswith('U'):
            has_u = True
            exd_string = exd_string[:-1].strip()

        # Разбиваем на части
        parts = exd_string.split()

        result = ExdFilterData(has_x=has_x, has_u=has_u)

        # Парсим части
        i = 0
        while i < len(parts):
            part = parts[i]

            # Метод или тип взрывозащиты
            if part in cls.METHODS:
                # Проверяем, не является ли это полным типом (ia, ib)
                if part in ['ia', 'ib', 'ic', 'ma', 'mb', 'mc']:
                    result.protection_type_code = part
                else:
                    result.method_code = part
                i += 1
                continue

            # Группа
            if part in cls.GAS_GROUPS or part in cls.DUST_GROUPS:
                result.group_code = part
                i += 1
                continue

            # Температурный класс
            if part in cls.TEMP_CLASSES:
                result.temperature_code = part
                i += 1
                continue

            # Уровень взрывозащиты
            if part in cls.GAS_LEVELS or part in cls.DUST_LEVELS:
                result.level_code = part
                i += 1
                continue

            # Температура для пыли (например, 85, 95, 100)
            if part.isdigit() and i == len(parts) - 1:
                result.dust_temperature = int(part)
                i += 1
                continue

            i += 1

        # Если нашли только метод, но не тип, то тип = метод
        if result.method_code and not result.protection_type_code:
            result.protection_type_code = result.method_code

        return result

    @classmethod
    def parse_to_filter_config(cls, exd_string: str) -> Dict:
        """
        Парсит строку и возвращает словарь для фильтрации ExdOption
        """
        parsed = cls.parse(exd_string)
        if not parsed:
            return {}

        filter_config = {}

        # Фильтр по типу взрывозащиты (Ex d, Ex e и т.д.)
        if parsed.protection_type_code:
            filter_config['explosion_protection_class__code'] = parsed.protection_type_code

        # Фильтр по методу
        if parsed.method_code:
            filter_config['explosion_protection_class__method__code'] = parsed.method_code

        # Фильтр по уровню
        if parsed.level_code:
            filter_config['explosion_protection_level__code'] = parsed.level_code

        # Фильтр по группе (с учетом совместимости)
        if parsed.group_code:
            # Для группы нужно использовать каскадный фильтр (rating >=)
            filter_config['_group_filter'] = parsed.group_code

        # Фильтр по температурному классу (с учетом совместимости)
        if parsed.temperature_code:
            # T6 > T5 > T4 > ...
            filter_config['_temperature_filter'] = parsed.temperature_code

        # Фильтр по температуре для пыли
        if parsed.dust_temperature:
            filter_config['dust_temperature__lte'] = parsed.dust_temperature

        # Суффиксы
        filter_config['has_x_suffix'] = parsed.has_x if parsed.has_x else None
        filter_config['has_u_suffix'] = parsed.has_u if parsed.has_u else None

        return filter_config