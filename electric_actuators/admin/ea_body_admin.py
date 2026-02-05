#electric_actuators/admin/ea_body_admin.py

from django.contrib import admin

from electric_actuators.models import ElectricActuatorBody


def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"

@admin.register(ElectricActuatorBody)
class ModelBodyAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'code', 'sorting_order', 'is_active')

    # Добавить фильтры для фильтрации по определенным полям
    list_filter = ('model_line', 'mounting_plate', 'stem_shape', 'stem_size')

    # Возможность поиска по полям
    search_fields = ('name', 'code', 'model_line__name')
    filter_horizontal = ('mounting_plate',)  # Это добавит горизонтальные чекбоксы для поля "mounting_plate"

    # Поля для редактирования в админке
    fieldsets = (
        ('Основные параметры', {
            'fields': (('name', 'model_line', 'code' ),('sorting_order', 'is_active'),)
        }),
        ('Опции и характеристики', {
            'fields': ( ('mounting_plate', 'stem_shape',
                       'stem_size'),( 'max_stem_height','max_stem_diameter') )
        }),
    )

    # # Поля для редактирования при добавлении или изменении записи
    # add_fieldsets = (
    #     ('Основные параметры', {
    #         'fields': ('name', 'model_line', 'text_description')
    #     }),
    #     ('Опции и характеристики', {
    #         'fields': ('cable_glands_holes', 'stem_shape', 'stem_size', 'max_stem_height',
    #                    'max_stem_diameter')
    #     }),
    # )
    # Возможность выбора отображаемых полей для инлайн-редактирования
    inlines = []  # Если есть инлайны для отображения других связанных объектов
    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования

