from django.contrib import admin
from django.db import models

from .models import EttDocument, MtrType, DnType,PnType, EttActuatorType, EttClimaticOption, EttMediumMaxTempOption, \
    EttSeismicOption, EttStatusSignal, EttControlSignal, EttFeedbackSignal, EttControlUnitHeater, \
    EttControlUnitType, EttControlUnitDisplayType, EttCableGlandType, EttElectricOptionsCombination, \
    EttControlOptionsCombination, EttOtherOptionsCombination, EttOpenTime


def duplicate_selected_action(model_admin, request, queryset):
    for obj in queryset:
        # Создаем копию объекта с обнулением pk
        # Create a new instance and copy field values (excluding the pk)
        # Object Copying: Instead of using obj.copy(), I manually create a new instance of the same class
        # (obj.__class__()) and copy the values from the original object to the new one.
        new_obj = obj.__class__()
        # Copy the field values from the original object to the new object
        for field in obj._meta.fields:
            if field.name != 'id':  # Exclude the primary key field
                setattr(new_obj, field.name, getattr(obj, field.name))

        # Проверяем, есть ли поле symbolic_code и добавляем 'K', если есть
        if hasattr(obj, 'symbolic_code') and isinstance(obj._meta.get_field('symbolic_code'), models.CharField):
            new_obj.symbolic_code = f"{new_obj.symbolic_code}(K"  # Добавляем 'K' в конец

        # Обнуляем pk для новой записи
        new_obj.pk = None
        new_obj.save()  # Сохраняем новый объект

        # Копируем ManyToMany связи для ett_doc
        if hasattr(obj, 'ett_doc') and isinstance(obj._meta.get_field('ett_doc'), models.ManyToManyField):
            for ett_document in obj.ett_doc.all():
                new_obj.ett_doc.add(ett_document)

    model_admin.message_user(request, "Выбранные записи успешно скопированы.")


duplicate_selected_action.short_description = "Скопировать выбранные записи"


class EttDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'ett_code')  # Отображаем нужные поля
    actions = [duplicate_selected_action]  # Кнопка копирования


# Метод для отображения ett_doc в list_display
class EttDocAdminBase(admin.ModelAdmin):
    # Метод для отображения ett_doc в list_display
    def ett_doc_display(self, obj):
        return ", ".join([doc.name for doc in obj.ett_doc.all()])

    ett_doc_display.short_description = "Документы"  # Название столбца в админке


class MtrTypeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description', 'ett_doc_display')  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttOpenTimeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'dn_from', 'dn_up_to', 'actuator_speed')  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей

class PnTypeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'valve_pn_value')  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class DnTypeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'valve_dn_value')  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttActuatorTypeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'actuator_type', 'actuator_speed', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttClimaticOptionAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttMediumMaxTempOptionAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttSeismicOptionAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttStatusSignalAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttControlSignalAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttFeedbackSignalAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttControlUnitHeaterAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'param_name', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttControlUnitLocationAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'param_name', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttControlUnitDisplayTypeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'param_name', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttCableGlandTypeAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttElectricOptionsCombinationAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttControlOptionsCombinationAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


class EttOtherOptionsCombinationAdmin(EttDocAdminBase):
    # fields = ('__all__',)  # Make it a tuple # Редактировать все поля, включая связь ManyToMany
    list_display = ('symbolic_code', 'text_description',)  # Отображение в списке

    actions = [duplicate_selected_action]  # Копирование записей


admin.site.register(EttDocument, EttDocumentAdmin)
admin.site.register(MtrType, MtrTypeAdmin)
admin.site.register(DnType, DnTypeAdmin)
admin.site.register(PnType, PnTypeAdmin)
admin.site.register(EttActuatorType, EttActuatorTypeAdmin)
admin.site.register(EttClimaticOption, EttClimaticOptionAdmin)
admin.site.register(EttMediumMaxTempOption, EttMediumMaxTempOptionAdmin)
admin.site.register(EttSeismicOption, EttSeismicOptionAdmin)
admin.site.register(EttStatusSignal, EttStatusSignalAdmin)
admin.site.register(EttControlSignal, EttControlSignalAdmin)
admin.site.register(EttFeedbackSignal, EttFeedbackSignalAdmin)
admin.site.register(EttControlUnitHeater, EttControlUnitHeaterAdmin)
admin.site.register(EttControlUnitType , EttControlUnitLocationAdmin)
admin.site.register(EttControlUnitDisplayType, EttControlUnitDisplayTypeAdmin)
admin.site.register(EttCableGlandType, EttCableGlandTypeAdmin)
admin.site.register(EttOtherOptionsCombination, EttOtherOptionsCombinationAdmin)
admin.site.register(EttControlOptionsCombination, EttControlOptionsCombinationAdmin)
admin.site.register(EttElectricOptionsCombination, EttElectricOptionsCombinationAdmin)
admin.site.register(EttOpenTime, EttOpenTimeAdmin)
