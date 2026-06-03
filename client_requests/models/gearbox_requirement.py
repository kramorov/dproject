# client_requests/models/gearbox_requirement.py
"""
Requirement model for gearbox (ручной дублер / редуктор).
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from client_requests.models.base_requirement import BaseRequirement


class GearboxRequirement(BaseRequirement):
    """
    Требования к ручному дублёру (редуктору).

    Наследует общие поля (IP, Exd, температура) от BaseRequirement.
    Добавляет специфичные: материал корпуса, момент, монтажная площадка.
    """

    body_material = models.ForeignKey(
        'materials.MaterialGeneral',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Материал корпуса"),
    )

    torque = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Рабочий момент не менее, Нм"),
    )

    mounting_plate = models.ForeignKey(
        'params.MountingPlateTypes',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Монтажная площадка"),
    )

    class Meta:
        verbose_name = _("Требование к редуктору")
        verbose_name_plural = _("Требования к редукторам")

    def to_filter_params(self):
        params = super().to_filter_params()
        if self.body_material_id:
            params['body_material_id'] = self.body_material_id
        if self.torque is not None:
            params['min_work_torque'] = str(self.torque)
        if self.mounting_plate_id:
            params['mounting_plate_top_id'] = self.mounting_plate_id
        return params
