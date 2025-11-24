from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from valve_data.models_valve_line import ValveLine


class ValveLineEAVSection(models.Model) :
    """Разделы для атрибутов ValveLine"""
    name = models.CharField(max_length=100 , verbose_name=_("Название раздела"))
    code = models.CharField(max_length=50 , unique=True , verbose_name=_("Код раздела"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    valve_varieties = models.ManyToManyField(
        ValveVariety ,
        related_name='eav_sections' ,
        verbose_name=_("Типы арматуры") ,
        help_text=_("Типы арматуры, для которых доступен этот раздел")
    )

    class Meta :
        ordering = ['sorting_order' , 'name']
        verbose_name = _("Раздел атрибутов ValveLine")
        verbose_name_plural = _("Разделы атрибутов ValveLine")

    def __str__(self) :
        return self.name


class ValveLineEAVAttribute(models.Model) :
    """Атрибут EAV системы для ValveLine"""
    name = models.CharField(max_length=100 , verbose_name=_("Название атрибута"))
    code = models.CharField(max_length=50 , unique=True , verbose_name=_("Код атрибута"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))

    # Связь с разделами
    section = models.ForeignKey(
        ValveLineEAVSection ,
        on_delete=models.CASCADE ,
        related_name='attributes' ,
        verbose_name=_("Раздел") ,
        help_text=_("Раздел, к которому принадлежит атрибут")
    )

    # Тип значения атрибута
    VALUE_TYPE_CHOICES = [
        ('string' , _('Строка')) ,
        ('integer' , _('Целое число')) ,
        ('float' , _('Десятичное число')) ,
        ('boolean' , _('Да/Нет')) ,
        ('choice' , _('Выбор из списка')) ,
        ('multi_choice' , _('Множественный выбор')) ,
    ]
    value_type = models.CharField(
        max_length=20 ,
        choices=VALUE_TYPE_CHOICES ,
        default='string' ,
        verbose_name=_("Тип значения")
    )

    # Единица измерения (опционально)
    unit = models.CharField(max_length=20 , blank=True , verbose_name=_("Единица измерения"))

    # Обязательность заполнения
    is_required = models.BooleanField(default=False , verbose_name=_("Обязательный"))

    # Порядок сортировки внутри раздела
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))

    # Активность атрибута
    is_active = models.BooleanField(default=True , verbose_name=_("Активный"))

    class Meta :
        ordering = ['section__sorting_order' , 'sorting_order' , 'name']
        verbose_name = _("Атрибут ValveLine")
        verbose_name_plural = _("Атрибуты ValveLine")
        unique_together = ['section' , 'code']

    def __str__(self) :
        return f"{self.section.name} - {self.name}"

    def clean(self) :
        """Валидация атрибута"""
        if self.section and self.section.pk :
            # Проверяем, что атрибут соответствует типам арматуры раздела
            pass
        super().clean()


class ValveLineEAVChoiceValue(models.Model) :
    """Значения для атрибутов типа choice/multi_choice"""
    attribute = models.ForeignKey(
        ValveLineEAVAttribute ,
        on_delete=models.CASCADE ,
        related_name='choice_values' ,
        verbose_name=_("Атрибут")
    )
    value = models.CharField(max_length=200 , verbose_name=_("Значение"))
    display_name = models.CharField(max_length=200 , verbose_name=_("Отображаемое название"))
    description = models.TextField(blank=True , verbose_name=_("Описание"))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки"))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно"))

    class Meta :
        ordering = ['attribute' , 'sorting_order' , 'display_name']
        verbose_name = _("Значение для выбора")
        verbose_name_plural = _("Значения для выбора")
        unique_together = ['attribute' , 'value']

    def __str__(self) :
        return f"{self.attribute.name}: {self.display_name}"


