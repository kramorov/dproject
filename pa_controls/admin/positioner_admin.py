# pa_controls/admin/positioner_admin.py
"""Админка позиционеров: справочники, серии с through-опциями, модели."""
import copy
import logging

from django.contrib import admin
from django.contrib import messages
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from pa_controls.models import (
    ActingType,
    LeverOption,
    SmartCapabilityOption,
    SmartCapabilitySet,
    PosiModelLine,
    PosiModelLineItem,
    PosiBodyConnections,
)
from pa_controls.models.posi_model_line import (
    PosiActingTypeOption,
    PosiBodyConnectionOption,
    PosiLeverOption,
    PosiTemperatureOption,
    PosiSignalProfileOption,
    PosiAlarmOption,
)


logger = logging.getLogger(__name__)

# Related names through-опций уровня серии — копируются вместе с серией
POSI_MODEL_LINE_OPTION_RELATED_NAMES = [
    'acting_type_options',
    'body_connection_options',
    'lever_options',
    'temperature_options',
    'signal_profile_options',
    'alarm_options',
]


def copy_posi_model_line(modeladmin, request, queryset):
    """Копировать выбранные серии позиционеров со всеми опциями и их кодировками.

    Глубокая копия: основные поля, M2M (exd, техдоки, сертификаты, галерея),
    все through-опции уровня серии (acting_type, body_connection, lever,
    temperature, signal_profile, alarm) с сохранением encoding.
    """
    if not request.user.has_perm('pa_controls.add_posimodelline'):
        messages.error(request, _('У вас нет прав на добавление новых записей.'))
        return

    success_count = 0
    error_count = 0

    for original_obj in queryset:
        try:
            with transaction.atomic():
                new_obj = original_obj.__class__()

                # Основные поля, кроме id (JSON — глубокой копией)
                for field in original_obj._meta.fields:
                    if field.name in ('id', 'pk'):
                        continue
                    value = getattr(original_obj, field.name)
                    if isinstance(field, models.JSONField) and value is not None:
                        value = copy.deepcopy(value)
                    setattr(new_obj, field.name, value)

                if new_obj.name:
                    new_obj.name = f"{new_obj.name} (Копия)"
                if new_obj.code:
                    new_obj.code = f"{new_obj.code} (Копия)"

                new_obj.save()

                # M2M-поля (exd, техдоки, сертификаты, изображения галереи)
                for m2m_field in original_obj._meta.many_to_many:
                    getattr(new_obj, m2m_field.name).set(
                        getattr(original_obj, m2m_field.name).all()
                    )

                # Through-опции уровня серии с кодировками
                for related_name in POSI_MODEL_LINE_OPTION_RELATED_NAMES:
                    _copy_posi_options(original_obj, new_obj, related_name)

                success_count += 1
                messages.success(
                    request, f"Скопировано: {original_obj.name} -> {new_obj.name}"
                )
                logger.info(
                    f"Скопирована серия позиционеров: {original_obj.name} -> {new_obj.name}"
                )
        except Exception as e:
            error_count += 1
            logger.error(f"Ошибка копирования {original_obj}: {e}", exc_info=True)
            messages.error(
                request, f"Ошибка при копировании {original_obj}: {str(e)[:100]}"
            )

    if success_count > 0:
        messages.success(request, f"Успешно скопировано серий: {success_count}.")
    if error_count > 0:
        messages.warning(request, f"Не удалось скопировать серий: {error_count}.")


copy_posi_model_line.short_description = _("Копировать серии со всеми опциями")


def _copy_posi_options(original_obj, new_obj, related_name):
    """Копирует through-опции одного related_name на новую серию, сохраняя кодировки."""
    for original_option in getattr(original_obj, related_name).all():
        new_option = original_option.__class__()

        for field in original_option._meta.fields:
            field_name = field.name
            if field_name in ('id', 'pk'):
                continue
            value = getattr(original_option, field_name)
            if isinstance(field, models.JSONField) and value is not None:
                value = copy.deepcopy(value)
            if (isinstance(field, models.ForeignKey)
                    and field.related_model is original_obj.__class__):
                # Поле связи с родительской серией — на новую серию
                setattr(new_option, field_name, new_obj)
            else:
                setattr(new_option, field_name, value)

        new_option.save()

        # M2M-поля опции, если появятся
        for m2m_field in original_option._meta.many_to_many:
            getattr(new_option, m2m_field.name).set(
                getattr(original_option, m2m_field.name).all()
            )


# ── Справочники ──

@admin.register(ActingType)
class ActingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    ordering = ['sorting_order', 'code']


@admin.register(LeverOption)
class LeverOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'acting_type', 'stroke_min_mm', 'stroke_max_mm',
                    'sorting_order', 'is_active']
    list_filter = ['acting_type', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'stroke_min_mm', 'stroke_max_mm', 'sorting_order', 'is_active']
    autocomplete_fields = ['acting_type']
    ordering = ['acting_type', 'stroke_min_mm', 'sorting_order', 'code']


@admin.register(SmartCapabilityOption)
class SmartCapabilityOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    ordering = ['sorting_order', 'code']


@admin.register(SmartCapabilitySet)
class SmartCapabilitySetAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    filter_horizontal = ['capabilities']
    ordering = ['sorting_order', 'code']


@admin.register(PosiBodyConnections)
class PosiBodyConnectionsAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'thread_in', 'thread_out', 'cable_gland_hole',
                    'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    ordering = ['sorting_order', 'code']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description'),
        }),
        (_('Присоединения'), {
            'fields': ('thread_in', 'thread_out', 'cable_gland_hole'),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active'),
        }),
    )


# ── Inline-опции серии ──

class PosiActingTypeOptionInline(admin.TabularInline):
    model = PosiActingTypeOption
    extra = 0
    fields = ['acting_type', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiBodyConnectionOptionInline(admin.TabularInline):
    model = PosiBodyConnectionOption
    extra = 0
    fields = ['body_connection', 'encoding', 'is_default', 'only_non_ex', 'sorting_order', 'is_active']


class PosiLeverOptionInline(admin.TabularInline):
    model = PosiLeverOption
    extra = 0
    fields = ['lever', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiTemperatureOptionInline(admin.TabularInline):
    model = PosiTemperatureOption
    extra = 0
    fields = ['work_temp_min', 'work_temp_max', 'encoding', 'is_default', 'only_non_ex',
              'sorting_order', 'is_active']


class PosiSignalProfileOptionInline(admin.TabularInline):
    model = PosiSignalProfileOption
    extra = 0
    fields = ['signal_profile', 'encoding', 'is_default', 'only_non_ex', 'sorting_order', 'is_active']


class PosiAlarmOptionInline(admin.TabularInline):
    model = PosiAlarmOption
    extra = 0
    fields = ['alarm', 'encoding', 'is_default', 'sorting_order', 'is_active']


# ── Серия ──

@admin.register(PosiModelLine)
class PosiModelLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'brand', 'actuator_action', 'body_material', 'is_active']
    list_filter = ['code','brand',  'body_material', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'actuator_action', 'is_active']
    autocomplete_fields = ['smart_capability_set']
    # raw_id_fields = ['brand', 'producer', 'body_material']
    filter_horizontal = ['exd']
    ordering = ['sorting_order', 'code']
    actions = [copy_posi_model_line, 'delete_selected']
    inlines = [
        PosiActingTypeOptionInline,
        PosiBodyConnectionOptionInline,
        PosiLeverOptionInline,
        PosiTemperatureOptionInline,
        PosiSignalProfileOptionInline,
        PosiAlarmOptionInline,
    ]
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'equipment_type', ('brand', 'producer'), 'description'),
        }),
        (_('Характеристики'), {
            'fields': ('body_material', 'weight',
                       ('supply_pressure_min', 'supply_pressure_max'),
                       'actuator_action'),
        }),
        (_('Взрывозащита и смарт-возможности'), {
            'fields': ('exd', 'smart_capability_set'),
        }),
        (_('Шаблоны'), {
            'fields': ('name_template', 'description_template'),
        }),
        (_('Дополнительно'), {
            'fields': ('extra_params', 'sorting_order', 'is_active'),
        }),
    )


# ── Модель (item) ──

@admin.register(PosiModelLineItem)
class PosiModelLineItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'model_line', 'acting_type', 'exd', 'is_active']
    list_filter = ['model_line', 'acting_type', 'exd', 'is_active']
    search_fields = ['name', 'code']
    autocomplete_fields = [
        'model_line', 'acting_type', 'exd', 'ip', 'lever', 'body_connection', 'smart_capability_set',
    ]
    # raw_id_fields = [
    #     'body_connection',
    #     'alarm', 'signal_profile',
    # ]
    ordering = ['sorting_order', 'code']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'model_line', 'description'),
        }),
        (_('Опции'), {
            'fields': ('acting_type', 'exd', 'ip',
                       'body_connection',
                       'lever', ('work_temp_min', 'work_temp_max')),
        }),
        (_('Сигналы'), {
            'fields': ('signal_profile', 'alarm'),
        }),
        (_('Смарт-возможности'), {
            'fields': ('smart_capability_set',),
        }),
        (_('Дополнительно'), {
            'fields': ('extra_params', 'sorting_order', 'is_active'),
        }),
    )
