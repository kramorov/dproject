from django.contrib import admin
# from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

from .models import ClientRequests , ClientRequestsType , ClientRequestItem , ElectricActuatorRequirement , \
     ClientRequestsStatus
from clients.models import CompanyPerson

class ClientRequestsTypeAdmin(admin.ModelAdmin):
    list_display = ('symbolic_code', 'need_valve_selection', 'need_electric_actuator_selection', 'need_pneumatic_actuator_selection')

# Inline для ElectricActuatorRequirement
class ElectricActuatorRequirementInline(admin.StackedInline):
    model = ElectricActuatorRequirement
    extra = 1
    # fields = ('client_request_line_item_parent', )
    fieldsets = (
        ('Основное', {
            'fields': (
                ('rotations_angle', 'safety_position', 'output_type','mechanical_indicator','operating_mode'),)
        }),
        ('Исполнение', {
            'fields': (('ip', 'exd', 'temperature','body_coating','hand_wheel'),)
        }),
        ('Датчики', {
            'fields': ((      'end_switches', 'way_switches', 'torque_switches'),)
        }),
        ('Блоки управления', {
            'fields': (
                ('digital_protocol_support','control_unit_type', 'control_unit_installed', 'control_unit_location'),)
        }),
        ('Время открытия и поворота', {
            'fields': (
                ('time_to_open', 'time_to_open_measure_unit' ),('rotations_to_open', 'rotations_to_open_measure_unit'))
        }),
        ('Прочее', {
            'fields': (
                'cable_glands_holes', 'blinker')
        }),
    )
    show_change_link = True

# # Inline для ValveRequirement
# class ValveRequirementInline(NestedStackedInline):
#     model = ValveRequirement
#     extra = 1
#
#     fieldsets = (
#         ('Тип, название и серия арматуры' , {
#             'fields' : (
#                 ('valve_type' , 'valve_model_model_line' , 'valve_model_model_line_str') ,)
#         }) ,
#         ('Dn, Pn арматуры', {
#             'fields': (
#                 'valve_model_dn', ('valve_model_pn', 'valve_model_pn_measure_unit'), ('valve_model_pn_delta', 'valve_model_pn_delta_measure_unit'),)
#         }),
#         ('Усилие, обороты', {
#             'fields': (
#                 ('valve_model_torque_to_open', 'valve_model_torque_to_close', 'valve_model_rotations_to_open'),)
#         }),
#         ('Монтажная площадка и шток', {
#             'fields': (
#                 'valve_model_mounting_plate', ('valve_model_stem_size','valve_stem_retract_type'))
#         }),
#     )
#     show_change_link = True

# # Inline для ClientRequestItem
# class ClientRequestItemInline(NestedTabularInline):
#     model = ClientRequestItem
#     extra = 1
#     fields = ('item_no', 'request_line_number', 'request_line_ol')
#     show_change_link = True
#     inlines = [ElectricActuatorRequirementInline, ValveRequirementInline]  # Вкладываем другие Inline

# Админка для ClientRequest
# @admin.register(ClientRequest)
class ClientRequestsAdmin(admin.ModelAdmin):
    list_display = ( 'symbolic_code', 'request_from_client_company', 'request_responsible_person', 'request_date','request_type' )
    list_filter = ('request_type', 'request_from_client_company')
    search_fields = ('symbolic_code', 'request_from_client_company__name')

    # Добавляем Inline для связанных моделей
    # inlines = [ClientRequestItemInline]

    # Поля, которые будут отображаться в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': (('request_date', 'request_status', 'symbolic_code', 'request_type'), ('request_from_client_company',
                       'request_responsible_person'), 'request_text'),
        }),
    )

# Регистрация модели в админке
admin.site.register(ClientRequests, ClientRequestsAdmin)
admin.site.register(ClientRequestsType, ClientRequestsTypeAdmin)
admin.site.register(ClientRequestsStatus)


