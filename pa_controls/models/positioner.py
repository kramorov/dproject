# pa_controls/models/positioner.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from typing import List , Optional , Tuple , Any , Dict , Union

import logging
logger = logging.getLogger(__name__)

# class PositionerType(models.Model):
#     """Тип позиционера"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=50, verbose_name=_("Название"))
#     code = models.CharField(max_length=30, unique=True, verbose_name=_("Код"))
#     description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))
#
#     class Meta:
#         verbose_name = _("Тип позиционера")
#         verbose_name_plural = _("Типы позиционеров")
#
#     def __str__(self):
#         return self.name
#
#
# class PositionerInputSignal(models.Model):
#     """Входной сигнал позиционера"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=50, verbose_name=_("Название"))
#     code = models.CharField(max_length=30, unique=True, verbose_name=_("Код"))
#     signal_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
#     signal_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
#     is_digital = models.BooleanField(default=False, verbose_name=_("Цифровой протокол"))
#     description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))
#
#     class Meta:
#         verbose_name = _("Входной сигнал")
#         verbose_name_plural = _("Входные сигналы")
#
#     def __str__(self):
#         return self.name
#
#
# class PositionerOutputSignal(models.Model):
#     """Выходной сигнал (обратная связь) позиционера"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=50, verbose_name=_("Название"))
#     code = models.CharField(max_length=30, unique=True, verbose_name=_("Код"))
#     signal_type = models.CharField(max_length=30, verbose_name=_("Тип сигнала"))
#     is_digital = models.BooleanField(default=False, verbose_name=_("Цифровой протокол"))
#     description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))
#
#     class Meta:
#         verbose_name = _("Выходной сигнал")
#         verbose_name_plural = _("Выходные сигналы")
#
#     def __str__(self):
#         return self.name
#
#
# class PositionerEnclosure(models.Model):
#     """Степень защиты позиционера"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=20, verbose_name=_("Название"))
#     code = models.CharField(max_length=20, unique=True, verbose_name=_("Код"))
#     rating = models.CharField(max_length=10, verbose_name=_("Рейтинг"))
#
#     class Meta:
#         verbose_name = _("Степень защиты")
#         verbose_name_plural = _("Степени защиты")
#
#     def __str__(self):
#         return self.name
#
#
# class PositionerCommunicationProtocol(models.Model):
#     """Цифровой протокол связи"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=50, verbose_name=_("Название"))
#     code = models.CharField(max_length=30, unique=True, verbose_name=_("Код"))
#     description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))
#
#     class Meta:
#         verbose_name = _("Протокол связи")
#         verbose_name_plural = _("Протоколы связи")
#
#     def __str__(self):
#         return self.name
#
#
# class Positioner(models.Model):
#     """Модель позиционера (каталог)"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100, verbose_name=_("Название"))
#     code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
#
#     # Основные характеристики
#     positioner_type = models.ForeignKey(
#         PositionerType, on_delete=models.SET_NULL, null=True,
#         verbose_name=_("Тип позиционера")
#     )
#     input_signal = models.ForeignKey(
#         PositionerInputSignal, on_delete=models.SET_NULL, null=True,
#         verbose_name=_("Входной сигнал")
#     )
#     output_signal = models.ForeignKey(
#         PositionerOutputSignal, on_delete=models.SET_NULL, null=True,
#         verbose_name=_("Выходной сигнал (обратная связь)")
#     )
#     enclosure = models.ForeignKey(
#         PositionerEnclosure, on_delete=models.SET_NULL, null=True,
#         verbose_name=_("Степень защиты IP")
#     )
#
#     # Коммуникационные протоколы
#     communication_protocols = models.ManyToManyField(
#         PositionerCommunicationProtocol, blank=True,
#         verbose_name=_("Цифровые протоколы")
#     )
#
#     # Дополнительные характеристики
#     has_exd = models.BooleanField(default=False, verbose_name=_("Exd взрывозащита"))
#     has_ati = models.BooleanField(default=False, verbose_name=_("ATI (датчик положения)"))
#     has_builtin_limit_switch = models.BooleanField(
#         default=False,
#         verbose_name=_("Встроенный блок концевых выключателей")
#     )
#     has_hmi = models.BooleanField(default=False, verbose_name=_("HMI интерфейс"))
#     has_pneumatic_relay = models.BooleanField(default=False, verbose_name=_("Пневматический реле"))
#
#     # Технические характеристики
#     air_consumption = models.DecimalField(
#         max_digits=6, decimal_places=2, null=True, blank=True,
#         verbose_name=_("Расход воздуха (л/мин)")
#     )
#     supply_pressure_min = models.DecimalField(
#         max_digits=5, decimal_places=2, null=True, blank=True,
#         verbose_name=_("Мин. давление питания (бар)")
#     )
#     supply_pressure_max = models.DecimalField(
#         max_digits=5, decimal_places=2, null=True, blank=True,
#         verbose_name=_("Макс. давление питания (бар)")
#     )
#     operating_temperature_min = models.IntegerField(
#         null=True, blank=True,
#         verbose_name=_("Мин. температура (°C)")
#     )
#     operating_temperature_max = models.IntegerField(
#         null=True, blank=True,
#         verbose_name=_("Макс. температура (°C)")
#     )
#     linearity = models.DecimalField(
#         max_digits=4, decimal_places=2, null=True, blank=True,
#         verbose_name=_("Линейность (%)")
#     )
#     hysteresis = models.DecimalField(
#         max_digits=4, decimal_places=2, null=True, blank=True,
#         verbose_name=_("Гистерезис (%)")
#     )
#
#     # Метки
#     is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
#     sort_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))
#
#     class Meta:
#         verbose_name = _("Позиционер")
#         verbose_name_plural = _("Позиционеры")
#         ordering = ['sort_order', 'name']
#
#     def __str__(self):
#         return f"{self.name} ({self.code})"