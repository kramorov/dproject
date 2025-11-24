# valve_line_data_table_import_export.py
import io
import base64
import pandas as pd
from django.http import HttpResponse , HttpResponseServerError
from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from params.models import DnVariety , PnVariety, MeasureUnits , StemSize , ValveTypes , MountingPlateTypes
from ..models import  ValveLine , ValveLineModelData


def export_valve_line_data_table_to_excel(valve_line_data_table):
    """Экспорт всех ValveLineModelData для определенного ValveModelDataTable в Excel"""

    # Получаем все модели для данной серии
    valve_models = ValveLineModelData.objects.filter(
        valve_model_data_table=valve_line_data_table
    ).select_related(
        'valve_model_stem_size'
    ).prefetch_related('valve_model_mounting_plate')
    print(f"DEBUG: valve_models type: {type(valve_models)}")  # Должен быть QuerySet
    print(f"DEBUG: valve_models count: {valve_models.count()}")  # Количество объектов

    # Подготавливаем данные
    data = []
    for obj in valve_models:
        print(f"DEBUG: current valve_model: {obj}")
        # Получаем названия монтажных площадок
        mounting_plates = ", ".join([plate.code for plate in
                                     obj.valve_model_mounting_plate.all()]) if obj.valve_model_mounting_plate.exists() else ""

        row = {
            'Артикул' : obj.name or "" ,
            'DN': obj.valve_model_dn.code if obj.valve_model_dn else  "",
            'PN': obj.valve_model_pn.code if obj.valve_model_pn else  "",
            # 'Единица измерения PN code': obj.valve_model_pn_measure_unit.code if obj.valve_model_pn_measure_unit else "",
            'Момент откр': obj.valve_model_torque_to_open or "",
            'Момент закр': obj.valve_model_torque_to_close or "",
            'Усилие на закр' : obj.valve_model_thrust_to_close or "" ,
            'Оборотов': obj.valve_model_rotations_to_open or "",
            'Шток': obj.valve_model_stem_size.code if obj.valve_model_stem_size else "",
            'Монт.площадка' : mounting_plates ,
            'Высота Шток' : obj.valve_model_stem_height or "" ,
            'Строит.длина' : obj.valve_model_construction_length or "" ,


        }
        print(f"DEBUG: current row: {row}")
        data.append(row)
    #
    # # Создаем DataFrame
    df = pd.DataFrame(data)

    # Если нет данных, создаем пустой DataFrame с колонками
    if df.empty:
        df = pd.DataFrame(columns=[
            'Артикул', 'DN', 'PN', 'Момент откр', 'Момент закр',
            'Усилие на закр', 'Оборотов',
            'Монт.площадка', 'Высота Шток', 'Строит.длина',
        ])

    # Создаем Excel файл в памяти
    output = io.BytesIO()

    try :
        with pd.ExcelWriter(output , engine='openpyxl') as writer :
            df.to_excel(writer , sheet_name='Модели арматуры' , index=False)

            # Форматирование
            workbook = writer.book
            worksheet = writer.sheets['Модели арматуры']

            # Автоподбор ширины колонок
            for column in worksheet.columns :
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column :
                    try :
                        if len(str(cell.value)) > max_length :
                            max_length = len(str(cell.value))
                    except :
                        pass
                adjusted_width = min(max_length + 2 , 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # writer автоматически сохраняется при выходе из контекста

        # Получаем данные после закрытия контекста
        excel_data = output.getvalue()
        output.seek(0)

        print(f"DEBUG: Excel data size: {len(excel_data)} bytes")

        # Проверяем, что данные не пустые
        if len(excel_data) == 0 :
            print("DEBUG: WARNING - Excel data is empty!")
            # Создаем тестовый файл
            test_df = pd.DataFrame({'Ошибка' : ['Нет данных для экспорта']})
            test_output = io.BytesIO()
            with pd.ExcelWriter(test_output , engine='openpyxl') as test_writer :
                test_df.to_excel(test_writer , index=False)
            excel_data = test_output.getvalue()
            test_output.close()

        response = HttpResponse(
            excel_data ,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="valve_model_data_table_{valve_line_data_table.code}.xlsx"'

        print(f"DEBUG: Response created successfully, size: {len(excel_data)} bytes")
        return response

    except Exception as e :
        print(f"DEBUG: Error creating Excel: {e}")
        import traceback
        traceback.print_exc()

        # Возвращаем ошибку с информацией
        error_df = pd.DataFrame({'Ошибка' : [f'Не удалось создать файл: {str(e)}']})
        error_output = io.BytesIO()
        with pd.ExcelWriter(error_output , engine='openpyxl') as error_writer :
            error_df.to_excel(error_writer , index=False)
        error_data = error_output.getvalue()
        error_output.close()

        response = HttpResponse(
            error_data ,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="error_{valve_line_data_table.code}.xlsx"'
        return response

    finally :
        output.close()


# НОВЫЕ ФУНКЦИИ ИМПОРТА
def import_valve_line_data_table_from_excel(valve_model_data_table , excel_file , request) :
    """Импорт ValveLineModelData из Excel файла - основная функция"""
    print(
        f"DEBUG: Import function called, confirm_delete: {request.POST.get('confirm_delete')}, excel_file: {excel_file}")

    # Если это подтверждение, у нас уже есть данные в сессии
    if request.POST.get('confirm_delete') :
        print("DEBUG: Processing confirmed import")
        return process_confirmed_import(valve_model_data_table , request)
    else :
        print("DEBUG: Processing initial import")
        if excel_file is None :
            return 'error' , "Файл не найден, и не был загружен"
        return process_initial_import(valve_model_data_table , excel_file , request)


def process_initial_import(valve_model_data_table , excel_file , request) :
    """Обработка первоначального импорта"""
    print("DEBUG: Starting initial import processing")

    try :
        # Читаем Excel файл
        df = pd.read_excel(excel_file)
        print(f"DEBUG: Read Excel file with {len(df)} rows, columns: {list(df.columns)}")

        # Проверяем обязательные колонки
        required_columns = ['DN' , 'PN']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns :
            error_msg = _("Отсутствуют обязательные колонки: {}").format(", ".join(missing_columns))
            print(f"DEBUG: Missing columns: {missing_columns}")
            return 'error' , error_msg
        else:
            print(f"All required columns: {required_columns} are found.")

        # Проверяем, есть ли данные в файле
        if df.empty :
            print("DEBUG: Excel file is empty")
            return 'error' , "Файл не содержит данных"
        else:
            print(f"DEBUG: Test is OK - file is not empty.")

        # Анализируем комбинации для удаления
        combinations_to_delete , combinations_display = analyze_import_file(valve_model_data_table , df)
        print(f"DEBUG: Found {len(combinations_to_delete)} combinations to delete")

        # Если есть комбинации для удаления, запрашиваем подтверждение
        if combinations_to_delete :
            print("DEBUG: Saving file to session and requesting confirmation")

            # Сохраняем файл и данные в сессии (кодируем в base64)
            excel_file.seek(0)
            excel_file_data = excel_file.read()

            encoded_file_data = base64.b64encode(excel_file_data).decode('utf-8')

            request.session['import_data'] = {
                'valve_model_data_table_id' : valve_model_data_table.id ,
                'file_data' : encoded_file_data ,
                'file_name' : excel_file.name ,
                'combinations_to_delete' : list(combinations_to_delete)
            }
            request.session.modified = True
            print("DEBUG: Data saved to session")

            return 'confirm_delete' , combinations_display

        # Если удалять нечего, сразу обрабатываем
        print("DEBUG: No combinations to delete, processing immediately")
        excel_file.seek(0)
        return process_data_import(valve_model_data_table , excel_file , [])

    except Exception as e :
        print(f"DEBUG: Error in initial import: {e}")
        import traceback
        traceback.print_exc()
        return 'error' , str(e)


def process_confirmed_import(valve_model_data_table , request) :
    """Обработка подтвержденного импорта"""
    print("DEBUG: Starting confirmed import processing")

    try :
        import_data = request.session.get('import_data' , {})
        if not import_data :
            error_msg = "Данные сессии утеряны. Пожалуйста, загрузите файл заново."
            print("DEBUG: Session data lost")
            return 'error' , error_msg

        if import_data.get('valve_line_data_table_id') != valve_model_data_table.id :
            error_msg = "Несоответствие данных сессии. Пожалуйста, загрузите файл заново."
            print("DEBUG: valve_line_data_table ID mismatch in session")
            return 'error' , error_msg

        # Восстанавливаем файл из сессии
        encoded_file_data = import_data['file_data']
        file_data = base64.b64decode(encoded_file_data)
        excel_file = BytesIO(file_data)
        excel_file.name = import_data['file_name']
        combinations_to_delete = import_data['combinations_to_delete']

        print(f"DEBUG: Restored file '{excel_file.name}' with {len(combinations_to_delete)} combinations to delete")

        # Очищаем сессию
        if 'import_data' in request.session :
            del request.session['import_data']
            request.session.modified = True
            print("DEBUG: Cleared session data")

        return process_data_import(valve_model_data_table , excel_file , combinations_to_delete)

    except Exception as e :
        print(f"DEBUG: Error in confirmed import: {e}")
        import traceback
        traceback.print_exc()
        return 'error' , str(e)


def analyze_import_file(valve_model_data_table , df) :
    """Анализирует DataFrame и возвращает комбинации для удаления"""
    print("DEBUG: Analyzing import file for combinations to delete")

    def find_dn_by_code_or_diameter(search_code) :
        if pd.isna(search_code) :
            return None
        code_str = str(search_code).strip()
        try :
            return DnVariety.objects.get(code=code_str , is_active=True)
        except DnVariety.DoesNotExist :
            pass
        try :
            dn_value = float(code_str)
            return DnVariety.objects.get(diameter_metric=dn_value , is_active=True)
        except (DnVariety.DoesNotExist , ValueError) :
            pass
        try :
            return DnVariety.objects.get(name=code_str , is_active=True)
        except DnVariety.DoesNotExist :
            pass
        return None

    def find_pn_by_code_or_pressure(search_code) :
        if pd.isna(search_code) :
            return None
        code_str = str(search_code).strip()
        try :
            return PnVariety.objects.get(code=code_str , is_active=True)
        except PnVariety.DoesNotExist :
            pass
        try :
            pn_value = float(code_str)
            return PnVariety.objects.get(pressure_bar=pn_value , is_active=True)
        except (PnVariety.DoesNotExist , ValueError) :
            pass
        try :
            return PnVariety.objects.get(name=code_str , is_active=True)
        except PnVariety.DoesNotExist :
            pass
        return None

    # Получаем существующие модели для этого ValveLineModelData
    existing_models = ValveLineModelData.objects.filter(valve_model_data_table=valve_model_data_table)
    existing_dn_pn_combinations = set(
        (model.valve_model_dn_id , model.valve_model_pn_id)
        for model in existing_models
        if model.valve_model_dn_id and model.valve_model_pn_id
    )
    print(f"DEBUG: Found {len(existing_dn_pn_combinations)} existing DN/PN combinations")

    # Получаем комбинации DN/PN из файла
    imported_dn_pn_combinations = set()
    for index , row in df.iterrows() :
        dn_code = row.get('DN')
        pn_code = row.get('PN')

        dn_obj = find_dn_by_code_or_diameter(dn_code)
        pn_obj = find_pn_by_code_or_pressure(pn_code)

        if dn_obj and pn_obj :
            imported_dn_pn_combinations.add((dn_obj.id , pn_obj.id))

    # Находим комбинации для удаления
    combinations_to_delete = existing_dn_pn_combinations - imported_dn_pn_combinations
    print(f"DEBUG: Found {len(combinations_to_delete)} combinations to delete")

    # Получаем объекты для отображения
    combinations_display = []
    for dn_id , pn_id in combinations_to_delete :
        try :
            dn_obj = DnVariety.objects.get(id=dn_id)
            pn_obj = PnVariety.objects.get(id=pn_id)
            combinations_display.append(
                (dn_obj.code or dn_obj.name , pn_obj.code or pn_obj.name))
        except (DnVariety.DoesNotExist , PnVariety.DoesNotExist) :
            continue

    return list(combinations_to_delete) , combinations_display


def process_data_import(valve_model_data_table , excel_file , combinations_to_delete) :
    """Основная логика импорта данных"""
    print("DEBUG: Starting data import processing")

    try :
        # Читаем Excel файл
        df = pd.read_excel(excel_file)
        print(f"DEBUG: Processing {len(df)} rows from Excel file")

        def find_dn_by_code_or_diameter(search_code) :
            if pd.isna(search_code) :
                return None
            code_str = str(search_code).strip()
            try :
                return DnVariety.objects.get(code=code_str , is_active=True)
            except DnVariety.DoesNotExist :
                pass
            try :
                dn_value = float(code_str)
                return DnVariety.objects.get(diameter_metric=dn_value , is_active=True)
            except (DnVariety.DoesNotExist , ValueError) :
                pass
            try :
                return DnVariety.objects.get(name=code_str , is_active=True)
            except DnVariety.DoesNotExist :
                pass
            return None

        def find_pn_by_code_or_pressure(search_code) :
            if pd.isna(search_code) :
                return None
            code_str = str(search_code).strip()
            try :
                return PnVariety.objects.get(code=code_str , is_active=True)
            except PnVariety.DoesNotExist :
                pass
            try :
                pn_value = float(code_str)
                return PnVariety.objects.get(pressure_bar=pn_value , is_active=True)
            except (PnVariety.DoesNotExist , ValueError) :
                pass
            try :
                return PnVariety.objects.get(name=code_str , is_active=True)
            except PnVariety.DoesNotExist :
                pass
            return None

        # Вся логика внутри transaction.atomic()
        try :
            with transaction.atomic() :
                # Удаляем старые комбинации
                if combinations_to_delete :
                    print(f"DEBUG: Deleting {len(combinations_to_delete)} old combinations")
                    for dn_id , pn_id in combinations_to_delete :
                        deleted_count = ValveLineModelData.objects.filter(
                            valve_model_data_table=valve_model_data_table ,
                            valve_model_dn_id=dn_id ,
                            valve_model_pn_id=pn_id
                        ).delete()
                        print(f"DEBUG: Deleted combinations for DN_id {dn_id}, PN_id {pn_id}")

                # Обрабатываем каждую строку файла
                success_count = 0
                error_count = 0
                errors = []

                for row_number , (index , row) in enumerate(df.iterrows() , start=2) :
                    try :
                        dn_code = row.get('DN')
                        pn_code = row.get('PN')

                        # Пропускаем строки без DN или PN
                        if pd.isna(dn_code) or pd.isna(pn_code) :
                            errors.append(f"Строка {row_number}: отсутствует DN_code или PN_code")
                            error_count += 1
                            continue

                        # Ищем DN и PN объекты
                        dn_obj = find_dn_by_code_or_diameter(dn_code)
                        pn_obj = find_pn_by_code_or_pressure(pn_code)

                        if not dn_obj :
                            errors.append(f"Строка {row_number}: DN '{dn_code}' не найден")
                            error_count += 1
                            continue

                        if not pn_obj :
                            errors.append(f"Строка {row_number}: PN '{pn_code}' не найден")
                            error_count += 1
                            continue

                        # Ищем существующую запись или создаем новую
                        valve_model , created = ValveLineModelData.objects.get_or_create(
                            valve_model_data_table=valve_model_data_table ,
                            valve_model_dn=dn_obj ,
                            valve_model_pn=pn_obj ,
                            defaults={'name' : row.get('Артикул' , '')}
                        )

                        # Обновляем числовые поля DN и PN
                        # valve_model.valve_model_dn = dn_obj.diameter_metric
                        # valve_model.valve_model_pn = float(pn_obj.pressure_bar)

                        # Единица измерения PN
                        # pn_measure_unit_code = row.get('Единица измерения PN code')
                        # if pd.notna(pn_measure_unit_code) :
                        #     try :
                        #         pn_measure_unit = MeasureUnits.objects.get(code=str(pn_measure_unit_code).strip())
                        #         valve_model.valve_model_pn_measure_unit = pn_measure_unit
                        #     except MeasureUnits.DoesNotExist :
                        #         print(f"DEBUG: MeasureUnits not found for code: {pn_measure_unit_code}")

                        # Размер штока
                        stem_size_code = row.get('Шток')
                        if pd.notna(stem_size_code) :
                            try :
                                stem_size = StemSize.objects.get(code=str(stem_size_code).strip())
                                valve_model.valve_model_stem_size = stem_size
                            except StemSize.DoesNotExist :
                                print(f"DEBUG: StemSize not found for code: {stem_size_code}")

                        # Монтажные площадки
                        mounting_plates_codes = row.get('Монт.площадка')
                        if pd.notna(mounting_plates_codes) :
                            try :
                                plate_codes = [code.strip() for code in str(mounting_plates_codes).split(',') if
                                               code.strip()]
                                plates = MountingPlateTypes.objects.filter(code__in=plate_codes)
                                valve_model.valve_model_mounting_plate.set(plates)
                            except Exception as e :
                                print(f"DEBUG: Error setting mounting plates: {e}")

                        # Простые поля
                        simple_fields = {
                            'valve_model_torque_to_open' : 'Момент откр' ,
                            'valve_model_torque_to_close' : 'Момент закр' ,
                            'valve_model_rotations_to_open' : 'Оборотов' ,
                            'name' : 'Артикул',
                            'valve_model_thrust_to_close' : 'Усилие на закр',
                            'valve_model_construction_length': 'Строит.длина',
                            'valve_model_stem_height': 'Высота Шток'
                        }

                        for field , column in simple_fields.items() :
                            value = row.get(column)
                            if pd.notna(value) :
                                setattr(valve_model , field , value)

                        valve_model.save()
                        success_count += 1
                        print(f"DEBUG: Successfully imported model {valve_model.name}")

                    except Exception as e :
                        error_msg = f"Строка {row_number}: {str(e)}"
                        errors.append(error_msg)
                        error_count += 1
                        print(f"DEBUG: Error in row {row_number}: {e}")

                # Формируем результат
                print(f"DEBUG: Import completed - Success: {success_count}, Errors: {error_count}")

                if error_count == 0 :
                    result_msg = f"Успешно импортировано {success_count} записей"
                    return 'success' , result_msg
                else :
                    error_message = f"Успешно: {success_count}, Ошибок: {error_count}. Первые ошибки: " + "; ".join(
                        errors[:5])
                    return 'partial_success' , error_message

        except Exception as e :
            # Ошибки внутри transaction.atomic()
            print(f"DEBUG: Error in atomic block: {e}")
            import traceback
            traceback.print_exc()
            return 'error' , f"Ошибка транзакции: {str(e)}"

    except Exception as e :
        # Ошибки вне transaction.atomic() (например, чтение файла)
        print(f"DEBUG: Error in data import (outside atomic): {e}")
        import traceback
        traceback.print_exc()
        return 'error' , str(e)