#pa_controls/admin/limit_switch_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from pa_controls.models import LimitSwitchSensorVariety, SignalType, ContactState, ContactForm, LimitSwitchBody, \
    SensorComponent
from pa_controls.models.limit_switch import LimitSwitchBox
from pa_controls.models.lsb_model_line import LimitSwitchModelLine


@admin.register(SensorComponent)
class SensorComponentAdmin(admin.ModelAdmin):
    """Админка для датчиков (компонентов)"""

    list_display = ['id',
        'name',
        'code',

        'wires_count',
        'electrical_specs',
        'is_active',
        'sorting_order'
    ]

    list_filter = [
        'is_active',
        'brand',
        'variety',
        'signal_type',
        'contact_form',
        'contact_state',
        'wires_count'
    ]

    search_fields = [
        'name',
        'code',
    ]

    list_editable = ['is_active', 'sorting_order']
    ordering = ['sorting_order']

    # Поля для отображения на странице редактирования
    fieldsets = (
        (_('Основная информация'), {
            'fields': (('name', 'code',  'brand'),)
        }),

        (_('Технические характеристики'), {
            'fields': (
                'variety',
                'signal_type',
                'contact_form',
                'contact_state',
                'electrical_specs',
                'wires_count'
            )
        }),

        (_('Искробезопасные параметры (Ex)'), {
            'fields': ('ui', 'ii', 'pi', 'ci', 'li'),
            'classes': ('collapse',),
        }),

        (_('Дополнительные параметры'), {
            'fields': ('description','extra_params',),
            # 'classes': ('collapse',),
        }),

        (_('Настройки отображения'), {
            'fields': ('sorting_order', 'is_active'),
        }),
    )


@admin.register(SignalType)
class SignalTypeAdmin(admin.ModelAdmin):
    """Админка для типов сигналов"""
    list_display = ['name', 'code', 'is_ex', 'is_active', 'sorting_order']
    list_filter = ['is_ex', 'is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Настройки'), {
            'fields': ('is_ex', 'is_active', 'sorting_order')
        }),
    )


@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    """Админка для форм контактов"""
    list_display = ['name', 'code', 'wires_required', 'is_active', 'sorting_order']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['wires_required', 'sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Технические параметры'), {
            'fields': ('wires_required',)
        }),
        (_('Настройки'), {
            'fields': ('is_active', 'sorting_order')
        }),
    )


@admin.register(ContactState)
class ContactStateAdmin(admin.ModelAdmin):
    """Админка для состояний контактов"""
    list_display = ['name', 'code', 'is_active', 'sorting_order']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Настройки'), {
            'fields': ('is_active', 'sorting_order')
        }),
    )

@admin.register(LimitSwitchSensorVariety)
class LimitSwitchSensorVarietyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active', 'short_description']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'name_template','description_template','description')
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
            'fields': ('producer', 'brand', 'equipment_type')
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
        'name', 'code', 'model_line', 'body', 'sensor_variety',
        'points', 'ip', 'get_exd_display',
    ]
    list_filter = [
         'code','sensor_variety',  'model_line',
        'ip', 'points', 'body',
    ]
    search_fields = ['name', 'code', ]
    list_editable = ['code', 'model_line', 'body','sensor_variety','points',]
    ordering = ['sorting_order', 'name']
    actions = ['copy_selected_boxes','save_selected_boxes']
    filter_horizontal = ['additional_sensor', 'exd']

    fieldsets = (
        (_('Основная информация'), {
            'fields': (('name', 'code', 'model_line'),
                       ( 'points','sensor_variety',),
                       ('ip', ),
                       ('work_temp_min', 'work_temp_max'),)
        }),
        (_('Описание'), {
            'fields': ('description',),
            'classes': ('wide',),
        }),
        (_('Материалы и вес'), {
            'fields': (('body_material', 'body_material_specified'), 'body')
        }),
        (_('Датчики') , {
            'fields' : ('primary_sensor' , 'additional_sensor', 'exd')
        }) ,
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

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        # Патчим __init__: пропускаем exd в model_to_dict, затем заполняем вручную
        original_init = form_class.__init__
        def patched_init(self_form, *args, **init_kwargs):
            opts = self_form._meta
            saved_fields = opts.fields
            if saved_fields and 'exd' in saved_fields:
                opts.fields = tuple(f for f in saved_fields if f != 'exd')
            original_init(self_form, *args, **init_kwargs)
            opts.fields = saved_fields
            # Заполняем exd вручную через raw SQL
            instance = init_kwargs.get('instance') or (args[0] if args else None)
            if instance and instance.pk:
                self_form.initial['exd'] = instance.exd_get_ids()
        form_class.__init__ = patched_init

        return form_class

    def save_related(self, request, form, formsets, change):
        # Вытаскиваем exd ДО save_m2m — иначе Django упадёт на .set()
        exd_data = form.cleaned_data.pop('exd', None)
        super().save_related(request, form, formsets, change)
        if exd_data is not None:
            form.instance.exd_set_ids([o.pk for o in exd_data])

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'sensor_variety',  'ip',
            'body_material', 'body_material_specified', 'body', 'primary_sensor'
        )

    def get_exd_display(self, obj):
        """Возвращает отображаемую маркировку взрывозащиты"""
        if not obj.exd_exists():
            return "-"
        return ", ".join([exd.name for exd in obj.exd_all])

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

    def save_selected_boxes(self, request, queryset):
        """
        Действие для перезаписи (сохранения) выбранных БКВ
        """
        saved_count = 0
        errors = []

        for obj in queryset:
            try:
                # Вызываем метод save() модели
                obj.save()
                saved_count += 1
            except Exception as e:
                errors.append(f"{obj.name}: {str(e)}")

        # Сообщение о результате
        if saved_count > 0:
            self.message_user(request, f"✅ Сохранено {saved_count} БКВ.", level=messages.SUCCESS)

        if errors:
            self.message_user(request, f"⚠️ Ошибки при сохранении: {', '.join(errors)}", level=messages.ERROR)

    save_selected_boxes.short_description = "💾 Перезаписать выбранные БКВ"