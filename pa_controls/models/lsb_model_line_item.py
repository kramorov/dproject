# pa_controls/models/lsb_model_line_item.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Any

import logging

from core.models import TechDocMixin, ImageGalleryMixin
from core.models.catalog_mixin import CatalogFilterMixin, FilterFieldConfig, CommonFilterConfigs
from core.models.mixins import TemplateMixin, CopyMixin, CatalogDictMixin
from core.models.smart_catalog_mixin import SmartCatalogMixin, FilterDefinition, FilterType, DataSourceType
from materials.models import MaterialGeneral, MaterialSpecified
from pa_controls.models.pa_control_options import LimitSwitchSensorVariety, SignalType, ContactForm, ContactState
from pa_controls.models.sensor import SensorComponent
from pa_controls.models.lsb_body import LimitSwitchBody
from pa_controls.models.lsb_model_line import LimitSwitchModelLine
from params.exd_models import ExdOption
from sku.models import SKUMixin

# from pa_controls.models import PaControlMountingStandard

logger = logging.getLogger(__name__)

from params.models import IpOption


# ============================================================
# БЛОК КОНЦЕВЫХ ВЫКЛЮЧАТЕЛЕЙ (Limit Switch Box)
# ============================================================
class LsbModelLineItem(CatalogDictMixin,
                     ImageGalleryMixin,
                     TechDocMixin,
                     SmartCatalogMixin,
                     TemplateMixin,
                     SKUMixin, CopyMixin, models.Model):
    """Модель блока концевых выключателей (каталог)
    points: int,
        1 точка - один датчик (обычно только на закрыто)
        2 точки - два датчика (на открыто и на закрыто) - самый распространенный вариант
        3 точки - три датчика (открыто, закрыто, промежуточное положение)
        4 точки - четыре датчика (два промежуточных положения + концевые)
    """
    name = models.TextField(
        verbose_name=_("Название"),
        help_text=_('Текстовое название БКВ'))
    code = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    model_line = models.ForeignKey(LimitSwitchModelLine, related_name='lsb_item_model_line', blank=True,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   help_text=_('Серия БКВ'),
                                   verbose_name=_("Серия"))
    body = models.ForeignKey(LimitSwitchBody, related_name='lsb_item_body', blank=True,
                             null=True,
                             on_delete=models.SET_NULL,
                             help_text=_('Корпус БКВ'),
                             verbose_name=_("Корпус"))
    # Характеристики
    sensor_variety = models.ForeignKey(
        LimitSwitchSensorVariety, on_delete=models.SET_NULL, null=True,
        help_text=_('Тип сенсора'),
        verbose_name=_("Тип сенсора")
    )

    primary_sensor = models.ForeignKey(
        SensorComponent,
        blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("Датчик основной"),
        help_text=_("Основной датчик"),
        related_name='lsb_item_primary_sensor'
    )
    # Добавляем Many-to-Many связь с дополнительными датчиками
    additional_sensor = models.ManyToManyField(
        SensorComponent,
        blank=True,
        verbose_name=_("Датчики дополнительные"),
        help_text=_("Дополнительные датчики"),
        related_name='lsb_item_additional_sensor'
    )

    points = models.IntegerField(default=2,
                                 verbose_name=_("Количество датчиков"),
                                 help_text=_("Количество точек переключения (датчиков)")
                                 )
    ip = models.ForeignKey(IpOption, on_delete=models.SET_NULL, null=True,
                           related_name='lsb_item_ip',
                           help_text=_('Степень защиты IP'),
                           verbose_name=_("IP")
                           )
    exd = models.ManyToManyField(
        'params.ExdOption',
        blank=True,
        related_name='+',
        help_text=_('Степень взрывозащиты (можно выбрать несколько вариантов)'),
        verbose_name=_("Взрывозащита")
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

    # Материалы
    body_material = models.ForeignKey(MaterialGeneral, related_name='lsb_item_body_material',
                                      blank=True,
                                      null=True,
                                      on_delete=models.SET_NULL,
                                      help_text=_('Корпус'),
                                      verbose_name=_('Тип материала корпуса'))
    body_material_specified = models.ForeignKey(MaterialSpecified,
                                                related_name='lsb_item_body_material_specified',
                                                blank=True, null=True,
                                                on_delete=models.SET_NULL,
                                                help_text=_('Материал корпуса арматуры'),
                                                verbose_name=_('Материал корпуса'))

    # Дополнительные характеристики
    is_pneumatic = models.BooleanField(default=False, verbose_name=_("Пневматический"))
    has_namur_interface = models.BooleanField(default=False, verbose_name=_("NAMUR интерфейс"))
    has_visual_indicator = models.BooleanField(default=False, verbose_name=_("Визуальный индикатор"))

    # ВСЁ остальное в JSON
    extra_params = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Параметры"),
        help_text=_("signal_type, resistance, range и т.д.")
    )
    # images заменён на image_gallery из ImageGalleryMixin
    # Переопределяем tech_docs из TechDocMixin
    tech_docs = models.ManyToManyField(
        'media_library.MediaLibraryItem',
        blank=True,
        related_name='+',
        verbose_name="Техдокументация",
    )

    class Meta:
        verbose_name = _("Блок концевых выключателей")
        verbose_name_plural = _("Блоки концевых выключателей")
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

    def _copy_custom_relations(self, new_copy):
        new_copy.exd.set(self.exd.all())
        new_copy.additional_sensor.set(self.additional_sensor.all())

    # def copy(self, suffix=" (Копия)", code_suffix="_copy"):
    #     """
    #     Создает копию текущего объекта
    #
    #     Args:
    #         suffix: суффикс для name
    #         code_suffix: суффикс для code
    #
    #     Returns:
    #         LimitSwitchBox: Скопированный объект
    #     """
    #     # Генерируем новые имена с суффиксом
    #     original_name = self.name or ""
    #     original_code = self.code or ""
    #
    #     # Для name
    #     if suffix in original_name:
    #         base_name = original_name.replace(suffix, "")
    #         new_name = f"{base_name}{suffix}"
    #     else:
    #         new_name = f"{original_name}{suffix}"
    #
    #     # Для code
    #     if original_code:
    #         if code_suffix in original_code:
    #             # Увеличиваем номер копии
    #             import re
    #             match = re.search(rf"{code_suffix}(\d+)$", original_code)
    #             if match:
    #                 num = int(match.group(1)) + 1
    #                 new_code = re.sub(rf"{code_suffix}\d+$", f"{code_suffix}{num}", original_code)
    #             else:
    #                 new_code = f"{original_code}{code_suffix}1"
    #         else:
    #             new_code = f"{original_code}{code_suffix}"
    #     else:
    #         new_code = None
    #
    #     # Создаем копию
    #     copy = LimitSwitchBox(
    #         name=new_name,
    #         code=new_code,
    #         description=f"Копия: {self.description}" if self.description else "Копия",
    #         sorting_order=self.sorting_order + 100,
    #         is_active=self.is_active,
    #         model_line=self.model_line,
    #         body=self.body,
    #         sensor_variety=self.sensor_variety,
    #         points=self.points,
    #         ip=self.ip,
    #         work_temp_min=self.work_temp_min,
    #         work_temp_max=self.work_temp_max,
    #         body_material=self.body_material,
    #         body_material_specified=self.body_material_specified,
    #         is_pneumatic=self.is_pneumatic,
    #         has_namur_interface=self.has_namur_interface,
    #         has_visual_indicator=self.has_visual_indicator,
    #         extra_params=self.extra_params if self.extra_params else {}
    #     )
    #     copy.save()
    #
    #     # Копируем exd через ручной метод
    #     copy.exd_set_ids(self.exd_get_ids())
    #     # Копируем ManyToMany поле additional_sensor
    #     copy.additional_sensor.set(self.additional_sensor.all())
    #     return copy



    @property
    def exd_display(self):
        """Возвращает отображаемую маркировку взрывозащиты"""
        names = [e.name for e in self.exd.all()]
        return ", ".join(names) if names else "Нет"

    def _get_name_template_source(self):
        """Переопределить в модели: вернуть шаблон названия или None."""
        return self.model_line.name_template or None

    def _get_description_template_source(self):
        """Переопределить в модели: вернуть шаблон описания или None."""
        return self.model_line.description_template or None

    def _get_default_name_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand};  {points} датчика, тип датчика: {sensor_variety}; {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Датчик: {sensors}, Отверстия под КВ:{cable_glands_holes}, вес {weight} кг."
        return default_description_template

    def _get_default_description_template(self) -> str:
        default_description_template = "{model_code} Блок концевых выключателей {brand}; {points} датчика, тип датчика: {sensor_variety}, {ip}, Взрывозащита: {exd}; Т.окр. {work_temp_min}..{work_temp_max} °С, Материал корпуса: {body_material_specified}, Отверстия под КВ:{cable_glands_holes}, Монтаж:{mounting}, вес {weight}кг. Датчики: {sensors_description}"
        return default_description_template

    # '{primary_sensor_contact_form}': 'primary_sensor__contact_form',

    @property
    def get_primary_sensor_contact_form(self) -> str:
        return '' if self.primary_sensor.contact_form.code == 'NONE' else self.primary_sensor.contact_form

    @property
    def get_sensors_signal_types_list(self) -> str:
        codes = []
        if self.primary_sensor and self.primary_sensor.signal_type:
            codes.append(self.primary_sensor.signal_type.name)
        for sensor in self.additional_sensor.all():
            if sensor.signal_type:
                codes.append(sensor.signal_type.name)

        if not codes:
            return ""
        if len(codes) == 1:
            return codes[0]
        return "+".join(codes[:-1]) + " + " + codes[-1]

    @property
    def get_sensors_description_list(self) -> str:
        """
        Возвращает  список поля description датчиков.
        Разделитель - символ "+"
        """
        sensor_components = self.additional_sensor.all()
        if not sensor_components:
            return ""

        names = [item.description for item in sensor_components]
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]}; + {names[1]}"
        else:
            return ", ".join(names[:-1]) + f" + {names[-1]}"

    @property
    def get_additional_sensors_names_list(self) -> str:
        """
        Возвращает текстовый список датчиков.
        Разделитель - символ "+"
        """
        sensor_components = self.additional_sensor.all()
        if not sensor_components:
            return ""

        names = [item.generate_name() for item in sensor_components]

        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]}; + {names[1]}"
        else:
            return ", ".join(names[:-1]) + f" + {names[-1]}"

    def _get_data_dict(self) -> Dict[str, str]:
        """Получить словарь соответствий плейсхолдеров и атрибутов для замены"""
        return {
            '{model_code}': 'code',
            '{brand}': 'model_line__brand__name',
            '{sensor_variety}': 'sensor_variety',
            '{points}': 'points',
            '{body_material}': 'body_material',
            '{body_material_specified}': 'body_material_specified',
            '{weight}': 'body__weight',
            '{cable_glands_holes}': 'body__cable_glands_holes_list_text',
            '{mounting}': 'body__mounting_list_text',
            '{work_temp_min}': 'work_temp_min',
            '{work_temp_max}': 'work_temp_max',
            '{exd}': 'exd_display',
            '{ip}': 'ip',
            # M2M поле - вызов метода get_sensors_list с подшаблоном
            # В подшаблоне можно использовать поля из SensorComponent (name, brand, signal_type, electrical_specs и т.д.)
            '{primary_sensor}': 'primary_sensor__description',
            '{primary_sensor_signal_type}': 'primary_sensor__signal_type',
            '{primary_sensor_contact_state}': 'primary_sensor__contact_state',
            '{primary_sensor_contact_form}': 'get_primary_sensor_contact_form',
            # '{primary_sensor}': 'primary_sensor__description',
            '{sensors}': 'get_additional_sensors_names_list',
            '{signals}': 'get_sensors_signal_types_list',
            '{sensors_description}': 'get_sensors_description_list',
        }

    # ========== КОНФИГУРАЦИЯ ДЛЯ МИКСИНА SmartCatalogMixin ==========

    FILTER_DEFINITIONS = [
        # Серия
        FilterDefinition(
            param_name='model_line_id',
            model_field='model_line',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.FOREIGN_KEY,
            label='Серия',
            order=1
        ),

        # Тип сенсора
        FilterDefinition(
            param_name='sensor_variety_id',
            model_field='sensor_variety',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Тип сенсора',
            order=2
        ),

        # Количество датчиков
        FilterDefinition(
            param_name='points',
            model_field='points',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.CHOICES,
            choices=[(1, '1 датчик'), (2, '2 датчика'), (3, '3 датчика'), (4, '4 датчика')],
            label='Количество датчиков',
            order=3
        ),

        # IP (с ранжированием)
        FilterDefinition(
            param_name='ip_id',
            model_field='ip',
            filter_type=FilterType.IP_RANK,
            data_source_type=DataSourceType.GLOBAL_MODEL,
            source_model=IpOption,
            label='IP',
            order=4
        ),

        # Температура
        FilterDefinition(
            param_name='work_temp_min',
            model_field='work_temp_min',
            filter_type=FilterType.TEMP_MIN,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура от',
            order=5
        ),
        FilterDefinition(
            param_name='work_temp_max',
            model_field='work_temp_max',
            filter_type=FilterType.TEMP_MAX,
            data_source_type=DataSourceType.FIELD_VALUES,
            label='Температура до',
            order=6
        ),

        # Материалы
        FilterDefinition(
            param_name='body_material_id',
            model_field='body_material',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.FOREIGN_KEY,
            label='Материал корпуса',
            order=7
        ),

        # Бренд через серию
        FilterDefinition(
            param_name='model_line_brand_id',
            model_field='model_line__brand',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
            label='Бренд серии',
            order=8
        ),

        # Тип сигнала (датчики)
        # FilterDefinition(  #Все значения из глобальной модели
        #     param_name='signal_type_id',
        #     model_field='primary_sensor__signal_type',
        #     filter_type=FilterType.EXACT,
        #     data_source_type=DataSourceType.GLOBAL_MODEL,
        #     source_model=SignalType,
        #     label='Тип сигнала',
        #     order=9
        # ),
        # Только имеющиеся в справочнике
        # Для ForeignKey полей - используем UNIQUE_FIELD_VALUES (только используемые)
        FilterDefinition(
            param_name='signal_type_id',
            model_field='primary_sensor__signal_type',
            filter_type=FilterType.EXACT,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,  # ← только используемые
            label='Тип сигнала',
            order=9
        ),
        FilterDefinition(
            param_name='exd_id',
            model_field='exd',  # имя ManyToMany поля
            filter_type=FilterType.EXD_COMPATIBLE,
            data_source_type=DataSourceType.CUSTOM,  # опции не автоматические
            label='Взрывозащита',
            order=10
        ),
    ]

    # ========== ОПЦИИ ДЛЯ ФИЛЬТРОВ (CUSTOM) ==========
    @classmethod
    def _get_exd_id_options(cls) -> List[Dict]:
        """Опции для фильтра Exd — все активные ExdOption"""
        return [
            {'id': obj.id, 'name': obj.name, 'code': obj.code}
            for obj in ExdOption.objects.filter(is_active=True).order_by('name')
        ]

    SEARCH_FIELDS = ['code', 'name', 'description']

    # Фильтры для быстрого подбора (QuickSelect)
    QUICKSELECT_FILTERS = [
        'sensor_variety_id',
        'points',
        'body_material_id',
        'signal_type_id',
    ]

    SELECT_RELATED_FIELDS = [
        'model_line', 'model_line__brand', 'sensor_variety',
        'image_gallery', 'model_line__image_gallery',
        'ip', 'body_material', 'primary_sensor', 'primary_sensor__signal_type',
    ]

    # ========== СЕРИАЛИЗАЦИЯ (CatalogDictMixin) ==========

    def _get_template_vars(self) -> dict:
        """Единый источник строковых значений для шаблонов и секций."""
        ml = self.model_line
        body = self.body
        return {
            'code': self.code or '',
            'name': self.name or '',
            'model_line_name': ml.name if ml else '',
            'brand_name': ml.brand.name if ml and ml.brand else '',
            'sensor_variety': self.sensor_variety.name if self.sensor_variety else '',
            'points': str(self.points) if self.points else '',
            'ip': self.ip.name if self.ip else '',
            'exd': self.exd_display or '',
            'work_temp': f'{self.work_temp_min}...+{self.work_temp_max} °С' if self.work_temp_min is not None else '',
            'work_temp_min': str(self.work_temp_min) if self.work_temp_min is not None else '',
            'work_temp_max': str(self.work_temp_max) if self.work_temp_max is not None else '',
            'body_material': self.body_material.name if self.body_material else '',
            'body_material_specified': self.body_material_specified.name if self.body_material_specified else '',
            'weight': str(body.weight) if body and body.weight else '',
            'cable_glands_holes': body.cable_glands_holes_list_text if body and body.cable_glands_holes_list_text else '',
            'mounting': body.mounting_list_text if body and body.mounting_list_text else '',
            'is_pneumatic': 'Да' if self.is_pneumatic else 'Нет',
            'has_namur_interface': 'Да' if self.has_namur_interface else 'Нет',
            'has_visual_indicator': 'Да' if self.has_visual_indicator else 'Нет',
            'primary_sensor': self.primary_sensor.name if self.primary_sensor else '',
            'primary_sensor_signal_type': self.primary_sensor.signal_type.name if self.primary_sensor and self.primary_sensor.signal_type else '',
            'sensors': self.get_additional_sensors_names_list or '',
            'sensors_description': self.get_sensors_description_list or '',
            'signals': self.get_sensors_signal_types_list or '',
            'cert_description': self.get_cert_docs_description() or '',
        }

    @staticmethod
    def _safe_m2m(instance, method_name):
        try:
            return getattr(instance, method_name)()
        except Exception:
            return []

    def _get_docs_section(self) -> list:
        docs = []
        seen = set()
        for doc in self.tech_docs.all():
            if doc.media_file and doc.id not in seen:
                seen.add(doc.id)
                has_email = doc.variants.filter(role='email').exists()
                docs.append({
                    'id': doc.id, 'name': getattr(doc, 'name', '') or '',
                    'url': f"/api/media/{doc.id}/download/",
                    'file_name': getattr(doc, 'name', '') or '',
                    'preview_url': f"/api/media/{doc.id}/view/",
                    'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
                })
        if self.model_line and hasattr(self.model_line, 'tech_docs'):
            for doc in self.model_line.tech_docs.all():
                if doc.media_file and doc.id not in seen:
                    seen.add(doc.id)
                    has_email = doc.variants.filter(role='email').exists()
                    docs.append({
                        'id': doc.id, 'name': getattr(doc, 'name', '') or '',
                        'url': f"/api/media/{doc.id}/download/",
                        'file_name': getattr(doc, 'name', '') or '',
                        'preview_url': f"/api/media/{doc.id}/view/",
                        'email_url': f"/api/media/{doc.id}/download/?variant=email" if has_email else None,
                    })
        return docs

    def _get_certs_section(self) -> list:
        certs = []
        if self.model_line and hasattr(self.model_line, 'cert_docs'):
            # Было: raw SQL в обход ошибки — сейчас работает через ORM
            # with connection.cursor() as c:
            #     c.execute(
            #         'SELECT certdata_id FROM pa_controls_limitswitchmodelline_cert_docs WHERE limitswitchmodelline_id = %s',
            #         [self.model_line.pk]
            #     )
            #     cert_ids = [row[0] for row in c.fetchall()]
            cert_ids = list(
                self.model_line.cert_docs
                .filter(is_active=True)
                .values_list('id', flat=True)
            )
            if cert_ids:
                from cert_doc.models import CertData
                for cert in CertData.objects.filter(id__in=cert_ids).select_related('media_item'):
                    media = getattr(cert, 'media_item', None)
                    if not media:
                        continue
                    has_email = media.variants.filter(role='email').exists()
                    certs.append({
                        'id': cert.id,
                        'name': getattr(cert, 'name', '') or '',
                        'file_name': f"Сертификат {getattr(getattr(cert, 'cert_variety', None), 'name', '') or ''} {getattr(cert, 'code', '') or ''}".strip() or 'certificate',
                        'url': f"/api/media/{media.id}/download/",
                        'preview_url': f"/api/media/{media.id}/view/",
                        'email_url': f"/api/media/{media.id}/download/?variant=email" if has_email else None,
                    })
        return certs

    def _get_model_line_summary(self) -> dict:
        if not self.model_line:
            return None
        ml = self.model_line
        return {
            'id': ml.id,
            'name': ml.name,
            'code': getattr(ml, 'code', '') or '',
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

    def to_dict(self) -> dict:
        """Структурированная сериализация БКВ (CatalogDictMixin)."""
        tv = self._get_template_vars()
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'description': self.description or '',
            'is_active': self.is_active,
            'sorting_order': self.sorting_order,
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
            'template_vars': tv,
            'sections': [
                {
                    'key': 'images', 'title': 'Изображения', 'type': 'gallery',
                    'order': 1, 'data': self._safe_m2m(self, '_get_images_section')
                },
                {
                    'key': 'specs', 'title': 'Характеристики', 'type': 'specs',
                    'order': 2, 'groups': [
                    {
                        'key': 'general', 'title': 'Основные', 'order': 1,
                        'fields': [
                            {'key': 'model_line_name', 'label': 'Серия', 'value': tv['model_line_name'], 'unit': '',
                             'type': 'text', 'order': 1},
                            {'key': 'brand_name', 'label': 'Бренд', 'value': tv['brand_name'], 'unit': '',
                             'type': 'text', 'order': 2},
                            {'key': 'sensor_variety', 'label': 'Тип сенсора', 'value': tv['sensor_variety'], 'unit': '',
                             'type': 'text', 'order': 3},
                            {'key': 'points', 'label': 'Количество датчиков', 'value': tv['points'], 'unit': '',
                             'type': 'number', 'order': 4},
                            {'key': 'ip', 'label': 'IP', 'value': tv['ip'], 'unit': '', 'type': 'text', 'order': 5},
                            {'key': 'exd', 'label': 'Взрывозащита', 'value': tv['exd'], 'unit': '', 'type': 'text',
                             'order': 6},
                            {'key': 'is_pneumatic', 'label': 'Пневматический', 'value': tv['is_pneumatic'], 'unit': '',
                             'type': 'text', 'order': 7},
                            {'key': 'has_namur_interface', 'label': 'NAMUR интерфейс',
                             'value': tv['has_namur_interface'], 'unit': '', 'type': 'text', 'order': 8},
                            {'key': 'has_visual_indicator', 'label': 'Визуальный индикатор',
                             'value': tv['has_visual_indicator'], 'unit': '', 'type': 'text', 'order': 9},
                        ]
                    },
                    {
                        'key': 'body', 'title': 'Корпус', 'order': 2,
                        'fields': [
                            {'key': 'body_material', 'label': 'Материал корпуса', 'value': tv['body_material'],
                             'unit': '', 'type': 'text', 'order': 1},
                            {'key': 'body_material_specified', 'label': 'Материал (уточн.)',
                             'value': tv['body_material_specified'], 'unit': '', 'type': 'text', 'order': 2},
                            {'key': 'weight', 'label': 'Вес', 'value': tv['weight'], 'unit': 'кг', 'type': 'number',
                             'order': 3},
                            {'key': 'cable_glands_holes', 'label': 'Отверстия под КВ',
                             'value': tv['cable_glands_holes'], 'unit': '', 'type': 'text', 'order': 4},
                            {'key': 'mounting', 'label': 'Монтаж', 'value': tv['mounting'], 'unit': '', 'type': 'text',
                             'order': 5},
                        ]
                    },
                    {
                        'key': 'sensors', 'title': 'Датчики', 'order': 3,
                        'fields': [
                            {'key': 'primary_sensor', 'label': 'Основной датчик', 'value': tv['primary_sensor'],
                             'unit': '', 'type': 'text', 'order': 1},
                            {'key': 'primary_sensor_signal_type', 'label': 'Тип сигнала',
                             'value': tv['primary_sensor_signal_type'], 'unit': '', 'type': 'text', 'order': 2},
                            {'key': 'sensors', 'label': 'Доп. датчики', 'value': tv['sensors'], 'unit': '',
                             'type': 'text', 'order': 3},
                            {'key': 'signals', 'label': 'Типы сигналов', 'value': tv['signals'], 'unit': '',
                             'type': 'text', 'order': 4},
                        ]
                    },
                    {
                        'key': 'conditions', 'title': 'Условия эксплуатации', 'order': 4,
                        'fields': [
                            {'key': 'work_temp', 'label': 'Рабочая температура', 'value': tv['work_temp'], 'unit': '',
                             'type': 'text', 'order': 1},
                        ]
                    },
                ]
                },
                {
                    'key': 'docs', 'title': 'Документация', 'type': 'files',
                    'order': 3, 'data': self._safe_m2m(self, '_get_docs_section')
                },
                {
                    'key': 'certs', 'title': 'Сертификаты', 'type': 'files',
                    'order': 4, 'data': self._safe_m2m(self, '_get_certs_section')
                },
                {
                    'key': 'description', 'title': 'Описание', 'type': 'text',
                    'order': 5, 'data': self.description or '',
                },
            ],
        }

    def to_values_dict(self) -> dict:
        """Облегчённая сериализация для списков."""
        first_img = self._get_first_image()
        tv = {'code': self.code or '', 'name': self.name or ''}
        return {
            'id': self.id,
            'code': self.code or '',
            'name': self.name or '',
            'title': self.generate_title(),
            'image_alt': self.name or '',
            'template_vars': tv,
            'values': tv,
            'images': [first_img] if first_img else [],
            'model_line': self._get_model_line_summary(),
            'sku': self._get_sku_summary(),
        }