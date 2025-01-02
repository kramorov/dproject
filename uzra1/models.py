# models.py
from django.db import models

class IPChoice(models.Model):
    # Справочник IP
    ip_value = models.CharField(max_length=4, unique=True)

    def __str__(self):
        return self.ip_value

class TempChoice(models.Model):
    # Справочник Temperature
    temp_value = models.CharField(max_length=3, unique=True)
    min = models.IntegerField()  # минимальная температура
    max = models.IntegerField()  # максимальная температура

    def __str__(self):
        return f'{self.temp_value} ({self.min} - {self.max})'

class MyModel(models.Model):
    # Связь с таблицами IP и Temp
    ip = models.ForeignKey(IPChoice, on_delete=models.SET_NULL, null=True)
    temp = models.ForeignKey(TempChoice, on_delete=models.SET_NULL, null=True)
    torque = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.ip} - {self.temp} - {self.torque}'
