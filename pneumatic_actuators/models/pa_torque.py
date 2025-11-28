# pneumatic_actuators/models/pa_torque.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse

from datetime import datetime
import logging

from pneumatic_actuators.models.pa_body import PneumaticActuatorBody
from pneumatic_actuators.models.pa_params import PneumaticActuatorSpringsQty
from params.models import PneumaticAirSupplyPressure

logger = logging.getLogger(__name__)


class BodyThrustTorqueTable(models.Model):
    """ Значения момента или усилия при заданном количестве пружин и давлении питания
        pressure - давление питания, code='spring' - для только пружин
        spring_qty - количество пружин,  code='DA' - привод без пружин, двойного действия
        body - модель (типоразмер) привода
        BTO (Beginning Torque to Open): Начальный момент открытия (момент страгивания для открытия).
            Это значение крутящего момента, необходимое для вывода запорного элемента арматуры из положения полного
            закрытия. Часто это наибольшее требуемое усилие из-за прилипания или уплотнения затвора.
        RTO (Running Torque to Open): Промежуточный момент открытия (или рабочий момент открытия).
            Это крутящий момент, необходимый во время основного движения запорного элемента (обычно в диапазоне
            от 0° до 90°, исключая крайние положения).
        ETO (End Torque to Open): Конечный момент открытия. Это крутящий момент, необходимый для достижения
            полностью открытого положения.
        BTC (Beginning Torque to Close): Начальный момент закрытия (момент страгивания для закрытия).
        RTC (Running Torque to Close): Промежуточный момент закрытия.
        ETC (End Torque to Close): Конечный момент закрытия (момент посадки затвора в уплотнение).
        В таблице указываются значения для НЗ привода - BTO, RTO, ETO
        При импорте для приводов с spring_qty.code='DA' все значения bto, rto, eto устанавливаются одинаковыми
            для приводов ДА имеет смысл только одно значение при заланном давлении
        Для НО привода при печати в заголовке значения должны инвертироваться на BTC, RTC, ETC
        геттеры:
        get_min_max_pressure_list_for_body(body, min_pressure, max_pressure) -возвращает список
            справочника PneumaticAirSupplyPressure, значение которых меньше или равно min_pressure,
            и больше или равно max_pressure
        get_torque_thrust_values(body_list, pressure_list default=null, spring_qty default=null или точное значение справочника,
         ncno default='NO')
         body_list - список ссылок на модель PneumaticActuatorBody, может состоять из одного элемента
         если pressure_list =null, spring_qty =null то возвращает
         структуру: заголовок и матрицу
         заголовок состоит из двух строк
            Первая строка - найденное в таблице давление, отсортированное по возрастанию sorting_order. Послений столбец "Пружины"
            Вторая строка - для каждого давления из первой строки делаем 1, 2 или 3 столбца значений:
                1 столбец - если привод DA - указываем bto
                2 стобца - если привод SR  и его тип шестерня-рейка - указываем bto, eto
                3 стоблца - если привод SR  и его тип кулисный (skotch-yoke) - указываем bto, rto, eto
                    Тип привода определяем через поле body, далее - PneumaticActuatorBody.model_line,
                    далее - PneumaticActuatorModelLine.pneumatic_actuator_construction_variety
            Первый столбец данных - body.code
            Второй стобец данных - spring_qty.code
            дальнейшие столбцы содержат данные из полей bto, rto, eto этой модели, отобранные в соответствии с заголовками
            т.е. какие поля брать и в каком порядке выводить.
        find_body_for_pressure_thrust_or_torque(pressure_min, pressure_max, thrust_or_torque, tolerance, PneumaticActuatorVariety)
            если PneumaticActuatorVariety.code='DA' то  возвращает список моделей, у которых
                есть pressure меньше или равно pressure_min, и значение bto
        """
    body = models.ForeignKey(PneumaticActuatorBody, on_delete=models.SET_NULL,
                             null=True, blank=True,  # ← ДОБАВЬТЕ ЭТО
                             related_name='body_thrust_torque_table',
                             verbose_name=_("Модель"),
                             help_text=_("Модель корпуса привода"))
    pressure = models.ForeignKey(PneumaticAirSupplyPressure, on_delete=models.SET_NULL,
                                 null=True, blank=True,  # ← ДОБАВЬТЕ ЭТО
                                 related_name='body_thrust_torque_table',
                                 verbose_name=_("Давление"),
                                 help_text=_("Давление питания или spring - для пружин"))
    spring_qty = models.ForeignKey(PneumaticActuatorSpringsQty, on_delete=models.SET_NULL,
                                   null=True, blank=True,  # ← ДОБАВЬТЕ ЭТО
                                   related_name='body_thrust_torque_table',
                                   verbose_name=_("Пружин / DA"),
                                   help_text=_("Количество пружин или DA"))
    bto = models.DecimalField(max_digits=10, decimal_places=1, verbose_name=_("Момент/усилие BTO"),
                              help_text=_("BTO Момент/усилие страгивания для открытия"))
    rto = models.DecimalField(max_digits=10, decimal_places=1, verbose_name=_("Момент/усилие RTC(MID)"),
                              help_text=_("RTC Момент/усилие в среднем положении"))
    eto = models.DecimalField(max_digits=10, decimal_places=1, verbose_name=_("Момент/усилие BTC"),
                              help_text=_("ETO Конечный Момент/Усилие открытия"))

    class Meta:
        verbose_name = _("Таблица моментов/усилий пневмоприводов")
        verbose_name_plural = _("Таблица моментов/усилий пневмоприводов")

    def __str__(self):
        return f"Таблица моментов/усилий для {self.body.name}"

    @classmethod
    def get_torque_thrust_values(cls, body_list, pressure_list=None, spring_qty=None, ncno='NO'):
        """
        Возвращает структурированные данные для таблицы моментов/усилий

        Args:
            body_list: список объектов PneumaticActuatorBody
            pressure_list: список объектов PneumaticAirSupplyPressure (None = все)
            spring_qty: конкретный объект PneumaticActuatorSpringsQty (None = все)
            ncno: 'NO' или 'NC' - тип привода
        """
        print(f"get_torque_thrust_values got arguments: body_list={body_list}, pressure_list={pressure_list}, spring_qty={spring_qty}")

        import logging
        logger = logging.getLogger(__name__)

        # ПРОВЕРЯЕМ РЕАЛЬНЫЙ ТИП, А НЕ СТРОКОВОЕ ПРЕДСТАВЛЕНИЕ
        logger.info(f"🔧 === REAL TORQUE DEBUG ===")
        logger.info(f"🔧 spring_qty REAL type: {type(spring_qty)}")
        if spring_qty:
            logger.info(f"🔧 spring_qty id: {spring_qty.id}")
            # ПРОВЕРЯЕМ ВСЕ ВОЗМОЖНЫЕ АТРИБУТЫ
            logger.info(f"🔧 spring_qty attributes: {[attr for attr in dir(spring_qty) if not attr.startswith('_')]}")
            logger.info(f"🔧 spring_qty name: {getattr(spring_qty, 'name', 'No name')}")
            logger.info(f"🔧 spring_qty springs_qty: {getattr(spring_qty, 'springs_qty', 'No springs_qty')}")
            logger.info(f"🔧 spring_qty encoding: {getattr(spring_qty, 'encoding', 'No encoding')}")
            logger.info(f"🔧 spring_qty __str__: {str(spring_qty)}")

        try:
            # Базовый запрос
            queryset = cls.objects.filter(body__in=body_list)
            initial_count = queryset.count()
            logger.info(f"🔧 Initial queryset count: {initial_count}")

            # ФИЛЬТРУЕМ
            if spring_qty:
                from pneumatic_actuators.models import PneumaticActuatorSpringsQty
                if isinstance(spring_qty, PneumaticActuatorSpringsQty):
                    filtered_queryset = queryset.filter(spring_qty=spring_qty)
                    filtered_count = filtered_queryset.count()
                    logger.info(f"🔧 After spring filter - count: {filtered_count}")

                    if filtered_count == 0:
                        logger.warning(
                            f"🔧 ⚠️  No data found for: body={body_list[0].code}, spring_qty_id={spring_qty.id}")
                        # Логируем какие spring_qty вообще есть в таблице для этого body
                        available_springs = cls.objects.filter(
                            body=body_list[0]
                        ).values_list('spring_qty_id', 'spring_qty__springs_qty').distinct()
                        logger.info(f"🔧 Available springs for {body_list[0].code}: {list(available_springs)}")

                    # Логируем найденные данные
                    for item in filtered_queryset[:5]:  # первые 5 записей
                        logger.info(
                            f"🔧 Found data: body={item.body.code}, spring={item.spring_qty.id}, pressure={item.pressure}")
                else:
                    logger.error(f"🔧 ❌ WRONG TYPE: {type(spring_qty)}")
            else:
                logger.info("🔧 No spring_qty filter applied")
        except:
            pass

        try:
            # Базовый запрос
            queryset = cls.objects.filter(body__in=body_list)

            # Фильтрация по давлению если указано
            if pressure_list:
                queryset = queryset.filter(pressure__in=pressure_list)

            # Фильтрация по количеству пружин если указано
            if spring_qty:
                queryset = queryset.filter(spring_qty=spring_qty)

            # Получаем ВСЕ данные одним запросом
            all_data = queryset.select_related(
                'body', 'pressure', 'spring_qty',
                'body__model_line',
                'body__model_line__pneumatic_actuator_construction_variety'
            ).order_by('body__sorting_order', 'spring_qty__sorting_order', 'pressure__sorting_order')

            if not all_data:
                return {
                    'headers': [[], []],
                    'data': [],
                    'pressures': [],
                    'bodies': []
                }

            # Получаем уникальные давления из данных
            pressures = sorted(
                set(item.pressure for item in all_data if item.pressure),
                key=lambda x: x.sorting_order
            )

            # Получаем уникальные пружины из данных
            springs = sorted(
                set(item.spring_qty for item in all_data if item.spring_qty),
                key=lambda x: x.sorting_order
            )

            # Получаем уникальные корпуса из данных
            bodies = sorted(
                set(item.body for item in all_data if item.body),
                key=lambda x: x.sorting_order
            )

            # Формируем заголовки как в export_table_template
            header_row1 = ['Корпус', 'Пружины']  # Первая строка заголовков
            header_row2 = ['Код', 'Код']  # Вторая строка заголовков

            # Добавляем столбцы для каждого давления (BTO, RTO, ETO)
            for pressure in pressures:
                # Первая строка: название давления объединенное на 3 столбца
                header_row1.extend([str(pressure), '', ''])
                # Вторая строка: BTO, RTO, ETO
                header_row2.extend(['BTO', 'RTO', 'ETO'])

            # Формируем строки данных как в export_table_template
            data_rows = []

            for body in bodies:
                for spring in springs:
                    # Начало строки: код корпуса, код пружины
                    row_data = [body.code, spring.code]

                    # Для каждого давления добавляем BTO, RTO, ETO
                    for pressure in pressures:
                        # Ищем данные для этой комбинации
                        torque_data = next(
                            (item for item in all_data
                             if item.body == body and item.spring_qty == spring and item.pressure == pressure),
                            None
                        )

                        if torque_data:
                            # Если данные есть - заполняем все три значения
                            row_data.extend([
                                float(torque_data.bto) if torque_data.bto else None,
                                float(torque_data.rto) if torque_data.rto else None,
                                float(torque_data.eto) if torque_data.eto else None
                            ])
                        else:
                            # Если данных нет - пустые значения
                            row_data.extend([None, None, None])

                    data_rows.append(row_data)
            return_data = {
                'headers': [header_row1, header_row2],
                'data': data_rows,
                'pressures': [
                    {
                        'id': pressure.id,
                        'code': pressure.code,
                        'name': str(pressure),
                        'value': getattr(pressure, 'value', None),
                        'unit': getattr(pressure, 'unit', None)
                    }
                    for pressure in pressures
                ],
                'bodies': [
                    {
                        'id': body.id,
                        'code': body.code,
                        'name': body.name
                    }
                    for body in bodies
                ],
                'springs': [
                    {
                        'id': spring.id,
                        'code': spring.code,
                        'name': spring.springs_qty
                    }
                    for spring in springs
                ]
            }
            logger.info(f"return_data: {return_data}")
            return return_data

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_torque_thrust_values: {e}")
            return {
                'headers': [[], []],
                'data': [],
                'pressures': [],
                'bodies': [],
                'springs': [],
                'error': str(e)
            }

    @staticmethod
    def export_table_template(pressure_min=2.5, pressure_max=8.0, springs_min=5, springs_max=12, output_path=None):
        """
        Экспорт таблицы моментов/усилий в Excel файл
        """
        from params.models import PneumaticAirSupplyPressure
        from pneumatic_actuators.models import PneumaticActuatorSpringsQty
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Получаем давления в диапазоне
            pressures = PneumaticAirSupplyPressure.objects.filter(
                Q(pressure_bar__gte=pressure_min) & Q(pressure_bar__lte=pressure_max)
            ).order_by('sorting_order')
            # добавляем давление с кодом 'spring' если оно существует
            spring_pressure = PneumaticAirSupplyPressure.objects.filter(code='spring').first()
            if spring_pressure and spring_pressure not in pressures:
                pressures = list(pressures) + [spring_pressure]

            # Получаем количества пружин в диапазоне
            if hasattr(PneumaticActuatorSpringsQty, 'value'):
                springs = PneumaticActuatorSpringsQty.objects.filter(
                    Q(value__gte=springs_min) & Q(value__lte=springs_max)
                ).order_by('sorting_order')
            else:
                # Если поля value нет, берем все активные пружины
                springs = PneumaticActuatorSpringsQty.objects.filter(
                    is_active=True
                ).order_by('sorting_order')

            # Получаем все корпуса
            bodies = PneumaticActuatorBody.objects.filter(is_active=True).order_by('sorting_order')

            # ИСПРАВЛЕНИЕ: получаем ВСЕ существующие данные для фильтрации
            all_torque_data = BodyThrustTorqueTable.objects.filter(
                body__in=bodies,
                pressure__in=pressures,
                spring_qty__in=springs
            ).select_related('body', 'pressure', 'spring_qty')

            # Создаем workbook
            wb = Workbook()

            # Стили для заголовков
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

            # Создаем основной лист с данными
            ws = wb.active
            ws.title = "Моменты_усилия"

            # ИСПРАВЛЕНИЕ: создаем заголовки таблицы с двумя строками
            headers_row1 = ['', '', '']  # Пустые для корпуса и пружины
            headers_row2 = ['Код корпуса', 'Название корпуса', 'Код пружины']

            # Добавляем столбцы для каждого давления (BTO, RTO, ETO для каждого давления)
            for pressure in pressures:
                # Первая строка: КОД давления объединенный на 3 столбца
                headers_row1.extend([pressure.code, pressure.code, pressure.code])
                # Вторая строка: BTO, RTO, ETO
                headers_row2.extend(['BTO', 'RTO', 'ETO'])

            # Записываем заголовки - первая строка
            for col_idx, header in enumerate(headers_row1, 1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill

            # Вторая строка заголовков
            for col_idx, header in enumerate(headers_row2, 1):
                cell = ws.cell(row=2, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill

            # ИСПРАВЛЕНИЕ: заполняем таблицу всеми комбинациями (начинаем с 3 строки)
            row_idx = 3

            # Получаем давление с кодом 'spring' для данных пружин
            spring_pressure = PneumaticAirSupplyPressure.objects.filter(code='spring').first()

            for body in bodies:
                for spring in springs:
                    # Начало строки: код корпуса, название, код пружины
                    row_data = [body.code, body.name, spring.code]

                    # Для каждого давления добавляем BTO, RTO, ETO
                    for pressure in pressures:
                        # Ищем данные для этой комбинации
                        torque_data = all_torque_data.filter(
                            body=body,
                            pressure=pressure,
                            spring_qty=spring
                        ).first()

                        if torque_data:
                            # Если данные есть - заполняем
                            row_data.extend([
                                torque_data.bto if torque_data.bto else '',
                                torque_data.rto if torque_data.rto else '',
                                torque_data.eto if torque_data.eto else ''
                            ])
                        else:
                            # Если данных нет - пустые ячейки
                            row_data.extend(['', '', ''])

                    # ИСПРАВЛЕНИЕ: добавляем данные для давления 'spring'
                    if spring_pressure:
                        spring_torque_data = all_torque_data.filter(
                            body=body,
                            pressure=spring_pressure,
                            spring_qty=spring
                        ).first()

                        if spring_torque_data:
                            row_data.extend([
                                spring_torque_data.bto if spring_torque_data.bto else '',
                                spring_torque_data.rto if spring_torque_data.rto else '',
                                spring_torque_data.eto if spring_torque_data.eto else ''
                            ])
                        else:
                            row_data.extend(['', '', ''])
                    else:
                        row_data.extend(['', '', ''])

                    # Записываем строку
                    for col_idx, value in enumerate(row_data, 1):
                        ws.cell(row=row_idx, column=col_idx, value=value)

                    row_idx += 1

            # Создаем лист с параметрами
            ws_params = wb.create_sheet(title="Параметры")

            # Заголовки параметров
            param_headers = ['Параметр', 'Значение']
            for col_idx, header in enumerate(param_headers, 1):
                cell = ws_params.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill

            # Данные параметров
            params_data = [
                ['Минимальное давление, бар', pressure_min],
                ['Максимальное давление, бар', pressure_max],
                ['Минимальное кол-во пружин', springs_min],
                ['Максимальное кол-во пружин', springs_max],
                ['Дата экспорта', datetime.now().strftime('%Y-%m-%d %H:%M')]
            ]

            for row_idx, row_data in enumerate(params_data, 2):
                for col_idx, value in enumerate(row_data, 1):
                    ws_params.cell(row=row_idx, column=col_idx, value=value)

            # Создаем лист со справочниками
            ws_ref = wb.create_sheet(title="Справочники")

            # Заголовки справочников
            ref_headers = ['Тип', 'Код', 'Название', 'Описание']
            for col_idx, header in enumerate(ref_headers, 1):
                cell = ws_ref.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill

            # Заполняем справочник давлений
            row_idx = 2
            for pressure in pressures:
                ws_ref.cell(row=row_idx, column=1, value='Давление')
                ws_ref.cell(row=row_idx, column=2, value=pressure.code)
                ws_ref.cell(row=row_idx, column=3, value=pressure.name)
                ws_ref.cell(row=row_idx, column=4, value=pressure.description or '')
                row_idx += 1

            # Заполняем справочник пружин
            for spring in springs:
                ws_ref.cell(row=row_idx, column=1, value='Пружины')
                ws_ref.cell(row=row_idx, column=2, value=spring.code)
                ws_ref.cell(row=row_idx, column=3, value=spring.name)
                ws_ref.cell(row=row_idx, column=4, value=spring.description or '')
                row_idx += 1

            # Заполняем справочник корпусов
            for body in bodies:
                ws_ref.cell(row=row_idx, column=1, value='Корпус')
                ws_ref.cell(row=row_idx, column=2, value=body.code)
                ws_ref.cell(row=row_idx, column=3, value=body.name)
                ws_ref.cell(row=row_idx, column=4, value=body.description or '')
                row_idx += 1

            # Авто-ширина колонок для всех листов
            for worksheet in wb.worksheets:
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min((max_length + 2), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            # Сохраняем файл
            if output_path is None:
                output_path = f"torque_thrust_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

            wb.save(output_path)
            logger.info("Успешно экспортировано данных в: %s", output_path)
            return output_path

        except Exception as e:
            logger.error("Ошибка при экспорте в Excel: %s", str(e))
            raise

    @staticmethod
    @transaction.atomic
    def import_from_excel(excel_file_path):
        """
        Импорт данных моментов/усилий из Excel файла

        Args:
            excel_file_path: путь к файлу Excel

        Returns:
            tuple: (количество импортированных записей, список ошибок)
        """
        import pandas as pd
        from params.models import PneumaticAirSupplyPressure
        from pneumatic_actuators.models import PneumaticActuatorSpringsQty
        from pneumatic_actuators.models.pa_body import PneumaticActuatorBody

        try:
            # Читаем Excel файл
            df = pd.read_excel(excel_file_path, header=None)
            logger.info(f"Файл успешно прочитан. Размер: {df.shape}")
        except Exception as e:
            logger.error(f"Ошибка чтения файла: {str(e)}")
            return 0, [f"Ошибка чтения файла: {str(e)}"]

        imported_count = 0
        errors = []

        # Проверяем структуру файла
        if len(df.columns) < 4:
            error_msg = "Файл должен содержать минимум 4 столбца"
            logger.error(error_msg)
            return 0, [error_msg]

        # Получаем данные из столбцов
        body_codes_col = df.iloc[:, 0]  # Первый столбец - коды корпусов
        pressure_codes_row = df.iloc[0, 3:]  # Первая строка, начиная с 4-го столбца - коды давлений
        spring_codes_col = df.iloc[:, 2]  # Третий столбец - коды пружин
        parameter_types_col = df.iloc[1, 3:]  # Вторая строка, начиная с 4-го столбца - типы параметров

        logger.info(f"Первый столбец (корпуса): {body_codes_col.tolist()}")
        logger.info(f"Коды давлений из первой строки: {pressure_codes_row.tolist()}")
        logger.info(f"Третий столбец (пружины): {spring_codes_col.tolist()}")
        logger.info(f"Типы параметров из второй строки: {parameter_types_col.tolist()}")

        # Собираем информацию о столбцах с данными
        columns_info = []
        current_pressure = None

        for col_idx in range(3, len(df.columns)):  # Начинаем с 4-го столбца
            pressure_code = df.iloc[0, col_idx]  # Давление из первой строки
            parameter_type = df.iloc[1, col_idx]  # Тип параметра из второй строки

            if pd.notna(pressure_code) and str(pressure_code).strip():
                current_pressure = str(pressure_code).strip()

            if current_pressure and pd.notna(parameter_type) and str(parameter_type).strip():
                column_info = {
                    'col_idx': col_idx,
                    'pressure_code': current_pressure,
                    'parameter_type': str(parameter_type).strip().upper()
                }
                columns_info.append(column_info)
                logger.debug(f"Столбец {col_idx}: давление={current_pressure}, параметр={parameter_type}")

        logger.info(f"Всего столбцов с данными: {len(columns_info)}")

        # Получаем уникальные коды пружин из третьего столбца (начиная с 3-й строки)
        spring_codes = set()
        for row_idx in range(2, len(spring_codes_col)):  # Начинаем с 3-й строки (индекс 2)
            spring_code = spring_codes_col.iloc[row_idx]
            if pd.notna(spring_code) and str(spring_code).strip():
                spring_codes.add(str(spring_code).strip())

        logger.info(f"Уникальные коды пружин: {spring_codes}")

        # Проверяем существование всех давлений
        pressure_codes = set(info['pressure_code'] for info in columns_info)
        logger.info(f"Найдены коды давлений: {pressure_codes}")

        existing_pressures = PneumaticAirSupplyPressure.objects.filter(code__in=pressure_codes)
        existing_pressure_codes = set(p.code for p in existing_pressures)
        logger.info(f"Существующие давления в БД: {existing_pressure_codes}")

        missing_pressures = pressure_codes - existing_pressure_codes
        if missing_pressures:
            error_msg = f"Не найдены давления с кодами: {', '.join(missing_pressures)}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Проверяем существование всех пружин
        existing_springs = PneumaticActuatorSpringsQty.objects.filter(code__in=spring_codes)
        existing_spring_codes = set(s.code for s in existing_springs)
        logger.info(f"Существующие пружины в БД: {existing_spring_codes}")

        missing_springs = spring_codes - existing_spring_codes
        if missing_springs:
            error_msg = f"Не найдены пружины с кодами: {', '.join(missing_springs)}"
            logger.error(error_msg)
            errors.append(error_msg)

        # Логируем все пружины в базе для отладки
        all_springs = PneumaticActuatorSpringsQty.objects.filter(is_active=True).values('code', 'name')
        logger.info(f"Все активные пружины в БД: {list(all_springs)}")

        # Если есть ошибки с давлениями или пружинами - прерываем импорт
        if errors:
            logger.error(f"Импорт прерван из-за ошибок: {errors}")
            return 0, errors

        # Создаем словари для быстрого доступа
        pressure_dict = {p.code: p for p in existing_pressures}
        spring_dict = {s.code: s for s in existing_springs}

        logger.info(f"Словарь давлений: {list(pressure_dict.keys())}")
        logger.info(f"Словарь пружин: {list(spring_dict.keys())}")

        # Обрабатываем данные начиная с 3-й строки
        logger.info(f"Начинаем обработку данных с {len(df) - 2} строк")

        for row_idx in range(2, len(df)):  # Начинаем с 3-й строки
            row = df.iloc[row_idx]
            logger.debug(f"Обработка строки {row_idx + 1}: {row.tolist()}")

            # Получаем код корпуса из первого столбца
            body_code = row.iloc[0] if len(row) > 0 else None
            # Получаем код пружины из третьего столбца
            spring_code = row.iloc[2] if len(row) > 2 else None

            if not body_code or pd.isna(body_code) or not spring_code or pd.isna(spring_code):
                logger.debug(f"Строка {row_idx + 1}: пропущена (пустой код корпуса или пружины)")
                continue

            body_code = str(body_code).strip()
            spring_code = str(spring_code).strip()
            logger.debug(f"Строка {row_idx + 1}: код корпуса '{body_code}', пружина '{spring_code}'")

            # Ищем корпус
            try:
                body = PneumaticActuatorBody.objects.get(code=body_code, is_active=True)
                logger.debug(f"Найден корпус: {body.name} (ID: {body.id})")
            except PneumaticActuatorBody.DoesNotExist:
                error_msg = f"Строка {row_idx + 1}: корпус с кодом '{body_code}' не найден"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
            except PneumaticActuatorBody.MultipleObjectsReturned:
                error_msg = f"Строка {row_idx + 1}: найдено несколько корпусов с кодом '{body_code}'"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

            # Получаем объект пружины
            spring = spring_dict.get(spring_code)
            if not spring:
                error_msg = f"Строка {row_idx + 1}: пружина с кодом '{spring_code}' не найдена"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

            # Обрабатываем данные для каждого столбца
            for col_info in columns_info:
                col_idx = col_info['col_idx']

                if col_idx >= len(row):
                    logger.debug(f"Столбец {col_idx} выходит за пределы строки")
                    continue

                value = row.iloc[col_idx]
                logger.debug(f"Столбец {col_idx}: значение '{value}'")

                # Пропускаем пустые значения
                if pd.isna(value) or value == '':
                    logger.debug(f"Столбец {col_idx}: пропущено (пустое значение)")
                    continue

                try:
                    pressure = pressure_dict[col_info['pressure_code']]
                    parameter_type = col_info['parameter_type']

                    logger.debug(
                        f"Обработка: давление={pressure.code}, пружина={spring.code}, параметр={parameter_type}")

                    # Преобразуем значение в число
                    try:
                        numeric_value = float(value)
                        logger.debug(f"Значение преобразовано в число: {numeric_value}")
                    except (ValueError, TypeError):
                        error_msg = f"Строка {row_idx + 1}, столбец {col_idx + 1}: значение '{value}' не является числом"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue

                    # Ищем существующую запись или создаем новую
                    torque_data, created = BodyThrustTorqueTable.objects.get_or_create(
                        body=body,
                        pressure=pressure,
                        spring_qty=spring,
                        defaults={
                            'bto': 0,
                            'rto': 0,
                            'eto': 0
                        }
                    )

                    action = "создана" if created else "обновлена"
                    logger.debug(
                        f"Запись {action}: body={body.code}, pressure={pressure.code}, spring={spring.code}")

                    # Обновляем соответствующее поле
                    if parameter_type == 'BTO':
                        torque_data.bto = numeric_value
                        logger.debug(f"BTO установлено: {numeric_value}")
                    elif parameter_type == 'RTO':
                        torque_data.rto = numeric_value
                        logger.debug(f"RTO установлено: {numeric_value}")
                    elif parameter_type == 'ETO':
                        torque_data.eto = numeric_value
                        logger.debug(f"ETO установлено: {numeric_value}")
                    else:
                        error_msg = f"Строка {row_idx + 1}, столбец {col_idx + 1}: неизвестный тип параметра '{parameter_type}'"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue

                    torque_data.save()
                    imported_count += 1
                    logger.debug(f"Запись сохранена. Всего импортировано: {imported_count}")

                except Exception as e:
                    error_msg = f"Строка {row_idx + 1}, столбец {col_idx + 1}: ошибка обработки - {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    continue

        logger.info(f"Импорт завершен. Импортировано записей: {imported_count}, ошибок: {len(errors)}")
        return imported_count, errors
