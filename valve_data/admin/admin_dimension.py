# valve_data/admin/admin_dimension.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django import forms

import logging

logger = logging.getLogger(__name__)

from valve_data.models.dimensions import (
    ValveDimensionTable, DimensionTableParameter,
    ValveDimensionData, WeightDimensionParameterVariety,
    DimensionTableDrawingItem
)
from valve_data.services.dimension_services import DimensionDataService


class ExcelImportForm(forms.Form):
    """Форма для импорта Excel"""
    excel_file = forms.FileField(
        label='Excel файл',
        help_text='Загрузите файл с данными ВГХ'
    )


class DimensionTableDrawingInline(admin.TabularInline):
    """Inline для чертежей таблицы ВГХ"""
    model = DimensionTableDrawingItem
    extra = 1
    filter_horizontal = ('allowed_dn',)
    fields = ('drawing', 'allowed_dn', 'description', 'display_order')
    verbose_name = "Чертеж"
    verbose_name_plural = "Чертежи таблицы ВГХ"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Фильтруем чертежи по категориям чертежей и технической документации"""
        if db_field.name == "drawing":
            from media_library.models import MediaCategory
            try:
                # Категории для чертежей и технической документации
                drawing_categories = MediaCategory.objects.filter(
                    code__in=['DRAWING', 'SCHEMA', 'DIAGRAM', 'TECH_DOC']
                )

                if drawing_categories.exists():
                    kwargs["queryset"] = db_field.related_model.objects.filter(
                        category__in=drawing_categories
                    ).select_related('category').order_by('title')

            except Exception as e:
                logger.warning(f"Ошибка фильтрации чертежей: {e}")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Фильтруем DN по сортировке"""
        if db_field.name == "allowed_dn":
            kwargs["queryset"] = db_field.related_model.objects.all().order_by('sorting_order')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class DimensionTableParameterInline(admin.TabularInline):
    """Inline для параметров таблицы ВГХ"""
    model = DimensionTableParameter
    extra = 1
    fields = ('legend', 'name', 'parameter_variety', 'sorting_order')
    ordering = ('sorting_order',)
    verbose_name = "Параметр"
    verbose_name_plural = "Параметры таблицы ВГХ"


