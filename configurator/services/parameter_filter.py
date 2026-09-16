"""
ParameterRule-based filter engine for catalog queries.

Replaces FilterDefinition-based _apply_filters with ParameterRule semantics:
directional (min/max), hierarchy, compatible, subset match types.
"""
import logging
import hashlib
from typing import Any
from django.db.models import Q, Model
from configurator.models import ParameterBinding
from params.exd_models import ExdOption

logger = logging.getLogger(__name__)

# Ключ версии кэша совместимости Exd. Инвалидируется сигналами
# params/apps.py (post_save/post_delete справочников взрывозащиты).
EXD_COMPAT_CACHE_VERSION_KEY = 'exd_compat_version'


def _resolve_hierarchy_compatible_ids(levels: list, value: Any) -> set | None:
    """ID видов, совместимых с уровнем иерархии — один SQL-запрос + кэш.

    Семантика (см. exd-option.md §1.3):
      * уровень 0 (общепром) → все активные виды;
      * иначе: виды, чьи имена соответствуют уровням value..max, расширяются
        их наборами «не хуже» (тот же метод, группа rating>= в той же среде,
        температура rating>= для газа / dust<= для пыли) и объединяются ОДНИМ
        OR-запросом вместо прежнего цикла get_compatible_ids() (N+1).

    Возвращает None, если значение не является уровнем; пустое множество —
    если подходящих видов нет (вызовет пустую выдачу, как прежний фолбэк).
    """
    from django.core.cache import cache

    _value = 'Ex d' if value == 'Exd' else value
    if _value not in levels:
        return None
    idx = levels.index(_value)
    if idx == 0:
        # общепром → все активные виды
        return set(ExdOption.objects.filter(is_active=True).values_list('id', flat=True))

    version = cache.get(EXD_COMPAT_CACHE_VERSION_KEY, 1)
    cache_key = 'exd_hierarchy:%s:%s' % (version, hashlib.md5(_value.encode('utf-8')).hexdigest())
    cached = cache.get(cache_key)
    if cached is not None:
        return set(cached)

    compatible_names = levels[idx:]
    name_q = Q()
    for name in compatible_names:
        name_q |= Q(name__icontains=name, is_active=True)
    matched = list(
        ExdOption.objects.filter(name_q).select_related(
            'explosion_protection_class__method',
            'hazardous_group',
            'temperature_class',
        )
    )
    if not matched:
        return set()

    branch_q = Q()
    unconstrained = False
    for opt in matched:
        cond = Q()
        has_constraint = False
        if opt.explosion_protection_class_id and opt.explosion_protection_class.method_id:
            cond &= Q(explosion_protection_class__method_id=opt.explosion_protection_class.method_id)
            has_constraint = True
        if opt.hazardous_group_id:
            cond &= Q(
                hazardous_group__rating__gte=opt.hazardous_group.rating,
                hazardous_group__group_type=opt.hazardous_group.group_type,
            )
            has_constraint = True
        if opt.temperature_class_id:
            cond &= Q(temperature_rating__gte=opt.temperature_class.strictness_rating)
            has_constraint = True
        elif opt.dust_temperature:
            cond &= Q(temperature_rating__lte=opt.dust_temperature)
            has_constraint = True
        if has_constraint:
            branch_q |= cond
        else:
            unconstrained = True

    if unconstrained:
        ids = set(ExdOption.objects.filter(is_active=True).values_list('id', flat=True))
    else:
        ids = set(
            ExdOption.objects.filter(is_active=True)
            .filter(branch_q)
            .values_list('id', flat=True)
        )
    # Прежний фолбэк: если набор «не хуже» пуст, допускались сами найденные
    # по имени виды (icontains-фолбэк по name).
    if not ids:
        ids = {opt.id for opt in matched}

    cache.set(cache_key, sorted(ids), timeout=300)
    return ids


def _build_q_from_parameter_rule(rule, param_name: str, value: Any) -> tuple | None:
    """Build a Django ORM lookup tuple from a ParameterRule.

    Used by FilterDefinition.build_filter_lookup when filter_type=PARAMETER_RULE.
    Returns (lookup_str, value) tuple or None.

    Args:
        rule: ParameterRule instance.
        param_name: Django model field name (from FilterDefinition.model_field).
        value: User-supplied value.

    Returns:
        (lookup, converted_value) or None.
    """
    match_type = rule.match_type
    match_config = rule.match_config

    try:
        if match_type == "directional":
            direction = match_config.get("direction", "min")
            if direction == "min":
                return f"{param_name}__lte", value
            else:
                return f"{param_name}__gte", value

        elif match_type == "hierarchy":
            # requirement at level N → модели с видами уровня >= N (M2M-поиск).
            levels: list = match_config.get("levels", [])
            if not levels:
                return None
            ids = _resolve_hierarchy_compatible_ids(levels, value)
            if ids is None:
                return None
            if ids:
                return f"{param_name}__in", list(ids)
            return f"{param_name}", value  # прежний фолбэк: точное совпадение

        elif match_type == "compatible":
            groups: list = match_config.get("groups", [])
            for group in groups:
                if value in group:
                    return f"{param_name}__in", group
            return f"{param_name}", value

        elif match_type == "subset":
            rank_field = match_config.get("field", "ip_rank")
            return f"{param_name}__{rank_field}__gte", value

        elif match_type == "exact":
            return f"{param_name}", value

        else:
            logger.warning(f"Unsupported match_type in filter lookup: {match_type}")
            return None

    except Exception as e:
        logger.warning(f"Failed build lookup for {param_name}={value}: {e}")
        return None


