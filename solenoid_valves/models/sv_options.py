# solenoid_valves/models/sv_options.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Optional, Any
from core.models import StructuredDataMixin



class ManualOverride(StructuredDataMixin, models.Model):
    """Справочник типов ручного дублирования соленоидного клапана"""

    class MechanismType(models.TextChoices):
        PUSH = 'push', _('Нажимной (Push)')
        TWIST = 'twist', _('Поворотный (Twist/Lock)')
        SCREW = 'screw', _('Под отвертку (Slot)')
        LEVER = 'lever', _('Рычажный (Lever)')
        NONE = 'none', _('Отсутствует')

    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Напр: С фиксацией, Кнопка без фиксации")
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Код")
    )

    mechanism = models.CharField(
        max_length=20,
        choices=MechanismType.choices,
        default=MechanismType.PUSH,
        verbose_name=_("Тип механизма")
    )

    has_fixation = models.BooleanField(
        default=False,
        verbose_name=_("С фиксацией"),
        help_text=_("Удерживает ли дублер клапан в рабочем состоянии без участия оператора")
    )

    description = models.TextField(blank=True, verbose_name=_("Описание"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _('Ручной дублер')
        verbose_name_plural = _('Ручные дублеры')

    def __str__(self):
        # fix_status = _("с фиксацией") if self.has_fixation else _("без фиксации")
        return f"{self.name}"


class ValveActuationVariety(StructuredDataMixin, models.Model):
    """Справочник типов управления: Моностабильный (1 катушка), Бистабильный (2 катушки)"""

    class ReturnType(models.TextChoices):
        # Обычный возврат в исходное (крайнее) положение
        SPRING = 'spring', _('Пружинный возврат (Spring Return)')

        # Специальный возврат в среднее положение для 3-позиционных клапанов
        SPRING_CENTERED = 'spring_centered', _('Пружинный возврат в центр (Spring Centered)')

        # Пневматический возврат (часто в пилотных клапанах)
        PNEUMATIC = 'pneumatic', _('Пневматический возврат (Pneumatic Return)')

        # Отсутствие возврата (для бистабильных/импульсных систем)
        NONE = 'none', _('Без возврата / Импульсный (No Return / Impulse)')

    # То, что пойдет в <option>{{ item.name }}</option>
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Напр: Моностабильный 24V")
    )

    # То, что удобно использовать в коде или поиске: 'mono-spring'
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Код")
    )

    # Логическая категория (choices)
    return_category = models.CharField(
        max_length=20,
        choices=ReturnType.choices,
        default=ReturnType.SPRING,
        verbose_name=_("Категория возврата")
    )

    solenoids_count = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Кол-во соленоидов")
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание варианта управления'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _('Вариант управления')
        verbose_name_plural = _('Варианты управления')

    def __str__(self):
        return self.name


class ValveDesign(StructuredDataMixin, models.Model):
    """Справочник типов конструкции: Золотниковый, Мембранный и т.д."""
    name = models.CharField(max_length=50,
                            verbose_name=_("Название"),
                            help_text=_('Название типа конструкции'))
    code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа конструкции"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа конструкции клапана'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Тип конструкции клапана')
        verbose_name_plural = _('Типы конструкции клапанов')

    def __str__(self):
        return self.name


class ValveOperationVariety(StructuredDataMixin, models.Model):
    """Справочник типов действия: Прямое, Пилотное"""
    name = models.CharField(max_length=50,
                            verbose_name=_("Тип"),
                            help_text=_('Тип действия'))
    code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Код"),
                            help_text=_("Код типа действия"))
    description = models.TextField(blank=True, verbose_name=_("Описание"),
                                   help_text=_('Текстовое описание типа действия клапана'))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Cортировка"),
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"),
                                    help_text=_('Активно свойство или нет'))

    class Meta:
        ordering = ['sorting_order']
        verbose_name = _('Тип действия клапана')
        verbose_name_plural = _('Типы действия клапанов')

    def __str__(self):
        return self.name


class ValveFunction(StructuredDataMixin, models.Model):
    """Справочник схем распределения: 3/2, 5/2, 5/3 и т.д."""
    name = models.CharField(max_length=20,
                            verbose_name=_("Схема (Функция)"),
                            help_text=_('Обозначение схемы, например, 5/2 или 3/2'))

    code = models.CharField(max_length=20, blank=True, null=True,
                            verbose_name=_("Код"),
                            help_text=_("Внутренний код или артикул типа схемы"))

    description = models.TextField(blank=True,
                                   verbose_name=_("Описание"),
                                   help_text=_('Например: "5-линейный 2-позиционный"'))

    sorting_order = models.IntegerField(default=0,
                                        verbose_name=_("Сортировка"))

    is_active = models.BooleanField(default=True,
                                    verbose_name=_("Активно"))
    ports_count = models.IntegerField(verbose_name=_("Кол-во портов"),
                                      help_text=_("Первое число в схеме (линейность)"))

    positions_count = models.IntegerField(verbose_name=_("Кол-во положений"),
                                          help_text=_("Второе число в схеме (позиционность)"))

    compatible_functions = models.ManyToManyField(
        'self', blank=True, symmetrical=True,
        verbose_name=_("Совместимые схемы"),
        help_text=_("Например: 3/2 ↔ 5/2")
    )

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _('Схема распределения (Функция)')
        verbose_name_plural = _('Схемы распределения (Функции)')

    def __str__(self):
        return self.name

    def get_compatible_ids(self):
        """Возвращает [свой id] + id совместимых схем"""
        ids = [self.id]
        ids.extend(self.compatible_functions.values_list('id', flat=True))
        return list(set(ids))


class ValvePilotVariety(StructuredDataMixin, models.Model):
    """Справочник типов управляющего сигнала (пилота)"""

    class SignalCategory(models.TextChoices):
        ELECTRIC = 'electric', _('Электрический (Соленоид)')
        PNEUMATIC = 'pneumatic', _('Пневматический (Воздух)')
        MECHANICAL = 'mechanical', _('Механический (Ролик/Рычаг)')
        MANUAL = 'manual', _('Ручной (Кнопка/Педаль)')

    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Напр: Электромагнитный, Пневмопривод")
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Код")
    )

    category = models.CharField(
        max_length=20,
        choices=SignalCategory.choices,
        default=SignalCategory.ELECTRIC,
        verbose_name=_("Категория сигнала")
    )

    description = models.TextField(blank=True, verbose_name=_("Описание"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активно"))
    sorting_order = models.IntegerField(default=0, verbose_name=_("Порядок"))

    class Meta:
        ordering = ['sorting_order', 'name']
        verbose_name = _('Тип управления (Пилот)')
        verbose_name_plural = _('Типы управления (Пилот)')

    def __str__(self):
        return self.name


