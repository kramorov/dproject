# cable_glands/models/cg_actual.py
"""Артикул каталога «кабельный ввод» — CableGland.

Состав: серия (CableGlandModelLine) + «модель в серии»
(CableGlandModelLineItem: корпус/металлорукав/вес) + выбранные резьба (thread)
и материал корпуса (body_material). Общие характеристики (IP, взрывозащита,
температуры, флаги кабеля, бренд) живут на серии и доступны путями model_line__*.

Контракт каталога (template_mixin.md):
- реестр полей — cable_glands/models/cg_item_fields.py (CG_ITEM_TEMPLATE_FIELDS);
- name/description генерируются из шаблонов серии (TemplateMixin.save());
- артикул (code) автогенерируется из model_line.model_item_code_template,
  если не задан вручную (encodings — из CODE_FIELD_KEYS реестра);
- серия денормализуется из model_line_item в save();
- SKU создаётся автоматически (SKUMixin.sync_sku()).
"""

import re

from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict

from core.models import ImageGalleryMixin, TechDocMixin
from core.models.mixins import TemplateMixin, CopyMixin
from core.models.catalog_serializer import CatalogSerializerMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin
from sku.models import SKUMixin

from params.models import ThreadSize

from .cg_item_fields import CG_ITEM_TEMPLATE_FIELDS


