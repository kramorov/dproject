# params/models.py
from django.db import models
# from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


# PowerSupplies, ExdOption, IpOption, BodyCoatingOption,BlinkerOption,SwitchesParameters, EnvTempParameters, \
# DigitalProtocolsSupportOption, ControlUnitInstalledOption,ActuatorType, ValveTypes, GearBoxTypes, \
# HandWheelInstalledOption, OperatingModeOption

class PowerSupplies(models.Model):
    VOLTAGE_TYPES = [
        ('AC', 'AC - Переменный ток'),
        ('DC', 'DC - Постоянный ток'),
    ]
    name = models.CharField(max_length=100,blank=True, null=True,
                            help_text=_("Символьное обозначение типа напряжения"),
                            verbose_name=_("Название"))
    code = models.CharField(max_length=50, blank=True, null=True,
                            help_text=_("Код типа напряжения"),
                            verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0,
                                        verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    voltage_value = models.IntegerField(verbose_name=_('Значение напряжения'))
    voltage_type = models.CharField(max_length=2, choices=VOLTAGE_TYPES, default='AC',
                                    verbose_name=_('Тип напряжения'))

    class Meta:
        verbose_name = _('Тип напряжения питания')
        verbose_name_plural = _('Типы напряжения питания')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ControlUnitLocationOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            help_text=_("Символьное обозначение типа размещения блока управления"),
                            verbose_name=_("Название"))
    code = models.CharField(max_length=50, blank=True, null=True,
                            help_text=_("Код типа размещения блока управления"),
                            verbose_name=_("Код"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0,
                                        verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))


    class Meta:
        verbose_name = _('Место размещения блока управления')
        verbose_name_plural = _('Места размещения блока управления')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ControlUnitTypeOption(models.Model):
    name = models.CharField(max_length=100,blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение типа размещения блока управления")
                            )
    code = models.CharField(max_length=50, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_("Код типа размещения блока управления"))
    description = models.TextField(blank=True,
                                   verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа блока управления'))
    sorting_order = models.IntegerField(default=0,
                                        verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                        help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Тип блока управления')
        verbose_name_plural = _('Типы блоков управления')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class SafetyPositionOption(models.Model):
    name = models.CharField(max_length=100,blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение положения функции безопасности")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код обозначение положения функции безопасности"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание положения функции безопасности'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Безопасное положение при отсутствии питания')
        verbose_name_plural = _('Безопасные положения при отсутствии питания')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ExdOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение вида взрывозащиты")
                            )
    code = models.CharField(max_length=50, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_("Код вида взрывозащиты"))
    description = models.TextField(blank=True,
                                   verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание вида взрывозащиты'))
    sorting_order = models.IntegerField(default=0,
                                        verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    exd_full_code = models.CharField(max_length=200, verbose_name=_('Полный код взрывозащиты'),
                                     help_text=_('Полный код вида взрывозащиты'))

    class Meta:
        verbose_name = _('Тип взрывозащиты')
        verbose_name_plural = _('Типы взрывозащиты')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class IpOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение исполнения IP")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код исполнения IP"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание исполнения IP'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    ip_rank = models.IntegerField(verbose_name=_('Ранг IP'), help_text=_('Приоритет исполнения IP (выше - лучше)'))


    class Meta:
        verbose_name = _('Вид защиты IP')
        verbose_name_plural = _('Виды защиты IP')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class BodyCoatingOption(models.Model):
    # TODO: Объединить этот класс с классом в Valve_data добавить толщину покрытия
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное название типа покрытия оболочки привода от коррозии")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа покрытия оболочки привода от коррозии"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа покрытия оболочки привода от коррозии'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Опция покрытия корпуса')
        verbose_name_plural = _('Опции покрытия корпуса')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class BlinkerOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение наличия блинкера")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код наличия блинкера"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание наличия блинкера'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Опция блинкера')
        verbose_name_plural = _('Опции блинкера')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class SwitchesParameters(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение характеристик выключателей")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код характеристик выключателей"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание характеристик выключателей'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Вид выключателей')
        verbose_name_plural = _('Параметры выключателей')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class EnvTempParameters(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение типа температурного исполнения")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код температурного исполнения"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа температурного исполнения'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    min_temp = models.IntegerField(verbose_name=_('Минимальная температура'))
    max_temp = models.IntegerField(verbose_name=_('Максимальная температура'))

    class Meta:
        verbose_name = _('Параметр температурной среды')
        verbose_name_plural = _('Параметры температурной среды')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ClimaticZoneClassifier(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Символьное обозначение типа климатической зоны")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код климатической зоны"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа климатической зоны'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Классификатор климатической зоны')
        verbose_name_plural = _('Классификаторы климатических зон')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ClimaticEquipmentPlacementClassifier(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название категории размещения оборудования")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код категории размещения оборудования"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание категории размещения оборудования'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Классификатор размещения оборудования')
        verbose_name_plural = _('Классификаторы размещения оборудования')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ClimaticConditions(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название значения температуры по климатическому исполнению")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код значения температуры по климатическому исполнению"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание значения температуры по климатическому исполнению'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    climaticZone = models.ForeignKey(ClimaticZoneClassifier, on_delete=models.SET_NULL, null=True,
                                     verbose_name=_('Климатическая зона'), help_text=_("Тип климатической зоны"))
    climaticPlacement = models.ForeignKey(ClimaticEquipmentPlacementClassifier, on_delete=models.SET_NULL, null=True,
                                          verbose_name=_('Категория размещения'),
                                          help_text=_("Тип климатической зоны"))
    min_temp_work = models.IntegerField(verbose_name=_("Мин. рабочая температура, °С"),
                                        help_text=_("Значение температуры воздуха при эксплуатации Рабочее, мин, °С"))
    max_temp_work = models.IntegerField(verbose_name=_("Макс. рабочая температура, °С"),
                                        help_text=_("Значение температуры воздуха при эксплуатации Рабочее, макс, °С"))
    min_temp_extremal = models.IntegerField(verbose_name=_("Мин. предельная температура, °С"), help_text=_(
        "Значение температуры воздуха при эксплуатации Предельное, мин, °С"))
    max_temp_extremal = models.IntegerField(verbose_name=_("Макс. предельная температура, °С"), help_text=_(
        "Значение температуры воздуха при эксплуатации Предельное, макс, °С"))

    class Meta:
        verbose_name = _('Значения температуры по климатическому исполнению по ГОСТ 15150-69')
        verbose_name_plural = _('Значения температуры по климатическому исполнению по ГОСТ 15150-69')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class DigitalProtocolsSupportOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название обозначения поддерживаемого цифрового протокола")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код обозначения поддерживаемого цифрового протокола"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание поддерживаемого цифрового протокола'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Поддерживаемый цифровой протокол')
        verbose_name_plural = _('Поддерживаемые цифровые протоколы')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class MechanicalIndicatorInstalledOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название обозначения установленного механического индикатора положения")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код обозначения установленного механического индикатора положения"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание установленного механического индикатора положения'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Вид механического индикатора')
        verbose_name_plural = _('Виды механических индикаторов')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ControlUnitInstalledOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название обозначения установленного на приводе блока управления")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код обозначения установленного на приводе блока управления"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание установленного на приводе блока управления'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    encoding = models.CharField(max_length=10, verbose_name=_('Кодировка'),
                                help_text=_('Кодировка поддерживаемого цифрового протокола'))


    class Meta:
        verbose_name = _('Вид блока управления')
        verbose_name_plural = _('Виды блоков управления')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ActuatorGearboxOutputType(models.Model):

    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название обозначения типа выхода привода/редуктора")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код обозначения типа выхода привода/редуктора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа выхода привода/редуктора'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Тип выхода привода/редуктора')
        verbose_name_plural = _('Типы выходов привода/редуктора')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ActuatorGearBoxCombinationTypes(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа комбинации привода и редуктора")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа комбинации привода и редуктора"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа комбинации привода и редуктора'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    # ---------------- End new data

    electric_actuator_type = models.CharField(max_length=2, blank=True, verbose_name=_('Тип электропривода'),
                                              help_text=_(
                                                  'Символьное обозначение типа комбинации электропривода и редуктора'))
    gearbox_type = models.CharField(max_length=2, blank=True, verbose_name=_('Тип редуктора'),
                                    help_text=_('Символьное обозначение типа редуктора'))
    pneumatic_actuator_type = models.CharField(max_length=2, blank=True, verbose_name=_('Тип пневмопривода'),
                                               help_text=_('Символьное обозначение типа комбинации пневмопривода'))

    class Meta:
        verbose_name = _('Тип комбинации привода и редуктора')
        verbose_name_plural = _('Типы комбинаций привода и редуктора')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ValveTypes(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа арматуры")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа арматуры"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа арматуры'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    actuator_gearbox_combinations = models.CharField(max_length=10, verbose_name=_('Комбинации привода/редуктора'),
                                                     help_text=_(
                                                         'Символьное обозначение подходящего типа привода и редуктора'))

    class Meta:
        verbose_name = _('Тип арматуры')
        verbose_name_plural = _('Типы арматуры')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class HandWheelInstalledOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа установленного на приводе ручного дублера")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа установленного на приводе ручного дублера"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа установленного на приводе ручного дублера'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    encoding = models.CharField(max_length=10, blank=True, verbose_name=_('Кодировка'),
                                help_text=_('Кодировка установленного на приводе ручного дублера'))


    class Meta:
        verbose_name = _('Опция ручного дублера')
        verbose_name_plural = _('Опции ручных дублеров')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class OperatingModeOption(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа режима работы электропривода")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа режима работы электропривода"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа режима работы электропривода'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Опция режима работы')
        verbose_name_plural = _('Опции режимов работы')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

