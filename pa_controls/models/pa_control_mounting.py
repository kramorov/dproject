# pa_controls/models/pa_control_mounting.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List, Optional, Tuple, Any, Dict, Union

import logging

logger = logging.getLogger(__name__)

class PaControlMountingStandard(models.Model):
    """
    Стандарт присоединения для БКВ и позиционеров
    """
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название стандарта")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код стандарта"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание стандарта'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    standard_type = models.CharField(
        max_length=30,
        choices=[
            ('namur', 'NAMUR VDI/VDE 3845'),
            ('namur_custom', 'NAMUR нестандартный'),
            ('din', 'DIN 3337'),
            ('iso', 'ISO 5211'),
            ('custom', 'Нестандартный'),
        ],
        default='namur',
        verbose_name=_("Тип стандарта")
    )

    # Размер по стандарту
    size = models.CharField(
        max_length=20, null=True, blank=True,
        verbose_name=_("Размер"),
        help_text=_("Размер: 1, 2, 3, 4, 80x130")
    )

    # Геометрия штока (квадрат)
    square_size_mm = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("Квадрат (мм)"),
        help_text=_("Размер квадратного отверстия под шток")
    )

    # Крепежные отверстия
    screw_thread = models.CharField(
        max_length=20, null=True, blank=True,
        verbose_name=_("Резьба крепления"),
        help_text=_("M5, M6, M8, M10")
    )

    # Межосевые расстояния
    mounting_holes_x_mm = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("Расстояние по оси X (мм)"),
        help_text=_("Межосевое расстояние по горизонтали")
    )
    mounting_holes_y_mm = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name=_("Расстояние по оси Y (мм)"),
        help_text=_("Межосевое расстояние по вертикали")
    )

    # Запасные отверстия (опционально)
    has_additional_holes = models.BooleanField(
        default=False,
        verbose_name=_("Дополнительные отверстия"),
        help_text=_("Наличие дополнительных крепежных отверстий")
    )
    additional_holes_pattern = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Схема доп. отверстий"),
        help_text=_("Например: 40x40, 60x60")
    )

    # Совместимость
    compatible_sizes = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name=_("Совместимые размеры"),
        help_text=_("Через запятую: 1,2,80x130")
    )

    extra_params = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Стандарт присоединения")
        verbose_name_plural = _("Стандарты присоединения")
        ordering = ['sorting_order']

    def __str__(self):
        if self.standard_type == 'namur':
            return f"NAMUR {self.size} (кв.{self.square_size_mm}, {self.mounting_holes_x_mm}x{self.mounting_holes_y_mm})"
        return self.name