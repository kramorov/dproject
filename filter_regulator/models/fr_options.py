#filter_requlator/models/fr_options.py

from django.db import models
from django.utils.translation import gettext_lazy as _

class DrainVariety(models.Model):
    """ Название типа слива: Ручной, Авто, Полуавто
    """
    name = models.CharField(max_length=200 ,
                            verbose_name=_("Название типа слива") ,
                            help_text=_('Текстовое название название типа слива'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код типа слива"))

    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание типа слива'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _("Тип слива")
        verbose_name_plural = _("Типы слива")

    def __str__(self): return self.name

class FilterRegulatorVariety(models.Model):
    """Тип фильтр-регулятора"""

    name = models.CharField(max_length=200 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Название типа фильтра-регулятора")
                            )
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код типа фильтра-регулятора"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание типа фильтра-регулятора'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        verbose_name = _("Тип фильтр-регулятора")
        verbose_name_plural = _("Типы фильтр-регуляторов")

    def __str__(self) :
        return self.name