class MountingPlateTypes(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа монтажной площадки")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа монтажной площадки"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа монтажной площадки'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Тип монтажной площадки')
        verbose_name_plural = _('Типы монтажных площадок')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class StemShapes(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа штока")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа штока"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа штока'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Форма штока')
        verbose_name_plural = _('Формы штоков')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class StemSize(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типоразмера штока")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типоразмера штока"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типоразмера штока'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    stem_type = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True, verbose_name=_('Тип штока'))
    stem_diameter = models.DecimalField(max_digits=3, decimal_places=0, verbose_name=_('Диаметр штока'))
    chunk_x = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True,
                                  verbose_name=_('Шпонка размер X'))
    chunk_y = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True,
                                  verbose_name=_('Шпонка размер Y'))
    chunk_z = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True,
                                  verbose_name=_('Шпонка размер Z'))
    thread_pitch = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True,
                                       verbose_name=_('Шаг резьбы'))
    class Meta:
        verbose_name = _('Размер штока')
        verbose_name_plural = _('Размеры штоков')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class ThreadTypes(models.Model):
    # TODO: не надо ли объединить с типами резьбы в valve_data
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа резьбы")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа резьбы"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа резьбы'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    class Meta:
        verbose_name = _('Тип резьбы')
        verbose_name_plural = _('Типы резьб')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class MeasureUnits(models.Model):
    MEASURE_TYPES = [
        ('length', _('Длина')),
        ('weight', _('Вес')),
        ('square', _('Площадь')),
        ('volume', _('Объем')),
        ('torque', _('Усилие')),
        ('pressure', _('Давление')),
        ('speed', _('Скорость')),
        ('temperature', _('Температура')),
        ('frequency', _('Частота')),
        ('power', _('Мощность')),
        ('time', _('Время')),
    ]
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название единицы измерения")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код единицы измерения"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание единицы измерения'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    measure_type = models.CharField(max_length=15, choices=MEASURE_TYPES, verbose_name=_('Тип измерения'))

    class Meta:
        verbose_name = _('Единица измерения')
        verbose_name_plural = _('Единицы измерения')
        ordering = ['measure_type', 'sorting_order']

    def __str__(self):
        return self.name


