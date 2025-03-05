# models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# PowerSupplies, ExdOption, IpOption, BodyCoatingOption,BlinkerOption,SwitchesParameters, EnvTempParameters, \
# DigitalProtocolsSupportOption, ControlUnitInstalledOption,ActuatorType, ValveTypes, GearBoxTypes, \
# HandWhellInstalledOption, OperatingModeOption

class PowerSupplies(models.Model):
    VOLTAGE_TYPES = [
        ('AC', 'AC - Переменный ток'),  # ('AC', 'Постоянный ток')
        ('DC', 'DC - Постоянный ток'),  # ('DC', 'Переменный ток')
    ]
    symbolic_code = models.CharField(max_length=10, help_text='Символьное обозначение типа напряжения')
    voltage_value = models.IntegerField()
    voltage_type = models.CharField(max_length=2, choices=VOLTAGE_TYPES, default='AC')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа напряжения')

    def __str__(self):
        return self.symbolic_code

class ControlUnitLocationOption(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Символьное обозначение типа размещения блока управления')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа размещения блока управления')

    def __str__(self):
        return self.text_description

class ControlUnitTypeOption(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Символьное обозначение типа блока управления')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа блока управления')

    def __str__(self):
        return self.text_description

class SafetyPositionOption(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Символьное обозначение положения функции безопасности')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание положения функции безопасности')

    def __str__(self):
        return self.symbolic_code

