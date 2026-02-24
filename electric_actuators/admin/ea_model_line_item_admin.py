# electric_actuators/admin/ea_model_line_item_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction

import logging

from electric_actuators.models import ElectricWaySwitchesOption , ElectricEndSwitchesOption , \
    ElectricTorqueSwitchesOption
from electric_actuators.models.ea_model_line_item import (
    ElectricActuatorModelLineItem ,

)

logger = logging.getLogger(__name__)


# ============================= ДЕЙСТВИЯ АДМИНКИ =============================

def copy_model_line_items_action(modeladmin , request , queryset) :
    """Копировать выбранные модели электроприводов"""
    success_count = 0
    error_count = 0

    for original_item in queryset :
        try :
            with transaction.atomic() :
                # Используем метод create_copy модели
                copy_item = original_item.create_copy()
                success_count += 1
                logger.info(f"Скопирована модель: {original_item.name} -> {copy_item.name}")

        except Exception as e :
            error_count += 1
            logger.error(f"Ошибка копирования {original_item}: {e}" , exc_info=True)
            messages.error(
                request ,
                f"Ошибка при копировании '{original_item.name}': {str(e)[:100]}"
            )

    if success_count > 0 :
        messages.success(request , f"Успешно скопировано {success_count} моделей.")
    if error_count > 0 :
        messages.warning(request , f"Не удалось скопировать {error_count} моделей.")


copy_model_line_items_action.short_description = _("Копировать выбранные модели")


# ============================= INLINE ДЛЯ СЕРТИФИКАТОВ =============================
#
# class ElectricActuatorModelLineCertRelationInline(admin.TabularInline) :
#     """Inline для связи сертификатов с сериями электроприводов"""
#     model = ElectricActuatorModelLineCertRelation
#     extra = 0
#     verbose_name = _("Сертификат")
#     verbose_name_plural = _("Сертификаты")
#
#     # Автодополнение для ForeignKey
#     autocomplete_fields = ['cert_data']
#
#     fields = [
#         'cert_data' ,
#         'is_default' ,
#         'valid_from' ,
#         'valid_until' ,
#         'is_active'
#     ]
#
#     def get_queryset(self , request) :
#         """Оптимизированный запрос"""
#         return super().get_queryset(request).select_related('cert_data')
#

