# cable_glands/admin/cg_dicts_admin.py
from django.contrib import admin
from django.contrib import messages

from cable_glands.models import CableGlandBodyMaterial, CableGlandItemType


# import logging
#
# # Получаем логгер
# logger = logging.getLogger(__name__)

@admin.register(CableGlandItemType)
class CableGlandItemTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']

@admin.register(CableGlandBodyMaterial)
class CableGlandBodyMaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'text_description']
    search_fields = ['name']