# core/models/equipment_type_mixin.py
from django.db import models


class EquipmentTypeMixin:
    """
    Миксин для привязки модели к типу оборудования.
    Добавляет ForeignKey на EquipmentType.
    """
    equipment_type = models.ForeignKey(
        'core.EquipmentType',
        on_delete=models.PROTECT,
        limit_choices_to={'is_active': True},
        verbose_name="Тип оборудования",
        help_text="К какому типу оборудования относится эта запись"
    )

    class Meta:
        abstract = True
