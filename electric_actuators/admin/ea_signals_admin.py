# electric_actuators/admin/ea_signals_admin.py
"""
Админка справочников сигналов ЭП (фаза 2 плана переезда).

Регистрирует: EaSignalForm, EaControlSignal, EaFeedbackSignal, EaCommProtocol,
EaFeedbackDevice.
"""
from django.contrib import admin

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
