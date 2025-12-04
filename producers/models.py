#producers\models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any

from core.models import StructuredDataMixin


class Brands(StructuredDataMixin , models.Model) :  # Добавить наследование
    """
    Модель бренда производителя
    """
    name = models.CharField(
        max_length=100 ,
        verbose_name=_('Название') ,
        help_text=_('Название бренда производителя')
    )
    code = models.CharField(
        max_length=50 ,
        blank=True ,
        null=True ,
        # unique=True,  # Раскомментируйте если нужно
        verbose_name=_("Код бренда") ,
        help_text=_('Уникальный код бренда')
    )
    description = models.TextField(
        blank=True ,
        verbose_name=_("Описание") ,
        help_text=_('Описание бренда и его особенностей')
    )
    sorting_order = models.IntegerField(
        default=0 ,
        verbose_name=_("Порядок сортировки") ,
        help_text=_('Порядок сортировки в списках')
    )
    is_active = models.BooleanField(
        default=True ,
        verbose_name=_("Активно") ,
        help_text=_('Активен ли бренд для использования')
    )

    class Meta :
        # Для обратной совместимости с существующей БД
        db_table = 'producers_brands'  # или другое реальное имя
        ordering = ['sorting_order' , 'name']
        verbose_name = _('Бренд')
        verbose_name_plural = _('Бренды')

    def __str__(self) :
        return self.name

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц
        """
        # Безопасный доступ к метаданным
        model_name = self._get_model_name()
        app_label = self._get_app_label()

        return {
            'id' : self.id ,
            'name' : self.name ,
            'code' : self.code ,
            'is_active' : self.is_active ,
            'model' : model_name ,  # Используем безопасный метод
            'app' : app_label ,  # Используем безопасный метод
        }

    def get_display_data(self , view_type: str = 'detail') -> Dict[str , Any] :
        """
        Данные для отображения в UI
        """
        # Используем константы из миксина
        if view_type == self.CARD :  # Используем self.CARD
            return {
                'title' : self.name ,
                'subtitle' : self.code or '' ,
                'description' : self.description[:100] + '...' if self.description else '' ,
                'badges' : [
                    {'text' : self.code , 'type' : 'code'} if self.code else None ,
                    {'text' : 'Активен' , 'type' : 'success'} if self.is_active
                    else {'text' : 'Неактивен' , 'type' : 'secondary'} ,
                ] ,
                'details' : [
                    {'label' : 'Сортировка' , 'value' : self.sorting_order} ,
                ]
            }

        elif view_type == self.LIST :  # Используем self.LIST
            return {
                'id' : self.id ,
                'name' : self.name ,
                'code' : self.code ,
                'is_active' : self.is_active ,
                'sorting_order' : self.sorting_order ,
            }

        elif view_type == self.BADGE :  # Используем self.BADGE
            return {
                'text' : self.name ,
                'code' : self.code ,
                'type' : 'brand' ,
                'color' : 'green' if self.is_active else 'gray' ,
            }

        # По умолчанию DETAIL - используем базовые поля
        fields = self._get_base_display_fields()  # Используем метод миксина

        # Добавляем description и sorting_order
        fields['description'] = self._format_field(
            self.description ,
            'text' ,
            label=_('Описание') ,
            icon='📄' ,
            priority=3 ,
            multiline=True
        )

        fields['sorting_order'] = self._format_field(
            self.sorting_order ,
            'number' ,
            label=_('Порядок сортировки') ,
            icon='🔢' ,
            priority=4
        )

        return {
            'title' : self.name ,
            'subtitle' : f'Код: {self.code}' if self.code else '' ,
            'fields' : fields ,
            'actions' : self._get_actions()  # Используем метод миксина
        }

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API
        """
        if include is None :
            include = ['form' , 'metadata' , 'related']

        # Используем безопасные методы для метаданных
        model_name = self._get_model_name()
        app_label = self._get_app_label()

        data = {
            'id' : self.id ,
            'model' : model_name ,
            'app' : app_label ,
            'is_active' : self.is_active ,
            'sorting_order' : self.sorting_order ,
            'display' : self.get_display_data() ,
        }

        if 'form' in include :
            data['form'] = {
                'name' : self.name ,
                'code' : self.code ,
                'description' : self.description ,
                'sorting_order' : self.sorting_order ,
                'is_active' : self.is_active ,
            }

        if 'metadata' in include :
            data['metadata'] = self._get_metadata()

        if 'related' in include :
            data['related'] = None #self._get_related_data()

        return data

    # ==================== Вспомогательные методы ====================

    def _get_metadata(self) -> Dict[str , Any] :
        """
        Метаданные для форм
        """
        return {
            'field_schema' : [
                {
                    'name' : 'name' ,
                    'type' : 'text' ,
                    'required' : True ,
                    'label' : _('Название бренда') ,
                    'help_text' : _('Название бренда производителя') ,
                    'max_length' : 100 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'code' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Код бренда') ,
                    'help_text' : _('Уникальный код бренда') ,
                    'max_length' : 50 ,
                    'widget' : 'text_input' ,
                    'pattern' : r'^[A-Z0-9_-]*$'
                } ,
                {
                    'name' : 'description' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Описание') ,
                    'help_text' : _('Описание бренда и его особенностей') ,
                    'widget' : 'textarea' ,
                    'rows' : 4
                } ,
                {
                    'name' : 'sorting_order' ,
                    'type' : 'number' ,
                    'required' : False ,
                    'label' : _('Порядок сортировки') ,
                    'help_text' : _('Порядок отображения в списках') ,
                    'min_value' : -100 ,
                    'max_value' : 100 ,
                    'default' : 0
                } ,
                {
                    'name' : 'is_active' ,
                    'type' : 'boolean' ,
                    'required' : False ,
                    'label' : _('Активно') ,
                    'help_text' : _('Активен ли бренд для использования') ,
                    'default' : True
                }
            ] ,
            'validation_rules' : {
                'name' : {
                    'required' : True ,
                    'min_length' : 2 ,
                    'max_length' : 100
                } ,
                'code' : {
                    'pattern' : r'^[A-Z0-9_-]*$' ,
                    'message' : _('Код должен содержать только буквы, цифры, дефисы и подчеркивания')
                }
            }
        }

    # ==================== Утилитарные методы ====================

    def get_absolute_url(self) :
        """
        URL для детальной страницы бренда
        """
        return f"/brands/{self.id}/"

    def get_admin_url(self) :
        """
        URL в админке Django
        """
        return f"/admin/producers/brand/{self.id}/change/"  # предполагаю app_label = producers

    def get_logo_url(self) :
        """
        Получить URL логотипа бренда (если есть)
        """
        # Можно оставить или убрать, если нет связи с логотипом
        if hasattr(self , 'logo') :
            return self.logo.url if self.logo else None
        return None


