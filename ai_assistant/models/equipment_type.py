from django.db import models


class EquipmentType(models.Model):
    """Справочник типов оборудования, участвующих в подборе.

    Каждый тип определяет:
    - На каком уровне вложенности он обычно находится.
    - Семантику своих параметров (направление сравнения: «не менее», «не хуже»).
    - API-эндпоинт для вызова фильтров (Фаза 3).

    Используется:
    - SelectionNode.equipment_type — привязка узла дерева к типу.
    - StepConfig.equipment_type — конфигурация шага для данного типа.
    - CascadeRule.parent_type / child_type — правила каскада параметров.

    Примеры записей:
        actuator      → уровень 2, фильтр: /api/pneumatic_actuators/selector/search/
        solenoid      → уровень 3, фильтр: /api/solenoid_valves/filter/
        cable_gland   → уровень 4, фильтр: /api/cable_glands/filter/
    """

    code = models.CharField(
        max_length=64, unique=True, db_index=True,
        help_text="Уникальный код: 'actuator', 'solenoid', 'bkv', 'cable_gland', ..."
    )
    label = models.CharField(
        max_length=128,
        help_text="Человекочитаемое название: «Пневмопривод», «Соленоидный клапан», ..."
    )
    level = models.IntegerField(
        default=1,
        help_text="Типичный уровень вложенности (1=позиция, 2=компонент, 3=субкомпонент)"
    )
    param_semantics = models.JSONField(
        default=dict, blank=True,
        help_text=(
            'Семантика параметров для сравнения требований и факта. '
            'Пример: {"torque_nm": {"direction": "min", "label": "не менее"}, '
            '"ip": {"direction": "min", "label": "не хуже"}}. '
            'direction: min (чем больше тем лучше), max, exact.'
        )
    )
    filter_endpoint = models.CharField(
        max_length=256, null=True, blank=True,
        help_text="API-эндпоинт для Фазы 3: POST /api/pneumatic_actuators/selector/search/"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Equipment Type"
        verbose_name_plural = "Equipment Types"
        ordering = ["level", "code"]

    def __str__(self):
        return f"{self.label} ({self.code})"
