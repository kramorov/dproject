#electric_actuators/admin/ea_cg_holes_set_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from electric_actuators.models import CableGlandHolesSet

import logging
logger = logging.getLogger(__name__)

@admin.register(CableGlandHolesSet)
class CableGlandHolesSetAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'cg1', 'cg2','cg3','cg4',)

    fields = ('name', 'cg1', 'cg2','cg3','cg4','text_description')
    # Поля для редактирования в админке
    # fieldsets = (
    #     ('Основные параметры', {
    #         'fields': (('name', 'code' ),('sorting_order', 'is_active'),)
    #     }),
    #     ('Р', {
    #         'fields': ('description',  )
    #     }),
    # )
