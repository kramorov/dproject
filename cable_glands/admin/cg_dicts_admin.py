# cable_glands/admin/cg_dicts_admin.py
from django.contrib import admin
from django.contrib import messages

from cable_glands.models import CableGlandBodyMaterial, CableGlandItemType, CableType


# import logging
#
# # Получаем логгер
# logger = logging.getLogger(__name__)

@admin.register(CableGlandItemType)
class CableGlandItemTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']

@admin.register(CableType)
class CableTypeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'code',
        'for_armored_cable', 'for_metal_sleeve_cable', 'for_pipelines_cable',
        'sorting_order', 'is_active',
    ]
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['for_armored_cable', 'for_metal_sleeve_cable', 'for_pipelines_cable', 'is_active']
    search_fields = ['name', 'code']

@admin.register(CableGlandBodyMaterial)
class CableGlandBodyMaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'text_description']
    search_fields = ['name']
