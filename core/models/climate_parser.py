# core/models/climate_parser.py
"""
Парсер строки климатического исполнения: «УХЛ4», «У2», «ТВ3» → zone_code + placement_code.

Используется ClimateParseView (core/views.py) для автозаполнения каскадного ClimateFilter.

Формат: [зона ГОСТ] + [цифра размещения]
Зона: У, ХЛ, УХЛ, Т, ТВ, ТС, УТ, М, ТМ, ОМ, О, В
Размещение: 1, 2, 3, 4, 5
"""
import re
from typing import Optional, Dict
from dataclasses import dataclass


# Маппинг русского обозначения → код в БД (ClimaticZoneCategory.code)
# Сортировка по убыванию длины для жадного матчинга
_ZONE_NAME_TO_CODE = [
    ('УХЛ', 'uhl'), ('ТВ', 'tv'), ('ТС', 'ts'), ('ТМ', 'tm'),
    ('ОМ', 'om'), ('УТ', 'ut'),
    ('У', 'u'), ('ХЛ', 'hl'), ('Т', 't'),
    ('М', 'm'), ('О', 'o'), ('В', 'v'),
]

_PLACEMENT_RE = re.compile(r'([1-5])\s*$')


@dataclass
class ClimateFilterData:
    """Результат парсинга строки климатического исполнения."""
    zone_code: Optional[str] = None       # код в БД: u, hl, uhl, t, tv...
    placement_code: Optional[str] = None  # код в БД: 1, 2, 3, 4, 5
    raw: str = ''


class ClimateStringParser:
    """Парсер строки климатического исполнения."""

    @classmethod
    def parse(cls, raw: str) -> Optional[ClimateFilterData]:
        if not raw or not raw.strip():
            return None

        s = raw.strip().upper()
        result = ClimateFilterData(raw=raw.strip())

        # 1. Выделяем категорию размещения (цифра в конце)
        m_place = _PLACEMENT_RE.search(s)
        if m_place:
            result.placement_code = m_place.group(1)
            s = _PLACEMENT_RE.sub('', s).strip()

        # 2. Выделяем климатическую зону (жадный матчинг по длине)
        for name, code in _ZONE_NAME_TO_CODE:
            if s.startswith(name):
                result.zone_code = code
                break

        if not result.zone_code:
            # Попробуем поиск в любом месте строки
            for name, code in _ZONE_NAME_TO_CODE:
                if name in s:
                    result.zone_code = code
                    break

        if not result.zone_code and not result.placement_code:
            return None

        return result
