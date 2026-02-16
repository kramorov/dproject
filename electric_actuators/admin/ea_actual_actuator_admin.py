# #electric_actuators/admin/ea_actual_actuator_admin.py
#
# from django.contrib import admin
#
#
# class ActualActuatorAdmin(admin.ModelAdmin):
#     # Показать только нужные поля в списке
#     # change_form_template = 'admin/electric_actuators/actualactuator/change_form.html'
#     list_display = ('name', 'actual_model', 'date_created', 'date_updated', 'actual_time_to_open',
#                     'actual_rotations_to_open',
#                     'actual_stem_shape', 'actual_stem_size', 'actual_cable_glands_holes')
#
#     # Фильтрация по полям
#     list_filter = ('actual_model', 'status', 'actual_ip', 'actual_exd', 'actual_temperature')
#
#     # Поиск по полям
#     search_fields = ('name', 'actual_model__name', 'status')
