# client_requests/models/base_requirement.py
"""
Abstract base model for equipment requirements.

Each equipment type (gearbox, filter-regulator, limit-switch, etc.)
inherits from this and adds its type-specific fields.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseRequirement(models.Model):
    """
    Абстрактная модель требований к оборудованию.

    Общие для всех типов поля: привязка к позиции запроса,
    IP-защита, взрывозащита, температурный диапазон.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # ── Связь с позицией запроса ──
    request_item = models.OneToOneField(
        'client_requests.ClientRequestItem',
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name=_("Позиция запроса"),
    )

    # ── Общие технические требования ──
    ip_protection = models.ForeignKey(
        'params.IpOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("IP защита"),
    )

    temp_min = models.IntegerField(
        default=-60,
        verbose_name=_("Мин. температура, °C"),
    )

    temp_max = models.IntegerField(
        default=120,
        verbose_name=_("Макс. температура, °C"),
    )

    climatic_designation = models.CharField(
        max_length=20, blank=True,
        verbose_name=_("Климатическое исполнение"),
        help_text=_("Обозначение по ГОСТ 15150, например «УХЛ4», «У2»"),
    )

    # ── Метаданные ──
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Создано"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Обновлено"),
    )

    class Meta:
        abstract = True
        verbose_name = _("Базовое требование")
        verbose_name_plural = _("Базовые требования")

    def __str__(self):
        item = self.request_item
        if item:
            return f"Требования к поз.{item.item_no} ({item.request_parent.code})"
        return f"Требования #{self.id}"

    @classmethod
    def get_defaults(cls):
        """
        Возвращает словарь значений по умолчанию для формы требований.

        None означает «Не указано» — фильтр не применяется.
        Наследники переопределяют для указания специфичных defaults.
        """
        return {
            'ip_protection': None,
            'temp_min': None,
            'temp_max': None,
            'climatic_designation': None,
        }

    def to_filter_params(self):
        """
        Преобразовать поля требования в словарь query-параметров
        для EngineerSelection API.

        Ключи словаря соответствуют param_name из FilterDefinition.
        Переопределить в наследниках для добавления спец. полей.
        """
        params = {}
        if self.ip_protection_id:
            params['ip_id'] = self.ip_protection_id
        if self.temp_min is not None:
            params['work_temp_min'] = str(self.temp_min)
        if self.temp_max is not None:
            params['work_temp_max'] = str(self.temp_max)
        return params
