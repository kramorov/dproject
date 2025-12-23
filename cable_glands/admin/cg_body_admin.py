# cable_glands/admin/cg_body_admin.py

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render
from django.urls import path  # Импортируем path

# from producers.models import Producer
import logging

from cable_glands.models import CableGlandModelLine, CableGlandBody, CableGlandThreadOption

# Получаем логгер
logger = logging.getLogger(__name__)

class CableGlandThreadOptionInline(admin.TabularInline) :
    """Inline для IP опций"""
    model = CableGlandThreadOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['thread_size' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Опции резьбы")
    verbose_name_plural = _("Опции резьбы")


@admin.register(CableGlandBody)
class CableGlandBodyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code','model_line', 'sorting_order', 'is_active']
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('name', 'model_line')
    # search_fields = ['name', 'code']
    ordering = ('sorting_order', 'name')

    inlines = [
        CableGlandThreadOptionInline,
    ]

    fieldsets = (
        ('Общая информация', {
            'fields': (('name', 'code', 'model_line'),),
        }),
        ('Диаметр кабеля', {
            'fields': (('cable_diameter_inner_min', 'cable_diameter_inner_max'),)

        }),
        ('Металлорукав', {'fields': ('metal_sleeve',)}),
        ('Диаметр металлорукава', {
            'fields': (('metal_sleeve_inner', 'metal_sleeve_outer'),)

        }),
        ('Размеры', {
            'fields': (('total_lenght', 'thread_lenght', 'weight'),)

        }),
    )

    filter_horizontal = ('metal_sleeve',)  # Это добавит горизонтальные чекбоксы для поля "metal_sleeve"
    def get_queryset(self , request) :
        """Оптимизация запросов с учетом through-моделей"""
        return super().get_queryset(request).select_related(
            'model_line' ,
        ).prefetch_related(
            'cg_thread_body' ,
        )
    # filter_horizontal = ('ip','exd',)  # Это добавит горизонтальные чекбоксы для поля "ip"

    # ordering = ['name', 'voltage', ]

    #
    # def show_full_description_popup(self, request, pk):
    #     logger.debug('Это отладочное сообщение show_full_description_popup (CableGlandModelLineAdmin)')
    #     obj = self.get_object(request, pk)
    #     full_description = obj.get_full_description()
    #
    #     context = {
    #         'full_description': full_description,
    #         'object': obj,
    #         'subtitle': 'Some subtitle value',  # Здесь добавляем subtitle
    #     }
    #
    #     return render(request, 'admin/full_description_popup.html', context)

    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path('show_description/<int:pk>/', self.show_full_description_popup),
    #     ]
    #     print("Свои URLs для CableGlandModelLineAdmin : ", custom_urls)  # Print custom URLs to verify
    #     return custom_urls + urls

    # def get_urls(self) :
    #     # Get the default admin URLs
    #     urls = super().get_urls()
    #
    #     # Define custom URLs for your admin
    #     custom_urls = [
    #         path(
    #             'show_description/<int:pk>/' ,  # URL pattern
    #             self.show_full_description_popup ,  # View that handles the URL
    #             name='show_full_description_popup' ,  # Optional name for the URL
    #         ) ,
    #     ]
    #
    #     # Combine custom URLs with the default admin URLs
    #     return custom_urls + urls