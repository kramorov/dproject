# valve_data/services/dimension_import_service.py
import pandas as pd
from django.db import transaction

from params.models import DnVariety
import logging

# from ..models.dimension_models import (
#     ValveModelDimensionDataTable , DimensionTableColumn ,
#     DimensionTableRow , DimensionTableCell
# )

logger = logging.getLogger(__name__)


class DimensionTableImportService :
    pass
    """Сервис для импорта таблиц ВГХ из Excel"""
    #
    # def __init__(self , dimension_table) :
    #     if not isinstance(dimension_table , ValveModelDimensionDataTable) :
    #         raise ValueError("dimension_table должен быть экземпляром ValveModelDimensionDataTable")
    #
    #     self.dimension_table = dimension_table
    #     logger.info("Сервис импорта создан для таблицы: %s (ID: %s)" ,
    #                 dimension_table.name , dimension_table.pk)
    #
    # @transaction.atomic
    # def import_from_excel(self , excel_file) :
    #     """Импорт таблицы из Excel файла"""
    #     print("=" * 60 , flush=True)
    #     print("=== НАЧАЛО ИМПОРТА ДЛЯ ТАБЛИЦЫ ===" , flush=True)
    #     print(f"Таблица: {self.dimension_table.name} (ID: {self.dimension_table.pk})" , flush=True)
    #     print(f"Файл: {excel_file.name}, размер: {excel_file.size} байт" , flush=True)
    #
    #     try :
    #         # Читаем Excel
    #         print("1. Читаем Excel файл..." , flush=True)
    #         df = pd.read_excel(excel_file)
    #         print(f"   Прочитано: {len(df)} строк, {len(df.columns)} колонок" , flush=True)
    #         print(f"   Колонки: {list(df.columns)}" , flush=True)
    #
    #         if df.empty :
    #             print("   ОШИБКА: Файл пустой!" , flush=True)
    #             return False , "Файл пустой"
    #
    #         # Очищаем существующие данные
    #         print("2. Очищаем существующие данные..." , flush=True)
    #         rows_before = self.dimension_table.rows.count()
    #         columns_before = self.dimension_table.columns.count()
    #         print(f"   Было: {rows_before} строк, {columns_before} столбцов" , flush=True)
    #
    #         # Удаляем через правильные связи
    #         DimensionTableCell.objects.filter(
    #             row__dimension_table=self.dimension_table
    #         ).delete()
    #         self.dimension_table.rows.all().delete()
    #         self.dimension_table.columns.all().delete()
    #
    #         # Первый столбец - названия параметров
    #         print("3. Обрабатываем параметры..." , flush=True)
    #         parameter_names = df.iloc[: , 0].dropna().tolist()
    #         print(f"   Найдено параметров: {len(parameter_names)}" , flush=True)
    #         print(f"   Параметры: {parameter_names}" , flush=True)
    #
    #         # Остальные столбцы - DN значения
    #         dn_columns = df.columns[1 :]
    #         print(f"4. DN колонки: {list(dn_columns)}" , flush=True)
    #
    #         if not dn_columns :
    #             print("   ОШИБКА: Нет колонок с DN!" , flush=True)
    #             return False , "Нет колонок с DN"
    #
    #         # Создаем столбцы (DN) - ИЗМЕНЕНО: не создаем новые DN
    #         print("5. Создаем столбцы DN..." , flush=True)
    #         columns_mapping = {}
    #         missing_dns = []
    #
    #         for i , dn_name in enumerate(dn_columns) :
    #             dn_value = str(dn_name).replace('DN' , '').strip()
    #             print(f"   Обрабатываем: '{dn_name}' -> '{dn_value}'" , flush=True)
    #
    #             # Ищем DN - ИЗМЕНЕНО: не создаем новые
    #             try :
    #                 dn = DnVariety.objects.get(name=dn_value)
    #                 print(f"   Найден DN: {dn}" , flush=True)
    #
    #                 # Создаем столбец таблицы
    #                 column = DimensionTableColumn.objects.create(
    #                     dimension_table=self.dimension_table ,
    #                     dn=dn ,
    #                     column_order=i
    #                 )
    #                 columns_mapping[dn_name] = column
    #                 print(f"   Создан столбец: {column}" , flush=True)
    #
    #             except DnVariety.DoesNotExist :
    #                 error_msg = f"DN '{dn_value}' не найден в базе данных"
    #                 print(f"   ОШИБКА: {error_msg}" , flush=True)
    #                 missing_dns.append(dn_value)
    #
    #         # Проверяем, есть ли отсутствующие DN
    #         if missing_dns :
    #             error_message = f"Следующие DN не найдены в базе данных: {', '.join(missing_dns)}. Добавьте их в справочник DN перед импортом."
    #             print(f"6. ОШИБКА: {error_message}" , flush=True)
    #             return False , error_message
    #
    #         print(f"6. Создано столбцов: {len(columns_mapping)}" , flush=True)
    #
    #         # Создаем строки и ячейки
    #         print("7. Создаем строки и ячейки..." , flush=True)
    #         created_rows = 0
    #         created_cells = 0
    #
    #         for row_index , param_name in enumerate(parameter_names) :
    #             if pd.isna(param_name) or not str(param_name).strip() :
    #                 continue
    #
    #             param_name_str = str(param_name).strip()
    #             print(f"   Создаем строку {row_index}: '{param_name_str}'" , flush=True)
    #
    #             # Создаем строку
    #             row = DimensionTableRow.objects.create(
    #                 dimension_table=self.dimension_table ,
    #                 parameter_name=param_name_str ,
    #                 row_order=row_index
    #             )
    #             created_rows += 1
    #
    #             # Создаем ячейки
    #             row_cells_created = 0
    #             for col_name , column in columns_mapping.items() :
    #                 cell_value = df.iloc[row_index][col_name]
    #
    #                 if pd.isna(cell_value) or cell_value == '' :
    #                     continue
    #
    #                 try :
    #                     cell_value_float = float(cell_value)
    #                     DimensionTableCell.objects.create(
    #                         row=row ,
    #                         column=column ,
    #                         value=cell_value_float
    #                     )
    #                     created_cells += 1
    #                     row_cells_created += 1
    #                     print(f"      Ячейка DN{column.dn.name}: {cell_value_float}" , flush=True)
    #                 except (ValueError , TypeError) as e :
    #                     print(f"      ОШИБКА ячейки {col_name}: '{cell_value}' - {e}" , flush=True)
    #
    #             print(f"   Создано ячеек для строки: {row_cells_created}" , flush=True)
    #
    #         # Финальная статистика
    #         final_rows = self.dimension_table.rows.count()
    #         final_columns = self.dimension_table.columns.count()
    #         final_cells = DimensionTableCell.objects.filter(
    #             row__dimension_table=self.dimension_table
    #         ).count()
    #
    #         print("=" * 60 , flush=True)
    #         print("=== ИМПОРТ ЗАВЕРШЕН ===" , flush=True)
    #         print(f"Создано: {created_rows} строк, {created_cells} ячеек" , flush=True)
    #         print(f"В таблице теперь: {final_rows} строк, {final_columns} столбцов, {final_cells} ячеек" , flush=True)
    #         print("=" * 60 , flush=True)
    #
    #         return True , "Импорт успешно завершен"
    #
    #     except Exception as e :
    #         print("=" * 60 , flush=True)
    #         print("=== ОШИБКА ИМПОРТА ===" , flush=True)
    #         print(f"Ошибка: {str(e)}" , flush=True)
    #         import traceback
    #         traceback.print_exc()
    #         print("=" * 60 , flush=True)
    #         return False , f"Ошибка импорта: {str(e)}"
