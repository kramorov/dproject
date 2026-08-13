"""
configurator/services/filter_engine.py

FilterEngine: требования → ParameterRule → Django Q → кандидаты.

Использует существующий API из parameter_filter.py (_build_q_from_binding).

Вызывается при подборе:
    filter_by_requirements(component)
    → component.filter_results = [candidates]
"""
from __future__ import annotations

import logging
from typing import Any

from django.db.models import Q, Model, QuerySet

from assemblies.models import ComponentRequirement
from configurator.models import ParameterBinding
from configurator.services.parameter_filter import _build_q_from_binding
from configurator.services.registry import get_product_model_class

logger = logging.getLogger(__name__)


def filter_by_requirements(
    component: ComponentRequirement,
    max_results: int = 100,
) -> dict:
    """
    Подбирает продукты по effective_requirements компонента.

    Для pneumatic-actuator — делегирует в PA selector
    (TorqueSelectorService + find_suitable_actuators).
    Для остальных типов — использует ParameterBinding/ParameterRule.

    Args:
        component: ComponentRequirement с заполненным effective_requirements.
        max_results: Максимальное количество кандидатов.

    Returns:
        {'candidates': [...], 'total': N, 'relaxed': bool, 'relaxation_detail': str}
    """
    if not component.equipment_type:
        return _empty_result("No equipment_type")

    # ── Спец-путь для пневмопривода: делегируем в PA selector ──
    if component.equipment_type.code == 'pneumatic-actuator':
        return _filter_pa_selector(component)

    effective = component.effective_requirements or {}
    if not effective:
        return _empty_result("No effective_requirements")

    try:
        model_class = get_product_model_class(component.equipment_type)
    except KeyError as e:
        return _empty_result(str(e))

    # 1. Загружаем все ParameterBinding для этого типа
    bindings = _load_bindings(component.equipment_type)

    # 2. Разделяем параметры на hard и soft
    hard_q = Q()
    soft_params: list[tuple[ParameterBinding, Any, int]] = []

    for param_name, value in effective.items():
        binding = bindings.get(param_name)
        if not binding:
            continue  # параметр без привязанного правила — пропускаем

        rule = binding.rule
        if rule.hardness == 'hard':
            q = _build_q_from_binding(binding, value)
            if q is not None:
                hard_q &= q
        else:
            soft_params.append((binding, value, rule.priority))

    # 3. HARD FILTER
    candidates = model_class.objects.filter(hard_q, is_active=True)

    # 4. RELAX — если кандидатов нет
    relaxed = False
    relaxation_detail = ""
    if not candidates.exists() and soft_params:
        candidates, relaxed, relaxation_detail = _relax_soft_params(
            soft_params, hard_q, model_class
        )

    # 5. SCORE + сортировка
    if soft_params and candidates.exists():
        candidates = _score_and_sort(candidates, soft_params)

    # 6. Сериализация
    total = len(candidates) if isinstance(candidates, list) else candidates.count()
    result_candidates = []
    for obj in candidates[:max_results]:
        result_candidates.append(_serialize_candidate(obj, soft_params))

    # 7. Сохраняем результат
    component.filter_results = {
        'candidates': result_candidates,
        'total': total,
        'relaxed': relaxed,
        'relaxation_detail': relaxation_detail,
    }
    component.status = 'filtered'
    component.save(update_fields=['filter_results', 'status'])

    return component.filter_results


