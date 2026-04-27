#pa_controls/admin/limit_switch_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from pa_controls.models import LimitSwitchSensorVariety, LimitSwitchOutput
from pa_controls.models.limit_switch import LimitSwitchModelLine, LimitSwitchBox


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
    list_display = ['name', 'code', 'contact_form', 'wire_count', 'sorting_order', 'is_active', 'extra_params_preview']
    list_filter = ['is_active', 'contact_form', 'wire_count']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sorting_order', 'is_active', 'wire_count']
    ordering = ['sorting_order', 'name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Электрические характеристики'), {
            'fields': ('contact_form', 'wire_count')
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


@admin.register(LimitSwitchBox)
class LimitSwitchBoxAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'model_line', 'sensor_variety', 'output_type',
        'points', 'ip', 'is_active', 'sorting_order'
    ]
    list_filter = [
        'is_active', 'sensor_variety', 'output_type', 'model_line',
        'ip', 'exd'
    ]
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']
    actions = ['copy_selected_boxes']  # <-- ВОТ ЭТА СТРОКА
    # Для ManyToMany полей
    filter_horizontal = ['cable_glands_holes', 'mounting_standards']
    fieldsets = (
        (_('Основная информация'), {
            'fields': (('name', 'code',  'model_line'),
            ('sensor_variety', 'output_type', 'points'),
                       ('ip', 'exd'),
                       ('work_temp_min', 'work_temp_max'),)
        }),
        (_('Температурный режим'), {
            'fields': ('description',),
            'classes': ('wide',),
        }),
        (_('Материалы и вес'), {
            'fields': (('body_material', 'body_material_specified'), ('weight', ))
        }),
        (_('Дополнительные опции'), {
            'fields': (('is_pneumatic', 'has_namur_interface', 'has_visual_indicator'),)
        }),
        (_('Кабельные вводы'), {
            'fields': ('cable_glands_holes',),
            'classes': ('wide',),
            'description': _('Отверстия под кабельные вводы (можно выбрать несколько)')
        }),
        (_('Присоединительные размеры'), {
            'fields': ('mounting_standards',),
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'sensor_variety', 'output_type', 'ip', 'exd',
            'body_material', 'body_material_specified'
        )

    def copy_selected_boxes(self, request, queryset):
        """
        Действие для копирования выбранных БКВ
        """
        copied_count = 0
        errors = []

        for original in queryset:
            try:
                # Генерируем новые имена с суффиксом
                original_name = original.name or ""
                original_code = original.code or ""

                # Если имя уже содержит суффикс, добавляем еще один
                if " (Копия)" in original_name:
                    base_name = original_name.replace(" (Копия)", "")
                    new_name = f"{base_name} (Копия)"
                else:
                    new_name = f"{original_name} (Копия)"

                # Для кода тоже добавляем суффикс (если есть)
                if original_code:
                    if "_copy" in original_code:
                        # Увеличиваем номер копии
                        import re
                        match = re.search(r"_copy(\d+)$", original_code)
                        if match:
                            num = int(match.group(1)) + 1
                            new_code = re.sub(r"_copy\d+$", f"_copy{num}", original_code)
                        else:
                            new_code = f"{original_code}_copy1"
                    else:
                        new_code = f"{original_code}_copy"
                else:
                    new_code = None

                # Создаем копию
                copy = LimitSwitchBox(
                    name=new_name,
                    code=new_code,
                    description=f"Копия: {original.description}" if original.description else "Копия",
                    sorting_order=original.sorting_order + 100,  # Сдвигаем порядок
                    is_active=original.is_active,
                    model_line=original.model_line,
                    sensor_variety=original.sensor_variety,
                    output_type=original.output_type,
                    points=original.points,
                    ip=original.ip,
                    exd=original.exd,
                    work_temp_min=original.work_temp_min,
                    work_temp_max=original.work_temp_max,
                    body_material=original.body_material,
                    body_material_specified=original.body_material_specified,
                    weight=original.weight,
                    is_pneumatic=original.is_pneumatic,
                    has_namur_interface=original.has_namur_interface,
                    has_visual_indicator=original.has_visual_indicator,
                    extra_params=original.extra_params.copy() if original.extra_params else {}
                )
                copy.save()

                # Копируем ManyToMany связи
                copy.cable_glands_holes.set(original.cable_glands_holes.all())
                copy.mounting_standards.set(original.mounting_standards.all())

                copied_count += 1

            except Exception as e:
                errors.append(f"{original.name}: {str(e)}")

        # Сообщение о результате
        if copied_count > 0:
            self.message_user(request, f"✅ Скопировано {copied_count} БКВ.")

        if errors:
            self.message_user(request, f"⚠️ Ошибки при копировании: {', '.join(errors)}", level='ERROR')

    copy_selected_boxes.short_description = "📋 Копировать выбранные БКВ"