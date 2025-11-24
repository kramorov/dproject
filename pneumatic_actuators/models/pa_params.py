# pneumatic_actuators/models/pa_params.py
from django.db import models
from django.utils.translation import gettext_lazy as _



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

class PneumaticActuatorConstructionVariety(models.Model) :
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