def select_product(
    component: ComponentRequirement,
    product_id: int,
) -> dict:
    """
    Выбирает продукт из кандидатов и сохраняет выбор.

    Для pneumatic-actuator: product_id = body_id из PA selector.
    Для остальных: product_id = ID записи в product model.

    Args:
        component: ComponentRequirement.
        product_id: ID выбранного продукта.

    Returns:
        selected_product_specs или пустой dict.
    """
    # ── PA: ищем кандидата в filter_results по body_id ──
    if component.equipment_type and component.equipment_type.code == 'pneumatic-actuator':
        candidates = (component.filter_results or {}).get('candidates', [])
        match = next((c for c in candidates if c.get('pa_body_id') == product_id), None)
        if not match:
            return {}
        specs = {
            'name': match.get('name', ''),
            'code': match.get('code', ''),
            'body_id': match.get('pa_body_id'),
            'body_code': match.get('pa_body_code'),
            'variety': match.get('variety'),
            'score': match.get('score'),
            'spring_margin': match.get('spring_margin'),
            'model_line': match.get('model_line'),
        }
        component.selected_sku = _resolve_sku(code=specs.get('code') or specs.get('body_code'))
        component.selected_product_specs = specs
        component.status = 'selected'
        component.save(update_fields=[
            'selected_sku', 'selected_product_specs', 'status',
        ])
        return specs

    # ── Generic path ──
    try:
        model_class = get_product_model_class(component.equipment_type)
    except KeyError:
        return {}

    try:
        obj = model_class.objects.get(id=product_id, is_active=True)
    except model_class.DoesNotExist:
        return {}

    specs = _serialize_candidate(obj, [])
    component.selected_sku = _resolve_sku(obj)
    component.selected_product_specs = specs
    component.status = 'selected'
    component.save(update_fields=[
        'selected_sku', 'selected_product_specs', 'status',
    ])
    return specs


# ── Private helpers ──


def _resolve_sku(obj=None, *, code=None):
    """Резолвит SKU для выбранного продукта: через .sku (SKUMixin) или по коду."""
    from sku.models import SKU
    sku = None
    if obj is not None:
        sku = getattr(obj, 'sku', None)
        if sku and getattr(sku, 'id', None):
            return sku
        code = code or getattr(obj, 'code', None)
    if code:
        return SKU.objects.filter(code=code).first()
    return None


def _load_bindings(equipment_type) -> dict[str, ParameterBinding]:
    """Загружает ParameterBinding для equipment_type, возвращает {param_name: binding}."""
    qs = ParameterBinding.objects.filter(
        equipment_type=equipment_type,
        is_active=True,
    ).select_related('rule')
    return {b.param_name: b for b in qs}


def _relax_soft_params(
    soft_params: list,
    hard_q: Q,
    model_class: type[Model],
) -> tuple[QuerySet, bool, str]:
    """
    Релаксация soft-параметров.

    Стратегия: перебираем комбинации релаксаций (от 1 параметра до всех),
    находим комбинацию с минимальным штрафом, дающую хотя бы одного кандидата.

    Returns:
        (candidates, relaxed, detail_string)
    """
    if not soft_params:
        return model_class.objects.none(), False, ""

    # Сортируем по приоритету (низкий = менее важно, релаксируем первым)
    sorted_params = sorted(soft_params, key=lambda x: x[2])

    # Пробуем релаксировать по одному параметру, начиная с наименее важного
    for i, (binding, value, priority) in enumerate(sorted_params):
        rule = binding.rule
        if rule.relaxation_strategy == 'none':
            continue

        if rule.relaxation_strategy == 'any':
            # Полное игнорирование параметра — не включаем его в Q
            relaxed_q = hard_q
            for j, (b, v, p) in enumerate(sorted_params):
                if j == i:
                    continue  # пропускаем этот параметр
                q = _build_q_from_binding(b, v)
                if q is not None:
                    relaxed_q &= q

            candidates = model_class.objects.filter(relaxed_q, is_active=True)
            if candidates.exists():
                detail = (
                    f"Relaxed '{binding.param_name}': "
                    f"ignored (strategy=any)"
                )
                logger.info("Relaxation found: %s → %d candidates", detail, candidates.count())
                return candidates, True, detail
            continue

        relaxed_values = _get_relaxed_values(rule, value)
        for relaxed_val, penalty in relaxed_values:
            relaxed_q = hard_q
            # Перестраиваем Q с релаксированным значением для этого параметра
            for j, (b, v, p) in enumerate(sorted_params):
                if j == i:
                    q = _build_q_from_binding(b, relaxed_val)
                else:
                    q = _build_q_from_binding(b, v)
                if q is not None:
                    relaxed_q &= q

            candidates = model_class.objects.filter(relaxed_q, is_active=True)
            if candidates.exists():
                detail = (
                    f"Relaxed '{binding.param_name}': "
                    f"{value} → {relaxed_val} "
                    f"(strategy={rule.relaxation_strategy}, penalty={penalty})"
                )
                logger.info("Relaxation found: %s → %d candidates", detail, candidates.count())
                return candidates, True, detail

    return model_class.objects.none(), False, "No relaxation produced candidates"


