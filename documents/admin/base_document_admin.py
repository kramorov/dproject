# documents/admin/base_document_admin.py
"""
BaseDocumentAdmin — базовый админ-класс для документов.

Общие настройки: list_display, list_filter, search_fields, readonly_fields.
Подклассы дополняют специфичными полями и autocomplete_fields.
"""
from django.contrib import admin


class BaseDocumentAdmin(admin.ModelAdmin):
    """
    Базовый ModelAdmin для документов.

    Подкласс может расширить:
        list_display  — добавить специфичные FK
        list_filter   — добавить фильтры по типу цены, валюте, ...
        search_fields — добавить поиск по коду
        autocomplete_fields — для FK с большим числом записей
    """

    list_display = [
        'name', 'code', 'document_date',
        'status', 'is_active', 'created_at',
    ]
    list_filter = ['status', 'is_active']
    actions = ['action_mark_deleted', 'action_hard_delete']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['code', 'status', 'created_at', 'updated_at']
    ordering = ['-document_date']
    date_hierarchy = 'document_date'

    # Поля только для чтения в форме редактирования
    # (статус меняется через действия, не через форму)
    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_posted:
            # Проведённый документ — всё readonly
            return [f.name for f in self.model._meta.fields]
        return fields

    def has_delete_permission(self, request, obj=None):
        """Физическое удаление — только через действие 'Удалить из БД'."""
        return False

    # ── Админ-действия ──

    @admin.action(description='Пометить выбранные документы на удаление')
    def action_mark_deleted(self, request, queryset):
        marked = 0
        errors = 0
        for doc in queryset:
            try:
                if not doc.is_deleted:
                    doc.mark_deleted()  # atomic внутри метода
                    marked += 1
            except Exception:
                errors += 1
        msg = f'{marked} док. помечено на удаление.'
        if errors:
            msg += f' Ошибок: {errors}.'
        self.message_user(request, msg)

    @admin.action(description='Физически удалить выбранные документы из БД')
    def action_hard_delete(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} док. удалено из базы.')
