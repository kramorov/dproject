#electric_actuators/models/ea_wiring_diagram.py
from django.db import models
# from electric_actuators.models import ElectricActuatorData , ElectricActuatorModelLine

# from params.models import PowerSupplies, ControlUnitInstalledOption


#
# class WiringDiagram(models.Model):
#     name = models.CharField(max_length=30, help_text='Название схемы подключения по чертежу')
#     applies_to_model_lines = models.ForeignKey(ElectricActuatorModelLine,
#                                                on_delete=models.CASCADE,
#                                                related_name='wiring_diagrams_applies_to_ea_model_lines')
#     applies_to_models = models.ManyToManyField(ElectricActuatorData, related_name='wiring_diagrams_applies_to_models')
#     voltage = models.ForeignKey(PowerSupplies, on_delete=models.CASCADE, related_name='wiring_diagrams_voltage')
#     cu = models.ForeignKey(ControlUnitInstalledOption,
#                            on_delete=models.CASCADE,
#                            related_name='wiring_diagrams_control_units')
#     text_description = models.CharField(max_length=200, blank=True, null=True,
#                                         help_text='Описание схемы подключения - к каким приводам и к какому '
#                                                   'напряжению относится')
#
#     def __str__(self):
#         return self.text_description

