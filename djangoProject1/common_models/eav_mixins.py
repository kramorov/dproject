# common_models/eav_mixins.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class EAVAttributeMixin(models.Model) :
    """Миксин для атрибутов EAV с поддержкой ссылок на модели"""
    name = models.CharField(
        max_length=100 ,
        unique=True ,
        verbose_name=_('Название атрибута')
    )

    description = models.TextField(
        blank=True ,
        verbose_name=_('Описание атрибута')
    )

    default_value = models.TextField(
        blank=True ,
        verbose_name=_('Значение по умолчанию')
    )

    value_type = models.CharField(
        max_length=20 ,
        choices=[
            ('string' , _('Строка')) ,
            ('number' , _('Число')) ,
            ('boolean' , _('Логическое')) ,
            ('json' , _('JSON')) ,
            ('choice' , _('Выбор из списка')) ,
            ('foreign_key' , _('Ссылка на модель')) ,  # ← НОВЫЙ ТИП
            ('many_to_many' , _('Множественная ссылка')) ,  # ← НОВЫЙ ТИП
        ] ,
        default='string' ,
        verbose_name=_('Тип значения')
    )

    # Поля для ссылок на модели
    target_model = models.ForeignKey(
        ContentType ,
        on_delete=models.SET_NULL ,
        null=True ,
        blank=True ,
        verbose_name=_('Целевая модель') ,
        help_text=_('Для типов "foreign_key" и "many_to_many"')
    )

    choices = models.TextField(
        blank=True ,
        verbose_name=_('Варианты выбора') ,
        help_text=_('Для type="choice". Разделите варианты переносом строки')
    )

    is_global = models.BooleanField(
        default=True ,
        verbose_name=_('Глобальный атрибут') ,
        help_text=_('Доступен для всех сущностей')
    )

    class Meta :
        abstract = True

    def __str__(self) :
        return self.name

    def get_choices_list(self) :
        # """Возвращает список вариантов для type="choice""""
        if self.value_type == 'choice' and self.choices :
            return [choice.strip() for choice in self.choices.split('\n') if choice.strip()]
        return []

    def get_target_model_class(self) :
        """Возвращает класс целевой модели"""
        if self.target_model :
            return self.target_model.model_class()
        return None


class EAVValueMixin(models.Model) :
    """Миксин для значений EAV с поддержкой GenericForeignKey"""

    # Текстовое значение (для простых типов)
    value_text = models.TextField(
        blank=True ,
        verbose_name=_('Текстовое значение') ,
        help_text=_('Используется для простых типов данных')
    )

    # Ссылка на любую модель (для foreign_key)
    value_object_id = models.PositiveIntegerField(
        null=True ,
        blank=True ,
        verbose_name=_('ID связанного объекта')
    )
    value_content_type = models.ForeignKey(
        ContentType ,
        on_delete=models.CASCADE ,
        null=True ,
        blank=True ,
        verbose_name=_('Тип связанного объекта') ,
        related_name='eav_value_%(class)s_set'  # Уникальное related_name
    )
    value_object = GenericForeignKey(
        'value_content_type' ,
        'value_object_id'
    )

    # Метаданные
    display_order = models.PositiveIntegerField(
        default=0 ,
        verbose_name=_('Порядок отображения')
    )

    is_required = models.BooleanField(
        default=False ,
        verbose_name=_('Обязательное поле')
    )

    created_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_('Создано')
    )
    updated_at = models.DateTimeField(
        auto_now=True ,
        verbose_name=_('Обновлено')
    )

    class Meta :
        abstract = True
        ordering = ['display_order' , 'attribute__name']

    def __str__(self) :
        if self.value_object :
            return f"{self.attribute.name}: {self.value_object}"
        return f"{self.attribute.name}: {self.value_text}"

    def get_typed_value(self) :
        """Возвращает значение в правильном типе"""
        if self.attribute.value_type == 'foreign_key' and self.value_object :
            return self.value_object

        elif self.attribute.value_type == 'many_to_many' :
            # Для many_to_many будем использовать отдельную модель связи
            return self.related_objects.all()

        # Простые типы данных
        value = self.value_text
        if self.attribute.value_type == 'number' :
            try :
                return float(value) if '.' in value else int(value)
            except (ValueError , TypeError) :
                return 0
        elif self.attribute.value_type == 'boolean' :
            return value.lower() in ('true' , '1' , 'yes' , 'on')
        elif self.attribute.value_type == 'json' :
            import json
            try :
                return json.loads(value)
            except (json.JSONDecodeError , TypeError) :
                return {}
        elif self.attribute.value_type == 'choice' :
            return value

        return value

    def set_value(self , value) :
        """Устанавливает значение в зависимости от типа"""
        if self.attribute.value_type in ['foreign_key' , 'many_to_many'] :
            if value is not None :
                self.value_object = value
                self.value_text = str(value.pk) if hasattr(value , 'pk') else ''
            else :
                self.value_object = None
                self.value_text = ''
        else :
            self.value_text = str(value) if value is not None else ''
            self.value_object = None

    def save(self , *args , **kwargs) :
        """Автоматически устанавливаем content_type при сохранении"""
        if self.value_object and not self.value_content_type :
            self.value_content_type = ContentType.objects.get_for_model(self.value_object)
        super().save(*args , **kwargs)


class EAVManyToManyValueMixin(models.Model) :
    """Миксин для хранения Many-to-Many связей через EAV"""
    value = models.ForeignKey(
        'self' ,  # Будет заменено на конкретную модель
        on_delete=models.CASCADE ,
        related_name='%(class)s_relations' ,
        verbose_name=_('Значение')
    )

    display_order = models.PositiveIntegerField(
        default=0 ,
        verbose_name=_('Порядок отображения')
    )

    created_at = models.DateTimeField(
        auto_now_add=True ,
        verbose_name=_('Создано')
    )

    class Meta :
        abstract = True
        ordering = ['display_order']