class ExdOption(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Символьное обозначение вида взрывозащиты')
    exd_full_code = models.CharField(max_length=200, help_text='Полный код вида взрывозащиты')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание вида взрывозащиты')

    def __str__(self):
        return self.symbolic_code


class IpOption(models.Model):
    # Справочник IP
    symbolic_code = models.CharField(max_length=4, help_text='Символьное обозначение исполнения IP')
    ip_rank = models.IntegerField(help_text='Приоритет исполнения IP (выше - лучше')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание исполнения IP')

    def __str__(self):
        return self.symbolic_code


class BodyCoatingOption(models.Model):
    symbolic_code = models.CharField(max_length=4, help_text='Символьное обозначение типа защиты\
     оболочки привода от коррозии')

    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа защиты\
     оболочки привода от коррозии')

    def __str__(self):
        return self.text_description


class BlinkerOption(models.Model):
    symbolic_code = models.CharField(max_length=15, help_text='Символьное обозначение наличия блинкера')

    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание наличия блинкера')

    def __str__(self):
        return self.text_description


class SwitchesParameters(models.Model):
    symbolic_code = models.CharField(max_length=15, help_text='Символьное обозначение \
    характеристик выключателей')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    характеристик выключателей')

    def __str__(self):
        return self.symbolic_code


class EnvTempParameters(models.Model):
    symbolic_code = models.CharField(max_length=4, help_text='Символьное обозначение \
    типа температурного исполнения')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа температурного исполнения')
    min_temp = models.IntegerField()
    max_temp = models.IntegerField()

    def __str__(self):
        return self.symbolic_code


class DigitalProtocolsSupportOption(models.Model):
    symbolic_code = models.CharField(max_length=4, help_text='Символьное обозначение \
    поддерживаемого цифрового протокола')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    поддерживаемого цифрового протокола')

    def __str__(self):
        return self.symbolic_code


class MechanicalIndicatorInstalledOption(models.Model):
    symbolic_code = models.CharField(max_length=15, help_text='Символьное обозначение \
    установленного механического индикатора положения')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    установленного механического индикатора положения')

    def __str__(self):
        return self.symbolic_code


class ControlUnitInstalledOption(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьное обозначение \
    установленного на приводе блока управления')
    encoding = models.CharField(max_length=10, help_text='Кодировка \
        поддерживаемого цифрового протокола')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    установленного на приводе блока управления')

    def __str__(self):
        return self.symbolic_code


class ActuatorGearboxOutputType(models.Model):
    symbolic_code = models.CharField(max_length=2, help_text='Символьное обозначение \
    типа привода')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа привода')

    def __str__(self):
        return self.text_description


class ActuatorGearBoxCombinationTypes(models.Model):
    symbolic_code = models.CharField(max_length=2, help_text='Символьное обозначение \
    типа комбинации привода и редуктора')
    electric_actuator_type = models.CharField(max_length=2, blank=True, help_text='Символьное обозначение \
    типа комбинации электропривода и редуктора')
    gearbox_type = models.CharField(max_length=2, blank=True, help_text='Символьное обозначение \
    типа редуктора')
    pneumatic_actuator_type = models.CharField(max_length=2, blank=True, help_text='Символьное обозначение \
    типа комбинации пневмопривода')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа комбинации привода и редуктора')

    def __str__(self):
        return self.text_description


class ValveTypes(models.Model):
    symbolic_code = models.CharField(max_length=2, help_text='Символьное обозначение \
    типа арматуры')
    actuator_gearbox_combinations = models.CharField(max_length=10, help_text='Символьное обозначение \
    подходящего типа привода и редуктора')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа арматуры')

    def __str__(self):
        return self.symbolic_code


class HandWheelInstalledOption(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьное обозначение \
    установленного на приводе ручного дублера')
    encoding = models.CharField(max_length=10, blank=True, help_text='Кодировка \
        установленного на приводе ручного дублера')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    установленного на приводе ручного дублера')

    def __str__(self):
        return self.symbolic_code


class OperatingModeOption(models.Model):
    symbolic_code = models.CharField(max_length=50, help_text='Символьное обозначение \
    режима работы электропривода')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    режима работы электропривода')

    def __str__(self):
        return self.symbolic_code


# ----------------------------------------------------

class MountingPlateTypes(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьное обозначение типа монтажной площадки')

    def __str__(self):
        return self.symbolic_code


class StemShapes(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьное обозначение типа штока')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа штока')

    def __str__(self):
        return self.symbolic_code


class StemSize(models.Model):
    symbolic_code = models.CharField(max_length=20, help_text='Символьное обозначение размера штока')
    stem_type = models.ForeignKey(StemShapes, on_delete=models.SET_NULL, null=True)
    stem_diameter = models.DecimalField(max_digits=3, decimal_places=0)
    chunk_x = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    chunk_y = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    chunk_z = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    thread_pitch = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа штока')

    def __str__(self):
        return self.symbolic_code


class ThreadTypes(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьное обозначение типа резьбы')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа резьбы')

    def __str__(self):
        return self.symbolic_code


class MeasureUnits(models.Model):
    MEASURE_TYPES = [
        ('length', 'Длина'),
        ('weight', 'Вес'),
        ('square', 'Площадь'),
        ('volume', 'Объем'),
        ('torque', 'Усилие'),
        ('pressure', 'Давление'),
        ('speed', 'Скорость'),
        ('temperature', 'Температура'),
        ('frequency', 'Частота'),
        ('power', 'Мощность'),
        ('time', 'Время'),
    ]

    symbolic_code = models.CharField(max_length=5, help_text='Символьное обозначение единицы измерения')
    measure_type = models.CharField(max_length=15, choices=MEASURE_TYPES)
    symbolic_description = models.CharField(max_length=10, blank=True,
                                            help_text='Символьное отображение единицы измерения в документах')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание единицы измерения')

    def __str__(self):
        return self.symbolic_code


class ThreadSize(models.Model):
    symbolic_code = models.CharField(max_length=25, help_text='Символьное обозначение типа резьбы')
    thread_type = models.ForeignKey(ThreadTypes, on_delete=models.SET_NULL, null=True)
    thread_diameter = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    thread_pitch = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    measure_units = models.ForeignKey(MeasureUnits, on_delete=models.SET_NULL, null=True)

    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа резьбы')

    def __str__(self):
        return self.text_description


class CertificateType(models.Model):
    symbolic_code = models.CharField(max_length=25, help_text='Символьное обозначение типа сертификата')
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание типа сертификата')

    def __str__(self):
        return self.symbolic_code


class Certificate(models.Model):
    certificate_type = models.ForeignKey(CertificateType, help_text='Тип сертификата', on_delete=models.CASCADE)
    text_description = models.CharField(max_length=200, blank=True, help_text='Номер сертификата')
    valid_from = models.DateField(blank=True, null=True, help_text='Срок действия с')
    valid_until = models.DateField(blank=True, null=True, help_text='Срок действия до')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.text_description
