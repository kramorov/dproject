# models.py
from django.db import models

class ElectroIPChoiceModel(models.Model):
    # Справочник IP
    ip_value = models.CharField(max_length=4, unique=True)

    def __str__(self):
        return self.ip_value

class ElectroModel(models.Model):
    # Связь с таблицами IP и Temp
    ip = models.ForeignKey(IPChoice, on_delete=models.SET_NULL, null=True)
    torque = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.ip} - {self.temp} - {self.torque}'