@admin.register(ValveDimensionTable)
class ValveDimensionTableAdmin(admin.ModelAdmin):
    """Админка для таблиц весо-габаритных характеристик"""
    list_display = [
        'name', 'code', 'valve_brand', 'valve_variety',
        'parameters_count', 'data_count', 'drawings_count', 'data_matrix_info'
    ]

    list_filter = ['valve_brand', 'valve_variety']
    search_fields = ['name', 'code', 'valve_brand__name', 'valve_variety__name']
    list_select_related = ['valve_brand', 'valve_variety']
    ordering = ['name']

    inlines = [DimensionTableParameterInline, DimensionTableDrawingInline]

    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'name', 'code', 'valve_brand', 'valve_variety', 'description'
            )
        }),
    )

    change_form_template = 'admin/valve_data/valvedimensiontable/change_form.html'
    # actions = [duplicate_dimension_table_action , export_selected_to_excel_action]

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/import-excel/' ,
                self.admin_site.admin_view(self.import_excel_view) ,
                name='dimension_table_import' ,
            ) ,
            path(
                '<path:object_id>/export-template/' ,
                self.admin_site.admin_view(self.export_template_view) ,
                name='dimension_table_export_template' ,
            ) ,
            path(
                '<path:object_id>/export-excel/' ,
                self.admin_site.admin_view(self.export_excel_view) ,  # ← ДОБАВЬТЕ ЭТОТ URL
                name='dimension_table_export_excel' ,
            ) ,
            path(
                '<path:object_id>/view-data/' ,
                self.admin_site.admin_view(self.view_data_view) ,
                name='dimension_table_view_data' ,
            ) ,
        ]
        return custom_urls + urls

    def import_excel_view(self, request, object_id):
        """Вью для импорта Excel"""
        dimension_table = self.get_object(request, object_id)

        if request.method == 'POST':
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    excel_file = request.FILES['excel_file']
                    imported_count, errors = DimensionDataService.import_data_to_table(
                        dimension_table, excel_file
                    )

                    if errors:
                        for error in errors:
                            messages.error(request, error)

                    if imported_count > 0:
                        messages.success(
                            request,
                            f'Успешно импортировано {imported_count} значений данных ВГХ'
                        )
                    else:
                        messages.warning(request, 'Не удалось импортировать данные')

                except Exception as e:
                    logger.error("Import exception: %s", str(e), exc_info=True)
                    messages.error(request, f'Ошибка импорта: {str(e)}')

                return redirect('admin:valve_data_valvedimensiontable_change', object_id)
        else:
            form = ExcelImportForm()

        context = self.admin_site.each_context(request)
        context.update({
            'title': f'Импорт данных ВГХ - {dimension_table.name}',
            'form': form,
            'dimension_table': dimension_table,
            'opts': self.model._meta,
        })

        return render(request, 'admin/valve_data/valvedimensiontable/import.html', context)

    def export_excel_view(self , request , object_id) :
        """Экспорт данных таблицы ВГХ в Excel"""
        dimension_table = self.get_object(request , object_id)

        try :
            # Получаем параметры из запроса (если есть)
            dn_list = request.GET.getlist('dn')
            pn_list = request.GET.getlist('pn')

            # Используем метод для экспорта в Excel
            excel_path = DimensionDataService.export_to_excel(
                dimension_table ,
                dn_list=dn_list if dn_list else None ,
                pn_list=pn_list if pn_list else None ,
                output_path=None
            )

            with open(excel_path , 'rb') as f :
                response = HttpResponse(
                    f.read() ,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="vgx_export_{dimension_table.code}.xlsx"'

            messages.success(request , 'Данные успешно экспортированы в Excel')
            return response

        except Exception as e :
            logger.error("Error exporting to Excel: %s" , str(e))
            messages.error(request , f'Ошибка при экспорте в Excel: {str(e)}')
            return redirect('admin:valve_data_valvedimensiontable_change' , object_id)

    def export_template_view(self , request , object_id) :
        """Экспорт пустого шаблона Excel для заполнения"""
        dimension_table = self.get_object(request , object_id)

        try :
            # Используем метод для создания пустого шаблона
            template_path = DimensionDataService.create_empty_template(dimension_table)

            with open(template_path , 'rb') as f :
                response = HttpResponse(
                    f.read() ,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="vgx_template_{dimension_table.code}.xlsx"'

            messages.success(request , 'Шаблон успешно скачан')
            return response

        except Exception as e :
            logger.error("Error exporting template: %s" , str(e))
            messages.error(request , f'Ошибка при создании шаблона: {str(e)}')
            return redirect('admin:valve_data_valvedimensiontable_change' , object_id)

    def view_data_view(self, request, object_id):
        """Просмотр данных таблицы ВГХ"""
        dimension_table = self.get_object(request, object_id)

        try:
            # ИСПРАВЛЕНО: используем новый метод get_display_data
            display_data = DimensionDataService.get_dimensions_display_data(
                dimension_table,
                dn_list=None,
                pn_list=None,
                export=False
            )

            context = self.admin_site.each_context(request)
            context.update({
                'title' : f'Данные ВГХ - {dimension_table.name}' ,
                **display_data  # ← если export_mode уже в display_data, он распакуется
            })

            # Если export_mode не передается из сервиса, добавьте явно
            if 'export_mode' not in display_data :
                context['export_mode'] = False

            return render(request , 'admin/valve_data/valvedimensiontable/view_data.html' , context)

        except Exception as e:
            logger.error("Error viewing data: %s", str(e))
            messages.error(request, f'Ошибка при получении данных: {str(e)}')
            return redirect('admin:valve_data_valvedimensiontable_change', object_id)

    def parameters_count(self, obj):
        """Количество параметров в таблице"""
        return obj.table_parameters.count()

    parameters_count.short_description = _('Параметры')
    parameters_count.admin_order_field = 'table_parameters__count'

    def data_count(self, obj):
        """Количество записей данных ВГХ"""
        return ValveDimensionData.objects.filter(
            parameter__dimension_table=obj
        ).count()

    data_count.short_description = _('Данные')

    def drawings_count(self, obj):
        """Количество чертежей"""
        return obj.drawing_relations.count()

    drawings_count.short_description = _('Чертежи')

    def data_matrix_info(self, obj):
        """Информация о матрице данных"""
        try:
            matrix = obj.pn_dn_matrix
            pns = len(matrix.get('available_pns', []))
            dns = len(matrix.get('available_dns', []))
            combinations = len(matrix.get('pn_dn_combinations', []))
            return format_html(
                'PN: <b>{}</b>, DN: <b>{}</b>, комбинаций: <b>{}</b>',
                pns, dns, combinations
            )
        except Exception as e:
            logger.error("Error getting matrix info: %s", e)
            return "Ошибка"

    data_matrix_info.short_description = _('Матрица данных')

    def get_queryset(self, request):
        """Аннотируем queryset количеством параметров"""
        return super().get_queryset(request).annotate(
            parameters_count=Count('table_parameters', distinct=True)
        )

@admin.register(WeightDimensionParameterVariety)
class WeightDimensionParameterVarietyAdmin(admin.ModelAdmin):
    """Админка для видов параметров ВГХ"""
    list_display = ['name', 'code', 'is_predefined', 'is_active']
    list_filter = ['is_predefined', 'is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['is_predefined']
    ordering = ['name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Статус'), {
            'fields': ('is_predefined', 'is_active')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Для предопределенных параметров запрещаем редактирование кода"""
        if obj and obj.is_predefined:
            return ['code', 'is_predefined', 'is_active'] + list(self.readonly_fields)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление предопределенных параметров"""
        if obj and obj.is_predefined:
            return False
        return super().has_delete_permission(request, obj)


# Действия для админки
def duplicate_dimension_table_action(modeladmin, request, queryset):
    """Действие для копирования таблиц ВГХ через метод модели"""
    success_count = 0
    errors = []

    for table in queryset:
        try:
            # Используем метод модели для копирования
            new_table = table.duplicate_table()
            success_count += 1

        except Exception as e:
            error_msg = f"Ошибка при копировании {table.name}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    # Показываем результаты
    if success_count > 0:
        messages.success(
            request,
            f'Успешно скопировано {success_count} таблиц ВГХ'
        )

    for error in errors:
        messages.error(request, error)

def export_selected_to_excel_action(modeladmin , request , queryset) :
    """Действие для экспорта выбранных таблиц в Excel"""
    if queryset.count() > 1 :
        messages.error(request , 'Массовый экспорт пока не поддерживается. Выберите одну таблицу.')
        return

    table = queryset.first()
    return redirect('admin:dimension_table_export_excel' , object_id=table.pk)

export_selected_to_excel_action.short_description = _("Экспорт выбранных таблиц в Excel")
duplicate_dimension_table_action.short_description = _("Копировать выбранные таблицы ВГХ")