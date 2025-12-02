# cert_doc/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from core.models import BaseModel , StructuredDataMixin
from producers.models import Brands


class CertVariety(BaseModel) :
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


class CertData(BaseModel , StructuredDataMixin) :
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


class AbstractCertRelation(models.Model) :
    """
    Абстрактная through-модель для связей сертификатов с другими объектами.

    Наследуйте эту модель для создания конкретных связей:

    class ProductCertRelation(AbstractCertRelation):
        product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class ProjectCertRelation(AbstractCertRelation):
        project = models.ForeignKey(Project, on_delete=models.CASCADE)
    """

    cert_data = models.ForeignKey(
        CertData ,
        on_delete=models.CASCADE ,
        verbose_name=_("Сертификат") ,
        related_name='%(class)s_relations'
    )

    # Общие поля для всех связей
    is_primary = models.BooleanField(
        default=False ,
        verbose_name=_("Основной сертификат") ,
        help_text=_("Отметьте если это основной сертификат для объекта")
    )

    valid_for_model = models.BooleanField(
        default=True ,
        verbose_name=_("Действует для модели") ,
        help_text=_("Действителен ли сертификат для этой конкретной модели")
    )

    notes = models.TextField(
        blank=True ,
        verbose_name=_("Примечания") ,
        help_text=_("Дополнительные примечания по применению сертификата")
    )

    applied_date = models.DateField(
        blank=True ,
        null=True ,
        verbose_name=_("Дата применения") ,
        help_text=_("Дата применения сертификата к объекту")
    )

    expires_on_model = models.DateField(
        blank=True ,
        null=True ,
        verbose_name=_("Действует до для модели") ,
        help_text=_("До какой даты сертификат действителен для этой модели")
    )

    # Системные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User' ,
        on_delete=models.SET_NULL ,
        null=True ,
        blank=True ,
        verbose_name=_("Кто создал связь")
    )

    # Для поддержки GenericForeignKey (опционально)
    content_type = models.ForeignKey(
        ContentType ,
        on_delete=models.CASCADE ,
        blank=True ,
        null=True ,
        verbose_name=_("Тип связанного объекта") ,
        help_text=_("Тип объекта к которому привязан сертификат")
    )

    object_id = models.PositiveIntegerField(
        blank=True ,
        null=True ,
        verbose_name=_("ID объекта")
    )

    content_object = GenericForeignKey('content_type' , 'object_id')

    class Meta :
        abstract = True
        unique_together = ['cert_data' , 'content_type' , 'object_id']
        ordering = ['-is_primary' , '-applied_date' , '-created_at']

    def __str__(self) :
        related_obj = self.get_related_object()
        return f"{self.cert_data} -> {related_obj}" if related_obj else str(self.cert_data)

    def clean(self) :
        """Валидация связи"""
        super().clean()

        # Проверяем, что заполнен либо конкретное поле, либо generic relation
        has_concrete_relation = any(
            hasattr(self , field) and getattr(self , field) is not None
            for field in self._get_concrete_relation_fields()
        )

        has_generic_relation = self.content_type and self.object_id

        if not (has_concrete_relation or has_generic_relation) :
            raise ValidationError(
                _("Необходимо указать связанный объект либо через конкретное поле, "
                  "либо через content_type/object_id")
            )

    def save(self , *args , **kwargs) :
        """Автоматически заполняем generic fields если есть конкретное поле"""
        self.clean()

        # Если есть конкретное поле, заполняем generic fields
        concrete_field = self._get_concrete_relation_field()
        if concrete_field :
            related_obj = getattr(self , concrete_field)
            if related_obj :
                self.content_type = ContentType.objects.get_for_model(related_obj)
                self.object_id = related_obj.id

        super().save(*args , **kwargs)

    # СТАНДАРТНЫЕ МЕТОДЫ ДЛЯ ВСЕХ THROUGH МОДЕЛЕЙ

    def get_compact_data(self) :
        """Минимальные данные для списков"""
        related_obj = self.get_related_object()

        return {
            'id' : self.id ,
            'cert_id' : self.cert_data_id ,
            'cert_code' : self.cert_data.code if self.cert_data.code else None ,
            'cert_name' : self.cert_data.name if self.cert_data.name else None ,
            'related_object' : str(related_obj) if related_obj else None ,
            'related_type' : self.content_type.model if self.content_type else None ,
            'is_primary' : self.is_primary ,
            'valid_for_model' : self.valid_for_model ,
            'applied_date' : self.applied_date.isoformat() if self.applied_date else None ,
            'expires_on_model' : self.expires_on_model.isoformat() if self.expires_on_model else None ,
            'model' : self.__class__.__name__ ,
            'app' : self._meta.app_label ,
        }

    def get_display_data(self , view_type='detail') :
        """Данные для отображения"""
        from django.utils.formats import date_format

        related_obj = self.get_related_object()

        base_fields = {
            'certificate' : {
                'label' : _('Сертификат') ,
                'value' : str(self.cert_data) if self.cert_data else _('Не указан') ,
                'type' : 'link' ,
                'icon' : '📋' ,
                'priority' : 1 ,
                'object' : self.cert_data
            } ,
            'related_object' : {
                'label' : _('Связанный объект') ,
                'value' : str(related_obj) if related_obj else _('Не указан') ,
                'type' : 'link' ,
                'icon' : '🔗' ,
                'priority' : 2 ,
                'object' : related_obj
            } ,
            'status' : {
                'label' : _('Статус связи') ,
                'value' : _('Основная') if self.is_primary else _('Дополнительная') ,
                'type' : 'badge' ,
                'icon' : '⭐' if self.is_primary else '📌' ,
                'priority' : 3
            } ,
            'validity' : {
                'label' : _('Действует для модели') ,
                'value' : _('Да') if self.valid_for_model else _('Нет') ,
                'type' : 'boolean' ,
                'icon' : '✅' if self.valid_for_model else '❌' ,
                'priority' : 4
            } ,
            'dates' : {
                'label' : _('Даты') ,
                'value' : self._format_dates() ,
                'type' : 'date_range' ,
                'icon' : '📅' ,
                'priority' : 5
            } ,
            'notes' : {
                'label' : _('Примечания') ,
                'value' : self.notes or _('Нет примечаний') ,
                'type' : 'textarea' ,
                'icon' : '📝' ,
                'priority' : 6 ,
                'is_empty' : not bool(self.notes)
            }
        }

        if view_type == 'card' :
            return {
                'title' : str(self.cert_data) if self.cert_data else _('Связь сертификата') ,
                'subtitle' : str(related_obj) if related_obj else '' ,
                'badges' : [
                    {'text' : 'Основной' , 'type' : 'primary'} if self.is_primary else
                    {'text' : 'Дополнительный' , 'type' : 'secondary'} ,
                    {'text' : 'Действует' , 'type' : 'success'} if self.valid_for_model else
                    {'text' : 'Не действует' , 'type' : 'warning'} ,
                ] ,
                'details' : base_fields
            }

        return {'fields' : base_fields}

    def get_full_data(self , include=None) :
        """Полные данные для форм и API"""
        if include is None :
            include = ['form' , 'metadata' , 'related']

        related_obj = self.get_related_object()

        data = {
            'id' : self.id ,
            'model' : self.__class__.__name__ ,
            'display' : self.get_display_data() ,
        }

        if 'form' in include :
            data['form'] = {
                'cert_data_id' : self.cert_data_id ,
                'is_primary' : self.is_primary ,
                'valid_for_model' : self.valid_for_model ,
                'notes' : self.notes ,
                'applied_date' : self.applied_date.isoformat() if self.applied_date else None ,
                'expires_on_model' : self.expires_on_model.isoformat() if self.expires_on_model else None ,
                'created_by_id' : self.created_by_id ,
            }

            # Добавляем поле конкретной связи если есть
            concrete_field = self._get_concrete_relation_field()
            if concrete_field :
                data['form'][f'{concrete_field}_id'] = getattr(self , f'{concrete_field}_id')

        if 'metadata' in include :
            data['metadata'] = self._get_metadata()

        if 'related' in include :
            data['related'] = {
                'cert_data' : self.cert_data.get_compact_data() if self.cert_data else None ,
                'related_object' : self._get_related_object_data(related_obj) ,
                'created_by' : {
                    'id' : self.created_by_id ,
                    'username' : self.created_by.username if self.created_by else None
                } if self.created_by else None
            }

        return data

    def get_related_object(self) :
        """
        Получить связанный объект.
        Сначала пытается получить через конкретное поле, затем через generic.
        """
        # Пытаемся получить через конкретное поле
        concrete_field = self._get_concrete_relation_field()
        if concrete_field :
            return getattr(self , concrete_field , None)

        # Иначе через generic relation
        if self.content_type and self.object_id :
            try :
                return self.content_type.get_object_for_this_type(pk=self.object_id)
            except :
                return None

        return None

    def get_certificate_data(self , format='compact') :
        """
        Получить данные сертификата в указанном формате.

        Args:
            format: 'compact', 'display', 'full'
        """
        if not self.cert_data :
            return None

        if format == 'compact' :
            return self.cert_data.get_compact_data()
        elif format == 'display' :
            return self.cert_data.get_display_data()
        elif format == 'full' :
            return self.cert_data.get_full_data()

        return self.cert_data.get_compact_data()

    def is_valid_for_date(self , date=None) :
        """
        Проверить действительность связи на указанную дату.

        Args:
            date: Дата для проверки (по умолчанию сегодня)
        """
        from datetime import date as date_type

        if date is None :
            date = date_type.today()

        # Проверяем основные условия
        if not self.valid_for_model :
            return False

        if self.expires_on_model and date > self.expires_on_model :
            return False

        if self.applied_date and date < self.applied_date :
            return False

        # Также проверяем валидность самого сертификата
        if self.cert_data and self.cert_data.valid_until :
            if date > self.cert_data.valid_until :
                return False

        return True

    # Вспомогательные методы

    def _get_concrete_relation_fields(self) :
        """
        Получить список полей конкретных связей в дочернем классе.
        Должен быть переопределен в дочерних классах.
        """
        # По умолчанию ищем ForeignKey поля кроме cert_data
        return [
            field.name for field in self._meta.get_fields()
            if field.is_relation and field.many_to_one and
               field.name not in ['cert_data' , 'content_type' , 'created_by']
        ]

    def _get_concrete_relation_field(self) :
        """
        Получить имя поля конкретной связи если оно заполнено.
        """
        for field_name in self._get_concrete_relation_fields() :
            if hasattr(self , field_name) and getattr(self , field_name) is not None :
                return field_name
        return None

    def _format_dates(self) :
        """Форматирование дат для отображения"""
        from django.utils.formats import date_format

        parts = []
        if self.applied_date :
            parts.append(f"{_('Применен')}: {date_format(self.applied_date , 'd.m.Y')}")
        if self.expires_on_model :
            parts.append(f"{_('Действует до')}: {date_format(self.expires_on_model , 'd.m.Y')}")

        return '; '.join(parts) if parts else _('Даты не указаны')

    def _get_metadata(self) :
        """Метаданные для форм"""
        return {
            'field_schema' : [
                {
                    'name' : 'cert_data_id' ,
                    'type' : 'select' ,
                    'required' : True ,
                    'label' : _('Сертификат') ,
                    'help_text' : _('Выберите сертификат')
                } ,
                {
                    'name' : 'is_primary' ,
                    'type' : 'boolean' ,
                    'required' : False ,
                    'label' : _('Основной сертификат') ,
                    'help_text' : _('Отметьте если это основной сертификат')
                } ,
                # ... другие поля
            ]
        }

    def _get_related_object_data(self , related_obj) :
        """Данные связанного объекта"""
        if not related_obj :
            return None

        data = {
            'id' : related_obj.id ,
            'str' : str(related_obj) ,
            'model' : related_obj.__class__.__name__ ,
            'app' : related_obj._meta.app_label ,
        }

        # Если у объекта есть методы get_*_data, используем их
        if hasattr(related_obj , 'get_compact_data') :
            try :
                data['compact'] = related_obj.get_compact_data()
            except :
                pass

        return data


