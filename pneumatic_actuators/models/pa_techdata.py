# pneumatic_actuators/models/pa_techdata.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from collections import defaultdict

from media_library.models import MediaLibraryItem
from params.models import DnVariety, PnVariety
from producers.models import Brands
# from valve_data.models import ValveVariety, DimensionTableParameter, DimensionTableDrawingItem

import logging
logger = logging.getLogger(__name__)

class PneumaticActuatorTechDataTable(models.Model):
    """Таблица ВГХ для линейки арматуры - к этой таблице привязываем все данные - чертежи, таблицы значений"""
    name = models.CharField(
        max_length=100,
        verbose_name=_('Название таблицы'),
        help_text=_('Название таблицы техданных серии пневмоприводов')
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text=_('Код таблицы техданных'),
        verbose_name=_('Код таблицы')
    )

    # Связь с чертежами из медиабиблиотеки
    drawings = models.ManyToManyField(
        MediaLibraryItem,
        # through='DimensionTableDrawingItem',
        through='PneumaticActuatorTechDataTableDrawingItem' ,  # ← строковая ссылка
        through_fields=('tech_data_table', 'drawing'),
        related_name='pneumatic_tech_data_tables',
        verbose_name=_("Чертежи"),
        help_text=_("Чертежи, связанные с этой таблицей техданных")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание'),
        help_text=_('Описание таблицы техданных')
    )

    class Meta:
        verbose_name = _("Таблица техданных")
        verbose_name_plural = _("Таблицы техданных")

    def __str__(self):
        return f"{self.name}"

    @property
    def related_bodies_display(self) :
        """Отображает связанные корпуса"""
        bodies = self.model_body_tech_data.all()
        if bodies :
            return ", ".join([f"{body.name}" for body in bodies])
        return _("Нет связанных моделей корпусов")