# electric_actuators/admin/ea_signals_admin.py
"""
Админка справочников сигналов ЭП (фаза 2 плана переезда).

Регистрирует: EaSignalForm, EaControlSignal, EaFeedbackSignal, EaCommProtocol,
EaFeedbackDevice, EaSignalSlot.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminCopyMixin
from electric_actuators.models.ea_signal_form import EaSignalForm, EaSignalFormCategory
from electric_actuators.models.ea_signals import (EaControlSignal,
                                                  EaFeedbackSignal,
                                                  EaControlSignalRole,
                                                  EaFeedbackSignalRole,
                                                  EaContactNormal)
from electric_actuators.models.ea_comm_protocol import (EaCommProtocol,
                                                        EaProtocolTransport)
from electric_actuators.models.ea_feedback_device import (
    EaFeedbackDevice, EaFeedbackDeviceKind, EaFeedbackTechnology,
)
from electric_actuators.models.ea_signal_slot import EaSignalSlot
from electric_actuators.models.ea_signal_matrix import (
    EaSignalMatrixEntry, EaWiringDiagramBinding,
)
from electric_actuators.models.ea_slot_option import EaSlotOption


@admin.register(EaSignalForm)
class EaSignalFormAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']


class _SimpleDictAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    search_fields = ['code', 'name']


for _model in (EaSignalFormCategory, EaControlSignalRole, EaFeedbackSignalRole,
               EaContactNormal, EaProtocolTransport):
    admin.site.register(_model, _SimpleDictAdmin)


@admin.register(EaControlSignal)
class EaControlSignalAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'role', 'category', 'form', 'voltage',
                    'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['category', 'form', 'hart', 'is_active']
    search_fields = ['code', 'name']
    autocomplete_fields = ['form']


@admin.register(EaFeedbackSignal)
class EaFeedbackSignalAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'role', 'category', 'form', 'max_voltage',
                    'max_current', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['category', 'form', 'hart', 'is_active']
    search_fields = ['code', 'name']
    autocomplete_fields = ['form']


@admin.register(EaCommProtocol)
class EaCommProtocolAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'transport', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['transport', 'is_active']
    search_fields = ['code', 'name']


@admin.register(EaFeedbackDevice)
class EaFeedbackDeviceAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'kind', 'technology', 'contactless',
                    'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['kind', 'technology', 'contactless', 'is_active']
    search_fields = ['code', 'name']
    autocomplete_fields = ['emits', 'equivalents']


@admin.register(EaFeedbackDeviceKind)
class EaFeedbackDeviceKindAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(EaFeedbackTechnology)
class EaFeedbackTechnologyAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(EaSignalSlot)
class EaSignalSlotAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'required', 'sorting_order', 'is_active']
    list_editable = ['required', 'sorting_order', 'is_active']
    list_filter = ['required', 'is_active']
    search_fields = ['code', 'name']


@admin.register(EaSlotOption)
class EaSlotOptionAdmin(AdminCopyMixin, admin.ModelAdmin):
    """Опции слотов матрицы — каталог для каркаса выгрузки и конфигуратора."""
    list_display = ['code', 'slot', 'kind', 'feedback_signal',
                    'control_signal', 'protocol', 'heater_supply',
                    'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['slot', 'kind', 'is_active']
    search_fields = ['code', 'name']
    autocomplete_fields = ['slot', 'feedback_signal', 'control_signal',
                           'protocol', 'heater_supply', 'device']


@admin.register(EaSignalMatrixEntry)
class EaSignalMatrixEntryAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['id', 'brand', 'model_line', 'body', 'model_line_item',
                    'control_unit', 'power_supply', 'mode', 'slot',
                    'availability', 'is_default', 'bundle']
    list_filter = ['availability', 'mode', 'slot']
    search_fields = ['name', 'bundle', 'encoding', 'ext_encoding']
    autocomplete_fields = ['brand', 'model_line', 'body', 'model_line_item',
                           'control_unit', 'power_supply', 'slot',
                           'control_signal', 'feedback_signal', 'protocol',
                           'device', 'heater_supply', 'conflicts']


@admin.register(EaWiringDiagramBinding)
class EaWiringDiagramBindingAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'model_line', 'body', 'model_line_item',
                    'control_unit', 'power_supply', 'mode', 'match_type',
                    'diagram', 'is_active']
    list_filter = ['match_type', 'mode', 'is_active']
    search_fields = ['name']
    autocomplete_fields = ['model_line', 'body', 'model_line_item',
                           'control_unit', 'power_supply', 'signals', 'diagram']
