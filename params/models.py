# models.py
from django.db import models


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


class ExdOption(models.Model):
    symbolic_code = models.CharField(max_length=10, help_text='Символьное обозначение вида взрывозащиты')
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
        return self.symbolic_code


class BlinkerOption(models.Model):
    symbolic_code = models.CharField(max_length=15, help_text='Символьное обозначение наличия блинкера')

    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание наличия блинкера')

    def __str__(self):
        return self.symbolic_code


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
        return self.symbolic_code


class ActuatorGearBoxCombinationTypes(models.Model):
    symbolic_code = models.CharField(max_length=2, help_text='Символьное обозначение \
    типа комбинации привода и редуктора')
    electric_actuator_type = models.ForeignKey(ActuatorGearboxOutputType, blank=True, null=True,
                                               on_delete=models.SET_NULL)
    gearbox_type = models.ForeignKey(ActuatorGearboxOutputType, blank=True, null=True,
                                     on_delete=models.SET_NULL)
    pneumatic_actuator_type = models.ForeignKey(ActuatorGearboxOutputType, blank=True, null=True,
                                                on_delete=models.SET_NULL)
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа комбинации привода и редуктора')

    def __str__(self):
        return self.symbolic_code


class ValveTypes(models.Model):
    symbolic_code = models.CharField(max_length=2, help_text='Символьное обозначение \
    типа арматуры')
    actuator_gearbox_combinations = models.ForeignKey(ActuatorGearBoxCombinationTypes, blank=True, null=True,
                                                      on_delete=models.SET_NULL)
    text_description = models.CharField(max_length=200, blank=True, help_text='Текстовое описание \
    типа арматуры')

    def __str__(self):
        return self.symbolic_code


class HandWheelInstalledOption(models.Model):
    symbolic_code = models.CharField(max_length=5, help_text='Символьное обозначение \
    установленного на приводе ручного дублера')
    encoding = models.CharField(max_length=10, help_text='Кодировка \
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
        if len(self.text_description) == 0:
            return self.symbolic_code
