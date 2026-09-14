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
        'code', 'brand_name', 'thread', 'body_material',
        'cable_diameter','cable_diameter_outer', 'weight', 'metal_sleeve_body_code',
        'metal_sleeve_inner', 'metal_sleeve_outer', 'metal_sleeve_range', 'metal_sleeve', 'body_code',
        'ip', 'exd', 'exd_short', 'temp_range', 'cable_types', 'extra_params',
    )

    CODE_FIELD_KEYS = (
        'code', 'thread', 'body_material', 'exd',
    )

    VARS_FIELD_KEYS = (
        'code', 'name', 'model_line_name', 'brand_name', 'thread',
        'body_material', 'cable_diameter', 'cable_diameter_outer','weight',
        'metal_sleeve_body_code', 'metal_sleeve_inner', 'metal_sleeve_outer',
        'metal_sleeve_range', 'metal_sleeve', 'body_code',
        'ip', 'exd', 'exd_short', 'temp_range', 'cable_types', 'extra_params',
    )

    # SPEC_FIELD_KEYS закомментирован: спецификация задаётся spec_template
    # (model_line → EquipmentType), фоллбэк — {model_code}.
    # SPEC_FIELD_KEYS = (
    #     'model_line_name', 'brand_name', 'ip', 'exd', 'exd_short',
    #     'thread', 'body_material', 'cable_diameter','cable_diameter_outer', 'weight',
    #     'metal_sleeve_body_code', 'metal_sleeve_inner', 'metal_sleeve_outer',
    #     'metal_sleeve_range', 'metal_sleeve', #'body_code',
    #     'temp_range', 'cable_types', 'extra_params',
    # )

    # SPEC_GROUP_TITLES закомментирован: названия групп задаются в spec_template (JSON).
    # SPEC_GROUP_TITLES = {
    #     'general': 'Основные',
    #     'body': 'Присоединения',
    #     'conditions': 'Условия эксплуатации',
    #     'extra': 'Дополнительно',
    # }

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

    # ── Выбранные опции через through-строки (источник encoding) ──
    thread_option = models.ForeignKey(
        'CableGlandThreadOption', blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='cable_gland_thread_articles',
        verbose_name=_("Опция резьбы"),
        help_text=_('Выбранная опция резьбы корпуса (through-строка)'))
    body_material_option = models.ForeignKey(
        'CableGlandBodyMaterialOption', blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='cable_gland_body_material_articles',
        verbose_name=_("Опция материала корпуса"),
        help_text=_('Выбранная опция материала корпуса (through-строка)'))
    exd_option = models.ForeignKey(
        'CableGlandExdOption', blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='cable_gland_exd_articles',
        verbose_name=_("Опция взрывозащиты"),
        help_text=_('Выбранная опция взрывозащиты серии; пусто — наследуется дефолт серии'))

    class Meta:
        verbose_name = _("Кабельный ввод")
        verbose_name_plural = _("Кабельные вводы")
        ordering = ['sorting_order']

    def save(self, *args, **kwargs):
        # Серия (источник шаблонов) денормализуется из «модели в серии».
        if not self.model_line_id and self.model_line_item_id:
            self.model_line = self.model_line_item.model_line
        self._validate_option_consistency()
        # Артикул автогенерируется из model_line.model_item_code_template,
        # если не задан вручную (pattern Posi/электроприводов).
        if not self.code:
            self.code = self.generated_model_item_code or None

        # Дедупликация: сочетание (модель + резьба + материал + взрывозащита)
        # — идентичность артикула. При создании дубля патчим существующую
        # строку, а не создаём новую.
        if self._state.adding:
            existing = self._get_duplicate()
            if existing is not None:
                self.pk = existing.pk
                self._state.adding = False

        super().save(*args, **kwargs)   # цепочка → TemplateMixin.save(): генерация name/description
        self.sync_sku()

    def _get_duplicate(self):
        """Существующий артикул с тем же сочетанием (модель + опции)."""
        if not self.model_line_item_id:
            return None
        qs = self.__class__.objects.filter(
            model_line_item_id=self.model_line_item_id,
            thread_option_id=self.thread_option_id,
            body_material_option_id=self.body_material_option_id,
            exd_option_id=self.exd_option_id,
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs.first()

    def clean(self):
        """Консистентность выбранных through-строк с корпусом/серией (для форм)."""
        self._validate_option_consistency()

    def _validate_option_consistency(self):
        """Консистентность выбранных through-строк с корпусом/серией.

        Вызывается и в clean() (админ-формы), и в save() — чтобы прямой
        программный save() тоже не пропускал невалидную комбинацию.
        """
        from django.core.exceptions import ValidationError
        errors = {}
        mli = self.model_line_item
        if self.thread_option_id and mli and mli.body_id:
            try:
                if self.thread_option.cable_gland_body_id != mli.body_id:
                    errors['thread_option'] = _('Резьба относится к другому корпусу.')
            except Exception:
                pass
        if self.body_material_option_id and self.model_line_id:
            try:
                if self.body_material_option.model_line_id != self.model_line_id:
                    errors['body_material_option'] = _('Материал относится к другой серии.')
            except Exception:
                pass
        if self.exd_option_id and self.model_line_id:
            try:
                if self.exd_option.model_line_id != self.model_line_id:
                    errors['exd_option'] = _('Взрывозащита относится к другой серии.')
            except Exception:
                pass
        if errors:
            raise ValidationError(errors)

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

    def _get_title_template_source(self):
        """Шаблон заголовка карточки — из серии (title_template)."""
        if not self.model_line:
            return None
        return getattr(self.model_line, 'title_template', None) or None

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
            self.model_line_item.code if self.model_line_item else None,
            self.thread_encoding or None,
            self.body_material_encoding or None,
        ]
        return '.'.join(p for p in parts if p)

    # ── Display-свойства для шаблонов и секций каталога ──

    def _get_effective_exd_row(self):
        """Эффективная through-строка взрывозащиты: выбранная (exd_option) или дефолт серии."""
        row = self.exd_option
        if row is None and self.model_line_id:
            from .cg_exd_option import CableGlandExdOption
            try:
                row = CableGlandExdOption.get_effective_row(parent_id=self.model_line_id)
            except Exception:
                row = None
        return row

    @property
    def get_exd_display(self) -> str:
        """Взрывозащита: список из полей name опций (через ' / ')."""
        row = self._get_effective_exd_row()
        if row is None:
            return ''
        items = []
        for x in row.exd_options.all():
            items.append(x.name or x.code or x.description or str(x))
        return ' / '.join(items)

    @property
    def get_exd_short_list(self) -> str:
        """Короткий список видов взрывозащиты: «Ex db / Ex ta / Ex eb / Ex nR» (паттерн позиционеров)."""
        row = self._get_effective_exd_row()
        return row.get_exd_short_list if row else ''

    @property
    def exd_encoding(self) -> str:
        """Encoding взрывозащиты: выбранная through-строка или дефолт серии."""
        row = self._get_effective_exd_row()
        return row.encoding if (row and row.encoding) else ''

    @property
    def thread_encoding(self) -> str:
        """Encoding резьбы — напрямую из выбранной through-строки."""
        return self.thread_option.encoding if (self.thread_option and self.thread_option.encoding) else ''

    @property
    def body_material_encoding(self) -> str:
        """Encoding материала корпуса — напрямую из выбранной through-строки."""
        return self.body_material_option.encoding if (self.body_material_option and self.body_material_option.encoding) else ''

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
    def get_outer_cable_diameter_display(self) -> str:
        """Диаметр внешний (по броне) обжимаемого кабеля из «модели в серии»."""
        mli = self.model_line_item
        if not mli:
            return ''
        parts = []
        if mli.cable_diameter_outer_min:
            parts.append(str(mli.cable_diameter_outer_min).rstrip('0').rstrip('.'))
        if mli.cable_diameter_outer_max:
            parts.append(str(mli.cable_diameter_outer_max).rstrip('0').rstrip('.'))
        return '…'.join(parts)
        
    @property
    def get_inner_min_cable_diameter_display(self) -> str:
        """Диаметр обжимаемого кабеля из корпуса «модели в серии»."""
        mli = self.model_line_item
        if not mli or not mli.body_id:
            return ''
        return str(mli.body.cable_diameter_inner_min).rstrip('0').rstrip('.') if mli.body.cable_diameter_inner_min else ''
    @property
    def get_inner_max_cable_diameter_display(self) -> str:
        """Диаметр обжимаемого кабеля из корпуса «модели в серии»."""
        mli = self.model_line_item
        if not mli or not mli.body_id:
            return ''
        return str(mli.body.cable_diameter_inner_max).rstrip('0').rstrip('.') if mli.body.cable_diameter_inner_max else ''        
        

    @property
    def get_outer_min_cable_diameter_display(self) -> str:
        """Диаметр обжимаемого кабеля из корпуса «модели в серии»."""
        mli = self.model_line_item
        if not mli:
            return ''
        return str(mli.cable_diameter_outer_min).rstrip('0').rstrip('.') if mli.cable_diameter_outer_min else ''
        
    @property
    def get_outer_max_cable_diameter_display(self) -> str:
        """Диаметр обжимаемого кабеля из «модели в серии»."""
        mli = self.model_line_item
        if not mli:
            return ''
        return str(mli.cable_diameter_outer_max).rstrip('0').rstrip('.') if mli.cable_diameter_outer_max else ''

    @property
    def get_metal_sleeve_display(self) -> str:
        """Список совместимых металлорукавов из крепления МР (пусто, если крепление не привязано)."""
        mli = self.model_line_item
        if not mli or not mli.metal_sleeve_body_id:
            return ''
        sleeves = mli.metal_sleeve_body.metal_sleeve.all()
        if not sleeves:
            return ''
        return ' / '.join(str(s) for s in sleeves)

    @property
    def get_metal_sleeve_range_display(self) -> str:
        """Диапазон внутр./внеш. ⌀ металлорукава из крепления МР (пусто, если крепление не привязано)."""
        mli = self.model_line_item
        if not mli or not mli.metal_sleeve_body_id:
            return ''
        body = mli.metal_sleeve_body
        parts = []
        if body.metal_sleeve_inner:
            parts.append(str(body.metal_sleeve_inner).rstrip('0').rstrip('.'))
        if body.metal_sleeve_outer:
            parts.append(str(body.metal_sleeve_outer).rstrip('0').rstrip('.'))
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
    def get_temp_min_display(self) -> str:
        """Мин температура из серии."""
        return str(self.model_line.temp_min) if self.model_line.temp_min is not None else ''
    @property
    def get_temp_max_display(self) -> str:
        """Мин температура из серии."""
        return str(self.model_line.temp_max) if self.model_line.temp_max is not None else ''
        
    @property
    def get_applicable_cable_types_display(self) -> str:
        """Тип кабеля по флагам серии."""
        ml = self.model_line
        if not ml:
            return ''
        parts = []
        if ml.for_armored_cable:
            parts.append(_('для бронированного кабеля'))
        else: 
            parts.append(_('для небронированного кабеля'))
        if ml.for_metal_sleeve_cable:
            parts.append(_('в металлорукаве'))
        if ml.for_pipelines_cable:
            parts.append(_('в трубопроводе'))
        return ' '.join(str(p) for p in parts)

    @property
    def get_extra_params(self) -> str:
        """Дополнительные параметры из extra_params серии (плейсхолдер {extra_params})."""
        ml = self.model_line
        if not ml or not ml.extra_params:
            return ''
        params = ml.extra_params
        if isinstance(params, str):
            import json
            try:
                params = json.loads(params)
            except Exception:
                return ''
        if not isinstance(params, dict):
            return ''
        parts = []
        for key, value in params.items():
            if not value:
                continue
            if isinstance(value, dict):
                name = value.get('name', key)
                val = value.get('value', '')
            else:
                name, val = key, value
            if val:
                parts.append(f"{name}: {val}")
        return '; '.join(parts)

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — из серии."""
        return self.model_line.equipment_type if self.model_line else None

    def get_brand_for_sku(self):
        """Бренд для SKU — из серии."""
        return self.model_line.brand if self.model_line else None

    def __str__(self):
        return self.name
