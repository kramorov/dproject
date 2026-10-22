from django.db import models
from django.utils.translation import gettext_lazy as _

'''
 class ActivationType(models.TextChoices):
        # Для дискретных сигналов
        ACTIVE_LOW = 'low', 'Active Low (Замыкание на ноль/минус)'
        ACTIVE_HIGH = 'high', 'Active High (Подача фазы/плюса)'
        PASSIVE_STOP = 'passive', 'Passive stop (Отсутствие сигналов Открыть/Закрыть)'
        
        # Для аналоговых сигналов (4-20 мА)
        ANALOG_ACTIVE = 'analog_act', 'Аналоговый АКТИВНЫЙ (Привод сам питает петлю током)'
        ANALOG_PASSIVE = 'analog_pas', 'Аналоговый ПАССИВНЫЙ (Требуется внешний БП для петли)'
        
        # Вариант отсутствия сигнала/функции
        NOT_IMPLEMENTED = 'none', 'Нет обработки сигнала (Функция отсутствует в данной модификации)'

class SignalForm(models.TextChoices):
        IMPULSE = 'impulse', 'Импульсный (самоподхват)'
        CONTINUOUS = 'continuous', 'Постоянный (пока есть подача - команда выполняется)'
        CONFIGURABLE = 'configurable', 'Настраиваемый (импульсный или постоянный)'
        ANALOG = 'analog', 'Аналоговый непрерывный (Токовая петля / Напряжение)'
        NOT_APPLICABLE = 'na', 'Не применимо (Для отсутствующих сигналов)'

class SignalType(models.TextChoices):
        OPEN = 'open', 'Открыть (Дискретный вход)'
        CLOSE = 'close', 'Закрыть (Дискретный вход)'
        STOP = 'stop', 'Стоп (Дискретный вход)'
        
        # Сигналы безопасности
        ESD = 'esd', 'ESD (Аварийный останов / Emergency Shutdown)'
        
        # Аналоговое управление позиционированием (задание положения)
        ANALOG_IN = 'analog_in', 'Аналоговый вход задания положения (4-20 мА / 0-10В)'
'''



class CuControlSignalPowerSourceType(models.Model):
    """Справочник: Источник питания сигналов управления Открыть/Закрыть/Стоп блока управления """
    # 1	Встроенный (выдается приводом)	Блок управления содержит собственный источник питания. На внешнюю клемму общего провода выдается потенциал +24 В. Внешнее питание цепей автоматики не требуется.
    # 2	Внешний (от сторонней системы)	Цепи управления изолированы от внутренней логики. Напряжение на управляющие входы поступает от стороннего источника (щита автоматики, термостата, внешнего БП).

    name = models.CharField(max_length=100, verbose_name="Источник питания")
    # Новое поле напряжения для питания цепей управления

    description = models.TextField(blank=True, verbose_name="Описание источника сигнала")

    class Meta:
        verbose_name = "Источник питания сигналов"
        verbose_name_plural = "Источники питания сигналов управления Открыть/Закрыть/Стоп блока управления"

    def __str__(self):
        return self.name


class CuControlSignalPower(models.Model):
    """Справочник: Источник питания и напряжение сигналов управления Открыть/Закрыть/Стоп блока управления """

    name = models.CharField(max_length=100, verbose_name="Источник питания")
    # Новое поле напряжения для питания цепей управления
    power_supply = models.ForeignKey(
        'params.PowerSupplies',
        on_delete=models.PROTECT, null=True, blank=True,
        verbose_name=_("Напряжение сигналов управления"),
        help_text=_("Напряжение сигналов управления БУ)")
    )
    power_source = models.ForeignKey(
        CuControlSignalPowerSourceType,
        on_delete=models.PROTECT, null=True, blank=True,
        verbose_name=_("Источник напряжения сигналов управления"),
        help_text=_("Напряжение сигналов управления БУ)")
    )
    description = models.TextField(blank=True, verbose_name="Описание схемотехники")

    class Meta:
        verbose_name = "Источник питания цепей"
        verbose_name_plural = "Источники питания цепей"

    def __str__(self):
        return self.name
'''
Модификация с управлением потенциальными сигналами ~220 В AC:
В данном исполнении блок управления привода оснащен гальванически изолированными входами (оптоэлектронная или релейная развязка). 
Это позволяет подключать внешние линии управления напрямую от сетей ~220 В (от термостатов, контакторов или сторонних ПЛК) 
без применения промежуточных реле в щите автоматики.

Логика сигналов:
• «ОТКРЫТЬ» / «ЗАКРЫТЬ» / «СТОП» — дискретные потенциальные сигналы ~220 В (активный высокий уровень / Active High).
• Общая точка (клемма Com / N) — подключается к нейтрали управляющего источника ~220 В.
• Управляющий импульс/потенциал — подается замыканием фазного провода (L) на соответствующую клемму привода.
'''
class ControlLogicMode(models.Model):
    """Справочник: Доступная программная логика (Импульсный, Потенциальный, Настраиваемый)
   Подача дискретного импульса Длина импульса: обычно не менее 0.5–1 секунды (зависит от времени срабатывания внутренних реле подхвата в плате привода).
• Подача короткого импульса на клемму «Открыть» запускает процесс, плата привода «запоминает» команду (встает на самоподхват) и крутит мотор до тех пор, пока:
    """
    name = models.CharField(max_length=100, verbose_name="Логика работы привода")
    has_self_holding = models.BooleanField(default=False, verbose_name="Поддержка самоподхвата")

    class Meta:
        verbose_name = "Режим логики работы"
        verbose_name_plural = "Режимы логики работы"

    def __str__(self):
        return self.name

class ControlSignalType(models.Model):
    """Справочник: Тип управляющего сигнала (Сухой контакт, Потенциальный 220В и т.д.)"""
    name = models.CharField(max_length=100, verbose_name="Тип сигнала")
    logic_type = models.CharField(
        max_length=50,
        choices=[('active_low', 'Active Low (NPN)'), ('active_high', 'Active High (PNP)')],
        verbose_name="Тип логики"
    )
    voltage = models.CharField(max_length=50, verbose_name="Напряжение сигнала (например, 24V или 220V)")

    class Meta:
        verbose_name = "Тип управляющего сигнала"
        verbose_name_plural = "Типы управляющих сигналов"

    def __str__(self):
        return f"{self.name} ({self.get_logic_type_display()})"
# Модели SignalType и ControlLogic остаются прежними...
#
# class ActuatorProduct(models.Model):
#     """Результирующая модель: Модификация электропривода"""
#     sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
#     name = models.CharField(max_length=255, verbose_name="Наименование")
#
#     # Силовое питание самого привода/мотора (например, 24V AC/DC)
#     main_voltage = models.CharField(max_length=50, verbose_name="Номинальное питание привода")
#
#     # Связи со схемотехникой
#     power_source = models.ForeignKey(PowerSourceType, on_delete=models.PROTECT, verbose_name="Питание цепей управления")
#     signal_type = models.ForeignKey(SignalType, on_delete=models.PROTECT, verbose_name="Управляющий сигнал")
#     control_logic = models.ForeignKey(ControlLogic, on_delete=models.PROTECT, verbose_name="Конфигурация логики")
#
#     # ... остальные поля (цена, статус)
