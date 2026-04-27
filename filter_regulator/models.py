import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


# ============================================================
# ФИЛЬТР-РЕГУЛЯТОР (Filter Regulator)
# ============================================================

class FilterRegulatorType(models.Model):
    """Тип фильтр-регулятора"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))

    class Meta:
        verbose_name = _("Тип фильтр-регулятора")
        verbose_name_plural = _("Типы фильтр-регуляторов")

    def __str__(self):
        return self.name


class FilterRegulatorSize(models.Model):
    """Размер подключения фильтр-регулятора"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, verbose_name=_("Название"))  # G1/4", G3/8", etc.
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Код"))
    thread_size = models.CharField(max_length=20, verbose_name=_("Размер резьбы"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))

    class Meta:
        verbose_name = _("Размер фильтр-регулятора")
        verbose_name_plural = _("Размеры фильтр-регуляторов")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class FilterRegulatorPressureRange(models.Model):
    """Диапазон регулировки давления"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30, verbose_name=_("Название"))  # 0-4 бар, 0-8 бар
    code = models.CharField(max_length=30, unique=True, verbose_name=_("Код"))
    min_pressure = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Мин. давление (бар)"))
    max_pressure = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Макс. давление (бар)"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))

    class Meta:
        verbose_name = _("Диапазон давления")
        verbose_name_plural = _("Диапазоны давления")
        ordering = ['min_pressure']

    def __str__(self):
        return f"{self.min_pressure}-{self.max_pressure} бар"


class FilterElement(models.Model):
    """Элемент фильтрации"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))
    filtration_rating = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        verbose_name=_("Тонкость фильтрации (мкм)")
    )
    has_auto_drain = models.BooleanField(default=False, verbose_name=_("Автоматический слив"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))

    class Meta:
        verbose_name = _("Элемент фильтрации")
        verbose_name_plural = _("Элементы фильтрации")
        ordering = ['filtration_rating', 'sort_order']

    def __str__(self):
        if self.filtration_rating:
            return f"{self.name} ({self.filtration_rating} мкм)"
        return self.name


class FilterRegulatorEnclosure(models.Model):
    """Тип защиты/колпак фильтр-регулятора"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name=_("Название"))
    code = models.CharField(max_length=30, unique=True, verbose_name=_("Код"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Описание"))

    class Meta:
        verbose_name = _("Тип защиты")
        verbose_name_plural = _("Типы защиты")

    def __str__(self):
        return self.name


class FilterRegulator(models.Model):
    """Модель фильтр-регулятора (каталог)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_("Название"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Код"))

    # Характеристики
    regulator_type = models.ForeignKey(
        FilterRegulatorType, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Тип")
    )
    size = models.ForeignKey(
        FilterRegulatorSize, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Размер подключения")
    )
    pressure_range = models.ForeignKey(
        FilterRegulatorPressureRange, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Диапазон регулировки")
    )
    filter_element = models.ForeignKey(
        FilterElement, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Элемент фильтрации")
    )
    enclosure = models.ForeignKey(
        FilterRegulatorEnclosure, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Колпак/защита")
    )

    # Технические характеристики
    max_pressure = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. давление (бар)")
    )
    max_flow = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name=_("Макс. расход (л/мин)")
    )
    bowl_material = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name=_("Материал стакана")
    )
    has_manometer = models.BooleanField(default=False, verbose_name=_("Манометр в комплекте"))
    has_shut_off_valve = models.BooleanField(default=False, verbose_name=_("Отсечной клапан"))

    # Метки
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    sort_order = models.IntegerField(default=0, verbose_name=_("Порядок сортировки"))

    class Meta:
        verbose_name = _("Фильтр-регулятор")
        verbose_name_plural = _("Фильтр-регуляторы")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"
