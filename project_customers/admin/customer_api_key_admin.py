# project_customers/admin/customer_api_key_admin.py
from django.contrib import admin
from django.utils.html import format_html
from ..models.customer_api_key import CustomerApiKey


@admin.register(CustomerApiKey)
class CustomerApiKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'key_prefix_display', 'is_active', 'access_until', 'last_used_at', 'created_at']
    list_filter = ['is_active', 'customer']
    search_fields = ['name', 'customer__name']
    filter_horizontal = ['allowed_apps']
    readonly_fields = ['key_hash', 'key_prefix', 'created_at', 'key_preview']
    fieldsets = [
        (None, {'fields': ['customer', 'name', 'is_active']}),
        ('Ключ', {'fields': ['key_prefix', 'key_hash', 'key_preview']}),
        ('Доступ', {'fields': ['allowed_apps', 'brand_filters', 'ip_whitelist', 'access_until']}),
        ('LLM', {'fields': ['llm_endpoint']}),
        ('Служебное', {'fields': ['created_at', 'last_used_at']}),
    ]

    def key_prefix_display(self, obj):
        return f"{obj.key_prefix}***"
    key_prefix_display.short_description = "Префикс"

    def key_preview(self, obj):
        if obj.pk:
            return format_html('<em>Хэш сохранён. Сырой ключ не отображается.</em>')
        return format_html('<em>Ключ будет сгенерирован при сохранении.</em>')
    key_preview.short_description = "Ключ"

    def save_model(self, request, obj, form, change):
        if not change:
            # Используем метод модели для генерации
            instance, raw = CustomerApiKey.generate_key(
                customer=obj.customer,
                name=obj.name,
            )
            # Копируем остальные поля из формы
            for field in ['allowed_apps', 'brand_filters', 'ip_whitelist',
                          'access_until', 'llm_endpoint', 'is_active']:
                if field in form.cleaned_data:
                    val = form.cleaned_data[field]
                    if field == 'allowed_apps':
                        instance.allowed_apps.set(val)
                    else:
                        setattr(instance, field, val)
            instance.save()
            self.message_user(
                request,
                f'Ключ создан! RAW KEY (показывается только раз): {raw}',
                level='WARNING'
            )
        else:
            super().save_model(request, obj, form, change)
