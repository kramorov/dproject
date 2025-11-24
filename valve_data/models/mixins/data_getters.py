from valve_data.models.mixins import ValveLineInheritanceMixin

class ValveLineDataGettersMixin(ValveLineInheritanceMixin):
    """Миксин для получения данных с наследованием"""

    # Properties для эффективных значений
    @property
    def effective_name(self):
        return self.get_field_value_with_fallback('name') or "Без названия"

    @property
    def effective_code(self):
        return self.get_field_value_with_fallback('code')

    @property
    def effective_description(self):
        return self.get_field_value_with_fallback('description')

    @property
    def effective_features_text(self):
        return self.get_field_value_with_fallback('features_text')

    @property
    def effective_application_text(self):
        return self.get_field_value_with_fallback('application_text')

    @property
    def effective_valve_producer(self):
        return self.get_field_value_with_fallback('valve_producer')

    @property
    def effective_valve_brand(self):
        return self.get_field_value_with_fallback('valve_brand')

    @property
    def effective_valve_variety(self):
        return self.get_field_value_with_fallback('valve_variety')

    @property
    def effective_valve_function(self):
        return self.get_field_value_with_fallback('valve_function')

    @property
    def effective_valve_actuation(self):
        return self.get_field_value_with_fallback('valve_actuation')

    @property
    def effective_valve_sealing_class(self):
        return self.get_field_value_with_fallback('valve_sealing_class')

    @property
    def effective_body_material(self):
        return self.get_field_value_with_fallback('body_material')

    @property
    def effective_body_material_specified(self):
        return self.get_field_value_with_fallback('body_material_specified')

    @property
    def effective_shut_element_material(self):
        return self.get_field_value_with_fallback('shut_element_material')

    @property
    def effective_shut_element_material_specified(self):
        return self.get_field_value_with_fallback('shut_element_material_specified')

    @property
    def effective_sealing_element_material(self):
        return self.get_field_value_with_fallback('sealing_element_material')

    @property
    def effective_sealing_element_material_specified(self):
        return self.get_field_value_with_fallback('sealing_element_material_specified')

    @property
    def effective_item_code_template(self):
        return self.get_field_value_with_fallback('item_code_template')

    @property
    def effective_option_variety(self):
        return self.get_field_value_with_fallback('option_variety')

    @property
    def effective_work_temp_min(self):
        return self.get_field_value_with_fallback('work_temp_min')

    @property
    def effective_work_temp_max(self):
        return self.get_field_value_with_fallback('work_temp_max')

    @property
    def effective_temp_min(self):
        return self.get_field_value_with_fallback('temp_min')

    @property
    def effective_temp_max(self):
        return self.get_field_value_with_fallback('temp_max')

    @property
    def effective_allowed_dn_table(self):
        return self.get_field_value_with_fallback('allowed_dn_table')

    @property
    def effective_port_qty(self):
        return self.get_field_value_with_fallback('port_qty')

    @property
    def effective_construction_variety(self):
        return self.get_field_value_with_fallback('construction_variety')

    @property
    def effective_valve_model_data_table(self):
        return self.get_field_value_with_fallback('valve_model_data_table')

    @property
    def effective_pipe_connection(self):
        return self.get_field_value_with_fallback('pipe_connection')

    @property
    def effective_warranty_period_min(self):
        return self.get_field_value_with_fallback('warranty_period_min')

    @property
    def effective_warranty_period_min_variety(self):
        return self.get_field_value_with_fallback('warranty_period_min_variety')

    @property
    def effective_warranty_period_max(self):
        return self.get_field_value_with_fallback('warranty_period_max')

    @property
    def effective_warranty_period_max_variety(self):
        return self.get_field_value_with_fallback('warranty_period_max_variety')

    @property
    def effective_valve_in_service_years(self):
        return self.get_field_value_with_fallback('valve_in_service_years')

    @property
    def effective_valve_in_service_years_comment(self):
        return self.get_field_value_with_fallback('valve_in_service_years_comment')

    @property
    def effective_valve_in_service_cycles(self):
        return self.get_field_value_with_fallback('valve_in_service_cycles')

    @property
    def effective_valve_in_service_cycles_comment(self):
        return self.get_field_value_with_fallback('valve_in_service_cycles_comment')

    @property
    def effective_valve_model_kv_data_table(self):
        return self.get_field_value_with_fallback('valve_model_kv_data_table')

    # Boolean properties для проверки наличия данных
    @property
    def has_technical_data(self):
        return bool(self.get_technical_specs())

    @property
    def has_options(self):
        return bool(self.get_body_colors_info())

    @property
    def has_kv_data(self):
        return self.get_kv_data_info()['has_data']

    @property
    def has_required_data(self):
        return len(self.get_missing_required_fields()) == 0

    # Строковые представления для GraphQL
    @property
    def effective_valve_producer_str(self):
        producer = self.effective_valve_producer
        return str(producer) if producer else None

    @property
    def effective_valve_brand_str(self):
        brand = self.effective_valve_brand
        return str(brand) if brand else None

    @property
    def effective_valve_variety_str(self):
        variety = self.effective_valve_variety
        return str(variety) if variety else None

    @property
    def effective_valve_function_str(self):
        function = self.effective_valve_function
        return str(function) if function else None

    @property
    def effective_valve_actuation_str(self):
        actuation = self.effective_valve_actuation
        return str(actuation) if actuation else None

    @property
    def effective_valve_sealing_class_str(self):
        sealing_class = self.effective_valve_sealing_class
        return str(sealing_class) if sealing_class else None

    @property
    def effective_body_material_str(self):
        material = self.effective_body_material
        return str(material) if material else None

    @property
    def effective_body_material_specified_str(self):
        material = self.effective_body_material_specified
        return str(material) if material else None

    @property
    def effective_shut_element_material_str(self):
        material = self.effective_shut_element_material
        return str(material) if material else None

    @property
    def effective_shut_element_material_specified_str(self):
        material = self.effective_shut_element_material_specified
        return str(material) if material else None

    @property
    def effective_sealing_element_material_str(self):
        material = self.effective_sealing_element_material
        return str(material) if material else None

    @property
    def effective_sealing_element_material_specified_str(self):
        material = self.effective_sealing_element_material_specified
        return str(material) if material else None

    @property
    def effective_port_qty_str(self):
        port_qty = self.effective_port_qty
        return str(port_qty) if port_qty else None

    @property
    def effective_construction_variety_str(self):
        construction = self.effective_construction_variety
        return str(construction) if construction else None

    @property
    def effective_allowed_dn_table_str(self):
        dn_table = self.effective_allowed_dn_table
        return str(dn_table) if dn_table else None

    @property
    def effective_option_variety_str(self):
        option = self.effective_option_variety
        return str(option) if option else None

    @property
    def effective_pipe_connection_str(self):
        connection = self.effective_pipe_connection
        return str(connection) if connection else None

    # Методы для группировки данных
    def get_basic_info(self, show_data_source=False):
        """Получает основную информацию с учетом наследования"""
        fields = [
            ('name', 'effective_name', 'Название'),
            ('code', 'effective_code', 'Код серии'),
            ('producer', 'effective_valve_producer', 'Производитель'),
            ('brand', 'effective_valve_brand', 'Бренд'),
            ('valve_variety', 'effective_valve_variety', 'Тип арматуры'),
            ('function', 'effective_valve_function', 'Функция'),
            ('option_variety', 'effective_option_variety', 'Стандарт или опция'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value not in [None, '', 'Нет данных']:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_technical_specs(self, show_data_source=False):
        """Получает технические характеристики с учетом наследования"""
        fields = [
            ('sealing_class', 'effective_valve_sealing_class', 'Класс герметичности'),
            ('body_material_type', 'effective_body_material', 'Материал корпуса (тип)'),
            ('body_material_specified', 'effective_body_material_specified', 'Материал корпуса (марка)'),
            ('shut_element_type', 'effective_shut_element_material', 'Материал запорного элемента (тип)'),
            ('shut_element_specified', 'effective_shut_element_material_specified', 'Материал запорного элемента (марка)'),
            ('sealing_element_type', 'effective_sealing_element_material', 'Тип материала уплотнения'),
            ('sealing_element_specified', 'effective_sealing_element_material_specified', 'Материал уплотнения'),
            ('valve_actuation', 'effective_valve_actuation', 'Тип механизма управления'),
            ('port_qty', 'effective_port_qty', 'Количество портов'),
            ('construction', 'effective_construction_variety', 'Тип конструкции'),
            ('pipe_connection', 'effective_pipe_connection', 'Присоединение к трубе'),
            ('allowed_dn_table', 'effective_allowed_dn_table', 'Допустимые Dn'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value not in [None, '', 'Нет данных']:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_temperature_info(self, show_data_source=False):
        """Получает информацию о температурных характеристиках"""
        fields = [
            ('work_temp_min', 'effective_work_temp_min', 'Минимальная рабочая температура, °С'),
            ('work_temp_max', 'effective_work_temp_max', 'Максимальная рабочая температура, °С'),
            ('temp_min', 'effective_temp_min', 'Минимальная температура, °С'),
            ('temp_max', 'effective_temp_max', 'Максимальная температура, °С'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value is not None:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result

    def get_body_colors_info(self, show_data_source=False):
        """Получает информацию о цветах корпуса"""
        body_colors = self.valve_line_body_colors.select_related(
            'body_color', 'option_variety'
        ).filter(is_available=True).order_by('option_variety__sorting_order', 'sorting_order')

        colors_data = []
        for color in body_colors:
            color_info = {
                'color_name': color.body_color.name,
                'option_type': color.option_variety.name,
                'additional_cost': float(color.additional_cost),
                'lead_time_days': color.lead_time_days,
                'option_code': color.option_code_template,
                'hex_color': getattr(color.body_color, 'hex_code', '#CCCCCC'),
                'source_comment': f"Цвет из текущей модели: {self.name}" if show_data_source else None
            }
            colors_data.append(color_info)

        if not colors_data and self.original_valve_line:
            return self.original_valve_line.get_body_colors_info(show_data_source)

        return colors_data

    def get_descriptions_info(self, show_data_source=False):
        """Получает описания с учетом наследования"""
        fields = [
            ('description', 'effective_description', 'Описание'),
            ('features', 'effective_features_text', 'Особенности'),
            ('application', 'effective_application_text', 'Применение'),
        ]

        result = []
        for key, prop, label in fields:
            value = getattr(self, prop)
            if value:
                result.append({
                    'key': key,
                    'label': label,
                    'value': value
                })
        return result