def _get_relaxed_values(rule, value) -> list[tuple[Any, int]]:
    """
    Генерирует список релаксированных значений с penalty.

    Returns:
        [(relaxed_value, penalty), ...] — отсортировано по penalty (возрастание).
    """
    strategy = rule.relaxation_strategy
    config = rule.relaxation_config or {}

    if strategy == 'step':
        step = config.get('step', 1)
        max_steps = config.get('max_steps', 3)
        result = []
        try:
            val = float(value) if not isinstance(value, (int, float)) else value
            for s in range(1, max_steps + 1):
                delta = step * s
                # Для min-параметров (temperature_min): требование -20 → +5 → -15 (менее строго)
                # Для max-параметров (temperature_max): требование +60 → -5 → +55 (менее строго)
                direction = rule.match_config.get('direction', 'min')
                if direction == 'min':
                    relaxed = val + delta  # ослабляем: -20 → -15 → -10
                else:
                    relaxed = val - delta  # ослабляем: +60 → +55 → +50
                result.append((relaxed, s))
        except (ValueError, TypeError):
            pass
        return sorted(result, key=lambda x: x[1])

    elif strategy == 'percentage':
        percent = config.get('percent', 5)
        max_steps = config.get('max_steps', 3)
        result = []
        try:
            val = float(value) if not isinstance(value, (int, float)) else value
            for s in range(1, max_steps + 1):
                delta = val * percent / 100 * s
                direction = rule.match_config.get('direction', 'min')
                if direction == 'min':
                    relaxed = val + delta  # ослабляем
                else:
                    relaxed = val - delta  # ослабляем
                result.append((relaxed, s))
        except (ValueError, TypeError):
            pass
        return sorted(result, key=lambda x: x[1])

    # 'any' обрабатывается в _relax_soft_params отдельно (полное игнорирование)

    return []


def _score_and_sort(
    candidates: QuerySet,
    soft_params: list,
) -> list:
    """
    Вычисляет penalty для каждого кандидата и сортирует.

    Штраф начисляется за каждое отклонение по soft-параметру:
        penalty = abs(model_value - required_value) * priority

    Для pneumatic-actuator: использует торк-скоринг близости к идеалу
    (аналогично TorqueSelectorService.calculate_score_sr/da).
    """
    scored = []
    for obj in candidates:
        total_penalty = 0
        for binding, req_value, priority in soft_params:
            penalty = _calculate_deviation(obj, binding, req_value)
            total_penalty += penalty * priority
        # Торк-скоринг для пневмоприводов
        torque_penalty = _score_torque_proximity(obj, soft_params)
        total_penalty += torque_penalty
        scored.append((total_penalty, obj))

    scored.sort(key=lambda x: x[0])
    ids = [obj.id for _, obj in scored]
    preserved = {obj.id: obj for obj in candidates}
    return [preserved[id] for id in ids if id in preserved]


def _score_torque_proximity(obj: Model, soft_params: list) -> float:
    """
    Скоринг близости крутящего момента к идеалу.

    Аналогичен логике TorqueSelectorService:
      - Для каждого варианта (body) вычисляется отклонение BTO/RTO
        от требуемого момента.
      - Чем меньше отклонение (запас) — тем лучше (меньше penalty).
      - Если момент привода недостаточен (torque_required >= bto) — большой штраф.

    Использует поля продукта: bto, rto, eto (если доступны).
    """
    # Ищем параметр torque_nm в soft_params
    torque_req = None
    for binding, req_value, _ in soft_params:
        if binding.param_name in ('torque_nm', 'torque_with_safety', 'bto'):
            try:
                torque_req = float(req_value)
            except (ValueError, TypeError):
                pass
            break

    if torque_req is None:
        return 0.0

    # Пытаемся получить BTO/RTO/ETO из продукта
    bto = _safe_float_attr(obj, 'bto')
    rto = _safe_float_attr(obj, 'rto')
    eto = _safe_float_attr(obj, 'eto')

    # Если нет torque-полей — не пневмопривод, пропускаем
    if bto is None:
        return 0.0

    # DA-привод: penalty = bto - torque (запас), 0 если не хватает → 999
    # SR-привод: penalty = abs(torque - center), где center = (bto + eto) / 2
    if eto is not None and eto != bto:
        # SR: центр между BTO и ETO
        center = (bto + eto) / 2.0
        spring_min = min(bto, eto)
        if torque_req >= spring_min:
            return 999.0  # пружина не справляется
        return abs(torque_req - center)
    else:
        # DA: запас по моменту
        if torque_req >= bto:
            return 999.0  # недостаточный момент
        margin = bto - torque_req
        # Нормализуем: чем меньше запас — тем лучше, но не 0
        return margin * 0.1  # масштабируем для совместимости с другими penalty


