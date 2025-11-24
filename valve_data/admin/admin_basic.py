#valve_data/admin/admin|_basic.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


from valve_data.models import (
    ValveVariety , ValveConnectionToPipe , PortQty , ConstructionVariety , AllowedDnTemplate , ValveLine
)


def duplicate_selected_action(modeladmin , request , queryset) :
    """
    Универсальное действие для копирования выбранных объектов
    Работает с любой моделью
    """
    for obj in queryset :
        try :
            # Создаем копию объекта
            new_obj = obj.__class__.objects.get(pk=obj.pk)
            new_obj.pk = None
            new_obj.id = None

            # Модифицируем уникальные поля в зависимости от модели
            if hasattr(new_obj , 'name') and new_obj.name :
                new_obj.name = f"{new_obj.name} (Копия)"
            if hasattr(new_obj , 'code') and new_obj.code :
                new_obj.code = f"{new_obj.code}_copy"
            if hasattr(new_obj , 'symbolic_code') and new_obj.symbolic_code :
                new_obj.symbolic_code = f"{new_obj.symbolic_code}_copy"

            # Сохраняем новую запись
            new_obj.save()

            # Копируем ManyToMany поля если они есть
            self._copy_m2m_fields(obj , new_obj)

        except Exception as e :
            modeladmin.message_user(
                request ,
                f"Ошибка при копировании {obj}: {str(e)}" ,
                level='error'
            )
            continue

    modeladmin.message_user(
        request ,
        f"Успешно скопировано {queryset.count()} записей." ,
        level='success'
    )


def _copy_m2m_fields(self , original_obj , new_obj) :
    """
    Копирует ManyToMany поля из оригинального объекта в новый
    """
    # Копируем поле 'dn' если оно есть (для AllowedDnTemplate)
    if hasattr(original_obj , 'dn') and hasattr(original_obj.dn , 'all') :
        new_obj.dn.set(original_obj.dn.all())

    # Копируем поле 'allowed_attributes' если оно есть (для ValveVariety)
    if hasattr(original_obj , 'allowed_attributes') and hasattr(original_obj.allowed_attributes , 'all') :
        new_obj.allowed_attributes.set(original_obj.allowed_attributes.all())

    # Добавьте другие ManyToMany поля по необходимости


@admin.register(ValveVariety)
class ValveVarietyAdmin(admin.ModelAdmin) :
    list_display = ['symbolic_code' , 'actuator_gearbox_combinations' , 'attributes_count']
    search_fields = ['symbolic_code' , 'actuator_gearbox_combinations']

    # inlines = [ValveVarietyAttributeInline]

    def attributes_count(self , obj) :
        return obj.allowed_attributes.count()

    attributes_count.short_description = _("Количество атрибутов")


@admin.register(ValveConnectionToPipe)
class ValveConnectionToPipeAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'sorting_order' , 'is_active']
    search_fields = ['name' , 'is_active']
    list_editable = ['code' , 'sorting_order' , 'is_active']
    actions = [duplicate_selected_action]


@admin.register(PortQty)
class PortQtyAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'sorting_order' , 'is_active']
    list_editable = ['code' , 'sorting_order' , 'is_active']
    actions = [duplicate_selected_action]


@admin.register(ConstructionVariety)
class ConstructionVarietyAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'valve_variety' , 'sorting_order' , 'is_active']
    list_editable = ['code' , 'sorting_order' , 'is_active']
    actions = [duplicate_selected_action]

@admin.register(AllowedDnTemplate)
class AllowedDnTemplateAdmin(admin.ModelAdmin):
    """Шаблон допустимых Dn в серии арматуры - для выбора в ValveLine"""
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']

    filter_horizontal = ['dn']  # Это создаст два списка: доступные и выбранные


