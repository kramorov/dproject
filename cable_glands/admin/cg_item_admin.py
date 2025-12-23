# cable_glands/admin/cg_dicts_admin.py
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path  # Импортируем path

from cable_glands.models import CableGlandBodyMaterial, CableGlandItemType, CableGlandItem

import logging

# Получаем логгер
logger = logging.getLogger(__name__)

class CableGlandItemForm(forms.ModelForm):
    class Meta:
        model = CableGlandItem
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        model_line = cleaned_data.get('model_line')

        if model_line:
            # Если поле model_line выбрано, обновляем temp_min и temp_max из связанной модели
            cleaned_data['temp_min'] = model_line.temp_min
            cleaned_data['temp_max'] = model_line.temp_max

        return cleaned_data


def copy_cable_gland_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


@admin.register(CableGlandItem)
class CableGlandItemAdmin(admin.ModelAdmin):
    form = CableGlandItemForm  # Используем кастомную форму для обновления данных
    list_display = ('id',
        'name', 'model_line', 'cable_gland_body_material', 'temp_min', 'temp_max', 'cable_diameter_inner_min', 'cable_diameter_inner_max',
        'dn_metal_sleeve')
    list_filter = ('model_line', 'model_line__cable_gland_type')
    # filter_horizontal = ['parent',]  # Это добавит горизонтальные чекбоксы для поля "parent"
    filter_horizontal = ('exd',)  # Это добавит горизонтальные чекбоксы для поля "ip"
    search_fields = ('name', 'model_line__symbolic_code')
    actions = [copy_cable_gland_data]  # Добавляем действие для копирования



    def show_full_description_popup(self, request, pk):
        logger.debug('Это отладочное сообщение show_full_description_popup (CableGlandItemAdmin)')
        obj = self.get_object(request, pk)
        full_description = obj.get_full_description()

        context = {
            'full_description': full_description,
            'object': obj,
            'subtitle': 'Some subtitle value',  # Здесь добавляем subtitle
        }

        return render(request, 'admin/full_description_popup.html', context)

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

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #
    #     # Проверка на for_metal_sleeve_cable, если False, скрываем поле dn_metal_sleeve
    #     if obj and obj.for_metal_sleeve_cable is False:
    #         form.base_fields['dn_metal_sleeve'].widget = forms.HiddenInput()
    #
    #     # Проверка на for_armored_cable, если False, скрываем поля с диаметром кабеля
    #     if obj and obj.for_armored_cable is False:
    #         form.base_fields['cable_diameter_inner_min'].widget = forms.HiddenInput()
    #         form.base_fields['cable_diameter_inner_max'].widget = forms.HiddenInput()
    #
    #     return form

    # def copy_object(self, request, obj):
    #     """Метод для копирования объекта CableGlandItem"""
    #     # Создаём новый объект как копию существующего
    #     new_obj = obj
    #     new_obj.pk = None  # обнуляем первичный ключ для создания нового объекта
    #     new_obj.name = f"Copy of {obj.name}"  # Можно изменить имя, если нужно
    #     new_obj.save()
    #     return new_obj

    # def get_actions(self, request):
    #     actions = super().get_actions(request)
    #
    #     # Добавляем действие для копирования элемента
    #     def copy_selected_items(modeladmin, request, queryset):
    #         for obj in queryset:
    #             self.copy_object(request, obj)
    #
    #     copy_selected_items.short_description = _("Copy selected items")
    #     actions['copy_selected_items'] = copy_selected_items
    #     return actions