class ThreadSize(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа и размера резьбы")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа и размера резьбы"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа и размера резьбы'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    thread_type = models.ForeignKey(ThreadTypes, on_delete=models.SET_NULL, null=True, verbose_name=_('Тип резьбы'))
    thread_diameter = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                          verbose_name=_('Диаметр резьбы'))
    thread_pitch = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                       verbose_name=_('Шаг резьбы'))
    measure_units = models.ForeignKey(MeasureUnits, on_delete=models.SET_NULL, null=True,
                                      verbose_name=_('Единицы измерения'))
    class Meta:
        verbose_name = _('Тип и размер резьбы')
        verbose_name_plural = _('Типы и размеры резьб')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class CertVariety(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название типа сертификата")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа сертификата"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа сертификата'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        verbose_name = _('Тип сертификата')
        verbose_name_plural = _('Типы сертификатов')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name


class CertData(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название сертификата")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код сертификата"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Номер сертификата'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    cert_variety = models.ForeignKey(CertVariety, on_delete=models.CASCADE, verbose_name=_('Тип сертификата'),
                                     help_text=_('Тип сертификата'))
    valid_from = models.DateField(blank=True, null=True, verbose_name=_('Действует с'),
                                  help_text=_('Срок действия с'))
    valid_until = models.DateField(blank=True, null=True, verbose_name=_('Действует до'),
                                   help_text=_('Срок действия до'))

    class Meta:
        verbose_name = _('Сертификата')
        verbose_name_plural = _('Сертификаты')
        ordering = ['-valid_until', 'cert_variety']

    def __str__(self):
        return self.name


class DnVariety(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Условный диаметр Dn (Ду)")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Символьный код Dn (Ду)"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание '))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    diameter_metric = models.IntegerField(default=0, verbose_name=_("Диаметр в мм"))
    diameter_inches = models.CharField(max_length=30, verbose_name=_("Диаметр в дюймах"))

    class Meta:
        verbose_name = _('Размер DN')
        verbose_name_plural = _('Размер DN')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

    @classmethod
    def find_dn(cls , search_value) :
        """
        Ищет DN по различным полям: name, code, diameter_metric (точные совпадения)

        Args:
            search_value: строка или число для поиска

        Returns:
            DnVariety object или None если не найден
        """
        if search_value is None :
            return None

        search_value = str(search_value).strip()

        # Пробуем найти в разных полях (точные совпадения)
        try :
            # Поиск по code (точное совпадение)
            if cls.objects.filter(code=search_value , is_active=True).exists() :
                return cls.objects.get(code=search_value , is_active=True)

            # Поиск по name (точное совпадение)
            if cls.objects.filter(name=search_value , is_active=True).exists() :
                return cls.objects.get(name=search_value , is_active=True)

            # Поиск по diameter_metric (числовое сравнение)
            try :
                diameter_value = int(search_value)
                if cls.objects.filter(diameter_metric=diameter_value , is_active=True).exists() :
                    return cls.objects.get(diameter_metric=diameter_value , is_active=True)
            except (ValueError , TypeError) :
                pass

        except cls.DoesNotExist :
            pass

        return None

    @classmethod
    def get_dn_objects(cls , dn_input) :
        """
        Универсальный геттер для получения объектов DN из различных входных данных

        Args:
            dn_input: строка, объект DnVariety, список строк или список объектов

        Returns:
            tuple: (dn_objects, errors)
                - dn_objects: список объектов DnVariety
                - errors: список сообщений об ошибках для ненайденных значений

        Raises:
            ValueError: если входные данные имеют неподдерживаемый тип
        """
        if dn_input is None :
            return [] , []

        errors = []
        dn_objects = []

        # Обработка одиночного значения
        if not isinstance(dn_input , (list , tuple)) :
            if isinstance(dn_input , (str , int)) :
                # Одиночная строка или число
                dn_obj = cls.find_dn(dn_input)
                if dn_obj :
                    dn_objects.append(dn_obj)
                else :
                    errors.append(f"DN '{dn_input}' не найден в справочнике")
            elif isinstance(dn_input , cls) :
                # Одиночный объект DnVariety
                dn_objects.append(dn_input)
            else :
                raise ValueError(f"Неподдерживаемый тип входных данных: {type(dn_input)}")

        # Обработка списка значений
        else :
            for i , dn_val in enumerate(dn_input) :
                if isinstance(dn_val , (str , int)) :
                    # Строка или число в списке
                    dn_obj = cls.find_dn(dn_val)
                    if dn_obj :
                        dn_objects.append(dn_obj)
                    else :
                        errors.append(f"DN[{i}]: '{dn_val}' не найден в справочнике")
                elif isinstance(dn_val , cls) :
                    # Объект DnVariety в списке
                    dn_objects.append(dn_val)
                else :
                    errors.append(f"DN[{i}]: неподдерживаемый тип данных '{type(dn_val)}'")

        # Сортируем по sorting_order
        dn_objects = sorted(dn_objects , key=lambda x : x.sorting_order)

        return dn_objects , errors

class PnVariety(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,
                            verbose_name=_("Название"),
                            help_text=_("Название давления PN в бар")
                            )
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Символьный код PN"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Описание'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))
    pressure_bar = models.DecimalField(max_digits=4, decimal_places=1, default=0.0, verbose_name=_("Давление в бар"))

    class Meta:
        verbose_name = _('Давление PN')
        verbose_name_plural = _('Давление PN')
        ordering = ['sorting_order']

    def __str__(self):
        return self.name

    @classmethod
    def find_pn(cls , search_value) :
        """
        Ищет PN по различным полям: name, code, pressure_bar (точные совпадения)

        Args:
            search_value: строка или число для поиска

        Returns:
            PnVariety object или None если не найден
        """
        if search_value is None :
            return None

        search_value = str(search_value).strip()

        # Пробуем найти в разных полях (точные совпадения)
        try :
            # Поиск по code (точное совпадение)
            if cls.objects.filter(code=search_value , is_active=True).exists() :
                return cls.objects.get(code=search_value , is_active=True)

            # Поиск по name (точное совпадение)
            if cls.objects.filter(name=search_value , is_active=True).exists() :
                return cls.objects.get(name=search_value , is_active=True)

            # Поиск по pressure_bar (числовое сравнение)
            try :
                pressure_value = float(search_value)
                if cls.objects.filter(pressure_bar=pressure_value , is_active=True).exists() :
                    return cls.objects.get(pressure_bar=pressure_value , is_active=True)
            except (ValueError , TypeError) :
                pass

        except cls.DoesNotExist :
            pass

        return None

    @classmethod
    def get_pn_objects(cls , pn_input) :
        """
        Универсальный геттер для получения объектов PN из различных входных данных

        Args:
            pn_input: строка, объект PnVariety, список строк или список объектов

        Returns:
            tuple: (pn_objects, errors)
                - pn_objects: список объектов PnVariety
                - errors: список сообщений об ошибках для ненайденных значений

        Raises:
            ValueError: если входные данные имеют неподдерживаемый тип
        """
        if pn_input is None :
            return [] , []

        errors = []
        pn_objects = []

        # Обработка одиночного значения
        if not isinstance(pn_input , (list , tuple)) :
            if isinstance(pn_input , (str , int , float)) :
                # Одиночная строка или число
                pn_obj = cls.find_pn(pn_input)
                if pn_obj :
                    pn_objects.append(pn_obj)
                else :
                    errors.append(f"PN '{pn_input}' не найден в справочнике")
            elif isinstance(pn_input , cls) :
                # Одиночный объект PnVariety
                pn_objects.append(pn_input)
            else :
                raise ValueError(f"Неподдерживаемый тип входных данных: {type(pn_input)}")

        # Обработка списка значений
        else :
            for i , pn_val in enumerate(pn_input) :
                if isinstance(pn_val , (str , int , float)) :
                    # Строка или число в списке
                    pn_obj = cls.find_pn(pn_val)
                    if pn_obj :
                        pn_objects.append(pn_obj)
                    else :
                        errors.append(f"PN[{i}]: '{pn_val}' не найден в справочнике")
                elif isinstance(pn_val , cls) :
                    # Объект PnVariety в списке
                    pn_objects.append(pn_val)
                else :
                    errors.append(f"PN[{i}]: неподдерживаемый тип данных '{type(pn_val)}'")

        # Сортируем по sorting_order
        pn_objects = sorted(pn_objects , key=lambda x : x.sorting_order)

        return pn_objects , errors

class OptionVariety(models.Model):
    """ Тип опций исполнения - под заказ/склад и т.п."""
    name = models.CharField(max_length=100, verbose_name=_("Название варианта исполнения изделия"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код варианта исполнения изделия"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _("Тип варианта исполнения изделия")
        verbose_name_plural = _("Типы вариантов исполнения изделия")

    def __str__(self):
        return self.name


class BodyColor(models.Model):
    """Цвет корпуса арматуры"""
    name = models.CharField(max_length=100, verbose_name=_("Название цвета"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код цвета"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    hex_code = models.CharField(max_length=7, blank=True, verbose_name=_("HEX код цвета"),
                                help_text=_("Например: #FF0000 для красного"))
    ral_code = models.CharField(max_length=20, blank=True, verbose_name=_("RAL код"),
                                help_text=_("Например: RAL 3000"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _("Цвет корпуса")
        verbose_name_plural = _("Цвета корпусов")

    def __str__(self) :
        if self.ral_code :
            return f"{self.name} RAL({self.ral_code})"
        return self.name

    def get_color_display(self) :
        """Отображаемое представление цвета"""
        if self.hex_code :
            return f'<span style="display: inline-block; width: 20px; height: 20px; background-color: {self.hex_code}; border: 1px solid #ccc; margin-right: 5px;"></span>{self.name}'
        return self.name


class ValveFunctionVariety(models.Model):
    """ Тип арматуры - регулирующая, запорная"""
    name = models.CharField(max_length=100,
                            verbose_name=_("Название типа назначения арматуры - регулирование и запорное"))
    code = models.CharField(max_length=50, unique=True,
                            verbose_name=_("Код типа назначения арматуры - регулирование и запорное"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _("Тип назначения арматуры - регулирование и запорное")
        verbose_name_plural = _("Типы назначения арматуры - регулирование и запорное")

    def __str__(self):
        return self.name

class ValveActuationVariety(models.Model):
    """ Тип механизма приведения в действие арматуры - ручка/редуктор/привод"""
    name = models.CharField(max_length=100, help_text=_("Название типа механизма приведения в действие арматуры - ручка/редуктор/привод"),
                            verbose_name=_("Название типа механизма приведения в действие арматуры - ручка/редуктор/привод"))
    code = models.CharField(max_length=50, unique=True,
                            verbose_name=_("Код типа механизма приведения в действие арматуры"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _("Тип механизма приведения в действие арматуры - ручка/редуктор/привод")
        verbose_name_plural = _("Типы механизмов приведения в действие арматуры")

    def __str__(self):
        return self.name

class SealingClass(models.Model):
    """ Класс герметичности арматуры - в зависимости от ее типа (регулирующая/запорная)"""
    name = models.CharField(max_length=100, verbose_name=_("Название класса герметичности арматуры"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код класса герметичности арматуры"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    valve_function_variety = models.ManyToManyField(ValveFunctionVariety,
                                               related_name="sealing_class_valve_function_variety",
                                               verbose_name=_('Тип назначения арматуры - регулирование и запорное'),
                                               help_text=_('Тип назначения арматуры - регулирование и запорное'))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _("Класс герметичности арматуры")
        verbose_name_plural = _("Классы герметичности арматуры")

    def __str__(self):
        return self.name


class CoatingVariety(models.Model):
    """ Типы покрытия арматуры"""
    name = models.CharField(max_length=100, verbose_name=_("Тип и толщина покрытия"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код типа и толщины покрытия"))
    thickness = models.IntegerField(default=0,
                                    verbose_name=_('Толщина покрытия в мкм'),
                                    help_text=_('Толщина покрытия в мкм'))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _("Тип и толщина покрытия")
        verbose_name_plural = _("Типы и толщина покрытия")

    def __str__(self):
        return self.name

class WarrantyTimePeriodVariety(models.Model):
    """ Варианты продолжительности гарантийного срока"""
    name = models.CharField(max_length=500, verbose_name=_("Текст продолжительности гарантийного срока"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код текста продолжительности гарантийного срока"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _("Описание продолжительности гарантийного срока")
        verbose_name_plural = _("Варианты продолжительности гарантийного срока")

    def __str__(self):
        return self.name


class PneumaticAirSupplyPressure(models.Model) :
    """
    Давление питания в пневмосистеме
    """
    name = models.CharField(max_length=10 ,
                            verbose_name=_("Давление, бар") ,
                            help_text=_('Давление в пневмосистеме, бар'))
    code = models.CharField(max_length=10 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код давления в пневмосистеме, бар"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание давления питания'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    pressure_bar = models.DecimalField(max_digits=4 , decimal_places=1 , verbose_name=_("Давление в бар"))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Давление питания в пневмосистеме')
        verbose_name_plural = _('Давления питания в пневмосистеме')

    def __str__(self) :
        return f"{self.name} бар"

    def get_pressure_in_units(self , unit='bar') :
        """
        Возвращает давление в различных единицах измерения

        Args:
            unit (str): единица измерения ('bar', 'mpa', 'atm', 'psi', 'kpa')

        Returns:
            float: давление в указанных единицах
        """
        unit = unit.lower()
        pressure_bar = float(self.pressure_bar)

        conversion_rates = {
            'bar' : 1.0 ,  # бар
            'mpa' : 0.1 ,  # мегапаскали (1 бар = 0.1 МПа)
            'kpa' : 100.0 ,  # килопаскали (1 бар = 100 кПа)
            'atm' : 0.986923 ,  # атмосферы (1 бар ≈ 0.987 атм)
            'psi' : 14.5038 ,  # фунты на кв. дюйм (1 бар ≈ 14.5 psi)
        }

        if unit in conversion_rates :
            return round(pressure_bar * conversion_rates[unit] , 4)
        else :
            raise ValueError(f"Неподдерживаемая единица измерения: {unit}. "
                             f"Доступные: {', '.join(conversion_rates.keys())}")

    def get_pressure_display(self , unit='bar') :
        """
        Возвращает отформатированную строку давления с единицами измерения

        Args:
            unit (str): единица измерения ('bar', 'mpa', 'atm', 'psi', 'kpa')

        Returns:
            str: отформатированная строка давления
        """
        pressure_value = self.get_pressure_in_units(unit)

        unit_display = {
            'bar' : 'бар' ,
            'mpa' : 'МПа' ,
            'kpa' : 'кПа' ,
            'atm' : 'атм' ,
            'psi' : 'psi'
        }

        return f"{pressure_value} {unit_display.get(unit , unit)}"

    @classmethod
    def find_by_pressure(cls , pressure_value , unit='bar') :
        """
        Ищет объект давления по значению в указанных единицах

        Args:
            pressure_value (float): значение давления
            unit (str): единица измерения входного значения

        Returns:
            PneumaticAirSupplyPressure or None: найденный объект или None
        """
        try :
            # Конвертируем в бар для поиска
            if unit != 'bar' :
                temp_obj = cls(pressure_bar=1.0)  # Временный объект для конвертации
                conversion_rate = temp_obj.get_pressure_in_units(unit)
                pressure_value_bar = pressure_value / conversion_rate
            else :
                pressure_value_bar = pressure_value

            # Ищем ближайшее значение (с учетом погрешности)
            return cls.objects.filter(
                pressure_bar__gte=pressure_value_bar - 0.05 ,
                pressure_bar__lte=pressure_value_bar + 0.05 ,
                is_active=True
            ).first()

        except (ValueError , TypeError) :
            return None

class PneumaticConnection(models.Model) :
    """
    Пневмоподключения - трубка, NAMUR
    """
    name = models.CharField(max_length=50 ,
                            verbose_name=_("Название") ,
                            help_text=_('Название пневмоподключения'))
    code = models.CharField(max_length=20 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код пневмоподключения"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание пневмоподключения'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Cортировка") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))

    class Meta :
        ordering = ['sorting_order']
        verbose_name = _('Тип пневмоподключение')
        verbose_name_plural = _('Типы пневмоподключений')

    def __str__(self) :
        return self.name