# client_requests/models/filter_regulator_requirement.py
"""
Requirement model for filter-regulator (фильтр-регулятор).
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from client_requests.models.base_requirement import BaseRequirement


class FilterRegulatorRequirement(BaseRequirement):
    """
    Требования к фильтр-регулятору.

    Наследует общие поля (IP, Exd, температура) от BaseRequirement.
    Добавляет: материал корпуса, расход, резьба портов, тонкость фильтрации.
    """

    body_material = models.ForeignKey(
        'materials.MaterialGeneral',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Материал корпуса"),
    )

    flow_rate = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Расход не менее, л/мин"),
    )

    thread = models.ForeignKey(
        'params.ThreadSize',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Резьба портов"),
    )

    filtration = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Тонкость фильтрации, мкм"),
    )

    class Meta:
        verbose_name = _("Требование к фильтр-регулятору")
        verbose_name_plural = _("Требования к фильтр-регуляторам")

    @classmethod
    def get_defaults(cls):
        """
        Defaults for filter-regulator requirement form: all fields «Не указано» (None).
        """
        defaults = super().get_defaults()
        defaults.update({
            'body_material': None,
            'flow_rate': None,
            'thread': None,
            'filtration': None,
        })
        return defaults

    def to_filter_params(self):
        params = super().to_filter_params()
        if self.body_material_id:
            params['body_material_id'] = self.body_material_id
        if self.flow_rate is not None:
            params['flow_rate_min'] = str(self.flow_rate)
        if self.thread_id:
            params['thread_id'] = self.thread_id
        if self.filtration is not None:
            params['filtration_rating_min'] = str(self.filtration)
        return params