# gearbox/models/gearbox.py
from typing import Dict, List, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import ImageGalleryMixin, TechDocMixin
from core.models.mixins import CatalogDictMixin, CopyMixin, TemplateMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, DataSourceType, FilterType, FilterDefinition
from materials.models import MaterialGeneral
from params.models import LockingMechanism, IpOption, MountingPlateTypes
from sku.models import SKUMixin


class GearBox(CatalogDictMixin, SmartCatalogMixin, CopyMixin, TemplateMixin, ImageGalleryMixin, TechDocMixin, SKUMixin, models.Model):
    """
    Модель редуктора (каталог).

    Наследует:
    - ``SmartCatalogMixin`` — фильтрация и поиск в каталоге
    - ``CopyMixin`` — копирование через админку
    - ``TemplateMixin`` — генерация названия/описания по шаблону из model_line
    - ``ImageGalleryMixin`` — галерея изображений (поле ``images``)
    - ``TechDocMixin`` — техническая документация (поле ``tech_docs``)
    - ``SKUMixin`` — привязка к номенклатуре (поле ``sku``, автосинхронизация)

    Если у конкретного редуктора нет своих изображений, страница каталога
    подхватывает их из ``GearBoxModelLine.images``.
    """
    name = models.TextField(blank=True,
                            verbose_name=_("Название"),
                            help_text=_('Текстовое название модели редуктора'))
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код модели редуктора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание модели редуктора'))

    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey('gearbox.GearBoxModelLine', related_name='gear_box_model_line',
                                   blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия модели редуктора'),
                                   verbose_name=_("Серия"))

    body = models.ForeignKey(
        'gearbox.GearBoxBody',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Корпус редуктора"),
        help_text=_("Корпус редуктора с писанием свойств")
    )
    # Материал корпуса - для фильтров
    body_material = models.ForeignKey(MaterialGeneral, related_name='gearbox_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))

    body_material_text = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Материал корпуса")
    )

    work_temp_min = models.IntegerField(
        null=True, blank=True, default=-40,
        help_text=_('Минимальная рабочая температура, °С'),
        verbose_name=_('Т раб.мин, °С')
    )
    work_temp_max = models.IntegerField(
        null=True, blank=True, default=120,
        help_text=_('Максимальная рабочая температура, °С'),
        verbose_name=_('Т раб.макс, °С'))

    override_mechanism = models.ForeignKey(
        'OverrideMechanism',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Механизм отключения"),
        help_text=_("Механизм отключения дублера")
    )
    locking_mechanism = models.ForeignKey(
        LockingMechanism,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_("Механизм блокировки"),
        help_text=_("Механизм блокировки дублера/переключателя")
    )
    DECLUTCHABLE_CHOICES = (
        ('yes', _('расцепляемый')),
        ('no', _('не расцепляемый')),
    )

    is_declutchable = models.CharField(
        max_length=3,
        choices=DECLUTCHABLE_CHOICES,
        default='yes',
        verbose_name=_("Расцепляемый (Declutchable)"),
        help_text=_("Можно ли физически отсоединить штурвал от привода")
    )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, blank=True, null=True,
                           related_name='gearbox_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    # Интерлок
    interlock = models.ForeignKey('gearbox.GearBoxInterlock', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='gearbox_interlock',
                                  help_text=_('Модель интерлока'),
                                  verbose_name=_("Модель интерлока")
                                  )
    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True, null=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )

    class Meta:
        verbose_name = _("Редуктор")
        verbose_name_plural = _("Редукторы")
        ordering = ['sorting_order']

    def __str__(self):
        return f"{self.name}"

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

    @property
    def is_declutchable_display(self):
        return dict(self.DECLUTCHABLE_CHOICES).get(self.is_declutchable, '')

    def copy(self):
        """
        Создаёт копию редуктора.

        Переопределяет ``CopyMixin.copy()``: добавляет суффикс « Копия»
        к названию и сбрасывает ``sorting_order`` и ``is_active``.
        Корпус (body) при копировании расшаривается (не клонируется).
        """
        copied_obj = super().copy(suffix=" Копия", reset_fields=['sorting_order', 'is_active'])
        return copied_obj

    def _get_data_dict(self) -> Dict[str, str]:
        """
        Словарь плейсхолдер → путь к атрибуту для шаблонов названия/описания.

        Используется ``TemplateMixin`` для подстановки значений в шаблоны
        ``name_template`` и ``description_template`` из model_line.

        Ключи — плейсхолдеры вида ``{model_code}``, значения — dotted-пути
        к атрибутам модели (поддерживает ``__`` для связанных полей).
        """
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand',
            '{gearbox_output_variety}': 'model_line__gearbox_output_variety',
            '{gearbox_variety}': 'model_line__gearbox_variety',
            '{turn_angle}': 'model_line__turn_angle',
            '{turn_tuning_limit}': 'model_line__turn_tuning_limit',
            '{weight}': 'body__weight',
            '{mechanical_advantage}': 'body__mechanical_advantage',
            '{max_stem_diameter_bottom}': 'body__max_stem_diameter_bottom',
            '{stem_height_bottom}': 'body__stem_height_bottom',
            '{stem_size_bottom}': 'body__stem_size_bottom',
            '{stem_shape_bottom}': 'body__stem_shape_bottom',
            '{mounting_plate_bottom_list_text}': 'body__mounting_plate_bottom_list_text',
            '{stem_height_top}': 'body__stem_height_top',
            '{stem_size_top}': 'body__stem_size_top',
            '{stem_shape_top}': 'body__stem_shape_top',
            '{mounting_plate_top_list_text}': 'body__mounting_plate_top_list_text',
            '{handwheel_diameter}': 'body__handwheel_diameter',
            '{handwheel_force_nominal}': 'body__handwheel_force_nominal',
            '{max_output_torque}': 'body__max_output_torque',
            '{max_input_torque}': 'body__max_input_torque',
            '{efficiency}': 'body__efficiency',
            '{amplification_factor}': 'body__amplification_factor',
            '{reduction_ratio_text}': 'body__reduction_ratio_text',
            '{transmission_variety}': 'body__transmission_variety',
            '{interlock}': 'interlock',
            '{ip}': 'ip',
            '{locking_mechanism}': 'locking_mechanism',
            '{is_declutchable}': 'is_declutchable_display',
            '{override_mechanism}': 'override_mechanism',
            '{body_material_text}': 'body_material_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
        }

    def _get_name_template_source(self):
        """
        Шаблон названия из model_line.

        Переопределяет ``TemplateMixin._get_name_template_source()``.
        Если шаблон не задан — возвращает None (используется стандартное название).
        """
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """
        Шаблон описания из model_line.

        Переопределяет ``TemplateMixin._get_description_template_source()``.
        Если шаблон не задан — возвращает None (используется стандартное описание).
        """
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        """
        Дефолтный шаблон названия (заглушка — для редукторов не используется).

        В реальности название редуктора задаётся шаблоном из model_line,
        этот метод — fallback из TemplateMixin.
        """
        return "{model_code} {brand} {gearbox_variety}"

    def _get_default_description_template(self) -> str:
        """
        Дефолтный шаблон описания (заглушка — для редукторов не используется).

        В реальности описание редуктора задаётся шаблоном из model_line,
        этот метод — fallback из TemplateMixin.
        """
        return "{model_code} {brand} {gearbox_variety} {gearbox_output_variety}"

    # FILTER_DEFINITIONS, M2M_FILTER_CONFIG, SEARCH_FIELDS
    # перенесены в gearbox/services/filters.py

    def _get_image_url(self, img):
        return CatalogDictMixin._get_image_url(self, img)

    def _get_file_info(self, doc):
        """Информация о файле — абсолютный URL для работы на сторонних сайтах."""
        if not doc:
            return None
        try:
            from django.conf import settings
            base = getattr(settings, 'MEDIA_API_BASE', 'http://localhost:8000')
            return {
                'id': doc.id,
                'name': getattr(doc, 'name', '') or '',
                'url': f"{base}/api/media/{doc.id}/download/",
                'file_name': getattr(doc, 'file_name', '') or '',
            }
        except Exception:
            return None

    def _get_image_alt(self) -> str:
        """Alt-текст для изображений."""
        parts = []
        if self.model_line:
            if self.model_line.gearbox_output_variety:
                parts.append(self.model_line.gearbox_output_variety.name)
            if self.model_line.gearbox_variety:
                parts.append(self.model_line.gearbox_variety.name)
        if self.code:
            parts.append(self.code)
        return ' '.join(parts) or self.name or ''

    def _get_template_vars(self) -> Dict[str, str]:
        """
        Единый источник готовых строковых значений для шаблонов и UI.

        ИСПОЛЬЗУЕТСЯ:
        - ``to_dict()`` — поля в ``sections[].groups[].fields[].value``
          берутся отсюда, а не из атрибутов модели напрямую.
          Это гарантирует, что label и value не расходятся.
        - Будущий шаблонизатор описаний (Jinja2) — рендерит через ``template_vars``.

        НЕ ПУТАТЬ с ``_get_data_dict()``:
        - ``_get_data_dict()`` — плейсхолдер → dotted-путь (для TemplateMixin)
        - ``_get_template_vars()`` — ключ → готовая строка (для UI и шаблонов)
        """
        body = self.body
        return {
            'code': self.code or '',
            'name': self.name or '',
            'model_line_name': self.model_line.name if self.model_line else '',
            'brand_name': self.model_line.brand.name if self.model_line and self.model_line.brand else '',
            'body_material': self.body_material_text or '',
            'reduction_ratio': body.reduction_ratio_text if body and body.reduction_ratio_text else '',
            'max_output_torque': str(body.max_output_torque) if body and body.max_output_torque else '',
            'max_input_torque': str(body.max_input_torque) if body and body.max_input_torque else '',
            'weight': str(body.weight) if body and body.weight else '',
            'ip': self.ip.name if self.ip else '',
            'work_temp_min': str(self.work_temp_min) if self.work_temp_min is not None else '',
            'work_temp_max': str(self.work_temp_max) if self.work_temp_max is not None else '',
            'is_declutchable': self.is_declutchable_display or '',
            'override_mechanism': self.override_mechanism.name if self.override_mechanism else '',
            'locking_mechanism': self.locking_mechanism.name if self.locking_mechanism else '',
            'transmission_variety': body.transmission_variety.name if body and body.transmission_variety else '',
            'handwheel_diameter': str(body.handwheel_diameter) if body and body.handwheel_diameter else '',
            'handwheel_force_nominal': str(body.handwheel_force_nominal) if body and body.handwheel_force_nominal else '',
            'interlock': self.interlock.name if self.interlock else '',
            # Составное поле — для секции «Условия эксплуатации» в to_dict()
            'work_temp': (
                f"{self.work_temp_min}...+{self.work_temp_max} °С"
                if self.work_temp_min is not None else ''
            ),
        }

    def _get_docs_section(self) -> list:
        """Секция документов."""
        docs = []
        for doc in self.tech_docs.all():
            info = self._get_file_info(doc)
            if info:
                docs.append(info)
        if self.model_line:
            for doc in self.model_line.tech_docs.all():
                info = self._get_file_info(doc)
                if info and not any(d['id'] == info['id'] for d in docs):
                    docs.append(info)
        return docs

    def _get_certs_section(self) -> list:
        """
        Секция сертификатов.

        CertData имеет поля ``name``, ``code``, ``media_item`` (FK на MediaLibraryItem).
        В отличие от tech_docs (у которых ``title``/``media_file``), здесь
        title = cert.name, file_name = cert.code, url = /api/media/{media_item.id}/download/
        """
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

    def to_dict(self) -> Dict[str, Any]:
        """
        Структурированная сериализация редуктора (CatalogDictMixin).

        ВСЕ значения полей в ``sections[].groups[].fields[].value`` берутся
        из ``_get_template_vars()`` — единого источника строковых значений.
        При добавлении нового поля:
          1. Добавить ключ в ``_get_template_vars()``
          2. Добавить запись в fields[] с тем же key и label

        Возвращает:
            - template_vars — плоский словарь для шаблонов
            - sections — список секций: gallery, specs, docs, certs, description
            - model_line, sku — сводки связанных объектов
        """
        tv = self._get_template_vars()

        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'description': self.description or '',
            'image_alt': self._get_image_alt(),
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,

            # ── Сводки связанных объектов ──
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),

            # ── Плоский словарь для шаблонов ──
            'template_vars': tv,

            # ── Секции ──
            'sections': [
                {
                    'key': 'images',
                    'title': str(_('\u0418\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f')),
                    'type': 'gallery',
                    'order': 1,
                    'data': self._get_images_section(),
                },
                {
                    'key': 'specs',
                    'title': str(_('\u0425\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a\u0438')),
                    'type': 'specs',
                    'order': 2,
                    'groups': [
                        {
                            'key': 'general',
                            'title': str(_('\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435')),
                            'order': 1,
                            'fields': [
                                # Все value — из tv, не из self.xxx напрямую
                                {'key': 'model_line_name', 'label': str(_('\u0421\u0435\u0440\u0438\u044f')), 'value': tv['model_line_name'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'brand_name', 'label': str(_('\u0411\u0440\u0435\u043d\u0434')), 'value': tv['brand_name'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'body_material', 'label': str(_('\u041c\u0430\u0442\u0435\u0440\u0438\u0430\u043b \u043a\u043e\u0440\u043f\u0443\u0441\u0430')), 'value': tv['body_material'], 'unit': '', 'type': 'text', 'order': 3},
                                {'key': 'ip', 'label': str(_('IP')), 'value': tv['ip'], 'unit': '', 'type': 'text', 'order': 4},
                                {'key': 'override_mechanism', 'label': str(_('\u041c\u0435\u0445\u0430\u043d\u0438\u0437\u043c \u043e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f')), 'value': tv['override_mechanism'], 'unit': '', 'type': 'text', 'order': 5},
                                {'key': 'locking_mechanism', 'label': str(_('\u041c\u0435\u0445\u0430\u043d\u0438\u0437\u043c \u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u043a\u0438')), 'value': tv['locking_mechanism'], 'unit': '', 'type': 'text', 'order': 6},
                                {'key': 'is_declutchable', 'label': str(_('\u0420\u0430\u0441\u0446\u0435\u043f\u043b\u044f\u0435\u043c\u044b\u0439')), 'value': tv['is_declutchable'], 'unit': '', 'type': 'text', 'order': 7},
                            ]
                        },
                        {
                            'key': 'body',
                            'title': str(_('\u041a\u043e\u0440\u043f\u0443\u0441')),
                            'order': 2,
                            'fields': [
                                {'key': 'transmission_variety', 'label': str(_('\u0422\u0438\u043f \u043f\u0435\u0440\u0435\u0434\u0430\u0447\u0438')), 'value': tv['transmission_variety'], 'unit': '', 'type': 'text', 'order': 1},
                                {'key': 'reduction_ratio', 'label': str(_('\u041f\u0435\u0440\u0435\u0434\u0430\u0442\u043e\u0447\u043d\u043e\u0435 \u0447\u0438\u0441\u043b\u043e')), 'value': tv['reduction_ratio'], 'unit': '', 'type': 'text', 'order': 2},
                                {'key': 'max_output_torque', 'label': str(_('\u041c\u0430\u043a\u0441. \u043c\u043e\u043c\u0435\u043d\u0442 \u043d\u0430 \u0432\u044b\u0445\u043e\u0434\u0435')), 'value': tv['max_output_torque'], 'unit': str(_('\u041d\u043c')), 'type': 'number', 'order': 3},
                                {'key': 'max_input_torque', 'label': str(_('\u041c\u0430\u043a\u0441. \u0432\u0445\u043e\u0434\u043d\u043e\u0439 \u043c\u043e\u043c\u0435\u043d\u0442')), 'value': tv['max_input_torque'], 'unit': str(_('\u041d\u043c')), 'type': 'number', 'order': 4},
                                {'key': 'weight', 'label': str(_('\u0412\u0435\u0441')), 'value': tv['weight'], 'unit': str(_('\u043a\u0433')), 'type': 'number', 'order': 5},
                                {'key': 'handwheel_diameter', 'label': str(_('\u0414\u0438\u0430\u043c\u0435\u0442\u0440 \u0448\u0442\u0443\u0440\u0432\u0430\u043b\u0430')), 'value': tv['handwheel_diameter'], 'unit': str(_('\u043c\u043c')), 'type': 'number', 'order': 6},
                            ]
                        },
                        {
                            'key': 'conditions',
                            'title': str(_('\u0423\u0441\u043b\u043e\u0432\u0438\u044f \u044d\u043a\u0441\u043f\u043b\u0443\u0430\u0442\u0430\u0446\u0438\u0438')),
                            'order': 3,
                            'fields': [
                                {'key': 'work_temp', 'label': str(_('\u0420\u0430\u0431\u043e\u0447\u0430\u044f \u0442\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430')), 'value': tv['work_temp'], 'unit': '', 'type': 'text', 'order': 1},
                            ]
                        },
                    ]
                },
                {
                    'key': 'docs',
                    'title': str(_('\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f')),
                    'type': 'files',
                    'order': 3,
                    'data': self._get_docs_section(),
                },
                {
                    'key': 'certs',
                    'title': str(_('\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u044b')),
                    'type': 'files',
                    'order': 4,
                    'data': self._get_certs_section(),
                },
                {
                    'key': 'description',
                    'title': str(_('\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435')),
                    'type': 'text',
                    'order': 5,
                    'data': self.description or '',
                },
            ],
        }

    def _get_model_line_summary(self) -> dict:
        """Краткая сводка model_line."""
        if not self.model_line:
            return None
        return {
            'id': self.model_line.id,
            'name': self.model_line.name,
            'code': getattr(self.model_line, 'code', '') or '',
            'gearbox_variety': self.model_line.gearbox_variety.name if self.model_line.gearbox_variety else None,
            'gearbox_output_variety': self.model_line.gearbox_output_variety.name if self.model_line.gearbox_output_variety else None,
            'brand': {
                'id': self.model_line.brand.id,
                'name': self.model_line.brand.name,
            } if self.model_line.brand else None,
        }

    def _get_sku_summary(self) -> dict:
        """Краткая сводка SKU (для цен)."""
        if not hasattr(self, 'sku') or not self.sku:
            return None
        return {
            'id': self.sku.id,
            'code': self.sku.code,
            'name': self.sku.name,
        }

    # ── Оптимизированные сериализаторы ──

    def to_values_dict(self) -> dict:
        """
        Облегчённая сериализация для списков — НЕ вызывает to_dict().

        В отличие от ``CatalogDictMixin.to_values_dict()``, не строит
        секции (sections), а собирает только нужное для карточек:
        значения полей, первое изображение, model_line, sku.

        Это убирает задержку при фильтрации/пагинации на больших списках.
        """
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