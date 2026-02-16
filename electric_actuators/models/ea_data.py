#electric_actuators/models/ea_data.py
from django.db import models


class ElectricActuatorData(models.Model):
    name = models.CharField(max_length=30, help_text='Название модели / корпуса')
    model_line = models.ForeignKey('ModelLine', related_name='electric_actuator_data_model_line', null=True,
                                   on_delete=models.PROTECT, help_text='Серия модели')
    model_body = models.ForeignKey('ModelBody', related_name='electric_actuator_data_model_body', null=True,
                                   on_delete=models.SET_NULL, help_text='Корпус модели')
    voltage = models.ForeignKey('params.PowerSupplies', related_name='electric_actuator_data_model_voltage', null=True,
                                on_delete=models.SET_NULL, help_text='Напряжение питания модели')
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text='Вес модели')
    time_to_open = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True,
                                       help_text='Время поворота на 90°')
    time_to_open_measure_unit = models.ForeignKey('params.MeasureUnits', related_name='electric_actuator_data_time_to_open',
                                                  null=True,
                                                  blank=True, on_delete=models.SET_NULL,
                                                  help_text='Ед.изм. времени поворота на 90°')
    rotation_speed = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True, help_text='Скорость')
    rotation_speed_measure_unit = models.ForeignKey('params.MeasureUnits', related_name='electric_actuator_data_rotation_speed',
                                                    null=True,
                                                    blank=True, on_delete=models.SET_NULL,
                                                    help_text='Ед.изм. скорости привода')
    torque_min = models.DecimalField(max_digits=5, decimal_places=0, help_text='Минимальное усилие')
    torque_max = models.DecimalField(max_digits=5, decimal_places=0, help_text='Максимальное усилие')

    motor_power = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                      help_text='Мощность двигателя')
    motor_power_measure_unit = models.ForeignKey('params.MeasureUnits', related_name='electric_actuator_data_power', null=True,
                                                 blank=True, on_delete=models.SET_NULL,
                                                 help_text='Ед.изм. мощности двигателя')
    motor_current_rated = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                              help_text='Номинальный ток двигателя')
    motor_current_rated_measure_unit = models.ForeignKey('params.MeasureUnits',
                                                         related_name='electric_actuator_data_current_rated',
                                                         null=True,
                                                         blank=True, on_delete=models.SET_NULL,
                                                         help_text='Ед.изм. номинального тока двигателя')
    motor_current_starting = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                 help_text='Пусковой ток двигателя')
    motor_current_starting_measure_unit = models.ForeignKey('params.MeasureUnits',
                                                            related_name='electric_actuator_data_current_starting',
                                                            null=True,
                                                            blank=True, on_delete=models.SET_NULL,
                                                            help_text='Ед.изм. пускового тока двигателя')

    def __str__(self):
        return self.name

