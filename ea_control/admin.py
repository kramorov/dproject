# ea_control/admin.py
"""
Админка ea_control — справочники БУ, паттерн-модели (узлы/слоты/опции/
матрица/правила) и сущность ControlUnit.

Это Django-админ для отладки паттерна на бэке; Vue-страница
`/admin/ea-control` (вкладки «БУ»/«Узлы»/«Слоты-Опции»/«Матрица»/«Правила»)
— фронтовая часть плана, делается отдельно.
"""
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ea_control.models import (CuCapability, CuCommProtocol, CuControlLogic,
                               CuControlSignal, CuControlSignalForm,
                               CuDisplayType, CuFeedbackDevice,
                               CuFeedbackSignal, CuFeedbackSignalForm,
                               CuHeaterSupply, CuLocalControlType,
                               CuLocationOption, CuMatrixEntry, CuSignalPower,
                               CuSignalPowerSource, CuSlot, CuSlotOption,
                               CuSlotRule, CuUnitPowerSource, ControlUnit,
                               CuSectionNode)


class _DictAdmin(admin.ModelAdmin):
    """Общий админ справочников: поиск по коду/имени, фильтр активности."""
    list_display = ('code', 'name', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)
    ordering = ('sorting_order', 'code')


@admin.register(CuControlSignalForm)
class CuControlSignalFormAdmin(_DictAdmin):
    list_display = ('code', 'name', 'category', 'sorting_order', 'is_active')
    list_filter = ('category', 'is_active')


@admin.register(CuFeedbackSignalForm)
class CuFeedbackSignalFormAdmin(_DictAdmin):
    list_display = ('code', 'name', 'category', 'sorting_order', 'is_active')
    list_filter = ('category', 'is_active')


@admin.register(CuControlSignal)
class CuControlSignalAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'role', 'category', 'form', 'is_active')
    list_filter = ('category', 'form', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'code')


@admin.register(CuFeedbackSignal)
class CuFeedbackSignalAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'role', 'category', 'form', 'is_active')
    list_filter = ('category', 'form', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'code')


@admin.register(CuCommProtocol)
class CuCommProtocolAdmin(_DictAdmin):
    list_display = ('code', 'name', 'transport', 'sorting_order', 'is_active')
    list_filter = ('transport', 'is_active')


@admin.register(CuFeedbackDevice)
class CuFeedbackDeviceAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'kind', 'technology', 'contactless', 'is_active')
    list_filter = ('kind', 'technology', 'is_active')
    search_fields = ('code', 'name')
    filter_horizontal = ('emits', 'equivalents')


@admin.register(CuHeaterSupply)
class CuHeaterSupplyAdmin(_DictAdmin):
    pass


@admin.register(CuLocationOption)
class CuLocationOptionAdmin(_DictAdmin):
    pass


@admin.register(CuCapability)
class CuCapabilityAdmin(_DictAdmin):
    pass


@admin.register(CuLocalControlType)
class CuLocalControlTypeAdmin(_DictAdmin):
    pass


@admin.register(CuDisplayType)
class CuDisplayTypeAdmin(_DictAdmin):
    pass


@admin.register(CuUnitPowerSource)
class CuUnitPowerSourceAdmin(_DictAdmin):
    pass


@admin.register(CuSignalPowerSource)
class CuSignalPowerSourceAdmin(_DictAdmin):
    list_display = ('code', 'name', 'internal', 'sorting_order', 'is_active')
    list_editable = ('internal', 'sorting_order', 'is_active')


@admin.register(CuSignalPower)
class CuSignalPowerAdmin(admin.ModelAdmin):
    list_display = ('name', 'source', 'power_supply', 'input_form',
                    'polarity', 'sorting_order', 'is_active')
    list_filter = ('source', 'power_supply', 'input_form', 'polarity',
                   'is_active')
    search_fields = ('name',)


@admin.register(CuControlLogic)
class CuControlLogicAdmin(_DictAdmin):
    list_display = ('code', 'name', 'has_self_holding', 'sorting_order', 'is_active')


@admin.register(ControlUnit)
class ControlUnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'brand', 'kind', 'is_active')
    list_filter = ('brand', 'kind', 'is_active')
    search_fields = ('code', 'name')
    filter_horizontal = ('accepts', 'emits', 'protocols', 'capabilities')
    ordering = ('brand', 'sorting_order', 'code')


@admin.register(CuSectionNode)
class CuSectionNodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'sorting_order', 'is_active')
    list_filter = ('parent', 'is_active')
    search_fields = ('code', 'name')


@admin.register(CuSlot)
class CuSlotAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'section', 'selection_mode', 'slot_kind',
                    'required', 'is_active')
    list_filter = ('section', 'selection_mode', 'slot_kind', 'required', 'is_active')
    search_fields = ('code', 'name')


class _CuSlotOptionForm(forms.ModelForm):
    """Валидация M2M display_types.

    В model.clean() M2M ещё не записан (admin вызывает save_m2m после
    clean), поэтому проверку делаем в форме: cleaned_data['display_types']
    уже содержит выбранные значения.
    """
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('kind') == 'display' and not cleaned.get('display_types'):
            raise ValidationError(
                _('Для опции отображения нужен хотя бы один вид отображения.'))
        return cleaned

    class Meta:
        model = CuSlotOption
        fields = '__all__'


@admin.register(CuSlotOption)
class CuSlotOptionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'slot', 'kind', 'is_active')
    list_filter = ('slot', 'kind', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'code')
    form = _CuSlotOptionForm


@admin.register(CuMatrixEntry)
class CuMatrixEntryAdmin(admin.ModelAdmin):
    list_display = ('slot', 'option', 'availability', 'is_default', 'bundle',
                    'control_unit', 'power_supply', 'mode', 'sorting_order')
    list_filter = ('slot', 'availability', 'mode', 'control_unit', 'power_supply')
    search_fields = ('name', 'bundle')
    ordering = ('sorting_order', 'id')


@admin.register(CuSlotRule)
class CuSlotRuleAdmin(admin.ModelAdmin):
    list_display = ('when_slot', 'when_operator', 'when_value', 'action',
                    'target_slot', 'priority', 'is_active')
    list_filter = ('action', 'is_active')
    ordering = ('-priority', 'id')
