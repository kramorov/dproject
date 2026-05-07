from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import TemplateFillerMixin, GetChoicesMixin


class SignalType(models.Model):
    """Тип сигнала (NAMUR, PNP, Сухой контакт, 4-20мА и т.д.)"""
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    code = models.CharField(max_length=50, verbose_name=_("Код"))
    is_ex = models.BooleanField(default=False, help_text=_(
        "Флаг определяет, требуется ли для данного сигнала расчет искробезопасных параметров и барьер"),
                                verbose_name="Взрывозащищенный (Ex)")
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Подробное описание физического принципа работы сигнала'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = "Тип сигнала"
        verbose_name_plural = "Типы сигналов"

    def __str__(self): return self.name


class ContactState(models.Model):
    """Состояние контакта (НО, НЗ, Перекидной)"""
    name = models.CharField(max_length=100, help_text=_("Пользовательское описание (например, 'Нормально разомкнутый')"
                                                        ), verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True,
                            help_text=_("Технический код состояния: NO (разомкнут), NC (замкнут), CO (перекидной)"
                                        ), verbose_name=_("Код"))  # NO, NC, CHANGE_OVER
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_(
                                       "Описание состояния контакта в 'нормальном' (невозбужденном) положении датчика"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = "Состояние контакта"
        verbose_name_plural = "Состояния контактов"

    def __str__(self): return self.name


class ContactForm(models.Model):
    """Форма контактов (SPST, SPDT, DPDT)"""
    name = models.CharField(max_length=100,
                            help_text=_("Техническое наименование (например, 'Однополюсный перекидной')"),
                            verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True, help_text=_("Международное сокращение (SPST, SPDT, DPDT, DPST)"
                                                                    ), verbose_name=_("Код"))
    wires_required = models.PositiveSmallIntegerField(
        help_text=_("Минимальное количество жил кабеля для подключения одной единицы (напр. SPDT = 3 провода)"
                    ), verbose_name="Базовое кол-во проводов")
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Схематичное описание работы или примечания по монтажу'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _("Форма контактов")
        verbose_name_plural = _("Формы контактов")

    def __str__(self): return f'{self.name}/{self.code}'


class LimitSwitchSensorVariety(TemplateFillerMixin, GetChoicesMixin, models.Model):
    """Тип сенсора концевого выключателя (механический, индуктивный, магнитный, пневматический)"""
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа сенсора БКВ")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа сенсора БКВ"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа сенсораа БКВ'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    name_template = models.TextField(blank=True , null=True ,
                                     verbose_name=_("Шаблон названия") ,
                                     help_text=_('Шаблон для текстового названия сенсора'))
    description_template = models.TextField(blank=True , null=True ,
                                            verbose_name=_("Шаблон описания") ,
                                            help_text=_('Шаблон для описания сенсора'))
    class Meta:
        verbose_name = _("Тип сенсора БКВ")
        verbose_name_plural = _("Типы сенсоров БКВ")

    def __str__(self):
        return self.name
