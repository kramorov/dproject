# filter_regulator/models/fr_model_line_item.py
from typing import Dict, List, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin
from core.models.mixins import CopyMixin, TemplateMixin, CatalogDictMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, FilterDefinition, FilterType, DataSourceType
from filter_regulator.models import FilterRegulatorBody
from filter_regulator.models.fr_model_line import FilterRegulatorModelLine
from filter_regulator.models.fr_options import FilterRegulatorVariety, DrainVariety
from sku.models import SKUMixin


class FilterRegulator(
    CatalogDictMixin,
    CopyMixin,
    ImageGalleryMixin,
    TechDocMixin,
    SmartCatalogMixin,
    TemplateMixin,
    SKUMixin,
    models.Model,
):
    """Модель фильтр-регулятора (каталог)"""
    name = models.TextField(blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название модели фильтр-регулятора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели фильтр-регулятора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели фильтр-регулятора'))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    GAUGE_CHOICES = [
        (0, _('Без манометра')),
        (1, _('1 манометр в комплекте')),
        (2, _('2 манометра в комплекте')),
    ]
    gauge_quantity = models.IntegerField(
        choices=GAUGE_CHOICES,
        default=1,
        verbose_name=_("Комплектация манометром")
    )

    model_line = models.ForeignKey(FilterRegulatorModelLine, related_name='filter_model_line',
                                   blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия модели фильтр-регулятора'),
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(FilterRegulatorBody, related_name='filter_body',
                             blank=True,
                             null=True,
                             on_delete=models.SET_NULL,
                             help_text=_('Корпус фильтр-регулятора'),
                             verbose_name=_("Корпус"))

    ip = models.ForeignKey('params.IpOption', related_name='filter_regulator_ip',
                           blank=True, null=True,
                           on_delete=models.SET_NULL,
                           verbose_name=_("Степень защиты IP"))

    body_material = models.ForeignKey('materials.MaterialGeneral',
                                      related_name='filter_regulator_body_material',
                                      blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      verbose_name=_('Материал корпуса'))

    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    filtration_rating = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("Тонкость фильтрации (мкм)")
    )
    MATERIAL_CHOICES = [
        ('bronze', 'Спеченная бронза'),
        ('plastic', 'Пористый полимер'),
        ('ss', 'Нержавеющая сетка'),
    ]
    filter_element_material = models.CharField(max_length=20, choices=MATERIAL_CHOICES,
                                               verbose_name=_("Материал фильтрующего элемента"))

    flow_rate = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. расход (л/мин)")
    )
    WALL_MOUNTING_CHOICES = [
        ('no', 'Нет'),
        ('yes', 'В комплекте'),
    ]
    wall_mounting_included = models.CharField(max_length=20, choices=WALL_MOUNTING_CHOICES, default='yes',
                                              verbose_name=_("Настенное крепление в комплекте"))
    has_shut_off_valve = models.BooleanField(default=False, verbose_name=_("Отсечной клапан в комплекте"))

    drain_variety = models.ForeignKey(DrainVariety, related_name='filter_drain_variety',
                                      blank=True, null=True,
                                      on_delete=models.SET_NULL,
                                      verbose_name=_("Слив"))

    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Фильтр-регулятор")
        verbose_name_plural = _("Фильтр-регуляторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name} ({self.code})"

    # ── SKUMixin ──

    def get_equipment_type_for_sku(self):
        """Тип оборудования для SKU — берётся из model_line."""
        return self.model_line.equipment_type

    def get_brand_for_sku(self):
        """Бренд для SKU — берётся из model_line."""
        return self.model_line.brand

    def save(self, *args, **kwargs):
        """
        Сохраняет модель и синхронизирует номенклатуру (SKU).

        Вызывает ``sync_sku()`` после сохранения — создаёт новую SKU
        или «подхватывает» существующую по коду, обогащая её полями модели.
        """
        super().save(*args, **kwargs)
        self.sync_sku()

    def copy(self):
        return super().copy(suffix=" Копия", reset_fields=[])

    @property
    def gauge_quantity_display(self):
        return self.get_gauge_quantity_display()

    @property
    def wall_mounting_included_display(self):
        return self.get_wall_mounting_included_display()

    # ── TemplateMixin helpers ──

    def _get_data_dict(self) -> Dict[str, str]:
        """Словарь плейсхолдер → dotted-путь для TemplateMixin."""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{flow_rate}': 'flow_rate',
            '{filter_variety}': 'model_line__filter_variety',
            '{pressure_min}': 'pressure_min',
            '{pressure_max}': 'pressure_max',
            '{pressure_inlet_max}': 'pressure_inlet_max',
            '{wall_mounting_included}': 'wall_mounting_included_display',
            '{body_material}': 'get_body_material_description',
            '{bowl_material}': 'get_bowl_material_description',
            '{protection_material}': 'get_protection_material_description',
            '{filter_element_material}': 'filter_element_material',
            '{filtration_rating}': 'filtration_rating',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{weight}': 'body__weight',
            '{thread}': 'body__thread',
            '{gauge_port_size}': 'body__gauge_port_size',
            '{drain_port_size}': 'body__drain_port_size',
            '{drain_variety}': 'drain_variety',
            '{gauge_quantity}': 'gauge_quantity_display',
        }

    def _get_name_template_source(self):
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        return (
            "{model_code} {filter_variety} {brand}; "
            "Расход {flow_rate} л/мин; {drain_variety}; "
            "Т.окр. {work_temp_min}..{work_temp_max} °С, "
            "Рег.давления {pressure_min}..{pressure_max} бар; "
            "Порты: {thread}; фильтрация {filtration_rating} мкм;"
        )

    def _get_default_description_template(self) -> str:
        return (
            "{model_code} {filter_variety} {brand}; "
            "Расход {flow_rate} л/мин; {drain_variety}; "
            "Т.окр. {work_temp_min}..{work_temp_max} °С, "
            "Материал корпуса: {body_material}, "
            "Материал стакана: {bowl_material_text}, "
            "Кожух: {protection_material} "
            "Порты: {thread}; слив: {drain_port_size}; "
            "{gauge_quantity}; фильтрация {filtration_rating} мкм; "
            "Диапазон регулировки давления {pressure_min}..{pressure_max} бар; "
            "Макс. входное давление {pressure_inlet_max} бар; "
            "вес {weight}кг. "
            "Настенное крепление: {wall_mounting_included}"
        )

    # ── CatalogDictMixin helpers ──

    def _get_image_url(self, img):
        return CatalogDictMixin._get_image_url(self, img)

    def _get_file_info(self, doc):
        if not doc:
            return None
        try:
            from django.conf import settings
            has_email = doc.variants.filter(role='email').exists()
            return {
                'id': doc.id,
                'name': getattr(doc, 'name', '') or '',
                'url': f"/api/media/{doc.id}/download/",
                'file_name': getattr(doc, 'file_name', '') or '',
                'preview_url': f"/api/media/{doc.id}/view/",
                'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
            }
        except Exception:
            return None

    def _get_image_alt(self) -> str:
        parts = []
        if self.model_line and self.model_line.filter_variety:
            parts.append(self.model_line.filter_variety.name)
        if self.code:
            parts.append(self.code)
        return ' '.join(parts) or self.name or ''

    def _get_template_vars(self) -> dict:
        body = self.body
        ml = self.model_line
        return {
            'code': self.code or '',
            'name': self.name or '',
            'model_line_name': ml.name if ml else '',
            'brand_name': ml.brand.name if ml and ml.brand else '',
            'filter_variety': ml.filter_variety.name if ml and ml.filter_variety else '',
            'body_material': ml.body_material_text if ml and ml.body_material_text else '',
            'bowl_material': ml.bowl_material_text if ml and ml.bowl_material_text else '',
            'protection_material': ml.protection_material if ml and ml.protection_material else '',
            'ip': self.ip.name if self.ip else '',
            'work_temp': f"{self.work_temp_min}...+{self.work_temp_max} °С" if self.work_temp_min is not None else '',
            'pressure_range': f"{ml.pressure_min}...{ml.pressure_max}" if ml and ml.pressure_min is not None else '',
            'pressure_inlet_max': str(ml.pressure_inlet_max) if ml and ml.pressure_inlet_max else '',
            'weight': str(body.weight) if body and body.weight else '',
            'thread': body.thread.name if body and body.thread else '',
            'gauge_port_size': body.gauge_port_size.name if body and body.gauge_port_size else '',
            'drain_port_size': body.drain_port_size.name if body and body.drain_port_size else '',
            'filtration_rating': str(self.filtration_rating) if self.filtration_rating else '',
            'flow_rate': str(self.flow_rate) if self.flow_rate else '',
            'filter_element_material': self.get_filter_element_material_display() if self.filter_element_material else '',
            'wall_mounting_included': self.get_wall_mounting_included_display() if self.wall_mounting_included else '',
            'has_shut_off_valve': 'Да' if self.has_shut_off_valve else 'Нет',
        }

    def _get_docs_section(self) -> list:
        docs = []
        for doc in self.tech_docs.all():
            info = self._get_file_info(doc)
            if info:
                docs.append(info)
        if self.model_line and hasattr(self.model_line, 'tech_docs'):
            for doc in self.model_line.tech_docs.all():
                info = self._get_file_info(doc)
                if info and not any(d['id'] == info['id'] for d in docs):
                    docs.append(info)
        return docs

    def _get_model_line_summary(self) -> dict:
        if not self.model_line:
            return None
        ml = self.model_line
        return {
            'id': ml.id,
            'name': ml.name,
            'code': getattr(ml, 'code', '') or '',
            'filter_variety': ml.filter_variety.name if ml.filter_variety else None,
            'brand': {
                'id': ml.brand.id,
                'name': ml.brand.name,
            } if ml.brand else None,
        }

    def _get_sku_summary(self) -> dict:
        if not hasattr(self, 'sku') or not self.sku:
            return None
        return {
            'id': self.sku.id,
            'code': self.sku.code,
            'name': self.sku.name,
        }


    def _get_certs_section(self) -> list:
        """Секция сертификатов (из model_line.cert_docs)."""
        certs = []
        if not (self.model_line and hasattr(self.model_line, 'cert_docs')):
            return certs

        for cert in self.model_line.cert_docs.all():
            from django.conf import settings
            base = getattr(settings, 'MEDIA_API_BASE', 'http://localhost:8000')
            try:
                title = getattr(cert, 'name', '') or ''
                code = getattr(cert, 'code', '') or ''
                media = getattr(cert, 'media_item', None)
                if not media:
                    continue

                certs.append({
                    'id': cert.id,
                    'title': title,
                    'file_name': code,
                    'url': f"{base}/api/media/{media.id}/download/",
                })
            except Exception:
                continue
        return certs

    def to_dict(self) -> dict:
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'description': self.description or '',
            'image_alt': self._get_image_alt(),
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
            'template_vars': tv,
            'sections': [
                {
                    'key': 'images',
                    'title': 'Изображения',
                    'type': 'gallery',
                    'order': 1,
                    'data': self._get_images_section(),
                },
                {
                    'key': 'specs',
                    'title': 'Характеристики',
                    'type': 'specs',
                    'order': 2,
                    'groups': [
                        {
                            'key': 'general',
                            'title': 'Основные',
                            'order': 1,
                            'fields': [
                                {'key': 'model_line_name', 'label': 'Серия', 'value': tv['model_line_name'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'brand_name', 'label': 'Бренд', 'value': tv['brand_name'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'filter_variety', 'label': 'Тип', 'value': tv['filter_variety'], 'unit': '', 'type': 'text', 'order': 3},
                                {'key': 'body_material', 'label': 'Материал корпуса', 'value': tv['body_material'], 'unit': '', 'type': 'text', 'order': 4},
                                {'key': 'bowl_material', 'label': 'Материал стакана', 'value': tv['bowl_material'], 'unit': '', 'type': 'text', 'order': 5},
                                {'key': 'protection_material', 'label': 'Материал кожуха', 'value': tv['protection_material'], 'unit': '', 'type': 'text', 'order': 6},
                                {'key': 'ip', 'label': 'IP', 'value': tv['ip'], 'unit': '', 'type': 'text', 'order': 7},
                                {'key': 'filtration_rating', 'label': 'Тонкость фильтрации', 'value': tv['filtration_rating'], 'unit': 'мкм', 'type': 'number', 'order': 8},
                                {'key': 'flow_rate', 'label': 'Расход', 'value': tv['flow_rate'], 'unit': 'л/мин', 'type': 'number', 'order': 9},
                                {'key': 'filter_element_material', 'label': 'Фильтрующий элемент', 'value': tv['filter_element_material'], 'unit': '', 'type': 'text', 'order': 10},
                            ]
                        },
                        {
                            'key': 'pressure',
                            'title': 'Давление',
                            'order': 2,
                            'fields': [
                                {'key': 'pressure_range', 'label': 'Диапазон выходного давления', 'value': tv['pressure_range'], 'unit': 'бар', 'type': 'text', 'order': 1},
                                {'key': 'pressure_inlet_max', 'label': 'Макс. входное давление', 'value': tv['pressure_inlet_max'], 'unit': 'бар', 'type': 'number', 'order': 2},
                            ]
                        },
                        {
                            'key': 'body_specs',
                            'title': 'Корпус',
                            'order': 3,
                            'fields': [
                                {'key': 'weight', 'label': 'Вес', 'value': tv['weight'], 'unit': 'кг', 'type': 'number', 'order': 1},
                                {'key': 'thread', 'label': 'Резьба портов', 'value': tv['thread'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'gauge_port_size', 'label': 'Резьба манометра', 'value': tv['gauge_port_size'], 'unit': '', 'type': 'text', 'order': 3},
                                {'key': 'drain_port_size', 'label': 'Резьба слива', 'value': tv['drain_port_size'], 'unit': '', 'type': 'text', 'order': 4},
                                {'key': 'wall_mounting_included', 'label': 'Настенное крепление', 'value': tv['wall_mounting_included'], 'unit': '', 'type': 'text', 'order': 5},
                                {'key': 'has_shut_off_valve', 'label': 'Отсечной клапан', 'value': tv['has_shut_off_valve'], 'unit': '', 'type': 'text', 'order': 6},
                            ]
                        },
                        {
                            'key': 'conditions',
                            'title': 'Условия эксплуатации',
                            'order': 4,
                            'fields': [
                                {'key': 'work_temp', 'label': 'Рабочая температура', 'value': tv['work_temp'], 'unit': '', 'type': 'text', 'order': 1},
                            ]
                        },
                    ]
                },
                {
                    'key': 'docs',
                    'title': 'Документация',
                    'type': 'files',
                    'order': 3,
                    'data': self._get_docs_section(),
                },
                {
                    'key': 'certs',
                    'title': 'Сертификаты',
                    'type': 'files',
                    'order': 4,
                    'data': self._get_certs_section(),
                },
                {
                    'key': 'description',
                    'title': 'Описание',
                    'type': 'text',
                    'order': 4,
                    'data': self.description or '',
                },
            ],
        }

    def to_values_dict(self) -> dict:
        first_img = self._get_first_image()
        tv = {'code': self.code or '', 'name': self.name or ''}
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'image_alt': self._get_image_alt(),
            'template_vars': tv,
            'values': tv,
            'images': [first_img] if first_img else [],
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
        }