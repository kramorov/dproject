# cert_doc/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from typing import List, Optional, Tuple, Any, Dict, Union
from django.core.exceptions import ValidationError
from core.models import BaseAbstractModel , StructuredDataMixin
from producers.models import Brands


class CertVariety(BaseAbstractModel) :
    """Тип сертификата"""
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название типа сертификата")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True ,
                            verbose_name=_("Код") ,
                            help_text=_("Код типа сертификата"))

    class Meta :
        verbose_name = _('Тип сертификата')
        verbose_name_plural = _('Типы сертификатов')

    def __str__(self) :
        return self.name or self.code or f"#{self.id}"


class CertData(BaseAbstractModel , StructuredDataMixin) :
    """Базовая модель сертификата"""
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название сертификата")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True ,
                            verbose_name=_("Код") ,
                            help_text=_("Код сертификата"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Описание сертификата - для каких серий и брендов'))

    cert_variety = models.ForeignKey(CertVariety , on_delete=models.CASCADE ,
                                     verbose_name=_('Тип сертификата') ,
                                     help_text=_('Тип сертификата'))

    issued_by = models.CharField(max_length=500 , blank=True , null=True ,
                                 verbose_name=_("Кем выдан") ,
                                 help_text=_("Название организации, выдавшей сертификат"))

    valid_from = models.DateField(blank=True , null=True ,
                                  verbose_name=_('Действует с') ,
                                  help_text=_('Срок действия с'))

    valid_until = models.DateField(blank=True , null=True ,
                                   verbose_name=_('Действует до') ,
                                   help_text=_('Срок действия до'))

    brand = models.ForeignKey(Brands , blank=True , null=True ,
                              on_delete=models.SET_NULL ,
                              related_name='cert_owner_brand' ,
                              help_text=_('Бренд для сертификата (для фильтрации)'))

    public_url = models.CharField(
        max_length=2000 ,
        blank=True ,
        null=True ,
        verbose_name=_("URL") ,
        help_text=_("URL адрес для скачивания")
    )

    # Связь с медиабиблиотекой
    media_item = models.ForeignKey(
        'media_library.MediaLibraryItem' ,
        on_delete=models.SET_NULL ,
        blank=True ,
        null=True ,
        related_name='certificates' ,
        verbose_name=_("Медиафайл") ,
        help_text=_("Связанный файл из медиабиблиотеки")
    )

    class Meta :
        verbose_name = _('Сертификат')
        verbose_name_plural = _('Сертификаты')
        ordering = ['sorting_order' , 'cert_variety']

    def __str__(self) :
        return self.name or self.code or f"#{self.id}"

    def get_compact_data(self) :
        """Минимальные данные для списков"""
        from django.utils.formats import date_format

        return {
            'id' : self.id ,
            'name' : self.name ,
            'code' : self.code ,
            'cert_variety' : str(self.cert_variety) if self.cert_variety else None ,
            'valid_until' : date_format(self.valid_until , 'd.m.Y') if self.valid_until else None ,
            'has_media' : bool(self.media_item) ,
            'has_url' : bool(self.public_url) ,
            'is_active' : self.is_active ,
            'model' : 'CertData' ,
            'app' : 'cert_doc' ,
        }

    def get_display_data(self , view_type='detail') :
        """Данные для отображения"""
        from django.utils.formats import date_format

        base_fields = {
            'name' : {
                'label' : _('Название') ,
                'value' : self.name or _('Не указано') ,
                'type' : 'text' ,
                'icon' : '📄' ,
                'priority' : 1
            } ,
            'code' : {
                'label' : _('Код сертификата') ,
                'value' : self.code or _('Не указан') ,
                'type' : 'code' ,
                'icon' : '🔢' ,
                'priority' : 2
            } ,
            'cert_variety' : {
                'label' : _('Тип сертификата') ,
                'value' : str(self.cert_variety) if self.cert_variety else _('Не указан') ,
                'type' : 'badge' ,
                'icon' : '🏷️' ,
                'priority' : 3
            } ,
            'issued_by' : {
                'label' : _('Кем выдан') ,
                'value' : self.issued_by or _('Не указано') ,
                'type' : 'text' ,
                'icon' : '🏢' ,
                'priority' : 4
            } ,
            'validity' : {
                'label' : _('Срок действия') ,
                'value' : self._format_validity_period() ,
                'type' : 'date_range' ,
                'icon' : '📅' ,
                'priority' : 5 ,
                'is_expired' : self._is_expired() if self.valid_until else None
            } ,
            'brand' : {
                'label' : _('Бренд') ,
                'value' : str(self.brand) if self.brand else _('Не указан') ,
                'type' : 'link' ,
                'icon' : '🏭' ,
                'priority' : 6
            } ,
            'public_url' : {
                'label' : _('Ссылка') ,
                'value' : self.public_url or _('Ссылки нет') ,
                'type' : 'url' ,
                'icon' : '🔗' ,
                'priority' : 7 ,
                'is_available' : bool(self.public_url)
            }
        }

        if view_type == 'card' :
            return {
                'title' : self.name or self.code or _('Сертификат') ,
                'subtitle' : str(self.cert_variety) if self.cert_variety else '' ,
                'badges' : [
                    {'text' : self.code , 'type' : 'code'} if self.code else None ,
                    {'text' : 'Активен' , 'type' : 'success'} if self.is_active else
                    {'text' : 'Неактивен' , 'type' : 'secondary'} ,
                ] ,
                'details' : [
                    {'label' : 'Выдан' , 'value' : self.issued_by} if self.issued_by else None ,
                    {'label' : 'Действует до' ,
                     'value' : date_format(self.valid_until , 'd.m.Y')} if self.valid_until else None ,
                ]
            }

        return {'fields' : base_fields}

    def get_full_data(self , include=None) :
        """Полные данные для форм и API"""
        if include is None :
            include = ['form' , 'metadata' , 'related']

        data = {
            'id' : self.id ,
            'model' : 'CertData' ,
            'is_active' : self.is_active ,
            'sorting_order' : self.sorting_order ,
            'display' : self.get_display_data() ,
        }

        if 'form' in include :
            data['form'] = {
                'name' : self.name ,
                'code' : self.code ,
                'description' : self.description ,
                'cert_variety_id' : self.cert_variety_id ,
                'issued_by' : self.issued_by ,
                'valid_from' : self.valid_from.isoformat() if self.valid_from else None ,
                'valid_until' : self.valid_until.isoformat() if self.valid_until else None ,
                'brand_id' : self.brand_id ,
                'public_url' : self.public_url ,
                'media_item_id' : self.media_item_id ,
            }

        if 'metadata' in include :
            data['metadata'] = self._get_metadata()

        if 'related' in include :
            data['related'] = self._get_related_data()

        return data

    def _format_validity_period(self) :
        """Форматирование периода действия"""
        from django.utils.formats import date_format

        if not self.valid_from and not self.valid_until :
            return _('Не указан')

        parts = []
        if self.valid_from :
            parts.append(f"{_('с')} {date_format(self.valid_from , 'd.m.Y')}")
        if self.valid_until :
            parts.append(f"{_('до')} {date_format(self.valid_until , 'd.m.Y')}")

        return ' '.join(parts)

    def _is_expired(self) :
        """Проверка истек ли срок"""
        from datetime import date
        if not self.valid_until :
            return False
        return date.today() > self.valid_until

    def _get_metadata(self) :
        """Метаданные для форм"""
        return {
            'field_schema' : [
                {
                    'name' : 'name' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Название') ,
                    'help_text' : _('Название сертификата') ,
                    'max_length' : 100
                } ,
                # ... другие поля
            ] ,
            'validation_rules' : {
                'public_url' : {
                    'type' : 'url' ,
                    'pattern' : r'^https?://' ,
                    'message' : _('URL должен начинаться с http:// или https://')
                }
            }
        }

    def _get_related_data(self) :
        """Связанные данные"""
        return {
            'cert_variety' : {
                'id' : self.cert_variety_id ,
                'name' : self.cert_variety.name if self.cert_variety else None ,
                'code' : self.cert_variety.code if self.cert_variety else None
            } if self.cert_variety else None ,
            'brand' : {
                'id' : self.brand_id ,
                'name' : self.brand.name if self.brand else None
            } if self.brand else None ,
            'media_item' : {
                'id' : self.media_item_id ,
                'title' : self.media_item.title if self.media_item else None ,
                'url' : self.media_item.media_file.url if self.media_item and self.media_item.media_file else None
            } if self.media_item else None
        }


class AbstractCertRelation(StructuredDataMixin , models.Model) :  # Добавляем миксин!
    """
    Абстрактная through-модель для связей сертификатов с другими объектами.
    """
    cert_data = models.ForeignKey(
        CertData ,
        on_delete=models.CASCADE ,
        verbose_name=_("Сертификат") ,
        related_name='%(class)s_relations'
    )
    sorting_order = models.IntegerField(
        default=0 ,
        verbose_name=_("Порядок сортировки")
    )
    is_active = models.BooleanField(
        default=True ,
        verbose_name=_("Активно")
    )

    class Meta :
        abstract = True
        ordering = ['sorting_order']

    def __str__(self) :
        related_obj = self.get_related_object()
        return f"{self.cert_data} → {related_obj}" if related_obj else str(self.cert_data)

    def get_related_object(self) :
        """
        Должен быть переопределен в дочерних классах.
        Возвращает объект, с которым связан сертификат.
        """
        raise NotImplementedError(
            f"Модель {self.__class__.__name__} должна реализовать get_related_object()"
        )

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц
        Включаем данные сертификата + информацию о связи
        """
        cert_data = self.cert_data.get_compact_data()

        # Добавляем информацию о связи
        cert_data.update({
            'relation_id' : self.id ,
            'relation_sorting_order' : self.sorting_order ,
            'relation_is_active' : self.is_active ,
            'relation_model' : self._get_model_name() ,
            'relation_app' : self._get_app_label() ,
        })

        # Добавляем информацию о связанном объекте
        related_obj = self.get_related_object()
        if related_obj :
            cert_data['related_object'] = related_obj.get_compact_data()

        return cert_data

    def get_display_data(self , view_type: str = 'detail') -> Dict[str , Any] :
        """
        Данные для отображения в UI
        Берем данные сертификата и добавляем контекст связи
        """
        cert_display = self.cert_data.get_display_data(view_type)

        # Добавляем информацию о связи в зависимости от типа отображения
        if view_type == self.CARD :
            if 'badges' not in cert_display :
                cert_display['badges'] = []

            cert_display['badges'].append({
                'text' : f'Приоритет: {self.sorting_order}' ,
                'type' : 'info'
            })

            if not self.is_active :
                cert_display['badges'].append({
                    'text' : 'Связь неактивна' ,
                    'type' : 'warning'
                })

        elif 'fields' in cert_display :
            # Для детального отображения
            cert_display['fields']['relation_info'] = {
                'label' : _('Информация о связи') ,
                'value' : {
                    'sorting_order' : self.sorting_order ,
                    'is_active' : 'Активна' if self.is_active else 'Неактивна' ,
                } ,
                'type' : 'relation_info' ,
                'icon' : '🔗' ,
                'priority' : 95
            }

        return cert_display

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API
        """
        if include is None :
            include = ['form' , 'metadata' , 'related']

        cert_full = self.cert_data.get_full_data(include)

        # Добавляем информацию о связи
        cert_full['relation'] = {
            'id' : self.id ,
            'sorting_order' : self.sorting_order ,
            'is_active' : self.is_active ,
        }

        # Добавляем данные связанного объекта
        related_obj = self.get_related_object()
        if related_obj :
            cert_full['related_object'] = related_obj.get_compact_data()
            if 'display' in include :
                cert_full['related_object_display'] = related_obj.get_display_data('badge')

        return cert_full