class Producer(StructuredDataMixin , models.Model) :
    name = models.CharField(max_length=100 ,
                            verbose_name=_("Название производителя"))
    code = models.CharField(max_length=50 , blank=True , null=True ,
                            verbose_name=_("Код производителя"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))
    organization = models.CharField(max_length=100 , blank=True , verbose_name='Организация')
    brands = models.ManyToManyField('Brands' , related_name='producer_brands' , verbose_name='Бренды')

    class Meta :
        verbose_name = _('Производитель')
        verbose_name_plural = _('Производители')
        ordering = ['sorting_order' , 'name']

    def __str__(self) :
        return self.name

    # ==================== StructuredDataMixin методы ====================

    def get_compact_data(self) -> Dict[str , Any] :
        """
        Минимальные данные для списков и таблиц
        """
        return {
            'id' : self.id ,
            'name' : self.name ,
            'code' : self.code ,
            'organization' : self.organization ,
            'brands_count' : self.brands.count() if hasattr(self , 'brands') else 0 ,
            'is_active' : self.is_active ,
            'model' : self._get_model_name() ,
            'app' : self._get_app_label() ,
        }

    def get_display_data(self , view_type: str = 'detail') -> Dict[str , Any] :
        """
        Данные для отображения в UI
        """
        # Используем базовые поля из миксина
        fields = self._get_base_display_fields()

        # Обновляем лейблы
        if 'name' in fields :
            fields['name']['label'] = _('Название производителя')
            fields['name']['priority'] = 1

        if 'code' in fields :
            fields['code']['label'] = _('Код производителя')
            fields['code']['priority'] = 2

        # Добавляем специфичные поля
        fields.update({
            'organization' : self._format_field(
                self.organization ,
                'text' ,
                label=_('Организация') ,
                icon='🏢' ,
                priority=3
            ) ,
            'description' : self._format_field(
                self.description ,
                'text' ,
                label=_('Описание') ,
                icon='📄' ,
                priority=4 ,
                multiline=True
            ) ,
            'sorting_order' : self._format_field(
                self.sorting_order ,
                'number' ,
                label=_('Порядок сортировки') ,
                icon='🔢' ,
                priority=5
            ) ,
        })

        # Добавляем бренды
        if hasattr(self , 'brands') :
            fields['brands'] = self._format_many_to_many(
                self.brands.all() ,
                label=_('Бренды') ,
                icon='🏷️' ,
                priority=6 ,
                include_data='compact'  # Используем compact данные брендов
            )

        if view_type == self.CARD :
            return {
                'title' : self.name ,
                'subtitle' : self.code or '' ,
                'description' : self.description[:100] + '...' if self.description else '' ,
                'badges' : [
                    {'text' : self.code , 'type' : 'code'} if self.code else None ,
                    {'text' : self.organization , 'type' : 'organization'} if self.organization else None ,
                    {'text' : 'Активен' , 'type' : 'success'} if self.is_active
                    else {'text' : 'Неактивен' , 'type' : 'secondary'} ,
                    {'text' : f'{self.brands.count()} брендов' , 'type' : 'info'} if hasattr(self ,
                                                                                             'brands') else None ,
                ] ,
                'details' : [
                    {'label' : 'Сортировка' , 'value' : self.sorting_order} ,
                ]
            }

        elif view_type == self.LIST :
            brands_count = self.brands.count() if hasattr(self , 'brands') else 0
            return {
                'id' : self.id ,
                'name' : self.name ,
                'code' : self.code ,
                'organization' : self.organization ,
                'brands_count' : brands_count ,
                'is_active' : self.is_active ,
                'sorting_order' : self.sorting_order ,
            }

        elif view_type == self.BADGE :
            return {
                'text' : self.name ,
                'code' : self.code ,
                'type' : 'producer' ,
                'color' : 'purple' if self.is_active else 'gray' ,
            }

        # По умолчанию DETAIL
        return {
            'title' : self.name ,
            'subtitle' : f'{self.organization} ({self.code})' if self.code and self.organization else
            self.code or self.organization or '' ,
            'fields' : fields ,
            'actions' : self._get_actions()
        }

    def get_full_data(self , include: Optional[List[str]] = None) -> Dict[str , Any] :
        """
        Полные данные для форм и API
        """
        if include is None :
            include = ['form' , 'metadata' , 'related']

        data = {
            'id' : self.id ,
            'model' : self._get_model_name() ,
            'app' : self._get_app_label() ,
            'is_active' : self.is_active ,
            'sorting_order' : self.sorting_order ,
            'display' : self.get_display_data() ,
        }

        if 'form' in include :
            data['form'] = {
                'name' : self.name ,
                'code' : self.code ,
                'description' : self.description ,
                'organization' : self.organization ,
                'sorting_order' : self.sorting_order ,
                'is_active' : self.is_active ,
                'brands_ids' : list(self.brands.values_list('id' , flat=True)) if hasattr(self , 'brands') else [] ,
            }

        if 'metadata' in include :
            data['metadata'] = self._get_metadata()

        if 'related' in include :
            data['related'] = self._get_related_data()

        return data

    # ==================== Вспомогательные методы ====================

    def _get_metadata(self) -> Dict[str , Any] :
        """
        Метаданные для форм
        """
        return {
            'field_schema' : [
                {
                    'name' : 'name' ,
                    'type' : 'text' ,
                    'required' : True ,
                    'label' : _('Название производителя') ,
                    'help_text' : _('Полное название производителя') ,
                    'max_length' : 100 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'code' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Код производителя') ,
                    'help_text' : _('Уникальный код производителя') ,
                    'max_length' : 50 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'organization' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Организация') ,
                    'help_text' : _('Юридическое название организации') ,
                    'max_length' : 100 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'description' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Описание') ,
                    'help_text' : _('Описание производителя и его особенностей') ,
                    'widget' : 'textarea' ,
                    'rows' : 4
                } ,
                {
                    'name' : 'sorting_order' ,
                    'type' : 'number' ,
                    'required' : False ,
                    'label' : _('Порядок сортировки') ,
                    'help_text' : _('Порядок отображения в списках') ,
                    'min_value' : -100 ,
                    'max_value' : 100 ,
                    'default' : 0
                } ,
                {
                    'name' : 'is_active' ,
                    'type' : 'boolean' ,
                    'required' : False ,
                    'label' : _('Активно') ,
                    'help_text' : _('Активен ли производитель для использования') ,
                    'default' : True
                } ,
                {
                    'name' : 'brands' ,
                    'type' : 'many_to_many' ,
                    'required' : False ,
                    'label' : _('Бренды') ,
                    'help_text' : _('Бренды, принадлежащие производителю') ,
                    'model' : 'producers.Brands' ,
                    'widget' : 'select_multiple'
                }
            ] ,
            'validation_rules' : {
                'name' : {
                    'required' : True ,
                    'min_length' : 2 ,
                    'max_length' : 100
                } ,
                'code' : {
                    'pattern' : r'^[A-Z0-9_-]*$' ,
                    'message' : _('Код должен содержать только буквы, цифры, дефисы и подчеркивания')
                }
            }
        }

    def _get_related_data(self) -> Dict[str , Any] :
        """
        Связанные данные
        """
        related_data = {
            'brands_count' : self.brands.count() if hasattr(self , 'brands') else 0 ,
        }

        # Добавляем compact данные брендов
        if hasattr(self , 'brands') :
            related_data['brands'] = [
                brand.get_compact_data()
                for brand in self.brands.all()
            ]

        return related_data

    # ==================== Утилитарные методы ====================

    def get_absolute_url(self) :
        """
        URL для детальной страницы производителя
        """
        return f"/producers/{self.id}/"

    def get_admin_url(self) :
        """
        URL в админке Django
        """
        return f"/admin/producers/producer/{self.id}/change/"

    def get_brands_list(self) :
        """
        Получить список брендов производителя
        """
        if hasattr(self , 'brands') :
            return list(self.brands.all())
        return []

    def get_brands_names(self) :
        """
        Получить названия брендов производителя
        """
        if hasattr(self , 'brands') :
            return [brand.name for brand in self.brands.all()]
        return []

    @property
    def active_brands_count(self) :
        """
        Количество активных брендов
        """
        if hasattr(self , 'brands') :
            return self.brands.filter(is_active=True).count()
        return 0

# Особенности реализации:
# ManyToManyField для brands - используем _format_many_to_many() с include_data='compact'
#
# Подсчет брендов в compact данных
#
# Отображение организации в карточке
#
# Полный список ID брендов в form данных
#
# Автоматическое получение данных брендов через их get_compact_data()
# Использование через UniversalAPIView:
# # Получить производителя с брендами
# GET /api/core/?model=producers.Producer&id=1&format=full&include=related
#
# # Получить список производителей
# GET /api/core/?model=producers.Producer&format=compact
#
# # Получить производителя для карточки
# GET /api/core/?model=producers.Producer&id=1&format=display&view=card
