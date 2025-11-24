from django.contrib import admin

from valve_data.admin.admin_drawing import DimensionTableDrawingAdmin
from valve_data.admin.admin_valve_line import ValveLineAdmin
from valve_data.models import ValveLine , ValveModelKvDataTable , ValveModelDataTable
from valve_data.admin.admin_valve_model_kv_data_table import ValveModelKvDataTableAdmin
from valve_data.admin.admin_valve_model_data_table import ValveModelDataTableAdmin
from valve_data.admin.admin_valve_line import ValveLineAdmin

from .models import DimensionTableDrawingItem

# Регистрируем модели
# admin.site.register(DimensionTableDrawing, DimensionTableDrawingAdmin)
# admin.site.register(ValveModelKvDataTable, ValveModelKvDataTableAdmin)
# admin.site.register(ValveModelDataTable, ValveModelDataTableAdmin)
# admin.site.register(ValveLine, ValveLineAdmin)