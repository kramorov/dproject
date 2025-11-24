from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from pneumatic_actuators.models.pa_params import (
    PneumaticActuatorSpringsQty ,
    PneumaticActuatorVariety ,
    PneumaticActuatorConstructionVariety
)

@admin.register(PneumaticActuatorSpringsQty)
class PneumaticActuatorSpringsQtyAdmin(admin.ModelAdmin) :
    """Админка для количества пружин в пневмоприводе SR"""

    list_display = ('name' , 'code' , 'sorting_order' , 'is_active')
    list_editable = ('sorting_order' , 'is_active')
    list_filter = ('is_active' ,)
    search_fields = ('name' , 'code' , 'description')
    ordering = ('sorting_order' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )


@admin.register(PneumaticActuatorVariety)
class PneumaticActuatorVarietyAdmin(admin.ModelAdmin) :
    """Админка для разновидностей пневмоприводов (DA/SR)"""

    list_display = ('name' , 'code' , 'sorting_order' , 'is_active')
    list_editable = ('sorting_order' , 'is_active')
    list_filter = ('is_active' ,)
    search_fields = ('name' , 'code' , 'description')
    ordering = ('sorting_order' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )


@admin.register(PneumaticActuatorConstructionVariety)
class PneumaticActuatorConstructionVarietyAdmin(admin.ModelAdmin) :
    """Админка для разновидностей конструкций пневмоприводов (RP/SY)"""

    list_display = ('name' , 'code' , 'sorting_order' , 'is_active')
    list_editable = ('sorting_order' , 'is_active')
    list_filter = ('is_active' ,)
    search_fields = ('name' , 'code' , 'description')
    ordering = ('sorting_order' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )