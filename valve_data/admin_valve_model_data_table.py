from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render , redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from params.models import DnVariety , PnVariety
from .utils.valve_line_data_table_import_export import export_valve_line_data_table_to_excel , import_valve_line_data_table_from_excel

from valve_data.models import ValveModelDataTable , ValveLineModelData


class ValveLineModelDataInline(admin.TabularInline) :  # или admin.StackedInline для формы
    model = ValveLineModelData
    extra = 1
    verbose_name = _("Модель арматуры")
    verbose_name_plural = _("Модели арматуры")
    # classes = ['collapse']  # Стандартные классы Django
    # Поля для отображения в таблице
    fields = ['name' ,
              'valve_model_dn' , 'valve_model_pn' ,
              'valve_model_torque_to_open' , 'valve_model_torque_to_close' , 'valve_model_thrust_to_close' ,
              'valve_model_rotations_to_open' ,
              'valve_model_stem_size' ,
              'valve_model_mounting_plate' ,
              'valve_model_stem_height' , 'valve_model_construction_length' ,

              ]

    # Фильтры для полей
    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        if db_field.name == "valve_model_dn" :
            kwargs["queryset"] = DnVariety.objects.filter(is_active=True)
        elif db_field.name == "valve_model_pn" :
            kwargs["queryset"] = PnVariety.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field , request , **kwargs)

    def get_queryset(self , request) :
        # Для отладки
        qs = super().get_queryset(request)
        print(f"DEBUG ValveLineModelDataInline: Found {qs.count()} ValveLineModelData records")
        for i , record in enumerate(qs) :
            print(
                f"DEBUG Record {i + 1}. ID:{record.id}, Name: {record.name}, "
                f"ValveModelDataTable id: {getattr(record.valve_model_data_table , 'id' , 'None')}, "
                f"DN: {getattr(record.valve_model_dn , 'value' , 'None')},"
                f"PN: {getattr(record.valve_model_pn , 'value' , 'None')}, "
                f"Torque to open: {record.valve_model_torque_to_open}, "
                f"Rotations to open: {record.valve_model_rotations_to_open}")

            # Также выведем информацию о текущем объекте ValveLine
        # if hasattr(request, '_obj') and request._obj:
        #     print(f"DEBUG Current ValveLine: ID={request._obj.id}, Name='{request._obj.name}'")

        return qs
    # Для ManyToMany поля монтажных площадок
    # filter_horizontal = ['valve_model_mounting_plate']
    # filter_vertical = ['valve_model_mounting_plate']

    # Можно добавить кастомный шаблон для более компактного отображения
    # template = 'admin/valve_model_data_inline.html'

