# pneumatic_fittings/fitting_parameters.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import StructuredDataMixin, LocalizedDictFieldsMixin

class SilencerShape(StructuredDataMixin , LocalizedDictFieldsMixin) :
    name = models.CharField(max_length=100 , verbose_name=_("Название формы"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Форма глушителя - описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Форма глушителя"
        verbose_name_plural = "Формы глушителей"

    def __str__(self) :
        return self.name

class PlugSilencerBodyMaterial(StructuredDataMixin , LocalizedDictFieldsMixin) :
    # сетчатый фильтрующий элемент из спеченной бронзы
    name = models.CharField(max_length=100 , verbose_name=_("Название материала корпуса"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Описание материала корпуса"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Материал корпуса глушителя/заглушки"
        verbose_name_plural = "Материалы корпуса глушителя/заглушки"

    def __str__(self) :
        return self.name

class SilencerFilterElement(StructuredDataMixin , LocalizedDictFieldsMixin) :
    # сетчатый фильтрующий элемент из спеченной бронзы
    name = models.CharField(max_length=100 , verbose_name=_("Название материала фильтрующего элемента глушителя"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Описание материала фильтрующего элемента глушителя"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Материал фильтрующего элемента глушителя"
        verbose_name_plural = "Материалы фильтрующего элемента глушителей"

    def __str__(self) :
        return self.name

class FittingShape(StructuredDataMixin , LocalizedDictFieldsMixin) :
    name = models.CharField(max_length=100 , verbose_name=_("Название формы"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Краткое описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Особенности применения"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Форма фитинга"
        verbose_name_plural = "Формы фитингов"

    def __str__(self) :
        return self.name


class FittingFixationMethod(StructuredDataMixin , LocalizedDictFieldsMixin) :
    name = models.CharField(max_length=100 , verbose_name=_("Название способа"))
    code = models.SlugField(max_length=50 , unique=True , verbose_name=_("Код"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    help_text_content = models.TextField(blank=True , verbose_name=_("Описание для подсказок"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = "Способ фиксации фитинга"
        verbose_name_plural = "Способы фиксации фитингов"

    def __str__(self) :
        return self.name
