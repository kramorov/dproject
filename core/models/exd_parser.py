# core/models/exd_parser.py
# Парсер строки взрывозащиты: "Ex db IIC T4", "ExdbIICT6" → структурированные данные.
# Используется ExdParseView (core/views.py) для автозаполнения каскадного ExdFilter.
# Обновлён 2026-06-03: regex, upper-case, вырезание уровней (Ga-Gc, Da-Dc) и X/U.

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ExdFilterData:
    """Результат парсинга строки взрывозащиты"""
    method_code: Optional[str] = None
    protection_type_code: Optional[str] = None
    temperature_code: Optional[str] = None
    group_code: Optional[str] = None
    has_x: Optional[bool] = False
    has_u: Optional[bool] = False
    dust_temperature: Optional[int] = None


class ExdStringParser:
    """
    Парсер строки взрывозащиты. Все сравнения case‑insensitive (upper).
    Уровни (Ga, Gb, Gc, Da, Db, Dc) и суффиксы X, U вырезаются до разбора.
    """

    _RE_EX_PREFIX = re.compile(r'^EX\s*')
    _RE_STRIP = re.compile(r'\b(G[ABC]|D[ABC]|[XU])\b')
    _RE_GROUP = re.compile(r'(I{1,3}[A-C])')
    _RE_TEMP = re.compile(r'(T[1-6])')
    _RE_TYPE = re.compile(r'\b([A-Z]{1,2})\b')
    _RE_DUST_TEMP = re.compile(r'(\d{2,3})\s*$')

    COMPOUND_TYPE_CODES = {
        'DB', 'DC', 'EB', 'EC', 'TB', 'TC',
        'IA', 'IB', 'IC', 'MA', 'MB', 'MC',
        'NA', 'NC', 'NR', 'NL',
    }

    @classmethod
    def parse(cls, exd_string: str) -> Optional[ExdFilterData]:
        if not exd_string or not exd_string.strip():
            return None

        s = exd_string.strip().upper()

        # Убираем префикс EX
        s = cls._RE_EX_PREFIX.sub('', s).strip()

        # Запоминаем X/U до вырезания
        has_x = 'X' in s.split()
        has_u = 'U' in s.split()

        # Вырезаем уровни и суффиксы X/U
        s = cls._RE_STRIP.sub(' ', s)
        s = re.sub(r'\s+', ' ', s).strip()

        result = ExdFilterData(has_x=has_x, has_u=has_u)

        # Группа, температура
        m_group = cls._RE_GROUP.search(s)
        m_temp = cls._RE_TEMP.search(s)
        m_dust_temp = cls._RE_DUST_TEMP.search(s) if not m_temp else None

        if m_group:
            result.group_code = m_group.group(1)
            s = s.replace(m_group.group(0), ' ')
        if m_temp:
            result.temperature_code = m_temp.group(1)
            s = s.replace(m_temp.group(0), ' ')
        if m_dust_temp:
            result.dust_temperature = int(m_dust_temp.group(1))
            s = s.replace(m_dust_temp.group(0), ' ')

        # Остаток — метод/тип
        s = s.strip()
        if s:
            m_type = cls._RE_TYPE.search(s)
            if m_type:
                code = m_type.group(1)
                if code in cls.COMPOUND_TYPE_CODES:
                    result.protection_type_code = code.lower()
                    result.method_code = code[0].lower()
                else:
                    result.method_code = code.lower()
                    result.protection_type_code = code.lower()

        if not any([result.method_code, result.group_code,
                     result.temperature_code, result.dust_temperature]):
            return None

        return result

    @classmethod
    def parse_to_filter_config(cls, exd_string: str) -> Dict:
        parsed = cls.parse(exd_string)
        if not parsed:
            return {}

        cfg = {}
        if parsed.protection_type_code:
            cfg['explosion_protection_class__code'] = parsed.protection_type_code
        if parsed.method_code:
            cfg['explosion_protection_class__method__code'] = parsed.method_code
        if parsed.group_code:
            cfg['_group_filter'] = parsed.group_code
        if parsed.temperature_code:
            cfg['_temperature_filter'] = parsed.temperature_code
        if parsed.dust_temperature:
            cfg['dust_temperature__lte'] = parsed.dust_temperature
        cfg['has_x_suffix'] = parsed.has_x or None
        cfg['has_u_suffix'] = parsed.has_u or None
        return cfg
