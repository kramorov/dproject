# materials/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    MaterialGeneral , MaterialGeneralMoreDetailed , MaterialStandard ,
    MaterialSpecified , MaterialCode , MaterialChemicalResistance , WorkingMedium
)
from .forms import MaterialSpecifiedAddForm , MaterialSpecifiedChangeForm


class MaterialCodeInline(admin.TabularInline) :
    model = MaterialCode
    extra = 1
    fields = ('standard' , 'code' , 'is_primary')
    verbose_name = _('Код материала')
    verbose_name_plural = _('Коды материалов')

    def get_formset(self , request , obj=None , **kwargs) :
        formset = super().get_formset(request , obj , **kwargs)
        # Упрощаем queryset для стандартов
        formset.form.base_fields['standard'].queryset = MaterialStandard.objects.all()
        return formset


class MaterialChemicalResistanceInline(admin.TabularInline) :
    model = MaterialChemicalResistance
    extra = 1
    fields = ('working_medium' , 'resistance_type')
    verbose_name = _('Химическая стойкость')
    verbose_name_plural = _('Химическая стойкость к средам')


@admin.register(MaterialSpecified)
class MaterialSpecifiedAdmin(admin.ModelAdmin) :
    # Разные формы для создания и редактирования
    def get_form(self , request , obj=None , **kwargs) :
        if obj is None :
            # Используем простую форму для создания
            kwargs['form'] = MaterialSpecifiedAddForm
        else :
            # Используем полную форму для редактирования
            kwargs['form'] = MaterialSpecifiedChangeForm
        return super().get_form(request , obj , **kwargs)

    # Разные inline для создания и редактирования
    def get_inlines(self , request , obj=None) :
        if obj and obj.pk :
            # Только для существующих объектов показываем inline
            return [MaterialCodeInline , MaterialChemicalResistanceInline]
        return []

    fieldsets = (
                (_('Обозначение')  , {
                    'fields' : ('name'  , 'code')
                }) ,
                (_('Материалы'), {
                    'fields': ('material_general', 'material_detailed',)
                }),
                (_('Описание') , {
                    'fields' : ( 'description', 'features_text', 'application_text') ,
                    'classes' : ('collapse' ,)
                }) ,
                (_('Температурные характеристики') , {
                    'fields' : ('work_temp_min' , 'work_temp_max' , 'temp_min' , 'temp_max')
                })
            )

    ordering = ['sorting_order']
    list_display = ('id', 'name', 'code', 'sorting_order','material_general' , 'material_detailed' , 'temp_min' , 'temp_max',  'is_active')
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ('material_general' , 'material_detailed')
    list_select_related = ('material_general' , 'material_detailed')
    list_per_page = 15

    def save_model(self , request , obj , form , change) :
        """Сохранение модели с обновлением symbolic_code"""
        # Сначала сохраняем объект без вызова update_name
        # чтобы избежать рекурсии при создании
        super().save_model(request , obj , form , change)

        # Обновляем symbolic_code только если это создание нового объекта
        # или если symbolic_code пустой
        if not change or not obj.name    :
            try :
                obj.update_name()
                # Сохраняем снова, чтобы обновить symbolic_code
                super().save_model(request , obj , form , change=True)
            except Exception as e :
                # Логируем ошибку, но не прерываем сохранение
                print(f"Error updating symbolic_code: {e}")

    def response_add(self , request , obj , post_url_continue=None) :
        """Перенаправление после успешного создания"""
        if "_addanother" in request.POST :
            return HttpResponseRedirect(reverse('admin:materials_materialspecified_add'))
        elif "_continue" in request.POST :
            return HttpResponseRedirect(reverse('admin:materials_materialspecified_change' , args=[obj.pk]))
        else :
            # По умолчанию перенаправляем на список материалов
            return HttpResponseRedirect(reverse('admin:materials_materialspecified_changelist'))


@admin.register(MaterialGeneral)
class MaterialGeneralAdmin(admin.ModelAdmin) :
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']


@admin.register(MaterialGeneralMoreDetailed)
class MaterialGeneralMoreDetailedAdmin(admin.ModelAdmin) :
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']
    list_select_related = ('material_general' ,)


@admin.register(MaterialStandard)
class MaterialStandardAdmin(admin.ModelAdmin) :
    list_display = ('name' , 'code' , 'description')
    search_fields = ('name' , 'code' , 'description')
    list_per_page = 20
    ordering = ('name' ,)


@admin.register(MaterialCode)
class MaterialCodeAdmin(admin.ModelAdmin) :
    list_display = ('material_specified' , 'standard' , 'code' , 'is_primary')
    list_filter = ('standard' , 'is_primary')
    search_fields = ('code' , 'material_specified__name' , 'standard__name')
    list_select_related = ('material_specified' , 'standard')
    list_per_page = 20
    list_editable = ('is_primary' ,)

    def save_model(self , request , obj , form , change) :
        """Сохраняем код и обновляем symbolic_code материала"""
        super().save_model(request , obj , form , change)

        # Обновляем symbolic_code связанного материала
        if obj.material_specified_id :
            try :
                obj.material_specified.update_name()
                obj.material_specified.save()
            except Exception as e :
                print(f"Error updating material symbolic_code: {e}")


@admin.register(WorkingMedium)
class WorkingMediumAdmin(admin.ModelAdmin) :
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']


@admin.register(MaterialChemicalResistance)
class MaterialChemicalResistanceAdmin(admin.ModelAdmin) :
    list_display = ('material_specified' , 'working_medium' , 'resistance_type')
    list_filter = ('resistance_type' , 'working_medium')
    search_fields = ('material_specified__name' , 'working_medium__name')
    list_select_related = ('material_specified' , 'working_medium')
    list_per_page = 20