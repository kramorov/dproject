#electric_actuators/admin/ea_model_body_admin.py

from django.contrib import admin

from electric_actuators.models import ModelBody


def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"

@admin.register(ModelBody)
class ModelBodyAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'model_line', 'text_description', 'max_stem_height', 'max_stem_diameter')

    # Добавить фильтры для фильтрации по определенным полям
    list_filter = ('model_line', 'mounting_plate', 'stem_shape', 'stem_size')

    # Возможность поиска по полям
    search_fields = ('name', 'text_description', 'model_line__name')
    filter_horizontal = ('mounting_plate',)  # Это добавит горизонтальные чекбоксы для поля "mounting_plate"

    # Поля для редактирования в админке
    fieldsets = (
        ('Основные параметры', {
            'fields': ('name', 'model_line', 'text_description', )
        }),
        ('Опции и характеристики', {
            'fields': (('default_cable_glands_holes', 'allowed_cable_glands_holes'), 'mounting_plate', 'stem_shape',
                       'stem_size', 'max_stem_height',
                       'max_stem_diameter')
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

    # Отображение связанного объекта (например, когда поля из связанных моделей показываются в форме)
    def get_related_fieldsets(self, request, obj=None):
        if obj:
            return super().get_related_fieldsets(request, obj)
        return self.add_fieldsets  # если объект еще не создан, показываем поля для добавления

    # Возможность выбора отображаемых полей для инлайн-редактирования
    inlines = []  # Если есть инлайны для отображения других связанных объектов
    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования

