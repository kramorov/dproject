from django.db import models
from django.contrib.postgres.fields import JSONField  # Для PostgreSQL


# Или для других БД: from django.db.models import JSONField

class ValveType(models.Model) :
    """Тип арматуры (шаровой кран, задвижка, клапан и т.д.)"""
    name = models.CharField(max_length=100 , verbose_name="Название типа")
    symbolic_code = models.CharField(max_length=10 , unique=True , verbose_name="Символьный код")
    description = models.TextField(blank=True , verbose_name="Описание")

    class Meta :
        verbose_name = "Тип арматуры"
        verbose_name_plural = "Типы арматуры"

    def __str__(self) :
        return f"{self.symbolic_code} - {self.name}"


class ParameterCategory(models.Model) :
    """Категория параметров (размерные, материалы, эксплуатационные и т.д.)"""
    name = models.CharField(max_length=100 , verbose_name="Название категории")
    code = models.CharField(max_length=20 , unique=True , verbose_name="Код категории")
    order = models.IntegerField(default=0 , verbose_name="Порядок отображения")

    class Meta :
        ordering = ['order' , 'name']
        verbose_name = "Категория параметров"
        verbose_name_plural = "Категории параметров"

    def __str__(self) :
        return self.name


class ParameterDefinition(models.Model) :
    """Определение параметра с метаданными"""
    name = models.CharField(max_length=100 , verbose_name="Название параметра")
    code = models.CharField(max_length=50 , unique=True , verbose_name="Код параметра")
    description = models.TextField(blank=True , verbose_name="Описание")
    data_type = models.CharField(
        max_length=20 ,
        choices=[
            ('string' , 'Строка') ,
            ('integer' , 'Целое число') ,
            ('float' , 'Десятичное число') ,
            ('boolean' , 'Да/Нет') ,
            ('choice' , 'Выбор из списка') ,
            ('range' , 'Диапазон значений') ,
        ] ,
        verbose_name="Тип данных"
    )
    unit = models.CharField(max_length=20 , blank=True , verbose_name="Единица измерения")
    category = models.ForeignKey(
        ParameterCategory ,
        on_delete=models.CASCADE ,
        related_name='parameters' ,
        verbose_name="Категория"
    )
    valve_types = models.ManyToManyField(
        ValveType ,
        related_name='available_parameters' ,
        verbose_name="Применимые типы арматуры"
    )
    is_required = models.BooleanField(default=False , verbose_name="Обязательный параметр")
    is_filterable = models.BooleanField(default=True , verbose_name="Используется для фильтрации")
    order = models.IntegerField(default=0 , verbose_name="Порядок отображения")

    # Для параметров типа choice
    choices = JSONField(
        blank=True ,
        null=True ,
        verbose_name="Варианты выбора" ,
        help_text="JSON массив вариантов для выбора"
    )

    # Для числовых параметров
    min_value = models.FloatField(blank=True , null=True , verbose_name="Минимальное значение")
    max_value = models.FloatField(blank=True , null=True , verbose_name="Максимальное значение")

    class Meta :
        ordering = ['category__order' , 'order' , 'name']
        verbose_name = "Определение параметра"
        verbose_name_plural = "Определения параметров"

    def __str__(self) :
        return f"{self.code} - {self.name}"