# Пример конкретной through-модели для продуктов
# class ProductCertRelation(AbstractCertRelation) :
#     """
#     Связь сертификатов с продуктами.
#     """
#     product = models.ForeignKey(
#         'products.Product' ,  # Замените на реальный путь к модели Product
#         on_delete=models.CASCADE ,
#         verbose_name=_("Продукт") ,
#         related_name='cert_relations'
#     )
#
#     # Можно добавить специфичные для продуктов поля
#     is_for_production = models.BooleanField(
#         default=True ,
#         verbose_name=_("Для производства") ,
#         help_text=_("Используется в производстве данного продукта")
#     )
#
#     class Meta(AbstractCertRelation.Meta) :
#         verbose_name = _("Связь сертификата с продуктом")
#         verbose_name_plural = _("Связи сертификатов с продуктами")
#         unique_together = ['cert_data' , 'product']
#
#     def get_display_data(self , view_type='detail') :
#         """Расширяем данные для продуктов"""
#         data = super().get_display_data(view_type)
#
#         if view_type == 'detail' and 'fields' in data :
#             data['fields']['production_use'] = {
#                 'label' : _('Использование в производстве') ,
#                 'value' : _('Да') if self.is_for_production else _('Нет') ,
#                 'type' : 'boolean' ,
#                 'icon' : '🏭' if self.is_for_production else '📦' ,
#                 'priority' : 7
#             }
#
#         return data


# Пример конкретной through-модели для проектов
# class ProjectCertRelation(AbstractCertRelation) :
#     """
#     Связь сертификатов с проектами.
#     """
#     project = models.ForeignKey(
#         'projects.Project' ,  # Замените на реальный путь к модели Project
#         on_delete=models.CASCADE ,
#         verbose_name=_("Проект") ,
#         related_name='cert_relations'
#     )
#
#     # Специфичные для проектов поля
#     requirement_type = models.CharField(
#         max_length=50 ,
#         choices=[
#             ('mandatory' , _('Обязательный')) ,
#             ('recommended' , _('Рекомендуемый')) ,
#             ('optional' , _('Опциональный')) ,
#         ] ,
#         default='mandatory' ,
#         verbose_name=_("Тип требования") ,
#         help_text=_("Тип требования к сертификату в проекте")
#     )
#
#     class Meta(AbstractCertRelation.Meta) :
#         verbose_name = _("Связь сертификата с проектом")
#         verbose_name_plural = _("Связи сертификатов с проектами")
#         unique_together = ['cert_data' , 'project']