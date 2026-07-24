"""Схема для intent = actuator_selection."""

ACTUATOR_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "valve_type":        {"type": "string", "enum": ["butterfly", "ball", "gate", "globe", "check", "plug"],
                              "description": "Тип арматуры"},
        "dn":                {"type": "integer", "description": "ДУ/номинальный диаметр в мм"},
        "pn":                {"type": "integer", "description": "PN/номинальное давление"},
        "torque_nm":         {"type": "number",  "description": "Момент без запаса, Нм"},
        "safety_factor":     {"type": "number",  "description": "Коэффициент запаса, по умолчанию 1.5"},
        "actuator_variety":  {"type": "string",  "enum": ["DA", "SR"],
                              "description": "Тип привода: DA — двойного действия, SR — с возвратной пружиной"},
        "safety_position":   {"type": "string",  "enum": ["NC", "NO"],
                              "description": "Положение безопасности: NC или NO"},
        "air_pressure_bar":  {"type": "number",  "description": "Давление в пневмосистеме, бар (обычно 6)"},
        "ip":                {"type": "string",  "description": "Степень защиты IP"},
        "exd":               {"type": "string",  "description": "Взрывозащита Exd"},
        "hand_wheel":        {"type": "boolean", "description": "Ручной дублёр на корпусе"},
        "temperature_min":   {"type": "number",  "description": "Минимальная температура"},
        "temperature_max":   {"type": "number",  "description": "Максимальная температура"},
    },
    "required": ["torque_nm"]
}

ACTUATOR_SELECTION_PROMPT_TEMPLATE = """Ты инженер по подбору промышленной арматуры и пневмоприводов.
Извлеки из запроса пользователя параметры для подбора пневмопривода.

Контекст: компания АБРА производит арматуру и пневмоприводы.
Приводы могут быть двух типов: DA (двойного действия) и SR (с возвратной пружиной).

Если параметр не указан — верни null.
Если момент указан с запасом — раздели на "момент без запаса" и "коэффициент запаса".
Для SR-приводов обязательно укажи safety_position (NC или NO).

Запрос пользователя:
{user_text}
"""
