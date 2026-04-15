# pneumatic_actuators/models/pa_params.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models.mixins import StructuredDataMixin

class PneumaticActuatorSpringsQty(models.Model) :
    """
    Количество пружин в пневмоприводе SR
    """
    name = models.CharField(max_length=10 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название кол-ва пружин'))
    code = models.CharField(max_length=10 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код кол-ва пружин"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание кол-ва пружин'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Название кол-ва пружин пневмопривода SR')
        verbose_name_plural = _('Названия кол-ва пружин пневмопривода SR')

    def __str__(self) :
        return self.name

class PneumaticActuatorVariety(models.Model) :
    """
    Разновидности пневмоприводов- DA или SR
    """
    name = models.CharField(max_length=10 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название разновидности'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код разновидности привода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание модели корпуса привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Название разновидности пневмопривода - DA/SR')
        verbose_name_plural = _('Названия разновидностей пневмопривода - DA/SR')

    def __str__(self) :
        return self.name

    @classmethod
    def get_for_select(cls , active_only=True) :
        """Получить виды приводов для выпадающего списка"""
        queryset = cls.objects.all()
        if active_only :
            queryset = queryset.filter(is_active=True)
        return [{'id' : obj.id , 'name' : obj.name , 'code' : obj.code} for obj in queryset]

class PneumaticActuatorConstructionVariety(StructuredDataMixin , models.Model) :
    """
    Разновидности конструкций пневмоприводов- шестерня-рейка или кулисный
    """
    name = models.CharField(max_length=10 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название разновидности конструкции'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код разновидности конструкции привода"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание разновидности конструкции привода'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Название разновидности конструкции привода - RP/SY')
        verbose_name_plural = _('Названия разновидностей конструкции привода - RP/SY')

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

        # Обновляем лейблы и приоритеты для нашей модели
        if 'name' in fields :
            fields['name']['label'] = _('Название конструкции')
            fields['name']['priority'] = 1

        if 'code' in fields :
            fields['code']['label'] = _('Код конструкции')
            fields['code']['priority'] = 2

        # Добавляем description
        fields['description'] = self._format_field(
            self.description ,
            'text' ,
            label=_('Описание') ,
            icon='📄' ,
            priority=3 ,
            multiline=True
        )

        # Добавляем sorting_order
        fields['sorting_order'] = self._format_field(
            self.sorting_order ,
            'number' ,
            label=_('Порядок сортировки') ,
            icon='🔢' ,
            priority=4
        )

        if view_type == self.CARD :
            return {
                'title' : self.name ,
                'subtitle' : self.code or '' ,
                'description' : self.description[:100] + '...' if self.description else '' ,
                'badges' : [
                    {'text' : self.code , 'type' : 'code'} if self.code else None ,
                    {'text' : 'Активна' , 'type' : 'success'} if self.is_active
                    else {'text' : 'Неактивна' , 'type' : 'secondary'} ,
                ] ,
                'details' : [
                    {'label' : 'Сортировка' , 'value' : self.sorting_order} ,
                ]
            }

        elif view_type == self.LIST :
            return {
                'id' : self.id ,
                'name' : self.name ,
                'code' : self.code ,
                'is_active' : self.is_active ,
                'sorting_order' : self.sorting_order ,
            }

        elif view_type == self.BADGE :
            return {
                'text' : self.name ,
                'code' : self.code ,
                'type' : 'construction_variety' ,
                'color' : 'blue' if self.is_active else 'gray' ,
            }

        # По умолчанию DETAIL
        return {
            'title' : self.name ,
            'subtitle' : f'Код: {self.code}' if self.code else '' ,
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
                'sorting_order' : self.sorting_order ,
                'is_active' : self.is_active ,
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
                    'label' : _('Название конструкции') ,
                    'help_text' : _('Название разновидности конструкции') ,
                    'max_length' : 10 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'code' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Код конструкции') ,
                    'help_text' : _('Код разновидности конструкции привода') ,
                    'max_length' : 50 ,
                    'widget' : 'text_input'
                } ,
                {
                    'name' : 'description' ,
                    'type' : 'text' ,
                    'required' : False ,
                    'label' : _('Описание') ,
                    'help_text' : _('Текстовое описание разновидности конструкции привода') ,
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
                    'help_text' : _('Активно свойство или нет') ,
                    'default' : True
                }
            ] ,
            'validation_rules' : {
                'name' : {
                    'required' : True ,
                    'min_length' : 2 ,
                    'max_length' : 10
                }
            }
        }

    def _get_related_data(self) -> Dict[str , Any] :
        """
        Связанные данные
        """
        # Можно добавить подсчет связанных серий пневмоприводов
        return {
            'model_lines_count' : getattr(self , '_model_lines_count' , 0) ,
        }

    # ==================== Утилитарные методы ====================

    def get_absolute_url(self) :
        """
        URL для детальной страницы
        """
        return f"/pneumatic-actuators/construction-varieties/{self.id}/"

    def get_admin_url(self) :
        """
        URL в админке Django
        """
        return f"/admin/pneumatic_actuators/pneumaticactuatorconstructionvariety/{self.id}/change/"


