# core/constants.py
from django.utils.translation import gettext_lazy as _


class DataFormat :
    """Форматы данных"""
    COMPACT = 'compact'
    DISPLAY = 'display'
    FULL = 'full'
    EXPORT = 'export'

    CHOICES = [
        (COMPACT , _('Компактный')) ,
        (DISPLAY , _('Для отображения')) ,
        (FULL , _('Полный')) ,
        (EXPORT , _('Для экспорта')) ,
    ]


class DisplayView :
    """Типы отображения"""
    LIST = 'list'
    CARD = 'card'
    DETAIL = 'detail'
    BADGE = 'badge'
    INLINE = 'inline'

    CHOICES = [
        (LIST , _('Список')) ,
        (CARD , _('Карточка')) ,
        (DETAIL , _('Детально')) ,
        (BADGE , _('Бейдж')) ,
        (INLINE , _('В строке')) ,
    ]


class FieldType :
    """Типы полей для UI"""
    TEXT = 'text'
    TEXTAREA = 'textarea'
    NUMBER = 'number'
    DATE = 'date'
    DATETIME = 'datetime'
    BOOLEAN = 'boolean'
    SELECT = 'select'
    MULTISELECT = 'multiselect'
    URL = 'url'
    EMAIL = 'email'
    IMAGE = 'image'
    FILE = 'file'
    COLOR = 'color'
    RICH_TEXT = 'rich_text'

    CHOICES = [
        (TEXT , _('Текст')) ,
        (TEXTAREA , _('Текстовая область')) ,
        (NUMBER , _('Число')) ,
        (DATE , _('Дата')) ,
        (DATETIME , _('Дата и время')) ,
        (BOOLEAN , _('Да/Нет')) ,
        (SELECT , _('Выбор')) ,
        (MULTISELECT , _('Множественный выбор')) ,
        (URL , _('Ссылка')) ,
        (EMAIL , _('Email')) ,
        (IMAGE , _('Изображение')) ,
        (FILE , _('Файл')) ,
        (COLOR , _('Цвет')) ,
        (RICH_TEXT , _('Текст с форматированием')) ,
    ]