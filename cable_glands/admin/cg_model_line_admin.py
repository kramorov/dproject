# cable_glands/admin/cg_model_line_admin.py
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render
from django.urls import path  # Импортируем path

# from producers.models import Producer
import logging

from cable_glands.models import CableGlandModelLine

# Получаем логгер
logger = logging.getLogger(__name__)


class CableGlandModelLineAdminForm(forms.ModelForm):
    class Meta:
        model = CableGlandModelLine
        fields = '__all__'
        # widgets = {
        #     'ip': forms.SelectMultiple(),
        #     'exd': forms.SelectMultiple(),
        # }
        widgets = {
            'for_armored_cable' : forms.CheckboxInput() ,
            'for_metal_sleeve_cable' : forms.CheckboxInput() ,
            'for_pipelines_cable' : forms.CheckboxInput() ,
            'thread_external' : forms.CheckboxInput() ,
            'thread_internal' : forms.CheckboxInput() ,
        }
    def save(self, commit=True):
        # Сохраняем объект без ManyToMany полей
        instance = super().save(commit=False)

        if commit:
            # Сохраняем объект, чтобы получить ID
            instance.save()

            # Теперь можем сохранить связи ManyToMany
            self.save_m2m()

        return instance

@admin.register(CableGlandModelLine)
class CableGlandModelLineAdmin(admin.ModelAdmin):
    form = CableGlandModelLineAdminForm
    list_display = ['id', 'name','code','brand', 'cable_gland_type',
                    'for_armored_cable', 'for_metal_sleeve_cable', 'for_pipelines_cable', 'thread_external',
                    'thread_internal', 'temp_min', 'temp_max','sorting_order', 'is_active']
    # list_editable = ('name','code','sorting_order', 'is_active')
    list_filter = ('name', 'brand', 'cable_gland_type')
    # search_fields = ['name', 'cable_gland_type', 'ip', 'exd', 'for_armored_cable',
    #                  'for_metal_sleeve_cable']
    fieldsets = (
        ('Общая информация', {
            'fields': (('name', 'code', 'cable_gland_type', 'brand'),
                        ('for_armored_cable', 'for_metal_sleeve_cable', 'for_pipelines_cable',),
                        ('thread_external', 'thread_internal'),
                        ('temp_min', 'temp_max'))
        }),
        ('ГОСТ, Описание', {
            'fields': ('gost', 'description')

        }),
        ('ip', {'fields':('ip', 'exd')}),
    )
    filter_horizontal = ('ip','exd',)  # Это добавит горизонтальные чекбоксы для поля "ip"
    # ordering = ['name', 'voltage', ]


    def show_full_description_popup(self, request, pk):
        logger.debug('Это отладочное сообщение show_full_description_popup (CableGlandModelLineAdmin)')
        obj = self.get_object(request, pk)
        full_description = obj.get_full_description()

        context = {
            'full_description': full_description,
            'object': obj,
            'subtitle': 'Some subtitle value',  # Здесь добавляем subtitle
        }

        return render(request, 'admin/full_description_popup.html', context)

    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path('show_description/<int:pk>/', self.show_full_description_popup),
    #     ]
    #     print("Свои URLs для CableGlandModelLineAdmin : ", custom_urls)  # Print custom URLs to verify
    #     return custom_urls + urls

    def get_urls(self) :
        # Get the default admin URLs
        urls = super().get_urls()

        # Define custom URLs for your admin
        custom_urls = [
            path(
                'show_description/<int:pk>/' ,  # URL pattern
                self.show_full_description_popup ,  # View that handles the URL
                name='show_full_description_popup' ,  # Optional name for the URL
            ) ,
        ]

        # Combine custom URLs with the default admin URLs
        return custom_urls + urls