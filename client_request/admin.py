from django.contrib import admin
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from .models import ClientRequest , ClientRequestType , ClientRequestItem , ElectricActuatorRequirement , \
    ValveRequirement
from clients.models import CompanyPerson

class ClientRequestTypeAdmin(admin.ModelAdmin):
    list_display = ('symbolic_code', 'need_valve_selection', 'need_electric_actuator_selection', 'need_pneumatic_actuator_selection')


# class ClientRequestAdmin(admin.ModelAdmin):
#     list_display = ('request_date','symbolic_code', 'request_from_client_company', 'request_responsible_person', 'request_type')
#     list_filter = ('request_type' , 'request_from_client_company')
#     search_fields = ('request_date', 'symbolic_code', 'request_from_client_company__symbolic_code', 'request_responsible_person__symbolic_code')
#
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         # Ограничиваем выбор request_responsible_person только сотрудниками выбранной компании
#         if db_field.name == "request_responsible_person":
#             # Получаем выбранную компанию из запроса
#             company_id = request.GET.get('request_from_client_company')
#             if company_id:
#                 kwargs["queryset"] = CompanyPerson.objects.filter(company_id=company_id)
#             else:
#                 kwargs["queryset"] = CompanyPerson.objects.none()
#         return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Inline для ElectricActuatorRequirement
class ElectricActuatorRequirementInline(NestedStackedInline):
    model = ElectricActuatorRequirement
    extra = 1
    fields = ('client_request_line_item_parent', )
    show_change_link = True

# Inline для ValveRequirement
class ValveRequirementInline(NestedStackedInline):
    model = ValveRequirement
    extra = 1

    fieldsets = (
        ('Тип, название и серия арматуры' , {
            'fields' : (
                ('valve_type' , 'valve_model_model_line' , 'valve_model_model_line_str') ,)
        }) ,
        ('Dn, Pn арматуры', {
            'fields': (
                'valve_model_dn', ('valve_model_pn', 'valve_model_pn_measure_unit'), ('valve_model_pn_delta', 'valve_model_pn_delta_measure_unit'),)
        }),
        ('Усилие, обороты', {
            'fields': (
                ('valve_model_torque_to_open', 'valve_model_torque_to_close', 'valve_model_rotations_to_open'),)
        }),
        ('Монтажная площадка и шток', {
            'fields': (
                'valve_model_mounting_plate', ('valve_model_stem_size','valve_stem_retract_type'))
        }),
    )
    show_change_link = True

# Inline для ClientRequestItem
class ClientRequestItemInline(NestedTabularInline):
    model = ClientRequestItem
    extra = 1
    fields = ('item_no', 'request_line_number', 'request_line_ol')
    show_change_link = True
    inlines = [ElectricActuatorRequirementInline, ValveRequirementInline]  # Вкладываем другие Inline

# Админка для ClientRequest
# @admin.register(ClientRequest)
class ClientRequestAdmin(NestedModelAdmin):
    list_display = ('symbolic_code', 'request_type', 'request_from_client_company', 'request_responsible_person', 'request_date')
    list_filter = ('request_type', 'request_from_client_company')
    search_fields = ('symbolic_code', 'request_from_client_company__name')

    # Добавляем Inline для связанных моделей
    inlines = [ClientRequestItemInline]

    # Поля, которые будут отображаться в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('symbolic_code', 'request_type', 'request_from_client_company', 'request_responsible_person', 'request_date'),
        }),
    )

# Регистрация модели в админке
admin.site.register(ClientRequest, ClientRequestAdmin)
admin.site.register(ClientRequestType, ClientRequestTypeAdmin)