class ValveModel(models.Model) :
    """Конкретная модель арматуры"""
    name = models.CharField(max_length=200 , verbose_name="Название модели")
    symbolic_code = models.CharField(max_length=50 , unique=True , verbose_name="Символьный код")
    valve_type = models.ForeignKey(
        ValveType ,
        on_delete=models.CASCADE ,
        related_name='models' ,
        verbose_name="Тип арматуры"
    )
    description = models.TextField(blank=True , verbose_name="Описание")
    is_active = models.BooleanField(default=True , verbose_name="Активна")

    # Все параметры хранятся в JSON для производительности
    parameters = JSONField(
        default=dict ,
        verbose_name="Параметры" ,
        help_text="JSON объект с значениями параметров"
    )

    # Дублирование часто используемых параметров для индексации
    dn = models.IntegerField(blank=True , null=True , verbose_name="DN (номинальный диаметр)")
    pn = models.IntegerField(blank=True , null=True , verbose_name="PN (номинальное давление)")
    material = models.CharField(max_length=100 , blank=True , verbose_name="Материал корпуса")
    temp_min = models.IntegerField(blank=True , null=True , verbose_name="Мин. температура, °C")
    temp_max = models.IntegerField(blank=True , null=True , verbose_name="Макс. температура, °C")

    class Meta :
        ordering = ['valve_type' , 'symbolic_code']
        verbose_name = "Модель арматуры"
        verbose_name_plural = "Модели арматуры"
        indexes = [
            models.Index(fields=['dn']) ,
            models.Index(fields=['pn']) ,
            models.Index(fields=['material']) ,
            models.Index(fields=['temp_min' , 'temp_max']) ,
            models.Index(fields=['valve_type' , 'is_active']) ,
        ]

    def __str__(self) :
        return f"{self.valve_type.symbolic_code}-{self.symbolic_code} - {self.name}"

    def save(self , *args , **kwargs) :
        """Обновляем индексируемые поля при сохранении"""
        self._update_indexed_fields()
        super().save(*args , **kwargs)

    def _update_indexed_fields(self) :
        """Обновление часто используемых полей для индексации"""
        params = self.parameters or {}

        self.dn = params.get('dn') or params.get('nominal_diameter')
        self.pn = params.get('pn') or params.get('nominal_pressure')
        self.material = params.get('body_material') or params.get('material')

        # Обработка температур
        temp_range = params.get('temperature_range') or {}
        self.temp_min = temp_range.get('min') or params.get('temp_min')
        self.temp_max = temp_range.get('max') or params.get('temp_max')


class ValveParameterValue(models.Model) :
    """
    Альтернативная таблица для сложных запросов и отчетов
    (опционально, для сложной аналитики)
    """
    valve_model = models.ForeignKey(
        ValveModel ,
        on_delete=models.CASCADE ,
        related_name='parameter_values'
    )
    parameter = models.ForeignKey(
        ParameterDefinition ,
        on_delete=models.CASCADE ,
        related_name='values'
    )
    value_string = models.CharField(max_length=200 , blank=True)
    value_int = models.IntegerField(blank=True , null=True)
    value_float = models.FloatField(blank=True , null=True)
    value_bool = models.BooleanField(blank=True , null=True)

    class Meta :
        unique_together = ['valve_model' , 'parameter']
        indexes = [
            models.Index(fields=['parameter' , 'value_int']) ,
            models.Index(fields=['parameter' , 'value_float']) ,
            models.Index(fields=['parameter' , 'value_string']) ,
        ]


# Сервисные функции
class ValveSearchService :
    """Сервис для поиска и фильтрации арматуры"""

    @staticmethod
    def search_valves(filters , valve_type=None) :
        """
        Поиск арматуры по параметрам
        filters: dict с параметрами фильтрации
        """
        queryset = ValveModel.objects.filter(is_active=True)

        if valve_type :
            queryset = queryset.filter(valve_type=valve_type)

        # Быстрая фильтрация по индексируемым полям
        if 'dn' in filters :
            queryset = queryset.filter(dn=filters['dn'])
        if 'pn' in filters :
            queryset = queryset.filter(pn=filters['pn'])
        if 'material' in filters :
            queryset = queryset.filter(material__icontains=filters['material'])
        if 'temp_min' in filters and 'temp_max' in filters :
            queryset = queryset.filter(
                temp_min__lte=filters['temp_min'] ,
                temp_max__gte=filters['temp_max']
            )

        # Медленная фильтрация по JSON полю (использовать осторожно)
        for param , value in filters.items() :
            if param not in ['dn' , 'pn' , 'material' , 'temp_min' , 'temp_max'] :
                queryset = queryset.filter(parameters__contains={param : value})

        return queryset

    @staticmethod
    def get_available_parameters(valve_type) :
        """Получить доступные параметры для типа арматуры"""
        return ParameterDefinition.objects.filter(
            valve_types=valve_type ,
            is_filterable=True
        ).select_related('category').order_by('category__order' , 'order')


# Сигналы для поддержания целостности
@receiver(models.signals.post_save , sender=ValveModel)
def update_parameter_values(sender , instance , **kwargs) :
    """
    Обновление таблицы ParameterValue при изменении модели
    (опционально, для сложных запросов)
    """
    # Здесь можно реализовать синхронизацию с ValveParameterValue
    pass