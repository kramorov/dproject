# admin_valve_model_kv_data_table.py
import pandas as pd
from django.http import HttpResponse
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction
from io import BytesIO
from django.urls import path , reverse
from django.shortcuts import render , redirect
from django import forms

from params.models import DnVariety
from .models import ValveModelKvDataTable, ValveLineModelKvData


class ExcelImportForm(forms.Form) :
    """Форма для загрузки Excel файла"""
    excel_file = forms.FileField(
        label=_('Excel файл') ,
        help_text=_('Загрузите файл Excel с данными Kvs')
    )


class ValveLineModelKvDataInline(admin.TabularInline) :
    model = ValveLineModelKvData
    extra = 0

    verbose_name = _("Значения Kv для модели арматуры")
    verbose_name_plural = _("Значения Kv для моделей арматуры")

    fields = ['valve_model_dn' , 'valve_model_pn' , 'valve_model_openinig_angle' ,'valve_model_kv' ]

# @admin.register(ValveModelKvDataTable)
class ValveModelKvDataTableAdmin(admin.ModelAdmin) :
    list_display = ('name' , 'valve_brand' , 'valve_variety' , 'sorting_order' , 'is_active')
    list_filter = ('valve_brand' , 'valve_variety' , 'is_active')
    search_fields = ('name' , 'code')
    ordering = ('sorting_order' ,)
    inlines = [ValveLineModelKvDataInline]

    change_form_template = 'admin/valve_model_kv_data_table_change_form.html'

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/export-kv-data/' ,
                self.admin_site.admin_view(self.export_kv_data_view) ,
                name='valve_model_kv_data_table_export_kv_data' ,
            ) ,
            path(
                '<path:object_id>/export-kv-template/' ,
                self.admin_site.admin_view(self.export_kv_template_view) ,
                name='valve_model_kv_data_table_export_kv_template' ,
            ) ,
            path(
                '<path:object_id>/import-kv-data/' ,
                self.admin_site.admin_view(self.import_kv_data_view) ,
                name='valve_model_kv_data_table_import_kv_data' ,
            ) ,
        ]
        return custom_urls + urls

    def change_view(self , request , object_id , form_url='' , extra_context=None) :
        extra_context = extra_context or {}
        extra_context['show_export_buttons'] = True
        return super().change_view(
            request , object_id , form_url , extra_context=extra_context ,
        )

    def export_kv_data_view(self , request , object_id) :
        """Вью для экспорта данных Kvs"""
        try :
            valve_model = ValveModelKvDataTable.objects.get(pk=object_id)

            # Получаем все данные Kv для выбранного шаблона
            kv_data = ValveLineModelKvData.objects.filter(
                valve_model_kv_data_table=valve_model
            ).select_related('valve_model_dn' , 'valve_model_pn')

            if not kv_data.exists() :
                messages.error(request , _("Нет данных Kvs для экспорта"))
                # ИСПРАВЛЕННЫЙ URL - используем reverse
                return redirect(reverse('admin:valve_data_valvemodelkvdatatable_change' , args=[object_id]))

            # Собираем уникальные углы открытия
            angles = sorted(set([float(data.valve_model_openinig_angle) for data in kv_data if
                                 data.valve_model_openinig_angle is not None]))

            # Собираем уникальные DN
            dns = sorted(set([data.valve_model_dn for data in kv_data if data.valve_model_dn]) ,
                         key=lambda x : x.diameter_metric)

            # Создаем DataFrame
            df_data = []
            for dn in dns :
                row = {'DN' : dn.diameter_metric}
                # Для каждого угла находим соответствующее значение Kv
                for angle in angles :
                    kv_value = next((data.valve_model_kv for data in kv_data
                                     if data.valve_model_dn == dn and
                                     float(data.valve_model_openinig_angle) == angle) , None)
                    row[str(angle)] = float(kv_value) if kv_value is not None else ''
                df_data.append(row)

            df = pd.DataFrame(df_data)

            # Создаем Excel файл
            output = BytesIO()
            with pd.ExcelWriter(output , engine='openpyxl') as writer :
                df.to_excel(writer , sheet_name='Kv Data' , index=False)

                # Форматирование
                worksheet = writer.sheets['Kv Data']
                for col_num , value in enumerate(df.columns.values , 1) :
                    worksheet.cell(row=1 , column=col_num).value = value

            output.seek(0)

            # Создаем HTTP response
            response = HttpResponse(
                output.getvalue() ,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="kv_data_{valve_model.code}.xlsx"'

            messages.success(request , _("Данные Kvs успешно экспортированы"))
            return response

        except ValveModelKvDataTable.DoesNotExist :
            messages.error(request , _("Шаблон не найден"))
            return redirect(reverse('admin:valve_data_valvemodelkvdatatable_changelist'))
        except Exception as e :
            messages.error(request , _(f"Ошибка при экспорте: {str(e)}"))
            return redirect(reverse('admin:valve_data_valvemodelkvdatatable_change' , args=[object_id]))

    def export_kv_template_view(self , request , object_id) :
        """Вью для экспорта шаблона таблицы Kvs"""
        try :
            valve_model = ValveModelKvDataTable.objects.get(pk=object_id)

            # Стандартные углы открытия
            standard_angles = [0 , 10 , 15 , 20 , 30 , 45 , 60 , 75 , 80 , 90]

            # Получаем все значения диаметров из DnVariety
            dn_varieties = DnVariety.objects.all().order_by('diameter_metric')

            # Создаем DataFrame
            df_data = []
            for dn in dn_varieties :
                row = {'DN' : dn.diameter_metric}
                for angle in standard_angles :
                    row[str(angle)] = ''  # Пустые значения для заполнения
                df_data.append(row)

            df = pd.DataFrame(df_data)

            # Создаем Excel файл
            output = BytesIO()
            with pd.ExcelWriter(output , engine='openpyxl') as writer :
                df.to_excel(writer , sheet_name='Kv Template' , index=False)

                # Добавляем инструкции
                instructions = [
                    "ИНСТРУКЦИЯ ПО ЗАПОЛНЕНИЮ:" ,
                    "1. Не изменяйте структуру таблицы (первую строку с углами и первый столбец с DN)" ,
                    "2. Заполняйте значения Kv в соответствующих ячейках" ,
                    "3. Убедитесь, что значения DN соответствуют существующим в системе" ,
                    "4. Углы открытия должны быть в диапазоне 0-90 градусов" ,
                    "5. Для импорта используйте соответствующую кнопку в админке"
                ]

                instructions_df = pd.DataFrame(instructions)
                instructions_df.to_excel(writer , sheet_name='Инструкция' , index=False , header=False)

            output.seek(0)

            # Создаем HTTP response
            response = HttpResponse(
                output.getvalue() ,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="kv_template_{valve_model.code}.xlsx"'

            messages.success(request , _("Шаблон таблицы Kvs успешно экспортирован"))
            return response

        except ValveModelKvDataTable.DoesNotExist :
            messages.error(request , _("Шаблон не найден"))
            return redirect(reverse('admin:valve_data_valvemodelkvdatatable_changelist'))
        except Exception as e :
            messages.error(request , _(f"Ошибка при экспорте шаблона: {str(e)}"))
            return redirect(reverse('admin:valve_data_valvemodelkvdatatable_change' , args=[object_id]))

    def import_kv_data_view(self , request , object_id) :
        """Вью для импорта данных Kvs"""
        try :
            valve_model = ValveModelKvDataTable.objects.get(pk=object_id)

            if request.method == 'POST' :
                form = ExcelImportForm(request.POST , request.FILES)
                if form.is_valid() :
                    excel_file = request.FILES['excel_file']

                    # Обрабатываем файл
                    success , message = self._process_imported_kv_data(valve_model , excel_file)

                    if success :
                        messages.success(request , message)
                    else :
                        messages.error(request , message)

                    # ИСПРАВЛЕННЫЙ URL
                    return redirect(reverse('admin:valve_data_valvemodelkvdatatable_change' , args=[object_id]))
            else :
                form = ExcelImportForm()

            context = self.admin_site.each_context(request)
            context.update({
                'title' : _('Импорт данных Kvs') ,
                'form' : form ,
                'valve_model' : valve_model ,
                'opts' : self.model._meta ,
                'has_view_permission' : True ,
            })

            return render(request , 'admin/valve_model_kv_data_table_import.html' , context)

        except ValveModelKvDataTable.DoesNotExist :
            messages.error(request , _("Шаблон не найден"))
            return redirect(reverse('admin:valve_data_valvemodelkvdatatable_changelist'))

    def _process_imported_kv_data(self , valve_model , excel_file) :
        """Исправленная простая версия"""
        try :
            with transaction.atomic() :
                # Читаем Excel
                df = pd.read_excel(excel_file , sheet_name=0)

                print("=== ДАННЫЕ ИЗ EXCEL ===")
                print("Исходные колонки:" , list(df.columns))

                # Преобразуем заголовки в правильный формат
                new_columns = []
                for col in df.columns :
                    if isinstance(col , (int , float)) :
                        # Для целых чисел убираем .0
                        if col == int(col) :
                            new_columns.append(str(int(col)))
                        else :
                            new_columns.append(str(col))
                    else :
                        new_columns.append(str(col))

                df.columns = new_columns
                print("Обработанные колонки:" , list(df.columns))
                print("Данные:")
                print(df)
                print("======================")

                # Получаем углы из заголовков (все кроме первого столбца 'DN')
                angles = []
                for col in df.columns[1 :] :
                    try :
                        # Убираем возможные пробелы и преобразуем в число
                        angle = float(str(col).strip())
                        if 0 <= angle <= 90 :
                            angles.append(angle)
                    except (ValueError , TypeError) :
                        continue

                print(f"Найдены углы: {angles}")

                records_to_create = []

                # Обрабатываем каждую строку
                for index , row in df.iterrows() :
                    dn_value = row['DN']

                    # Пропускаем пустые DN
                    if pd.isna(dn_value) or dn_value == '' :
                        continue

                    try :
                        # Преобразуем DN в число и находим объект
                        dn_value_float = float(dn_value)
                        dn_obj = DnVariety.objects.get(diameter_metric=dn_value_float)
                        print(f"Обрабатывается DN: {dn_value_float}")

                    except (ValueError , TypeError) :
                        print(f"Невалидный DN: {dn_value}")
                        continue
                    except DnVariety.DoesNotExist :
                        print(f"DN {dn_value} не найден в базе")
                        continue

                    # Обрабатываем значения Kv для каждого угла
                    for angle in angles :
                        # Пробуем разные варианты ключей
                        kv_value = None

                        # Вариант 1: как строка (для целых чисел)
                        key1 = str(int(angle)) if angle == int(angle) else str(angle)
                        # Вариант 2: как есть в DataFrame
                        key2 = str(angle)

                        if key1 in df.columns :
                            kv_value = row[key1]
                        elif key2 in df.columns :
                            kv_value = row[key2]

                        # Пропускаем пустые значения
                        if pd.isna(kv_value) or kv_value == '' :
                            continue

                        try :
                            kv_float = float(kv_value)
                            print(f"  Угол {angle}°: Kv = {kv_float}")

                            # Создаем запись
                            records_to_create.append(
                                ValveLineModelKvData(
                                    valve_model_kv_data_table=valve_model ,
                                    valve_model_dn=dn_obj ,
                                    valve_model_openinig_angle=angle ,
                                    valve_model_kv=kv_float
                                )
                            )

                        except (ValueError , TypeError) as e :
                            print(f"  Невалидный Kv '{kv_value}': {e}")
                            continue

                print(f"\n=== РЕЗУЛЬТАТ ===")
                print(f"Найдено записей: {len(records_to_create)}")

                # Удаляем старые данные
                old_count = ValveLineModelKvData.objects.filter(
                    valve_model_kv_data_table=valve_model
                ).count()
                ValveLineModelKvData.objects.filter(
                    valve_model_kv_data_table=valve_model
                ).delete()
                print(f"Удалено старых записей: {old_count}")

                # Создаем новые записи
                if records_to_create :
                    ValveLineModelKvData.objects.bulk_create(records_to_create)
                    print(f"Создано новых записей: {len(records_to_create)}")
                    return True , _(f"Успешно импортировано {len(records_to_create)} записей Kvs")
                else :
                    print("Нет данных для импорта")
                    return False , _("Не найдено валидных данных Kvs в файле")

        except Exception as e :
            print(f"Общая ошибка при импорте: {str(e)}")
            import traceback
            traceback.print_exc()
            return False , _(f"Ошибка при импорте: {str(e)}")

    # Добавьте временно в admin_valve_model_kv_data_table.py
    def debug_urls(self , request) :
        """Временная функция для отладки URL"""
        from django.urls import reverse
        urls = {
            'changelist' : reverse('admin:valve_data_valvemodelkvdatatable_changelist') ,
            'add' : reverse('admin:valve_data_valvemodelkvdatatable_add') ,
            'change' : reverse('admin:valve_data_valvemodelkvdatatable_change' , args=[1]) ,
        }
        print(urls)  # Посмотрите в консоли
        return HttpResponse(str(urls))