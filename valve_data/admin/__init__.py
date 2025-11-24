"""
Собираем все регистрации моделей в одном месте
"""
from django.contrib import admin

# Импортируем все админки чтобы гарантировать регистрацию
from .admin_basic import *
from .admin_valve_line import *
from .admin_valve_model_data_table import *
from .admin_valve_model_kv_data_table import *
from .admin_drawing import *
from .admin_dimension import *

# Альтернативно можно зарегистрировать здесь все модели
# from valve_data.models import *
# admin.site.register(ValveLine)
# admin.site.register(ValveVariety)
# и т.д.