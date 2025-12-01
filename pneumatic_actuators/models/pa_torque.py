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

        # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    @classmethod
    def _get_base_queryset(cls, body_list, pressure_list=None, spring_qty_list=None):
        """Базовый QuerySet для всех форматов"""
        queryset = cls.objects.filter(body__in=body_list)

        if pressure_list:
            queryset = queryset.filter(pressure__in=pressure_list)

        if spring_qty_list:
            queryset = queryset.filter(spring_qty__in=spring_qty_list)

        return queryset

    @classmethod
    def _get_torque_fields_for_construction(cls, construction_variety_code, spring_code, ncno='NO'):
        """
        Определяет, какие поля моментов нужны для данного типа конструкции
        Возвращает список кортежей (field_name, display_name)
        """
        # Для DA приводов - только BTO
        if spring_code == 'DA':
            return [('bto', 'BTO' if ncno == 'NC' else 'BTC')]

        # Для SR приводов (пружинных)
        if construction_variety_code == 'rack_pinion':  # шестерня-рейка
            return [
                ('bto', 'BTO' if ncno == 'NC' else 'BTC'),
                ('eto', 'ETO' if ncno == 'NC' else 'ETC')
            ]
        elif construction_variety_code == 'scotch_yoke':  # кулисный
            return [
                ('bto', 'BTO' if ncno == 'NC' else 'BTC'),
                ('rto', 'RTO' if ncno == 'NC' else 'RTC'),
                ('eto', 'ETO' if ncno == 'NC' else 'ETC')
            ]
        else:
            # По умолчанию все три
            return [
                ('bto', 'BTO' if ncno == 'NC' else 'BTC'),
                ('rto', 'RTO' if ncno == 'NC' else 'RTC'),
                ('eto', 'ETO' if ncno == 'NC' else 'ETC')
            ]

    @classmethod
    def _spring_sort_key(cls, spring_code):
        """Ключ сортировки для пружин"""
        if spring_code == 'DA':
            return 0
        try:
            return int(spring_code)
        except ValueError:
            return 999

    @classmethod
    def _get_construction_variety_code(cls, body):
        """Получает код типа конструкции для корпуса"""
        try:
            if (body and body.model_line and
                    body.model_line.pneumatic_actuator_construction_variety):
                return body.model_line.pneumatic_actuator_construction_variety.code
        except Exception:
            pass
        return None

    # ==================== ОСНОВНОЙ МЕТОД ====================

    @classmethod
    def get_torque_thrust_values(cls, body_list, pressure_list=None,
                                 spring_qty_list=None, ncno='NO',
                                 format='structured'):
        """
        Основной метод получения данных таблицы моментов/усилий

        Args:
            body_list: список объектов PneumaticActuatorBody или их ID
            pressure_list: список объектов PneumaticAirSupplyPressure или их ID (опционально)
            spring_qty_list: список объектов PneumaticActuatorSpringsQty или их ID (опционально)
            ncno: 'NO' или 'NC' - тип привода
            format: формат возвращаемых данных:
                - 'structured' (default) - структурированные данные с метаданными
                - 'matrix' - матричный формат для таблиц
                - 'raw' - сырые QuerySet данные
                - 'api' - оптимизировано для REST/GraphQL (аналогично structured)
                - 'legacy' - старый формат для обратной совместимости

        Returns:
            Dict или QuerySet в зависимости от формата
        """
        logger = logging.getLogger(__name__)

        try:
            # Преобразуем ID в объекты если нужно
            if body_list and all(isinstance(x, (int, str)) for x in body_list):
                body_list = PneumaticActuatorBody.objects.filter(id__in=body_list)

            # Базовый запрос
            queryset = cls._get_base_queryset(body_list, pressure_list, spring_qty_list)

            # Выбор формата ответа
            if format == 'raw':
                return queryset

            elif format == 'matrix':
                return cls._format_as_matrix(queryset, ncno)

            elif format in ['api', 'structured']:
                return cls._format_structured(queryset, ncno)

            else:
                raise ValueError(f"Unknown format: {format}")

        except Exception as e:
            logger.error(f"Error in get_torque_thrust_values: {e}", exc_info=True)
            return {
                'error': str(e),
                'format': format,
                'data': [],
                'metadata': {}
            }

    # ==================== ФОРМАТЫ ВЫВОДА ====================

    @classmethod
    def _format_structured(cls, queryset, ncno='NO'):
        """
        Структурированный формат с метаданными
        Идеально подходит для API и дальнейшей обработки
        """
        logger = logging.getLogger(__name__)

        try:
            # Получаем все данные с prefetch
            all_data = queryset.select_related(
                'body', 'pressure', 'spring_qty',
                'body__model_line__pneumatic_actuator_construction_variety'
            ).order_by('body__sorting_order', 'spring_qty__sorting_order', 'pressure__sorting_order')

            if not all_data:
                return {
                    'format': 'structured',
                    'data': [],
                    'metadata': {},
                    'ncno': ncno,
                    'count': 0
                }

            # Группируем данные по корпусу и пружинам
            grouped = {}
            for item in all_data:
                if not item.body or not item.spring_qty or not item.pressure:
                    logger.warning(f"Skipping item with missing relations: {item.id}")
                    continue

                key = f"{item.body_id}_{item.spring_qty_id}"

                if key not in grouped:
                    construction_variety = cls._get_construction_variety_code(item.body)

                    grouped[key] = {
                        'body': {
                            'id': item.body.id,
                            'code': item.body.code,
                            'name': item.body.name,
                            'construction_variety': construction_variety,
                            'construction_variety_name': (
                                item.body.model_line.pneumatic_actuator_construction_variety.name
                                if construction_variety and item.body.model_line and
                                   hasattr(item.body.model_line, 'pneumatic_actuator_construction_variety')
                                else None
                            )
                        },
                        'spring_qty': {
                            'id': item.spring_qty.id,
                            'code': item.spring_qty.code,
                            'name': item.spring_qty.name
                        },
                        'pressures': {}
                    }

                # Определяем, какие поля нужны для этого типа привода
                construction_variety = grouped[key]['body']['construction_variety']
                spring_code = grouped[key]['spring_qty']['code']

                torque_fields = cls._get_torque_fields_for_construction(
                    construction_variety,
                    spring_code,
                    ncno
                )

                # Формируем значения моментов для этого давления
                torque_values = {}
                for field_name, display_name in torque_fields:
                    value = getattr(item, field_name, None)
                    if value is not None:
                        try:
                            torque_values[field_name] = {
                                'value': float(value),
                                'display_name': display_name,
                                'field': field_name
                            }
                        except (TypeError, ValueError) as e:
                            logger.warning(f"Error converting value for {field_name}: {e}")
                            torque_values[field_name] = {
                                'value': None,
                                'display_name': display_name,
                                'field': field_name
                            }

                grouped[key]['pressures'][item.pressure.code] = {
                    'pressure': {
                        'id': item.pressure.id,
                        'code': item.pressure.code,
                        'name': str(item.pressure),
                        'sorting_order': getattr(item.pressure, 'sorting_order', 0)
                    },
                    'torque_values': torque_values
                }

            # Преобразуем в список и сортируем
            result = list(grouped.values())
            result.sort(key=lambda x: (
                x.get('body', {}).get('code', ''),
                cls._spring_sort_key(x.get('spring_qty', {}).get('code', ''))
            ))

            # Формируем метаданные для рендеринга
            metadata = cls._build_metadata(result, ncno)

            return {
                'format': 'structured',
                'data': result,
                'metadata': metadata,
                'ncno': ncno,
                'count': len(result)
            }

        except Exception as e:
            logger.error(f"Error in _format_structured: {e}", exc_info=True)
            return {
                'format': 'structured',
                'error': str(e),
                'data': [],
                'metadata': {},
                'ncno': ncno,
                'count': 0
            }

    @classmethod
    def _build_metadata(cls, data, ncno='NO'):
        """Строит метаданные для рендеринга таблицы"""
        if not data:
            return {
                'headers': [[], []],
                'column_templates': [],
                'pressures': [],
                'columns_per_pressure': 0
            }

        try:
            # Собираем все уникальные давления
            pressure_codes = set()
            for item in data:
                if isinstance(item, dict) and 'pressures' in item:
                    pressure_codes.update(item['pressures'].keys())

            # Сортируем давления по sorting_order
            pressures_sorted = []
            seen_codes = set()

            for item in data:
                if not isinstance(item, dict) or 'pressures' not in item:
                    continue

                for pressure_code, pressure_data in item['pressures'].items():
                    if pressure_code not in seen_codes:
                        seen_codes.add(pressure_code)
                        pressure_info = pressure_data.get('pressure', {})
                        pressures_sorted.append({
                            'code': pressure_code,
                            'id': pressure_info.get('id'),
                            'name': pressure_info.get('name', pressure_code),
                            'sorting_order': pressure_info.get('sorting_order', 0)
                        })

            pressures_sorted.sort(key=lambda x: x.get('sorting_order', 0))

            # Определяем шаблоны колонок на основе первой записи
            first_item = data[0] if data else {}

            if isinstance(first_item, dict):
                body_info = first_item.get('body', {})
                spring_info = first_item.get('spring_qty', {})

                construction_variety = body_info.get('construction_variety')
                spring_code = spring_info.get('code', '')
            else:
                construction_variety = None
                spring_code = ''

            column_templates = cls._get_column_templates(construction_variety, spring_code, ncno)

            # Генерируем заголовки
            pressure_codes_list = [p.get('code', '') for p in pressures_sorted]
            headers = cls._generate_headers(pressure_codes_list, column_templates)

            return {
                'headers': headers,
                'column_templates': column_templates,
                'pressures': pressures_sorted,
                'columns_per_pressure': len(column_templates)
            }

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in _build_metadata: {e}", exc_info=True)
            return {
                'headers': [[], []],
                'column_templates': [],
                'pressures': [],
                'columns_per_pressure': 0,
                'error': str(e)
            }

    @classmethod
    def _get_column_templates(cls, construction_variety, spring_code, ncno='NO'):
        """Шаблоны колонок для заголовков"""
        fields = cls._get_torque_fields_for_construction(construction_variety, spring_code, ncno)

        return [
            {
                'field': field_name,
                'display_name': display_name,
                'width': 1
            }
            for field_name, display_name in fields
        ]

    @classmethod
    def _generate_headers(cls, pressure_codes, column_templates):
        """Генерирует заголовки таблицы"""
        if not pressure_codes or not column_templates:
            return [[], []]

        try:
            # Первая строка заголовков
            header_row1 = ['Корпус', 'Пружины']
            # Вторая строка заголовков
            header_row2 = ['Код', 'Код']

            for pressure_code in pressure_codes:
                if not isinstance(pressure_code, str):
                    pressure_code = str(pressure_code)

                # Для каждого давления добавляем нужное количество колонок
                for i, template in enumerate(column_templates):
                    if not isinstance(template, dict):
                        continue

                    # Первая строка: название давления только для первой колонки
                    if i == 0:
                        header_row1.append(pressure_code)
                    else:
                        header_row1.append('')

                    # Вторая строка: название типа момента
                    display_name = template.get('display_name', '')
                    header_row2.append(display_name)

            return [header_row1, header_row2]

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in _generate_headers: {e}")
            return [[], []]

    @classmethod
    def _format_as_matrix(cls, queryset, ncno='NO'):
        """
        Матричный формат для табличного отображения
        Каждая строка - словарь с плоской структурой
        """
        # Сначала получаем структурированные данные
        structured = cls._format_structured(queryset, ncno)

        if 'error' in structured:
            return structured

        # Проверяем, что есть данные
        if not structured.get('data'):
            return {
                'format': 'matrix',
                'data': [],
                'headers': [[], []],
                'metadata': {},
                'ncno': ncno,
                'count': 0
            }

        matrix_data = []

        for item in structured['data']:
            # Здесь item - это уже словарь из structured формата
            # Проверяем структуру
            if not isinstance(item, dict):
                continue

            # Базовые поля
            row = {
                'body_id': item.get('body', {}).get('id'),
                'body_code': item.get('body', {}).get('code'),
                'body_name': item.get('body', {}).get('name'),
                'spring_qty_id': item.get('spring_qty', {}).get('id'),
                'spring_qty_code': item.get('spring_qty', {}).get('code'),
                'spring_qty_name': item.get('spring_qty', {}).get('name'),
                'construction_variety': item.get('body', {}).get('construction_variety')
            }

            # Добавляем значения для каждого давления
            pressures = item.get('pressures', {})

            for pressure_meta in structured.get('metadata', {}).get('pressures', []):
                pressure_code = pressure_meta.get('code')

                if pressure_code in pressures:
                    pressure_data = pressures[pressure_code]
                    torque_values = pressure_data.get('torque_values', {})

                    for field_name, value_data in torque_values.items():
                        if isinstance(value_data, dict):
                            col_key = f"pressure_{pressure_code}_{field_name}"
                            row[col_key] = value_data.get('value')

                            # Также можно добавить поле с отображаемым именем
                            display_key = f"pressure_{pressure_code}_{field_name}_display"
                            row[display_key] = value_data.get('display_name')
                else:
                    # Заполняем None для отсутствующих данных
                    column_templates = structured.get('metadata', {}).get('column_templates', [])
                    for template in column_templates:
                        if isinstance(template, dict):
                            field_name = template.get('field')
                            if field_name:
                                col_key = f"pressure_{pressure_code}_{field_name}"
                                row[col_key] = None

            matrix_data.append(row)

        return {
            'format': 'matrix',
            'data': matrix_data,
            'headers': structured.get('metadata', {}).get('headers', [[], []]),
            'metadata': structured.get('metadata', {}),
            'ncno': ncno,
            'count': len(matrix_data)
        }

    # ==================== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ====================

    @classmethod
    def find_body_for_pressure_thrust_or_torque(cls, pressure_min, pressure_max,
                                                thrust_or_torque, tolerance,
                                                pneumatic_actuator_variety):
        """
        Поиск подходящих корпусов по давлению и моменту/усилию
        """
        queryset = cls.objects.select_related('body', 'pressure', 'spring_qty')

        # Фильтрация по давлению
        if pressure_min is not None:
            # Нужно адаптировать под вашу модель PneumaticAirSupplyPressure
            pass

        # Для DA приводов
        if pneumatic_actuator_variety.code == 'DA':
            queryset = queryset.filter(
                spring_qty__code='DA',
                bto__gte=thrust_or_torque - tolerance,
                bto__lte=thrust_or_torque + tolerance
            )

        # TODO: Добавить логику для других типов приводов

        return queryset.values_list('body', flat=True).distinct()

    @classmethod
    def get_min_max_pressure_list_for_body(cls, body, min_pressure, max_pressure):
        """
        Возвращает список давлений в заданном диапазоне для корпуса
        """

        pressures = PneumaticAirSupplyPressure.objects.filter(
            body_thrust_torque_table__body=body
        ).distinct()

        if min_pressure is not None:
            # Адаптируйте под вашу логику сравнения давлений
            pass

        if max_pressure is not None:
            # Адаптируйте под вашу логику сравнения давлений
            pass

        return pressures

    # # 1. Для API/веб-интерфейса - структурированные данные
    # structured_data = BodyThrustTorqueTable.get_torque_thrust_values(
    #     body_list=[body1, body2],
    #     spring_qty_list=[spring_qty],
    #     ncno='NC',
    #     format='structured'
    # )
    #
    # # 2. Для табличного вывода
    # table_data = BodyThrustTorqueTable.get_torque_thrust_values(
    #     body_list=[body1],
    #     format='matrix'
    # )
    #
    # # 3. Для поиска и фильтрации
    # raw_data = BodyThrustTorqueTable.get_torque_thrust_values(
    #     body_list=bodies,
    #     format='raw'
    # ).filter(
    #     pressure__code='spring',
    #     bto__gte=1000
    # )
    #
    # # 4. Для обратной совместимости
    # legacy_data = BodyThrustTorqueTable.get_torque_thrust_values(
    #     body_list=bodies,
    #     format='legacy'
    # )
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