# ============================= ОСНОВНАЯ АДМИНКА =============================
class ElectricWaySwitchesOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricWaySwitchesOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['way_switches_option', 'encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Путевые выключатели")
    verbose_name_plural = _("Опции путевых выключателей")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset

class ElectricEndSwitchesOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricEndSwitchesOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['end_switches_option', 'encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Конечные выключатели")
    verbose_name_plural = _("Опции конечных выключателей")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset
class ElectricTorqueSwitchesOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricTorqueSwitchesOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['torque_switches_option', 'encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Моментные выключатели")
    verbose_name_plural = _("Опции моментных выключателей")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset

@admin.register(ElectricActuatorModelLineItem)
class ElectricActuatorModelLineItemAdmin(admin.ModelAdmin) :
    """Админка для моделей в серии электроприводов"""

    # ========== НАСТРОЙКИ ОТОБРАЖЕНИЯ СПИСКА ==========
    list_display = [
        'name' ,
        'code' ,
        'model_line_display' ,
        'body_display' ,
        'sorting_order' ,
    ]

    list_editable = ['sorting_order']
    list_display_links = ['name']

    list_filter = [
        'is_active' ,
        ('model_line' , admin.RelatedOnlyFieldListFilter) ,
        ('body' , admin.RelatedOnlyFieldListFilter) ,
    ]

    search_fields = [
        'name' ,
        'code' ,
        'model_line__name' ,
        'model_line__code' ,
        'body__name'
    ]

    list_per_page = 50
    list_select_related = [ 'model_line' , 'body']

    # ========== ПОЛЯ В ФОРМЕ РЕДАКТИРОВАНИЯ ==========

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (('name' ,'code' ,) ,('model_line' , 'body') ,
             ('sorting_order' , 'is_active') ),
            'classes' : ('wide' ,)
        }) ,

        (_('Механические параметры') , {
            'fields' : (
                ('torque_min' , 'torque_max') ,
                ('time_to_open' , 'rotation_speed') ,
            )
        }) ,
    )

    inlines = [ElectricEndSwitchesOptionInline,ElectricWaySwitchesOptionInline,ElectricTorqueSwitchesOptionInline]
    # ========== АВТОДОПОЛНЕНИЕ И ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР ==========
    autocomplete_fields = ['model_line' , 'body']

    # ========== ДЕЙСТВИЯ ==========
    actions = [
        copy_model_line_items_action

    ]


    # ========== МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ В СПИСКЕ ==========


    def model_line_display(self , obj) :
        """Отображение серии с брендом"""
        if obj.model_line :
            brand = obj.model_line.brand.name if obj.model_line.brand else ''
            return f"{obj.model_line.name} ({brand})"
        return "-"

    model_line_display.short_description = _("Серия")
    model_line_display.admin_order_field = 'model_line__name'

    def brand_display(self , obj) :
        """Отображение бренда"""
        return obj.brand.name if obj.brand else "-"

    brand_display.short_description = _("Бренд")
    brand_display.admin_order_field = 'model_line__brand__name'

    def body_display(self , obj) :
        """Отображение корпуса"""
        return obj.body.name if obj.body else "-"

    body_display.short_description = _("Корпус")
    body_display.admin_order_field = 'body__name'

    def is_active_badge(self , obj) :
        """Красивое отображение активного статуса"""
        if obj.is_active :
            return '<span style="color: green; font-weight: bold;">✓ Активно</span>'
        return '<span style="color: red;">✗ Неактивно</span>'

    is_active_badge.short_description = _("Статус")
    is_active_badge.allow_tags = True

    def created_info(self , obj) :
        """Информация о создании (если есть поля created_at/modified_at)"""
        # Если в модели есть эти поля, можно добавить:
        # if hasattr(obj, 'created_at'):
        #     return f"Создано: {obj.created_at.strftime('%d.%m.%Y')}"
        return ""

    created_info.short_description = _("Информация")

    # ========== МЕТОДЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ ==========

    def get_queryset(self , request) :
        """Оптимизированный запрос с предзагрузкой связанных данных"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'model_line' ,
            'model_line__brand' ,
            'body'
        ).only(
            'id' ,
            'name' ,
            'code' ,
            'sorting_order' ,
            'is_active' ,
            'model_line__name' ,
            'model_line__brand__name' ,
            'body__name'
        )

    def get_search_results(self , request , queryset , search_term) :
        """Оптимизированный поиск с предзагрузкой"""
        queryset , use_distinct = super().get_search_results(
            request , queryset , search_term
        )
        # Дополнительная оптимизация для поиска
        return queryset , use_distinct

    # ========== МЕТОДЫ СОХРАНЕНИЯ ==========

    def save_model(self , request , obj , form , change) :
        """Кастомное сохранение модели"""
        # Можно добавить логирование изменений
        if change :
            logger.info(f"Обновлена модель электропривода: {obj.name} (ID: {obj.id})")
        else :
            logger.info(f"Создана новая модель электропривода: {obj.name}")

        super().save_model(request , obj , form , change)

    def delete_model(self , request , obj) :
        """Кастомное удаление модели"""
        logger.warning(f"Удалена модель электропривода: {obj.name} (ID: {obj.id})")
        super().delete_model(request , obj)

    def delete_queryset(self , request , queryset) :
        """Кастомное удаление нескольких моделей"""
        model_names = [obj.name for obj in queryset]
        logger.warning(f"Удалены модели электроприводов: {', '.join(model_names)}")
        super().delete_queryset(request , queryset)

    # ========== КАСТОМНЫЕ ВЬЮХИ И ФОРМЫ ==========

    def change_view(self , request , object_id , form_url='' , extra_context=None) :
        """Кастомный вид редактирования"""
        extra_context = extra_context or {}
        extra_context['title'] = _("Редактирование модели электропривода")

        # Можно добавить дополнительную информацию в контекст
        try :
            obj = self.get_object(request , object_id)
            if obj :
                extra_context['model_info'] = {
                    'brand' : obj.brand ,
                    'series' : obj.model_line ,
                    'calculated_fields' : {
                        'ip' : obj.ip_display ,
                        'exd' : obj.exd_display ,
                        'coating' : obj.body_coating_display ,
                        'temperature' : obj.temperature_range_display ,
                    }
                }
        except Exception as e :
            logger.error(f"Ошибка получения объекта для админки: {e}")

        return super().change_view(
            request , object_id , form_url , extra_context=extra_context
        )


    # ========== РАСШИРЕННАЯ ФИЛЬТРАЦИЯ ==========

    def get_list_filter(self , request) :
        """Динамические фильтры в зависимости от пользователя"""
        filters = super().get_list_filter(request)

        # Добавляем дополнительные фильтры для суперпользователей
        if request.user.is_superuser :
            filters = list(filters) if filters else []
            # Можно добавить дополнительные фильтры
            # filters.append('created_at')

        return filters
#
#
# # Регистрация модели сертификатов (если нужна отдельная админка)
# @admin.register(ElectricActuatorModelLineCertRelation)
# class ElectricActuatorModelLineCertRelationAdmin(admin.ModelAdmin) :
#     """Админка для связи сертификатов с сериями электроприводов"""
#
#     list_display = [
#         'model_line' ,
#         'cert_data' ,
#         'is_default' ,
#         'is_active' ,
#         'valid_from' ,
#         'valid_until'
#     ]
#
#     list_filter = [
#         'is_default' ,
#         'is_active' ,
#         'model_line' ,
#         'cert_data__cert_type'
#     ]
#
#     search_fields = [
#         'model_line__name' ,
#         'cert_data__name' ,
#         'cert_data__number'
#     ]
#
#     autocomplete_fields = ['model_line' , 'cert_data']
#     list_select_related = ['model_line' , 'cert_data']
#     list_per_page = 30