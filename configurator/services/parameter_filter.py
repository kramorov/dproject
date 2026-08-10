"""
ParameterRule-based filter engine for catalog queries.

Replaces FilterDefinition-based _apply_filters with ParameterRule semantics:
directional (min/max), hierarchy, compatible, subset match types.
"""
import logging
from typing import Any
from django.db.models import Q, Model
from configurator.models import ParameterBinding
from params.exd_models import ExdOption

logger = logging.getLogger(__name__)


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
            levels: list = match_config.get("levels", [])
            if not levels:
                return None
            _value = value
            if value == "Exd":
                _value = "Ex d"
            if _value not in levels:
                return None
            idx = levels.index(_value)
            compatible_names = levels[idx:]
            is_all_levels = (idx == 0)

            try:
                if is_all_levels:
                    exd_options = ExdOption.objects.filter(is_active=True)
                else:
                    name_q = Q()
                    for name in compatible_names:
                        name_q |= Q(name__icontains=name, is_active=True)
                    exd_options = ExdOption.objects.filter(name_q)

                if exd_options.exists():
                    all_ids: set[int] = set()
                    for opt in exd_options:
                        all_ids.update(opt.get_compatible_ids())
                    if all_ids:
                        return f"{param_name}__in", list(all_ids)
            except Exception as e:
                logger.warning(f"Hierarchy lookup for {param_name}={value}: {e}")

            return f"{param_name}", value

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
            # requirement at level N → models at level >= N.
            # Uses ExdOption.get_compatible_ids() to find all acceptable options.
            levels: list = match_config.get("levels", [])
            if not levels:
                return None

            # Normalize common input variants: "Exd" → "Ex d"
            _value = value
            if value == "Exd":
                _value = "Ex d"

            if _value not in levels:
                return None

            idx = levels.index(_value)
            compatible_names = levels[idx:]
            is_all_levels = (idx == 0)  # общепром → match all

            try:
                if is_all_levels:
                    # общепром → all ExdOptions
                    exd_options = ExdOption.objects.filter(is_active=True)
                else:
                    # Find ExdOption objects matching the compatible level names.
                    # Level names like "Ex d", "Ex ia" match via name__icontains
                    # against full ExdOption names like "Ex db IIB T6 Gb".
                    name_q = Q()
                    for name in compatible_names:
                        name_q |= Q(name__icontains=name, is_active=True)
                    exd_options = ExdOption.objects.filter(name_q)

                if exd_options.exists():
                    all_ids: set[int] = set()
                    for opt in exd_options:
                        all_ids.update(opt.get_compatible_ids())
                    if all_ids:
                        return Q(**{f"{param_name}__in": list(all_ids)})
            except Exception as e:
                logger.warning(f"Hierarchy filter for {param_name}={value}: {e}")

            # Fallback: direct __name__icontains OR.
            # Also try common abbreviation normalizations (Exd → Ex d).
            name_q = Q()
            for name in compatible_names:
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
