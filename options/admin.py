# options/admin.py
from django.contrib import admin


class BaseExdOptionInline(admin.TabularInline):
    """Общий инлайн through-строк взрывозащиты (см. exd-option.md §4.6).

    Подклассы задают только ``model`` (+ при желании ``ordering``,
    ``verbose_name``/``verbose_name_plural``).
    """
    extra = 0
    fields = ['exd_options', 'encoding', 'is_default', 'sorting_order', 'is_active']
    filter_horizontal = ['exd_options']
