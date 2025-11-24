class ValveLineDrawingPropertiesMixin:
    """Миксин для properties работы с чертежами через таблицу ВГХ с наследованием"""

    def get_dimension_table_with_inheritance(self):
        """
        Получает таблицу ВГХ с учетом наследования через цепочку серий
        """
        current_table = self.valve_model_dimension_data_table

        # Если у текущей серии есть своя таблица ВГХ
        if current_table:
            return current_table

        # Если таблицы нет, проверяем исходную серию
        if self.original_valve_line:
            return self.original_valve_line.get_dimension_table_with_inheritance()

        return None

    @property
    def effective_valve_model_dimension_data_table(self):
        """Получает таблицу ВГХ с учетом наследования между сериями"""
        return self.get_dimension_table_with_inheritance()

    def get_drawings_with_inheritance(self):
        """
        Получает все чертежи с учетом наследования через цепочку таблиц ВГХ
        """
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return []

        # Собираем чертежи из всей цепочки наследования таблиц
        all_drawings = []
        visited_tables = set()
        current_table = dimension_table

        while current_table and current_table.id not in visited_tables:
            visited_tables.add(current_table.id)

            # Добавляем чертежи текущей таблицы
            table_drawings = current_table.drawings.filter(is_active=True)
            all_drawings.extend(table_drawings)

            # Переходим к исходной таблице (если есть наследование таблиц)
            current_table = current_table.original_dimension_table

        return all_drawings

    @property
    def has_drawings(self):
        """Проверяет, есть ли чертежи у серии (с учетом наследования)"""
        return len(self.get_drawings_with_inheritance()) > 0

    @property
    def all_drawings(self):
        """Возвращает все активные чертежи с учетом наследования"""
        drawings = self.get_drawings_with_inheritance()
        # Убираем дубликаты по ID
        seen = set()
        unique_drawings = []
        for drawing in drawings:
            if drawing.id not in seen:
                seen.add(drawing.id)
                unique_drawings.append(drawing)
        return unique_drawings

    def get_drawings_for_dn(self, dn):
        """
        Получает чертежи для конкретного DN с учетом наследования

        Args:
            dn: значение DN (строка или число)
        Returns:
            list: чертежи, применимые для указанного DN
        """
        try:
            dn_str = str(dn).replace('DN', '').strip()
            all_drawings = self.get_drawings_with_inheritance()

            # Фильтруем чертежи по DN
            applicable_drawings = []

            for drawing in all_drawings:
                # Общие чертежи (без привязки к DN)
                if not drawing.applicable_dn.exists():
                    applicable_drawings.append(drawing)
                # Чертежи для конкретного DN
                elif drawing.applicable_dn.filter(name=dn_str).exists():
                    applicable_drawings.append(drawing)

            return applicable_drawings

        except Exception:
            return []

    def get_drawings_grouped_by_dn(self):
        """
        Получает чертежи сгруппированные по DN с учетом наследования

        Returns:
            dict: {
                'general': [drawing1, drawing2, ...],  # Общие чертежи
                'by_dn': {
                    '50': [drawing1, drawing3, ...],
                    '80': [drawing2, drawing4, ...],
                    ...
                }
            }
        """
        all_drawings = self.get_drawings_with_inheritance()

        result = {
            'general': [],
            'by_dn': {}
        }

        for drawing in all_drawings:
            if not drawing.applicable_dn.exists():
                # Общий чертеж для всех DN
                if drawing not in result['general']:
                    result['general'].append(drawing)
            else:
                # Чертеж для конкретных DN
                for dn in drawing.applicable_dn.all():
                    dn_key = dn.name
                    if dn_key not in result['by_dn']:
                        result['by_dn'][dn_key] = []
                    if drawing not in result['by_dn'][dn_key]:
                        result['by_dn'][dn_key].append(drawing)

        return result

    def get_drawing_info(self, show_data_source=False):
        """
        Получает информацию о чертежах с учетом наследования

        Returns:
            dict: информация о чертежах
        """
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return {
                'drawings': [],
                'has_drawings': False,
                'total_count': 0,
                'source_comment': None
            }

        drawings_data = []
        source_tables = set()

        # Собираем информацию о чертежах с указанием источника
        for drawing in self.all_drawings:
            # Определяем источник чертежа
            source_table = drawing.dimension_table
            source_tables.add(source_table.name)

            # Получаем DN, для которых применим чертеж
            applicable_dn = [dn.name for dn in drawing.applicable_dn.all()]

            drawing_info = {
                'id': drawing.id,
                'name': drawing.name,
                'description': drawing.description,
                'file_url': drawing.drawing_file.url if drawing.drawing_file else None,
                'file_type': drawing.file_type,
                'file_name': drawing.drawing_file.name.split('/')[-1] if drawing.drawing_file else None,
                'applicable_dn': applicable_dn,
                'is_general': len(applicable_dn) == 0,
                'sorting_order': drawing.sorting_order,
                'source_table': source_table.name,
                'is_inherited': source_table != dimension_table  # Унаследован из другой таблицы
            }
            drawings_data.append(drawing_info)

        # Сортируем по порядку
        drawings_data.sort(key=lambda x: x['sorting_order'])

        # Формируем комментарий об источниках
        source_comment = None
        if show_data_source:
            sources = list(source_tables)
            if dimension_table.name in sources:
                sources.remove(dimension_table.name)
                source_comment = f"Чертежи из таблицы ВГХ: {dimension_table.name}"
                if sources:
                    source_comment += f" + унаследовано из: {', '.join(sources)}"
            else:
                source_comment = f"Чертежи унаследованы из: {', '.join(sources)}"

        return {
            'drawings': drawings_data,
            'has_drawings': len(drawings_data) > 0,
            'total_count': len(drawings_data),
            'dimension_table': dimension_table.name,
            'source_tables': list(source_tables),
            'source_comment': source_comment
        }

    def get_drawings_for_model(self, dn, pn=None):
        """
        Получает чертежи для конкретной модели (DN и опционально PN) с наследованием

        Args:
            dn: значение DN
            pn: значение PN (опционально)
        Returns:
            list: список чертежей для модели
        """
        drawings = self.get_drawings_for_dn(dn)

        result = []
        for drawing in drawings:
            drawing_data = {
                'id': drawing.id,
                'name': drawing.name,
                'description': drawing.description,
                'file_url': drawing.drawing_file.url,
                'file_type': drawing.file_type,
                'file_name': drawing.drawing_file.name.split('/')[-1],
                'is_specific': not drawing.is_general,
                'source_table': drawing.dimension_table.name,
                'is_inherited': drawing.dimension_table != self.effective_valve_model_dimension_data_table
            }
            result.append(drawing_data)

        return result

    def get_combined_dimension_data_with_drawings(self, dn=None):
        """
        Получает объединенные данные ВГХ и чертежи для конкретного DN или всех

        Args:
            dn: конкретный DN или None для всех
        Returns:
            dict: объединенные данные
        """
        dimension_data = self.get_dimension_data_table()
        drawings_info = self.get_drawing_info()

        # Если указан конкретный DN, фильтруем чертежи
        if dn:
            filtered_drawings = self.get_drawings_for_dn(dn)
            drawings_info['drawings'] = [
                {
                    'id': drawing.id,
                    'name': drawing.name,
                    'description': drawing.description,
                    'file_url': drawing.drawing_file.url,
                    'file_type': drawing.file_type,
                    'is_general': drawing.is_general,
                    'source_table': drawing.dimension_table.name
                }
                for drawing in filtered_drawings
            ]
            drawings_info['total_count'] = len(drawings_info['drawings'])
            drawings_info['has_drawings'] = drawings_info['total_count'] > 0

        return {
            'dimension_data': dimension_data,
            'drawings': drawings_info,
            'has_data': dimension_data['has_data'] or drawings_info['has_drawings']
        }