def _safe_float_attr(obj, attr_name: str) -> float | None:
    """Безопасно получает float-атрибут объекта."""
    try:
        val = getattr(obj, attr_name, None)
        if val is None:
            return None
        return float(val)
    except (ValueError, TypeError, AttributeError):
        return None


def _calculate_deviation(obj: Model, binding: ParameterBinding, req_value) -> float:
    """Вычисляет отклонение значения модели от требования (0 = точное совпадение)."""
    rule = binding.rule
    param_name = binding.param_name

    try:
        model_value = _get_nested_attr(obj, param_name)
    except AttributeError:
        return 0.0

    if model_value is None:
        return 0.0
    if req_value is None:
        return 0.0

    match_type = rule.match_type
    if match_type == 'exact':
        return 0.0 if str(model_value) == str(req_value) else 1.0

    elif match_type == 'directional':
        try:
            mv = float(model_value)
            rv = float(req_value)
            direction = rule.match_config.get('direction', 'min')
            if direction == 'min':
                # model_value <= req_value — ОК (чем меньше модель, тем лучше для min-температуры)
                return 0.0 if mv <= rv else mv - rv
            else:
                return 0.0 if mv >= rv else rv - mv
        except (ValueError, TypeError):
            return 0.0

    return 0.0


def _get_nested_attr(obj, path: str):
    """Traverse nested attributes via __ (e.g. 'body__max_work_torque')."""
    parts = path.split('__')
    value = obj
    for part in parts:
        value = getattr(value, part, None)
        if value is None:
            return None
    return value


def _serialize_candidate(obj: Model, soft_params: list) -> dict:
    """Сериализует продукт в словарь для фронта."""
    result = {
        'id': obj.id,
        'name': getattr(obj, 'name', str(obj)),
        'code': getattr(obj, 'code', '') or '',
    }
    # Добавляем значения полей, участвовавших в подборе
    for binding, _, _ in soft_params:
        try:
            result[binding.param_name] = str(_get_nested_attr(obj, binding.param_name))
        except Exception:
            result[binding.param_name] = None

    # Пытаемся вызвать to_dict() если есть
    if hasattr(obj, 'to_dict'):
        try:
            result.update(obj.to_dict())
        except Exception:
            pass

    return result


# ── PA Selector delegation ──

def _build_pa_reverse_map(equipment_type) -> dict[str, str]:
    """Строит обратную карту: field_path → param_name для EquipmentTypeParameter."""
    from configurator.models import EquipmentTypeParameter as ETP
    params = ETP.objects.filter(
        equipment_type=equipment_type,
        is_active=True,
    ).values('param_name', 'field_path')
    return {p['field_path']: p['param_name'] for p in params if p['field_path']}


def _get_value(effective: dict, own: dict, rev_map: dict, param: str, default=None):
    """
    Ищет значение параметра в effective и own с учётом трансляции ключей.

    Пробует: own[param], effective[param], effective[rev_mapped_param].
    """
    if param in own and own[param] is not None:
        return own[param]
    if param in effective and effective[param] is not None:
        return effective[param]
    # Обратная трансляция: field_path → param_name
    for field_path, param_name in rev_map.items():
        if param_name == param and field_path in effective:
            return effective[field_path]
    return default