class ValveLineEAVValue(models.Model) :
    """Значения атрибутов для конкретного ValveLine"""
    valve_line = models.ForeignKey(
        ValveLine ,
        on_delete=models.CASCADE ,
        related_name='eav_values' ,
        verbose_name=_("Семейство серий арматуры")
    )
    attribute = models.ForeignKey(
        ValveLineEAVAttribute ,
        on_delete=models.CASCADE ,
        related_name='values' ,
        verbose_name=_("Атрибут")
    )

    # Различные типы значений
    string_value = models.CharField(max_length=500 , blank=True , verbose_name=_("Строковое значение"))
    integer_value = models.IntegerField(null=True , blank=True , verbose_name=_("Числовое значение"))
    float_value = models.FloatField(null=True , blank=True , verbose_name=_("Десятичное значение"))
    boolean_value = models.BooleanField(null=True , blank=True , verbose_name=_("Логическое значение"))

    # Для выбора из списка
    choice_value = models.ForeignKey(
        ValveLineEAVChoiceValue ,
        on_delete=models.CASCADE ,
        null=True ,
        blank=True ,
        related_name='eav_usages' ,
        verbose_name=_("Значение из списка")
    )

    # Для множественного выбора (через отдельную модель)
    multi_choice_values = models.ManyToManyField(
        ValveLineEAVChoiceValue ,
        blank=True ,
        related_name='multi_eav_usages' ,
        verbose_name=_("Множественные значения")
    )

    created_at = models.DateTimeField(auto_now_add=True , verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True , verbose_name=_("Обновлено"))

    class Meta :
        verbose_name = _("Значение атрибута ValveLine")
        verbose_name_plural = _("Значения атрибутов ValveLine")
        unique_together = ['valve_line' , 'attribute']

    def __str__(self) :
        return f"{self.valve_line} - {self.attribute.name}"

    def clean(self) :
        """Валидация значения в зависимости от типа атрибута"""
        if self.attribute :
            # Проверяем соответствие типа атрибута и заполненных полей
            if self.attribute.value_type == 'string' and not self.string_value :
                if self.attribute.is_required :
                    raise ValidationError(_("Для строкового атрибута должно быть заполнено строковое значение"))

            elif self.attribute.value_type == 'integer' and self.integer_value is None :
                if self.attribute.is_required :
                    raise ValidationError(_("Для числового атрибута должно быть заполнено числовое значение"))

            elif self.attribute.value_type == 'float' and self.float_value is None :
                if self.attribute.is_required :
                    raise ValidationError(_("Для десятичного атрибута должно быть заполнено десятичное значение"))

            elif self.attribute.value_type == 'boolean' and self.boolean_value is None :
                if self.attribute.is_required :
                    raise ValidationError(_("Для логического атрибута должно быть указано значение"))

            elif self.attribute.value_type == 'choice' and not self.choice_value :
                if self.attribute.is_required :
                    raise ValidationError(_("Для атрибута выбора должно быть выбрано значение из списка"))
                # Проверяем, что выбранное значение принадлежит атрибуту
                if self.choice_value and self.choice_value.attribute != self.attribute :
                    raise ValidationError(_("Выбранное значение не соответствует атрибуту"))

            elif self.attribute.value_type == 'multi_choice' :
                # Для множественного выбора проверяем, что выбрано хотя бы одно значение
                if self.attribute.is_required and not self.multi_choice_values.exists() :
                    raise ValidationError(
                        _("Для атрибута множественного выбора должно быть выбрано хотя бы одно значение"))

        super().clean()

    def get_display_value(self) :
        """Получить отображаемое значение"""
        if self.attribute.value_type == 'string' :
            return self.string_value
        elif self.attribute.value_type == 'integer' :
            return str(self.integer_value) if self.integer_value is not None else ""
        elif self.attribute.value_type == 'float' :
            return str(self.float_value) if self.float_value is not None else ""
        elif self.attribute.value_type == 'boolean' :
            return _("Да") if self.boolean_value else _("Нет") if self.boolean_value is not None else ""
        elif self.attribute.value_type == 'choice' :
            return self.choice_value.display_name if self.choice_value else ""
        elif self.attribute.value_type == 'multi_choice' :
            values = self.multi_choice_values.all()
            return ", ".join([v.display_name for v in values]) if values.exists() else ""
        return ""

    def get_actual_value(self) :
        """Получить фактическое значение"""
        if self.attribute.value_type == 'string' :
            return self.string_value
        elif self.attribute.value_type == 'integer' :
            return self.integer_value
        elif self.attribute.value_type == 'float' :
            return self.float_value
        elif self.attribute.value_type == 'boolean' :
            return self.boolean_value
        elif self.attribute.value_type == 'choice' :
            return self.choice_value.value if self.choice_value else None
        elif self.attribute.value_type == 'multi_choice' :
            return [v.value for v in self.multi_choice_values.all()]
        return None


# Методы для ValveLine модели для удобной работы с EAV
def add_eav_methods_to_valve_line() :
    """Добавляем методы к модели ValveLine для работы с EAV"""

    def get_eav_values(self , section_code=None) :
        """Получить EAV значения для этого ValveLine"""
        qs = self.eav_values.select_related(
            'attribute' ,
            'attribute__section' ,
            'choice_value'
        ).prefetch_related('multi_choice_values')

        if section_code :
            qs = qs.filter(attribute__section__code=section_code)

        return qs

    def get_eav_value(self , attribute_code , default=None) :
        """Получить значение конкретного атрибута"""
        try :
            eav_value = self.eav_values.get(attribute__code=attribute_code)
            return eav_value.get_actual_value()
        except ValveLineEAVValue.DoesNotExist :
            return default

    def set_eav_value(self , attribute_code , value) :
        """Установить значение атрибута"""
        from django.shortcuts import get_object_or_404

        attribute = get_object_or_404(ValveLineEAVAttribute , code=attribute_code , is_active=True)
        eav_value , created = ValveLineEAVValue.objects.get_or_create(
            valve_line=self ,
            attribute=attribute
        )

        # Устанавливаем значение в зависимости от типа атрибута
        if attribute.value_type == 'string' :
            eav_value.string_value = str(value)
        elif attribute.value_type == 'integer' :
            eav_value.integer_value = int(value)
        elif attribute.value_type == 'float' :
            eav_value.float_value = float(value)
        elif attribute.value_type == 'boolean' :
            eav_value.boolean_value = bool(value)
        elif attribute.value_type == 'choice' :
            choice_value = get_object_or_404(ValveLineEAVChoiceValue , attribute=attribute , value=str(value))
            eav_value.choice_value = choice_value
        elif attribute.value_type == 'multi_choice' :
            if not isinstance(value , (list , tuple)) :
                value = [value]
            choice_values = ValveLineEAVChoiceValue.objects.filter(attribute=attribute , value__in=value)
            eav_value.multi_choice_values.set(choice_values)

        eav_value.save()
        return eav_value

    # Добавляем методы к модели ValveLine
    ValveLine.get_eav_values = get_eav_values
    ValveLine.get_eav_value = get_eav_value
    ValveLine.set_eav_value = set_eav_value


# Вызываем функцию для добавления методов
add_eav_methods_to_valve_line()