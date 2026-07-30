# core/models/selection_wizard.py
"""
Мастер подбора (Selection Wizard) — пошаговый конфигуратор фильтров.

Хранит JSON-конфигурацию шагов и фильтров. Подчинён EquipmentType.
Фильтры ссылаются на FILTER_DEFINITIONS модели оборудования по param_name.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseAbstractModel


class SelectionWizard(BaseAbstractModel):
    """
    Мастер подбора оборудования.

    steps_json — JSON из двух частей:
    {
        "pages": [
            {"step_number": 1, "title": "Заголовок шага", "description": "Описание"},
            ...
        ],
        "filters": [
            {
                "param_name": "sensor_variety_id",
                "page": 1,
                "order": 1,
                "label": "Тип сенсора",
                "default_value": null
            },
            ...
        ]
    }
    """

    equipment_type = models.ForeignKey(
        'core.EquipmentType',
        on_delete=models.CASCADE,
        related_name='selection_wizards',
        verbose_name=_("Тип оборудования"),
        help_text=_("Тип оборудования, для которого создан мастер подбора")
    )

    steps_json = models.JSONField(
        default=dict,
        verbose_name=_("Шаги мастера (JSON)"),
        help_text=_(
            'JSON-конфигурация: {"pages": [...], "filters": [...]}. '
            'pages: step_number, title, description. '
            'filters: param_name, page (номер шага), order, label, default_value.'
        )
    )

    class Meta:
        db_table = 'core_selectionwizard'
        verbose_name = _("Мастер подбора")
        verbose_name_plural = _("Мастера подбора")
        ordering = ['sorting_order', 'name']

    def get_steps(self) -> list:
        """Вернуть список шагов мастера, отсортированных по step_number."""
        data = self.steps_json or {}
        pages = data.get('pages', [])
        filters = data.get('filters', [])

        # Группируем фильтры по step_number
        from collections import defaultdict
        filters_by_page = defaultdict(list)
        for f in filters:
            filters_by_page[f.get('page', 1)].append(f)

        # Сортируем внутри каждой страницы по order
        for page_num in filters_by_page:
            filters_by_page[page_num].sort(key=lambda x: x.get('order', 0))

        steps = []
        for page in sorted(pages, key=lambda p: p.get('step_number', 0)):
            step_num = page.get('step_number', 0)
            steps.append({
                'step_number': step_num,
                'title': page.get('title', ''),
                'description': page.get('description', ''),
                'filters': filters_by_page.get(step_num, []),
            })
        return steps

    def __str__(self):
        et_name = self.equipment_type.name if self.equipment_type else '?'
        return f"{self.name or 'Мастер'} ({et_name})"