class ValveLineDimensionPropertiesMixin:
    """Миксин для properties работы с весо-габаритными характеристиками"""

    @property
    def effective_valve_model_dimension_data_table(self):
        """Получает таблицу ВГХ с учетом наследования"""
        return self.get_field_value_with_fallback('valve_model_dimension_data_table')

    @property
    def has_dimension_data(self):
        """Проверяет, есть ли данные по ВГХ"""
        return self.get_dimension_data_info()['has_data']

    @property
    def dimension_table_columns(self):
        """Возвращает список DN столбцов таблицы ВГХ"""
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return []

        from ..dimension_models import DimensionTableColumn
        return DimensionTableColumn.objects.filter(
            dimension_table=dimension_table
        ).select_related('dn').order_by('column_order')

    @property
    def dimension_table_rows(self):
        """Возвращает список строк таблицы ВГХ"""
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return []

        from ..dimension_models import DimensionTableRow
        return DimensionTableRow.objects.filter(
            dimension_table=dimension_table
        ).select_related('system_parameter').order_by('row_order')

    def get_dimension_value_by_dn_and_param(self, dn, parameter_identifier):
        """
        Получает значение ВГХ по DN и параметру (системному или текстовому)

        Args:
            dn: значение DN (строка или число)
            parameter_identifier: системный параметр, код параметра или название
        """
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return None

        from ..dimension_models import DimensionTableCell

        try:
            # Приводим DN к строке
            dn_str = str(dn).replace('DN', '').strip()

            # Ищем ячейку
            cell = DimensionTableCell.objects.filter(
                row__dimension_table=dimension_table,
                column__dn__name=dn_str,
            ).select_related('row', 'row__system_parameter', 'column__dn').first()

            if not cell:
                return None

            # Проверяем параметр разными способами
            if hasattr(parameter_identifier, 'pk'):  # Объект системного параметра
                if cell.row.system_parameter == parameter_identifier:
                    return cell.value

            elif isinstance(parameter_identifier, str):
                # По коду системного параметра
                if (cell.row.system_parameter and
                        cell.row.system_parameter.code == parameter_identifier):
                    return cell.value

                # По названию системного параметра
                if (cell.row.system_parameter and
                        cell.row.system_parameter.name == parameter_identifier):
                    return cell.value

                # По текстовому названию в строке
                if cell.row.parameter_name == parameter_identifier:
                    return cell.value

            return None

        except (DimensionTableCell.DoesNotExist, ValueError):
            return None

    def get_dimension_column_by_dn(self, dn):
        """
        Получает данные столбца по DN для вывода в информации

        Returns:
            dict: {'dn': '50', 'values': [{'param_name': 'Вес', 'value': 10.5}, ...]}
        """
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return None

        from ..dimension_models import DimensionTableCell

        try:
            dn_str = str(dn).replace('DN', '').strip()

            cells = DimensionTableCell.objects.filter(
                column__dimension_table=dimension_table,
                column__dn__name=dn_str
            ).select_related(
                'row',
                'row__system_parameter',
                'column__dn'
            ).order_by('row__row_order')

            if not cells:
                return None

            column_data = {
                'dn': dn_str,
                'values': []
            }

            for cell in cells:
                value_info = {
                    'parameter_name': cell.row.parameter_name,
                    'system_parameter': cell.row.system_parameter,
                    'value': float(cell.value) if cell.value else None,
                    'unit': getattr(cell.row.system_parameter, 'unit', '') if cell.row.system_parameter else ''
                }
                column_data['values'].append(value_info)

            return column_data

        except DimensionTableCell.DoesNotExist:
            return None

    def get_dimension_row_by_parameter(self, parameter_identifier):
        """
        Получает данные строки по параметру

        Returns:
            dict: {'parameter_name': 'Вес', 'values': [{'dn': '50', 'value': 10.5}, ...]}
        """
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return None

        from ..dimension_models import DimensionTableRow, DimensionTableCell

        try:
            # Ищем строку
            row_query = DimensionTableRow.objects.filter(
                dimension_table=dimension_table
            )

            # Поиск по разным идентификаторам
            if hasattr(parameter_identifier, 'pk'):  # Объект
                row = row_query.filter(system_parameter=parameter_identifier).first()
            elif isinstance(parameter_identifier, str):
                # Сначала по системному параметру
                row = row_query.filter(
                    system_parameter__code=parameter_identifier
                ).first()
                if not row:
                    row = row_query.filter(
                        system_parameter__name=parameter_identifier
                    ).first()
                if not row:
                    row = row_query.filter(
                        parameter_name=parameter_identifier
                    ).first()

            if not row:
                return None

            # Получаем ячейки строки
            cells = DimensionTableCell.objects.filter(
                row=row
            ).select_related('column__dn').order_by('column__column_order')

            row_data = {
                'parameter_name': row.parameter_name,
                'system_parameter': row.system_parameter,
                'values': []
            }

            for cell in cells:
                value_info = {
                    'dn': cell.column.dn.name,
                    'value': float(cell.value) if cell.value else None
                }
                row_data['values'].append(value_info)

            return row_data

        except (DimensionTableRow.DoesNotExist, DimensionTableCell.DoesNotExist):
            return None

    def get_dimension_data_table(self):
        """
        Получает всю таблицу ВГХ в удобном для отображения формате

        Returns:
            dict: {
                'columns': [{'dn': '50', 'display_name': 'DN50'}, ...],
                'rows': [
                    {
                        'parameter_name': 'Вес',
                        'system_parameter': obj,
                        'cells': [{'value': 10.5, 'dn': '50'}, ...]
                    },
                    ...
                ]
            }
        """
        dimension_table = self.effective_valve_model_dimension_data_table
        if not dimension_table:
            return {'columns': [], 'rows': [], 'has_data': False}

        from ..dimension_models import DimensionTableCell

        # Получаем все ячейки с предзагрузкой
        cells = DimensionTableCell.objects.filter(
            row__dimension_table=dimension_table
        ).select_related(
            'row',
            'row__system_parameter',
            'column',
            'column__dn'
        ).order_by('row__row_order', 'column__column_order')

        if not cells:
            return {'columns': [], 'rows': [], 'has_data': False}

        # Собираем столбцы
        columns_dict = {}
        for cell in cells:
            dn_key = cell.column.dn.name
            if dn_key not in columns_dict:
                columns_dict[dn_key] = {
                    'dn': dn_key,
                    'display_name': f'DN{dn_key}',
                    'column_order': cell.column.column_order
                }

        columns = sorted(columns_dict.values(), key=lambda x: x['column_order'])

        # Собираем строки
        rows_dict = {}
        for cell in cells:
            row_key = cell.row.id
            if row_key not in rows_dict:
                rows_dict[row_key] = {
                    'parameter_name': cell.row.parameter_name,
                    'system_parameter': cell.row.system_parameter,
                    'system_parameter_code': cell.row.system_parameter.code if cell.row.system_parameter else None,
                    'row_order': cell.row.row_order,
                    'cells': {}
                }

            rows_dict[row_key]['cells'][cell.column.dn.name] = {
                'value': float(cell.value) if cell.value else None,
                'display_value': f"{cell.value}" if cell.value else "-"
            }

        # Сортируем строки и заполняем ячейки для всех столбцов
        rows = sorted(rows_dict.values(), key=lambda x: x['row_order'])
        for row in rows:
            row['cells'] = [row['cells'].get(col['dn'], {'value': None, 'display_value': '-'})
                            for col in columns]

        return {
            'columns': columns,
            'rows': rows,
            'has_data': True
        }

    def get_dimension_data_info(self, show_data_source=False):
        """Получает информацию о данных ВГХ для использования в get_full_data"""
        table_data = self.get_dimension_data_table()

        return {
            'table_data': table_data,
            'has_data': table_data['has_data'],
            'source_comment': f"Данные ВГХ из: {self.name}" if show_data_source else None
        }


class ValveLinePropertiesMixin(ValveLineDimensionPropertiesMixin) :
    """Миксин для специфических properties (только dimension-related)"""

    # Наследует все properties из ValveLineDimensionPropertiesMixin
    # и может добавлять дополнительные специфические properties

    @property
    def has_any_technical_data(self) :
        """Проверяет наличие любых технических данных"""
        return (self.has_technical_data or
                self.has_kv_data or
                self.has_dimension_data or
                self.has_options)

    @property
    def data_completeness_score(self) :
        """Оценка полноты данных (0-100%)"""
        score = 0
        total_fields = 4

        if self.has_technical_data :
            score += 1
        if self.has_kv_data :
            score += 1
        if self.has_dimension_data :
            score += 1
        if self.has_options :
            score += 1

        return (score / total_fields) * 100 if total_fields > 0 else 0

