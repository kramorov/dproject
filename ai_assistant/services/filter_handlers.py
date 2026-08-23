"""
Фильтр-хендлеры для AI-пайплайна.
Вызываются напрямую (без HTTP) из tree_processor._call_filter_handler.
Принимают params: dict с extracted параметрами (param_name → value).
Возвращают: dict с ключами 'options' (список) и 'total' (количество).
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _apply_filters(model_class, filter_definitions, params: dict, limit: int = 100, base_queryset=None):
    """
    Применяет FilterDefinition к модели и возвращает результаты.
    
    Args:
        model_class: Django-класс модели.
        filter_definitions: список FilterDefinition.
        params: dict param_name → value из extract_output.
        limit: максимальное количество результатов.
    
    Returns:
        dict: {'options': [...], 'total': N}
    """
    from django.db.models import Q
    
    qs = base_queryset if base_queryset is not None else model_class.objects.filter(is_active=True)
    q_filters = Q()
    
    for fd in filter_definitions:
        value = params.get(fd.param_name)
        if value is None:
            continue
        
        filter_type = fd.filter_type
        field = fd.model_field
        
        try:
            if filter_type.value in ('exact',):
                q_filters &= Q(**{field: value})
            elif filter_type.value in ('gte', 'temp_min', 'min'):
                q_filters &= Q(**{f"{field}__gte": value})
            elif filter_type.value in ('lte', 'temp_max', 'max'):
                q_filters &= Q(**{f"{field}__lte": value})
            elif filter_type.value == 'icontains':
                q_filters &= Q(**{f"{field}__icontains": value})
            elif filter_type.value == 'compatible':
                q_filters &= Q(**{f"{field}__gte": value})
            elif filter_type.value == 'ip_rank':
                q_filters &= Q(**{f"{field}_id__gte": value})
            elif filter_type.value == 'exd_compatible':
                q_filters &= Q(**{field: value})
        except Exception as e:
            logger.warning(f"Filter {fd.param_name}={value} failed: {e}")
    
    qs = qs.filter(q_filters)
    total = qs.count()  # полное число совпадений (до лимита)
    qs = qs[:limit]
    
    # Serialize
    options = []
    for obj in qs:
        options.append({
            'id': obj.id,
            'name': getattr(obj, 'name', str(obj)),
            'code': getattr(obj, 'code', ''),
        })
    
    return {'options': options, 'total': total}


# ── Solenoid valves ──

def solenoid_valves_filter(params: dict) -> dict:
    from solenoid_valves.catalog.config import SOLENOID_VALVES_CONFIG
    from solenoid_valves.models import DirectionValve
    return _apply_filters(DirectionValve, SOLENOID_VALVES_CONFIG.get_filter_set("engineer").definitions, params)


# ── Limit switch box ──

def limit_switch_filter(params: dict) -> dict:
    from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG
    from pa_controls.models.limit_switch import LimitSwitchBox
    return _apply_filters(LimitSwitchBox, LIMIT_SWITCH_CONFIG.get_filter_set("engineer").definitions, params)


# ── Limit switch box (ParameterRule-based, v2) ──

def limit_switch_filter_v2(params: dict) -> dict:
    """БКВ фильтр на основе ParameterRule (configurator).

    Использует ParameterBinding → ParameterRule для определения
    семантики сравнения (directional, hierarchy, subset) вместо
    жёстко закодированных FilterType в _apply_filters.
    """
    from pa_controls.models.limit_switch import LimitSwitchBox
    from configurator.services.parameter_filter import apply_parameter_rules
    return apply_parameter_rules(LimitSwitchBox, "lsb", params)


# ── Gearbox ──

def gearbox_filter(params: dict) -> dict:
    from gearbox.catalog.config import GEARBOX_CONFIG
    from gearbox.models import GearBox
    return _apply_filters(GearBox, GEARBOX_CONFIG.get_filter_set("engineer").definitions, params)


# ── Filter regulator ──

def filter_regulator_filter(params: dict) -> dict:
    from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG
    from filter_regulator.models import FilterRegulator
    return _apply_filters(FilterRegulator, FILTER_REGULATOR_CONFIG.get_filter_set("engineer").definitions, params)


# ── Pneumatic fittings ──

def pneumatic_fittings_filter(params: dict) -> dict:
    from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG
    from pneumatic_fittings.models import PneumaticFitting
    return _apply_filters(
        PneumaticFitting,
        PNEUMATIC_FITTINGS_CONFIG.get_filter_set("engineer").definitions,
        params,
        # Каталог фитингов разделён по видам: AI-подбор в каталоге трубок
        # ищет только вид 'fitting-thread-pipe' (KindCatalogConfig).
        base_queryset=PNEUMATIC_FITTINGS_CONFIG.get_scoped_queryset(),
    )