def _build_q_from_binding(binding: ParameterBinding, value: Any) -> Q | None:
    """Build a Q object for a single parameter binding and value.

    Uses the bound ParameterRule.match_type to determine the filter strategy.

    Returns None if the value can't be converted or the rule type is unsupported.
    """
    rule = binding.rule
    param_name = binding.param_name
    match_type = rule.match_type
    match_config = rule.match_config

    try:
        if match_type == "directional":
            direction = match_config.get("direction", "min")
            if direction == "min":
                # requirement: -20 → model.work_temp_min <= -20
                # i.e. model must handle AT LEAST as cold
                return Q(**{f"{param_name}__lte": value})
            else:  # max
                # requirement: +60 → model.work_temp_max >= +60
                return Q(**{f"{param_name}__gte": value})

        elif match_type == "hierarchy":
            # requirement at level N → модели с видами уровня >= N.
            # Поиск по M2M видов: модель проходит, если хотя бы один
            # приписанный вид совместим с требованием (EXISTS-семантика).
            levels: list = match_config.get("levels", [])
            if not levels:
                return None

            ids = _resolve_hierarchy_compatible_ids(levels, value)
            if ids is None:
                return None
            if ids:
                return Q(**{f"{param_name}__in": list(ids)})

            # Fallback: direct __name__icontains OR (как прежде, когда набор пуст).
            _value = 'Ex d' if value == 'Exd' else value
            idx = levels.index(_value)
            name_q = Q()
            for name in levels[idx:]:
                name_q |= Q(**{f"{param_name}__name__icontains": name})
                # Normalize common variants: "Exd" → also search "Ex d"
                if name == "Exd":
                    name_q |= Q(**{f"{param_name}__name__icontains": "Ex d"})
                elif name == "Ex d":
                    name_q |= Q(**{f"{param_name}__name__icontains": "Exd"})
            return name_q

        elif match_type == "compatible":
            groups: list = match_config.get("groups", [])
            for group in groups:
                if value in group:
                    return Q(**{f"{param_name}__in": group})
            # Not found in any group → exact match
            return Q(**{param_name: value})

        elif match_type == "subset":
            # IP subset: model.ip_rank >= required ip_rank
            rank_field = match_config.get("field", "ip_rank")
            return Q(**{f"{param_name}__{rank_field}__gte": value})

        elif match_type == "exact":
            return Q(**{param_name: value})

        else:
            logger.warning(f"Unsupported match_type: {match_type}")
            return None

    except Exception as e:
        logger.warning(f"Failed to build Q for {param_name}={value}: {e}")
        return None


def apply_parameter_rules(
    model_class: type[Model],
    equipment_type_code: str,
    params: dict,
    limit: int = 100,
) -> dict:
    """Apply ParameterRule-based filtering to a catalog model.

    Looks up ParameterBinding for the given equipment_type_code,
    builds Q objects using the bound ParameterRule semantics,
    and returns filtered + serialized results.

    Args:
        model_class: Django model class (e.g., LimitSwitchBox).
        equipment_type_code: EquipmentType.code to resolve bindings.
        params: dict param_name → value (e.g., {'work_temp_min': -20}).
        limit: max results.

    Returns:
        {'options': [...], 'total': N}
    """
    from core.models import EquipmentType

    try:
        eq_type = EquipmentType.objects.get(code=equipment_type_code)
    except EquipmentType.DoesNotExist:
        logger.error(f"EquipmentType '{equipment_type_code}' not found")
        return {"options": [], "total": 0}

    bindings = ParameterBinding.objects.filter(
        equipment_type=eq_type,
        is_active=True,
    ).select_related("rule")

    qs = model_class.objects.filter(is_active=True)
    q_filters = Q()
    applied = 0

    for binding in bindings:
        value = params.get(binding.param_name)
        if value is None or value == "":
            continue

        q = _build_q_from_binding(binding, value)
        if q is not None:
            q_filters &= q
            applied += 1

    if applied == 0:
        # No applicable filters — return first N
        qs = qs[:limit]
    else:
        qs = qs.filter(q_filters)[:limit]

    options = []
    for obj in qs:
        options.append({
            "id": obj.id,
            "name": getattr(obj, "name", str(obj)),
            "code": getattr(obj, "code", ""),
        })

    total = model_class.objects.filter(is_active=True).filter(q_filters).count() if applied > 0 else 0

    return {"options": options, "total": total or len(options)}