class ValveModelDataTableAdmin(admin.ModelAdmin) :
    """Шаблон моделей арматуры - для выбора в ValveLine"""
    change_form_template = 'admin/valve_model_data_table_change_form.html'
    list_display = ['id' , 'name' , 'code' , 'valve_brand' , 'valve_variety' , 'is_active' ]
    list_filter = ['is_active' , 'valve_brand' , 'valve_variety']
    # search_fields = ['name', 'code']
    list_editable = ['name' , 'code' , 'valve_brand' , 'is_active']

    inlines = [ValveLineModelDataInline]  # Используем тот же inline

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/export-model-data-table/' ,
                 self.admin_site.admin_view(self.export_model_data_table) ,
                 name='model_data_table_export') ,
            path('<path:object_id>/import-model-data-table/' ,
                 self.admin_site.admin_view(self.import_model_data_table) ,
                 name='model_data_table_import') ,
        ]
        return custom_urls + urls

    def export_model_data_table(self , request , object_id) :
        """Экспорт моделей арматуры для конкретного ValveLine"""
        try :
            valve_line_data_table = ValveModelDataTable.objects.get(id=object_id)

            response = export_valve_line_data_table_to_excel(valve_line_data_table)

            # ВАЖНО: возвращаем response!
            return response

        except ValveModelDataTable.DoesNotExist :
            from django.contrib import messages
            messages.error(request , _("Таблица данных для серии арматуры не найдена"))
            return redirect('..')
        except Exception as e :
            from django.contrib import messages
            messages.error(request , _("Ошибка при экспорте: {}").format(str(e)))
            return redirect('..')

    def import_model_data_table(self , request , object_id) :
        """Импорт моделей арматуры для конкретного ValveLine"""
        try :
            valve_line_data_table = ValveModelDataTable.objects.get(id=object_id)
            print(f"DEBUG: Starting import_models for {valve_line_data_table.name}")

            if request.method == 'GET' :
                print("DEBUG: GET request - showing form")
                return render(request, 'admin/valve_model_data_table_import.html', {
                    'valve_line_data_table' : valve_line_data_table ,
                    'opts' : self.model._meta ,
                    'title' : _('Импорт моделей арматуры')
                })

            elif request.method == 'POST' :
                print("DEBUG: POST request - processing")

                # ЕСЛИ ЭТО ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ - файл уже в сессии
                if request.POST.get('confirm_delete') :
                    print("DEBUG: This is a confirmation POST - file is in session")
                    # Просто вызываем функцию импорта, файл будет восстановлен из сессии
                    result = import_valve_line_data_table_from_excel(valve_line_data_table , None , request)
                else :
                    # ЭТО ПЕРВОНАЧАЛЬНАЯ ЗАГРУЗКА ФАЙЛА
                    print("DEBUG: This is initial file upload POST")

                    # Обрабатываем загруженный файл
                    if 'excel_file' not in request.FILES :
                        messages.error(request , _("Файл не был загружен"))
                        return redirect('..')

                    excel_file = request.FILES['excel_file']

                    # Проверяем расширение файла
                    if not excel_file.name.endswith(('.xlsx' , '.xls')) :
                        messages.error(request , _("Поддерживаются только файлы Excel (.xlsx, .xls)"))
                        return redirect('..')

                    # Вызываем функцию импорта с файлом
                    result = import_valve_line_data_table_from_excel(valve_line_data_table , excel_file , request)

                print(f"DEBUG: import_valve_line_models_from_excel returned: {result}")

                # Проверяем, что функция вернула кортеж
                if result is None :
                    print("DEBUG: ERROR - import function returned None")
                    messages.error(request , _("Ошибка импорта: функция не вернула результат"))
                    return redirect('..')

                if not isinstance(result , tuple) or len(result) != 2 :
                    print(f"DEBUG: ERROR - import function returned invalid type: {type(result)}")
                    messages.error(request , _("Ошибка импорта: неверный формат результата"))
                    return redirect('..')

                result_type , result_data = result

                # Обрабатываем результат
                if result_type == 'confirm_delete' :
                    print("DEBUG: Need confirmation for deletion")
                    return render(request, 'admin/valve_model_data_table_import_confirm.html', {
                        'valve_line' : valve_line_data_table ,
                        'combinations_to_delete' : result_data ,
                        'opts' : self.model._meta ,
                        'title' : _('Подтверждение удаления')
                    })
                elif result_type == 'success' :
                    print("DEBUG: Import successful")
                    messages.success(request , _("Данные успешно импортированы"))
                    return redirect('..')
                elif result_type == 'partial_success' :
                    print("DEBUG: Import completed with warnings")
                    messages.warning(request , _("Импорт завершен с ошибками: {}").format(result_data))
                    return redirect('..')
                elif result_type == 'error' :
                    print("DEBUG: Import failed")
                    messages.error(request , _("Ошибка при импорте: {}").format(result_data))
                    return redirect('..')
                else :
                    print(f"DEBUG: Unknown result type: {result_type}")
                    messages.error(request , _("Неизвестный результат импорта"))
                    return redirect('..')

        except ValveModelDataTable.DoesNotExist :
            print("DEBUG: ValveModelDataTable not found")
            messages.error(request , _("Таблица данных для серии арматуры не найдена"))
            return redirect('..')
        except Exception as e :
            print(f"DEBUG: Exception in import_models: {e}")
            messages.error(request , _("Ошибка при импорте: {}").format(str(e)))
            return redirect('..')

    def change_view(self , request , object_id , form_url='' , extra_context=None) :
        # Добавляем кнопки импорта/экспорта в контекст
        if extra_context is None :
            extra_context = {}

        extra_context['export_url'] = f'export-model-data-table/'
        extra_context['import_url'] = f'import-model-data-table/'

        return super().change_view(request , object_id , form_url , extra_context=extra_context)