class CableGland(CatalogSerializerMixin, SmartCatalogMixin, TemplateMixin,
                 CopyMixin, ImageGalleryMixin, TechDocMixin, SKUMixin,
                 models.Model):
    """Артикул каталога — конкретный кабельный ввод (единица продажи).

    Третий уровень иерархии (подробности — в докстринге модуля и серии):

        CableGlandModelLine (серия)
          └─ CableGlandModelLineItem (корпус + крепление МР + вес)
               └─ CableGland        ← эта модель

    Артикул фиксирует КОНФИГУРАЦИЮ: «модель в серии» (model_line_item),
    выбранную резьбу (thread → params.ThreadSize) и материал корпуса
    (body_material → CableGlandBodyMaterial). Общие характеристики (IP, exd,
    температуры, флаги кабеля, бренд, equipment_type) артикул наследует от
    серии через прямой FK model_line (денормализуется из model_line_item
    в save()).

    Поведение (контракт каталога, template_mixin.md):
      * name/description — автогенерация из шаблонов серии (TemplateMixin),
        словари подстановок — из реестра TEMPLATE_FIELDS (cg_item_fields.py);
      * code — автогенерация из model_item_code_template серии (если пуст),
        уникален (unique=True);
      * SKU — автоматически через SKUMixin.sync_sku() в save()
        (equipment_type/brand — из серии);
      * сериализация каталога — CatalogSerializerMixin (to_dict/to_values_dict,
        секции images/specs/docs/certs/description), SmartCatalogMixin —
        декларативные фильтры для будущего поиска;
      * копирование — CopyMixin/AdminCopyMixin (sku сбрасывается, M2M tech_docs
        копируются).
    """

    # ── Реестр полей (единый источник правды) — cg_item_fields.py ──
    TEMPLATE_FIELDS = CG_ITEM_TEMPLATE_FIELDS

    required_model_line_fields = (
        'name_template', 'description_template', 'model_item_code_template',
    )

    # Составы словарей (по ключам реестра).
    NAME_FIELD_KEYS = (
        'code', 'brand_name', 'size', 'thread', 'body_material',
        'cable_diameter', 'weight', 'ip', 'exd', 'temp_range', 'flags',
    )

    CODE_FIELD_KEYS = (
        'code', 'size', 'thread', 'body_material',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name', 'size', 'thread',
        'body_material', 'cable_diameter', 'weight', 'ip', 'exd',
        'temp_range', 'flags',
    )

    SPEC_FIELD_KEYS = (
        'model_line_name', 'brand_name', 'size', 'ip', 'exd',
        'thread', 'body_material', 'cable_diameter', 'weight',
        'temp_range', 'flags',
    )

    SPEC_GROUP_TITLES = {
        'general': 'Основные',
        'body': 'Корпус',
        'conditions': 'Условия эксплуатации',
    }

    name = models.TextField(blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Название модели кабельного ввода (генерируется из шаблона серии)'))
    code = models.CharField(max_length=150, blank=True, null=True, unique=True,
                            verbose_name=_("Код"),
                            help_text=_('Код артикула (автогенерируется из шаблона серии, если пуст); уникален'))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели кабельного ввода (генерируется из шаблона серии)'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line_item = models.ForeignKey(
        'CableGlandModelLineItem',
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='cable_gland_model_line', help_text=_('Модель в серии (корпус/металлорукав/вес)'))

    model_line = models.ForeignKey(
        'CableGlandModelLine',
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='cable_gland_articles',
        verbose_name=_("Серия"),
        help_text=_('Серия кабельных вводов (источник шаблонов названия/описания/артикула)'))

    body_material = models.ForeignKey(
        'CableGlandBodyMaterial', blank=True, null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Материал корпуса"),
        help_text=_('Материал корпуса'))
    thread = models.ForeignKey(
        ThreadSize, blank=True, null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Резьба"),
        help_text=_('Резьба'))

    class Meta:
        verbose_name = _("Кабельный ввод")
        verbose_name_plural = _("Кабельные вводы")
        ordering = ['sorting_order']

    def save(self, *args, **kwargs):
        # Серия (источник шаблонов) денормализуется из «модели в серии».
        if not self.model_line_id and self.model_line_item_id:
            self.model_line = self.model_line_item.model_line
        # Артикул автогенерируется из model_line.model_item_code_template,
        # если не задан вручную (pattern Posi/электроприводов).
        if not self.code:
            self.code = self.generated_model_item_code or None
        super().save(*args, **kwargs)   # цепочка → TemplateMixin.save(): генерация name/description
        self.sync_sku()

    # ── Защита от «родовых» имён: без кода и без шаблона серии не
    #    перезаписываем введённое вручную имя/описание. ──
    def update_name(self, save: bool = False) -> bool:
        if not self.code and not self._get_name_template_source():
            return False
        return super().update_name(save=save)

    def update_description(self, save: bool = False) -> bool:
        if not self.code and not self._get_description_template_source():
            return False
        return super().update_description(save=save)

    # ── TemplateMixin: шаблоны — из серии (CableGlandModelLine) ──

    def _get_name_template_source(self):
        if not self.model_line:
            return None
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        if not self.model_line:
            return None
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        return "{model_code} Кабельный ввод {brand}"

    def _get_default_description_template(self) -> str:
        return "{model_code} Кабельный ввод {brand}"

    # ── Артикул: рендер model_item_code_template (encodings из реестра) ──

    @property
    def generated_model_item_code(self) -> str:
        """Артикул по шаблону серии; пустые сегменты схлопываются."""
        template = getattr(self.model_line, 'model_item_code_template', None) if self.model_line else None
        if not template or not template.strip():
            return self._generate_fallback_code()
        result = self._fill_template(template, self._get_code_data_dict())
        result = re.sub(r'\.{2,}', '.', result)
        result = re.sub(r'\.\s+', ' ', result)
        return result.strip('. ')

    def _generate_fallback_code(self) -> str:
        parts = [
            self.model_line.code if self.model_line else None,
            self.model_line_item.code if self.model_line_item else None,
            self.thread.code if self.thread else None,
            self.body_material.code if self.body_material else None,
        ]
        return '.'.join(p for p in parts if p)

    # ── Display-свойства для шаблонов и секций каталога ──

    @property
    def get_exd_display(self) -> str:
        """Взрывозащита серии из through-строки (CableGlandExdOption) — через ' / '."""
        if not self.model_line_id:
            return ''
        from .cg_exd_option import CableGlandExdOption
        try:
            row = CableGlandExdOption.get_effective_row(parent_id=self.model_line_id)
        except Exception:
            return ''
        if row is None:
            return ''
        items = []
        for x in row.exd_options.all():
            items.append(x.code or x.name or x.description or str(x))
        return ' / '.join(items)

    @property
    def get_cable_diameter_display(self) -> str:
        """Диаметр обжимаемого кабеля из корпуса «модели в серии»."""
        mli = self.model_line_item
        if not mli or not mli.body_id:
            return ''
        b = mli.body
        parts = []
        if b.cable_diameter_inner_min:
            parts.append(str(b.cable_diameter_inner_min).rstrip('0').rstrip('.'))
        if b.cable_diameter_inner_max:
            parts.append(str(b.cable_diameter_inner_max).rstrip('0').rstrip('.'))
        return '…'.join(parts)

    @property
    def get_temp_range_display(self) -> str:
        """Диапазон температур из серии (заполненные границы)."""
        ml = self.model_line
        if not ml:
            return ''
        parts = []
        if ml.temp_min is not None:
            parts.append(str(ml.temp_min))
        if ml.temp_max is not None:
            parts.append(str(ml.temp_max))
        return '…'.join(parts)

    @property
    def get_cable_flags_display(self) -> str:
        """Тип кабеля по флагам серии."""
        ml = self.model_line
        if not ml:
            return ''
        parts = []
        if ml.for_armored_cable:
            parts.append(_('бронированный кабель'))
        if ml.for_metal_sleeve_cable:
            parts.append(_('металлорукав'))
        if ml.for_pipelines_cable:
            parts.append(_('трубопровод'))
        return ', '.join(parts)

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — из серии."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — из серии."""
        return self.model_line.brand if self.model_line else None

    def __str__(self):
        return self.name
