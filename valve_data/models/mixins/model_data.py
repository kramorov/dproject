class ValveLineModelDataMixin:
    """Миксин для работы с модельными данными"""

    def get_model_data_info(self, show_data_source=False):
        """Получает информацию о модельных данных (DN/PN таблица) с учетом наследования"""
        model_data_table = self.effective_valve_model_data_table
        allowed_dn_table = self.effective_allowed_dn_table

        if not model_data_table or not allowed_dn_table:
            return {
                'model_data': [],
                'has_data': False,
                'source_comment': None
            }

        allowed_dn_ids = allowed_dn_table.dn.values_list('id', flat=True)
        from ..base_models import ValveLineModelData

        model_data_queryset = ValveLineModelData.objects.filter(
            valve_model_data_table=model_data_table,
            valve_model_dn__id__in=allowed_dn_ids
        ).select_related('valve_model_dn', 'valve_model_pn').order_by(
            'valve_model_dn__sorting_order', 'valve_model_pn__sorting_order'
        )

        model_data = self._get_model_data_table(model_data_queryset)

        return {
            'model_data': model_data,
            'has_data': bool(model_data),
            'source_comment': f"Данные из: {self.name}" if show_data_source else None
        }

    def _format_model_data_row(self, data):
        """Формирует строку данных модели арматуры"""
        item_code = f"{self.effective_valve_brand}-{self.effective_code}-{data.valve_model_dn.name}-{data.valve_model_pn.name}"

        return {
            'item_code': item_code,
            'dn': data.valve_model_dn.name,
            'pn': data.valve_model_pn.name,
            'torque_open': data.valve_model_torque_to_open or 0,
            'torque_close': data.valve_model_torque_to_close or 0,
            'thrust_close': data.valve_model_thrust_to_close or 0,
            'rotations': data.valve_model_rotations_to_open or 0,
            'stem_size': data.valve_model_stem_size.name if data.valve_model_stem_size else "",
            'stem_height': data.valve_model_stem_height or 0,
            'construction_length': data.valve_model_construction_length or 0,
            'mounting_plate': data.get_mounting_plates_list_text() if hasattr(data,
                                                                              'get_mounting_plates_list_text') else "",
        }

    def _get_model_data_table(self, model_data_queryset):
        """Вспомогательный метод для форматирования данных моделей"""
        model_data = [
            self._format_model_data_row(data)
            for data in model_data_queryset
        ]
        model_data.sort(key=lambda x: (float(x['pn']), float(x['dn'])))
        return model_data

    def get_model_data_by_dn_pn(self, dn, pn):
        """Получает данные модели по DN и PN с учетом наследования"""
        from ..base_models import ValveLineModelData

        model_data_table = self.effective_valve_model_data_table
        if not model_data_table:
            return None

        try:
            model_data = ValveLineModelData.objects.filter(
                valve_model_data_table=model_data_table,
                valve_model_dn__name=dn,
                valve_model_pn__name=pn
            ).select_related('valve_model_dn', 'valve_model_pn').first()

            if model_data:
                return self._format_model_data_row(model_data)
            return None
        except ValveLineModelData.DoesNotExist:
            return None

    def get_all_models_list(self):
        """Возвращает список всех моделей для использования в других модулях"""
        model_data_table = self.effective_valve_model_data_table
        if not model_data_table:
            return []

        from ..base_models import ValveLineModelData
        model_data_queryset = ValveLineModelData.objects.filter(
            valve_model_data_table=model_data_table
        ).select_related('valve_model_dn', 'valve_model_pn').order_by(
            'valve_model_dn__sorting_order', 'valve_model_pn__sorting_order'
        )

        return self._get_model_data_table(model_data_queryset)