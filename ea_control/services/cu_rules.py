# ea_control/services/cu_rules.py
"""
Движок правил динамики конфигуратора БУ (Паттерн В).

Плоская логика: «если значение слота-условия [оператор] значение → действие
над слотом-целью». В отличие от матрицы (статичная доступность по контексту)
правила реагируют на **выбранное значение**.

Применение:

- правила сортируются по ``priority`` (больше — позже) и id; позже
  применённое перезаписывает состояние (при конфликте show/hide побеждает
  правило с большим priority);
- ``hide``/``show`` — видимость слота; ``block`` — слот виден, но выбор
  заблокирован; ``require`` — слот обязателен; ``set_default`` — значение по
  умолчанию (``action_value``).

Значение слота в ``selection`` — код опции (для слотов с опциями) или
произвольное значение; сравнение — ``CuSlotRule.evaluate``.
"""


def evaluate_rule(rule, selection):
    """Выполнено ли правило для текущего выбора.

    ``selection`` — {slot_code: value}. Возвращает True/False.
    """
    if not rule.is_active:
        return False
    current = selection.get(rule.when_slot.code)
    return rule.evaluate(current)


def apply_rules(rules, selection):
    """Применить правила к выбору: {slot_code: состояние слота}.

    ``rules`` — итерируемый CuSlotRule (queryset/список);
    ``selection`` — {slot_code: value} текущего выбора.
    Возвращает ``{slot_code: {visible, blocked, required, default}}``.
    """
    ordered = sorted(rules, key=lambda r: (r.priority, r.id or 0))
    result = {}
    for rule in ordered:
        if not evaluate_rule(rule, selection):
            continue
        state = result.setdefault(rule.target_slot.code, {
            'visible': True, 'blocked': False, 'required': False,
            'default': None,
        })
        if rule.action == 'show':
            state['visible'] = True
        elif rule.action == 'hide':
            state['visible'] = False
        elif rule.action == 'block':
            state['blocked'] = True
        elif rule.action == 'require':
            state['required'] = True
        elif rule.action == 'set_default':
            state['default'] = rule.action_value
    return result
