# valve_data/models/dimensions/dimension_table_parameter.py
from django.db import models
from django.utils.translation import gettext_lazy as _

import logging

logger = logging.getLogger(__name__)

class DimensionTableParameter(models.Model):
    """ Параметр в таблице ВГХ
        Параметр в составе таблицы ВГХ с порядком отображения
        Может быть строкой, или выбранным из справочника предопределенных параметров
        sorting_order нужен для упорядочивания параметров в таблице - в паспорте или техничке"""
    # from valve_data.models import ValveDimensionTable
    dimension_table = models.ForeignKey(
        # ValveDimensionTable,
        'valve_data.ValveDimensionTable',  # ← строка вместо импорта
        on_delete=models.CASCADE,
        related_name='table_parameters',
        verbose_name=_('Таблица ВГХ')
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("Описание"),
        help_text=_("Текстовое описание параметра на чертеже")
    )
    legend = models.CharField(
        max_length=50,
        blank=True, null=True,
        verbose_name=_("Обозначение"),
        help_text=_("Символ или обозначение параметра на чертеже")
    )
    parameter_variety = models.ForeignKey(
        # WeightDimensionParameterVariety,
        'valve_data.WeightDimensionParameterVariety',  # ← строка вместо импорта
        related_name='dimension_parameter_variety',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Системный параметр"),
        help_text=_("Сопоставленный системный параметр (опционально)")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Порядок строки"),
        help_text=_("Порядок отображения в таблице")
    )

    class Meta:
        verbose_name = _("Параметр ВГХ")
        verbose_name_plural = _("Параметры ВГХ")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def get_structured_parameters_list_for_table(cls, owner_dimension_table):
        """
        Получить структурированные параметры для таблицы ВГХ

        Args:
            dimension_table: таблица ВГХ

        Returns:
            list: структурированные параметры
        """
        parameters = cls.objects.filter(
            dimension_table=owner_dimension_table
        ).select_related('parameter_variety').order_by('sorting_order')

        structured_list = []
        for param in parameters:
            display_name = param.name
            if not display_name and param.parameter_variety:
                display_name = param.parameter_variety.name

            param_data = {
                'id': param.id,
                'name': display_name,
                'legend': param.legend or '',
                'sorting_order': param.sorting_order,
                'parameter_variety': {
                    'id': param.parameter_variety.id,
                    'code': param.parameter_variety.code,
                    'name': param.parameter_variety.name,
                    'description': param.parameter_variety.description,
                    'is_predefined': param.parameter_variety.is_predefined,
                } if param.parameter_variety else None,
            }
            structured_list.append(param_data)

        return structured_list