def _filter_pa_selector(component: ComponentRequirement) -> dict:
    """
    Делегирует подбор пневмопривода в PA selector.

    Преобразует effective_requirements в формат, ожидаемый
    process_selection_params(), и вызывает find_suitable_actuators().
    """
    from pneumatic_actuators.actuator_selector_handler import process_selection_params

    effective = component.effective_requirements or {}
    own = component.own_requirements or {}
    rev_map = _build_pa_reverse_map(component.equipment_type)

    # Строим payload для PA selector
    torque_val = _get_value(effective, own, rev_map, 'torque_nm', 0)
    if not torque_val or float(torque_val) <= 0:
        return _empty_result("Не указан крутящий момент (torque_nm). Заполните требования.")

    # Резолвим actuator_variety_code из ID
    variety_code = _get_value(effective, own, rev_map, 'actuator_variety_code', 'DA')
    variety_id = _get_value(effective, own, rev_map, 'actuator_variety_id') or own.get('actuator_variety_id')
    if variety_id and not effective.get('actuator_variety_code'):
        variety_code = _resolve_variety_code(variety_id)

    payload = {
        'torque_with_safety': float(torque_val),
        'air_pressure_id': _get_value(effective, own, rev_map, 'air_pressure_id'),
        'actuator_variety_id': variety_id,
        'actuator_variety_code': variety_code,
        'safety_position_id': _get_value(effective, own, rev_map, 'safety_position_id'),
        'ip_id': _get_value(effective, own, rev_map, 'ip_id') or _get_value(effective, own, rev_map, 'ip'),
        'exd_id': _resolve_exd_id(_get_value(effective, own, rev_map, 'exd')),
        'coating_id': _get_value(effective, own, rev_map, 'coating_id'),
        'hand_wheel_id': _get_value(effective, own, rev_map, 'hand_wheel_id'),
        'temp_min': int(_get_value(effective, own, rev_map, 'temp_min', 0) or 0),
        'temp_max': int(_get_value(effective, own, rev_map, 'temp_max', 0) or 0),
    }
    # Убираем None-значения — PA selector сам подставит дефолты
    payload = {k: v for k, v in payload.items() if v is not None}

    result = process_selection_params(payload)

    if not result.get('success'):
        return _empty_result(result.get('error', 'PA selector failed'))

    # Преобразуем результаты PA selector в формат FilterEngine
    candidates = []
    for ml in result.get('search_results', []):
        for item in ml.get('model_line_items', []):
            candidates.append({
                'id': item.get('body_id'),
                'pa_body_id': item.get('body_id'),
                'pa_body_code': item.get('body_code'),
                'name': f"{ml.get('model_line_name', '')} {item.get('body_name', '')}",
                'code': item.get('body_code', ''),
                'variety': item.get('actuator_variety_code', ''),
                'score': item.get('score'),
                'spring_margin': item.get('spring_margin'),
                'model_line': ml.get('model_line_name'),
                'model_line_code': ml.get('model_line_code'),
            })

    component.filter_results = {
        'candidates': candidates,
        'total': len(candidates),
        'relaxed': False,
        'relaxation_detail': '',
    }
    component.status = 'filtered'
    component.save(update_fields=['filter_results', 'status'])

    return component.filter_results


def _resolve_variety_code(variety_id) -> str:
    """Резолвит actuator_variety_code (DA/SR) из ID."""
    try:
        from pneumatic_actuators.models import PneumaticActuatorVariety
        v = PneumaticActuatorVariety.objects.filter(id=int(variety_id)).first()
        return v.code if v else 'DA'
    except Exception:
        return 'DA'


def _resolve_exd_id(exd_value) -> int | None:
    """Преобразует exd значение в ID ExdOption."""
    if exd_value is None:
        return None
    if isinstance(exd_value, int):
        return exd_value
    try:
        from params.exd_models import ExdOption
        opt = ExdOption.objects.filter(
            name__icontains=str(exd_value), is_active=True
        ).first()
        return opt.id if opt else None
    except Exception:
        return None


def _empty_result(reason: str) -> dict:
    return {
        'candidates': [],
        'total': 0,
        'relaxed': False,
        'relaxation_detail': reason,
    }
