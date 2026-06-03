# client_requests/models/limit_switch_requirement.py
"""
Requirement model for limit-switch box (блок концевых выключателей / БКВ).
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from client_requests.models.base_requirement import BaseRequirement


class LimitSwitchRequirement(BaseRequirement):
    """
    Требования к блоку концевых выключателей (БКВ).

    Наследует общие поля (IP, Exd, температура) от BaseRequirement.
    Добавляет: материал корпуса, тип сенсора, количество датчиков, тип сигнала.
    """

    body_material = models.ForeignKey(
        'materials.MaterialGeneral',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Материал корпуса"),
    )

    sensor_variety = models.ForeignKey(
        'pa_controls.LimitSwitchSensorVariety',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Тип сенсора"),
    )

    points = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        verbose_name=_("Количество датчиков"),
    )

    exd_protection = models.ForeignKey(
        'params.ExdOption',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Взрывозащита"),
    )

    signal_type = models.ForeignKey(
        'pa_controls.SignalType',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Тип сигнала"),
    )

    class Meta:
        verbose_name = _("Требование к БКВ")
        verbose_name_plural = _("Требования к БКВ")

    def to_filter_params(self):
        params = super().to_filter_params()
        if self.body_material_id:
            params['body_material_id'] = self.body_material_id
        if self.sensor_variety_id:
            params['sensor_variety_id'] = self.sensor_variety_id
        if self.points is not None:
            params['points'] = str(self.points)
        if self.signal_type_id:
            params['signal_type_id'] = self.signal_type_id
        if self.exd_protection_id:
            params['exd_id'] = str(self.exd_protection_id)
        return params
