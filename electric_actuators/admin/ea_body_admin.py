#electric_actuators/admin/ea_body_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from electric_actuators.models import ElectricActuatorBody , ElectricActuatorBodyTable , ElectricExdOption , \
    CableGlandHolesSetBodyOption
import logging
logger = logging.getLogger(__name__)

def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"
class CableGlandHolesSetBodyOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = CableGlandHolesSetBodyOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['cg_set', 'encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Кабельные вводы")
    verbose_name_plural = _("Опции кабельных вводов")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset

@admin.register(ElectricActuatorBodyTable)
class ElectricActuatorBodyTableAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'code', 'sorting_order', 'is_active')
    # Поля для редактирования в админке
    fieldsets = (
        ('Основные параметры', {
            'fields': (('name', 'code' ),('sorting_order', 'is_active'),)
        }),
        ('Описание', {
            'fields': ('description',  )
        }),
    )

@admin.register(ElectricActuatorBody)
class ElectricActuatorBodyAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'code', 'sorting_order', 'is_active')

    # Добавить фильтры для фильтрации по определенным полям
    list_filter = ('model_line', 'mounting_plate', 'stem_shape', 'stem_size')
    list_editable = ('code', 'sorting_order', 'is_active')

    # Возможность поиска по полям
    search_fields = ('name', 'code', 'model_line__name')
    filter_horizontal = ('mounting_plate',)  # Это добавит горизонтальные чекбоксы для поля "mounting_plate"

    # Поля для редактирования в админке
    fieldsets = (
        ('Основные параметры', {
            'fields': (('name', 'sorting_order', 'is_active', 'code' ),('model_line','body_table')),
        }),
        ('Опции и характеристики', {
            'fields': ( ('mounting_plate',), ('stem_shape',
                       'stem_size'),( 'max_stem_height','max_stem_diameter'),'weight_body' )
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
    inlines = [CableGlandHolesSetBodyOptionInline]  # Если есть инлайны для отображения других связанных объектов
    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования

@admin.register(ElectricExdOption)
class ElectricExdOptionAdmin(admin.ModelAdmin):
    # Показать важные поля в списке объектов модели
    list_display = ('model_line','encoding',  'exd_option')

    # Поля для редактирования в админке
    fieldsets = (
        ('Основные параметры', {
            'fields': ('model_line','encoding',  'exd_option'),
        }),
    )