#pa_controls/admin/limit_switch_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from pa_controls.models import LimitSwitchSensorVariety, LimitSwitchOutput
from pa_controls.models.limit_switch import LimitSwitchModelLine , LimitSwitchBox , LimitSwitchBody


@admin.register(LimitSwitchSensorVariety)
class LimitSwitchSensorVarietyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active', 'short_description']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    def short_description(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'

    short_description.short_description = _('Краткое описание')


@admin.register(LimitSwitchOutput)
class LimitSwitchOutputAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'code', 'contact_form', 'wires_per_sensor', 'signal_type', 'sorting_order', ]
    list_filter = ['is_active', 'contact_form', 'wires_per_sensor']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sorting_order', ]
    ordering = ['sorting_order', 'name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Электрические характеристики'), {
            'fields': ('contact_form', 'signal_type', 'wires_per_sensor')
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _(
                'JSON формат: {"is_namur": true, "is_analog": true, "is_pneumatic": true, "resistance": 1, "signal_type": "4-20mA"}')
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    def extra_params_preview(self, obj):
        if obj.extra_params:
            # Показываем ключевые параметры
            params = []
            if obj.extra_params.get('is_namur'):
                params.append('NAMUR')
            if obj.extra_params.get('is_analog'):
                params.append('Аналоговый')
            if obj.extra_params.get('is_pneumatic'):
                params.append('Пневматический')
            if obj.extra_params.get('resistance'):
                params.append(f"{obj.extra_params['resistance']} кОм")
            if obj.extra_params.get('signal_type'):
                params.append(obj.extra_params['signal_type'])

            if params:
                return format_html('<span style="color: #666;">{}</span>', ', '.join(params))
        return '-'

    extra_params_preview.short_description = _('Доп. параметры')


@admin.register(LimitSwitchModelLine)
class LimitSwitchModelLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'producer', 'brand', 'sorting_order', 'is_active']
    list_filter = ['is_active', 'producer', 'brand']
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Шаблоны'), {
            'fields': ('name_template', 'description_template'),
            'classes': ('wide',),
            'description': _('Шаблоны для автоматического формирования названия и описания')
        }),
        (_('Производитель и бренд'), {
            'fields': ('producer', 'brand')
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _('JSON формат: {"material": "aluminum", "color": "blue", "features": ["visual", "led"]}')
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )

@admin.register(LimitSwitchBody)
class LimitSwitchBodyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'is_active', 'sorting_order'
    ]
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order']
    # Для ManyToMany полей
    filter_horizontal = ['cable_glands_holes', 'mounting']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'weight', )
        }),

        (_('Кабельные вводы'), {
            'fields': ('cable_glands_holes',),
            'classes': ('wide',),
            'description': _('Отверстия под кабельные вводы (можно выбрать несколько)')
        }),
        (_('Присоединительные размеры'), {
            'fields': ('mounting',),
            'classes': ('wide',),
            'description': _('Стандарты присоединения NAMUR (можно выбрать несколько)')
        }),
        (_('Дополнительные параметры JSON'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _('JSON формат: {"material": "aluminum", "features": ["led", "visual"]}')
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )


@admin.register(LimitSwitchBox)
class LimitSwitchBoxAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'model_line', 'sensor_variety', 'output_type',
        'points', 'ip', 'get_exd_display', 'is_active', 'sorting_order'
    ]
    list_filter = [
        'is_active', 'sensor_variety', 'output_type', 'model_line',
        'ip', 'exd'
    ]
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']
    actions = ['copy_selected_boxes']
    filter_horizontal = ['exd']  # Для ManyToMany полей

    fieldsets = (
        (_('Основная информация'), {
            'fields': (('name', 'code', 'model_line'),
                       ('sensor_variety', 'output_type', 'points'),
                       ('ip', 'exd'),  # exd теперь ManyToMany
                       ('work_temp_min', 'work_temp_max'),)
        }),
        (_('Описание'), {
            'fields': ('description',),
            'classes': ('wide',),
        }),
        (_('Материалы и вес'), {
            'fields': (('body_material', 'body_material_specified'), 'body')
        }),
        (_('Дополнительные опции'), {
            'fields': (('is_pneumatic', 'has_namur_interface', 'has_visual_indicator'),)
        }),
        (_('Дополнительные параметры JSON'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _('JSON формат: {"material": "aluminum", "features": ["led", "visual"]}')
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'sensor_variety', 'output_type', 'ip',
            'body_material', 'body_material_specified'
        ).prefetch_related('exd')  # prefetch_related для ManyToMany

    def get_exd_display(self, obj):
        """Возвращает отображаемую маркировку взрывозащиты"""
        if not obj.exd.exists():
            return "-"
        return ", ".join([exd.name for exd in obj.exd.all()])

    get_exd_display.short_description = _("Взрывозащита")

    def copy_selected_boxes(self, request, queryset):
        """
        Действие для копирования выбранных БКВ
        """
        copied_count = 0
        errors = []

        for original in queryset:
            try:
                # Вызываем метод copy() модели
                original.copy()
                copied_count += 1
            except Exception as e:
                errors.append(f"{original.name}: {str(e)}")

        # Сообщение о результате
        if copied_count > 0:
            self.message_user(request, f"✅ Скопировано {copied_count} БКВ.", level=messages.SUCCESS)

        if errors:
            self.message_user(request, f"⚠️ Ошибки при копировании: {', '.join(errors)}", level=messages.ERROR)

    copy_selected_boxes.short_description = "📋 Копировать выбранные БКВ"

