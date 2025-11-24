class ValveLineKvDataMixin:
    """Миксин для работы с Kv данными"""

    def get_kv_data_info(self, show_data_source=False):
        """Получает информацию о Kv данных с учетом наследования"""
        kv_data_table = self.effective_valve_model_kv_data_table
        allowed_dn_table = self.effective_allowed_dn_table

        if not kv_data_table or not allowed_dn_table:
            return {
                'kv_data': [],
                'has_data': False,
                'source_comment': None,
                'kv_table': None
            }

        allowed_dn_ids = allowed_dn_table.dn.values_list('id', flat=True)
        from ..base_models import ValveLineModelKvData

        kv_data_queryset = ValveLineModelKvData.objects.filter(
            valve_model_kv_data_table=kv_data_table,
            valve_model_dn__id__in=allowed_dn_ids
        ).select_related('valve_model_dn', 'valve_model_pn').order_by(
            'valve_model_dn__sorting_order',
            'valve_model_pn__sorting_order',
            'valve_model_openinig_angle'
        )

        kv_data = self._get_kv_data_table(kv_data_queryset)

        # Формируем таблицу с углами в столбцах
        kv_table = self._format_kv_table(kv_data_queryset)

        return {
            'kv_data': kv_data,
            'kv_table': kv_table,
            'has_data': bool(kv_data),
            'source_comment': f"Kv данные из: {self.name}" if show_data_source else None
        }

    def _format_kv_table(self, kv_data_queryset):
        """Формирует таблицу Kv с углами в столбцах и DN в строках"""
        # Собираем уникальные углы и DN
        angles = set()
        dns = set()
        pn_values = set()
        kv_dict = {}

        for data in kv_data_queryset:
            if data.valve_model_dn and data.valve_model_openinig_angle is not None:
                dn = data.valve_model_dn.name
                angle = float(data.valve_model_openinig_angle)
                kv_value = float(data.valve_model_kv) if data.valve_model_kv else 0

                angles.add(angle)
                dns.add(dn)

                if data.valve_model_pn:
                    pn_values.add(data.valve_model_pn.name)

                if dn not in kv_dict:
                    kv_dict[dn] = {}
                kv_dict[dn][angle] = kv_value

        # Сортируем углы и DN
        sorted_angles = sorted(angles)
        sorted_dns = sorted(dns, key=lambda x: float(x))

        # Формируем строки для таблицы
        dn_rows = []
        for dn in sorted_dns:
            # Создаем список значений Kv для каждого угла в правильном порядке
            angle_values = []
            for angle in sorted_angles:
                angle_values.append({
                    'angle': angle,
                    'kv_value': kv_dict[dn].get(angle)
                })

            row = {
                'dn': dn,
                'angle_values': angle_values  # Список значений в порядке углов
            }
            dn_rows.append(row)

        return {
            'angles': sorted_angles,
            'dn_rows': dn_rows,
            'pn_info': ', '.join(sorted(pn_values, key=lambda x: float(x))) if pn_values else None,
            'available_combinations': [f"DN{dn}/PN{pn}" for dn in sorted_dns for pn in
                                       sorted(pn_values, key=lambda x: float(x))]
        }

    def _get_kv_data_table(self, kv_data_queryset):
        """Вспомогательный метод для форматирования данных Kv в линейном виде"""
        kv_data = [
            self._format_kv_data_row(data)
            for data in kv_data_queryset
        ]
        return kv_data

    def _format_kv_data_row(self, data):
        """Формирует строку данных Kv арматуры"""
        return {
            'dn': data.valve_model_dn.name if data.valve_model_dn else "",
            'pn': data.valve_model_pn.name if data.valve_model_pn else "",
            'opening_angle': float(data.valve_model_openinig_angle) if data.valve_model_openinig_angle else 0,
            'kv_value': float(data.valve_model_kv) if data.valve_model_kv else 0,
        }

    def get_kv_by_dn_pn_angle(self, dn, pn, angle):
        """Получает значение Kv по DN, PN и углу открытия с учетом наследования"""
        from ..valve_line_model_kv_data import ValveLineModelKvData

        kv_data_table = self.effective_valve_model_kv_data_table
        if not kv_data_table:
            return None

        try:
            kv_data = ValveLineModelKvData.objects.filter(
                valve_model_kv_data_table=kv_data_table,
                valve_model_dn__name=dn,
                valve_model_pn__name=pn,
                valve_model_openinig_angle=angle
            ).select_related('valve_model_dn', 'valve_model_pn').first()

            if kv_data:
                return self._format_kv_data_row(kv_data)
            return None
        except ValveLineModelKvData.DoesNotExist:
            return None

    def get_kv_curve_by_dn_pn(self, dn, pn):
        """Получает кривую Kv (значения по углам) для конкретной DN/PN комбинации"""
        from ..valve_line_model_kv_data import ValveLineModelKvData

        kv_data_table = self.effective_valve_model_kv_data_table
        if not kv_data_table:
            return []

        kv_data_queryset = ValveLineModelKvData.objects.filter(
            valve_model_kv_data_table=kv_data_table,
            valve_model_dn__name=dn,
            valve_model_pn__name=pn
        ).select_related('valve_model_dn', 'valve_model_pn').order_by('valve_model_openinig_angle')

        return [
            {
                'angle': float(data.valve_model_openinig_angle) if data.valve_model_openinig_angle else 0,
                'kv_value': float(data.valve_model_kv) if data.valve_model_kv else 0,
            }
            for data in kv_data_queryset
        ]

    def get_all_kv_combinations(self):
        """Возвращает все доступные комбинации DN/PN с Kv данными"""
        kv_data_table = self.effective_valve_model_kv_data_table
        if not kv_data_table:
            return []

        from ..valve_line_model_kv_data import ValveLineModelKvData
        combinations = ValveLineModelKvData.objects.filter(
            valve_model_kv_data_table=kv_data_table
        ).values_list(
            'valve_model_dn__name',
            'valve_model_pn__name'
        ).distinct()

        return [f"{dn}/{pn}" for dn, pn in combinations]

    def get_kv_data_summary(self, show_data_source=False):
        """Получает сводную информацию по Kv данным"""
        kv_info = self.get_kv_data_info(show_data_source)

        if not kv_info['has_data']:
            return {
                'total_entries': 0,
                'dn_range': [],
                'pn_range': [],
                'angle_range': [],
                'has_data': False
            }

        kv_data = kv_info['kv_data']
        dn_set = set()
        pn_set = set()
        angle_set = set()

        for entry in kv_data:
            if entry['dn']:
                dn_set.add(entry['dn'])
            if entry['pn']:
                pn_set.add(entry['pn'])
            if entry['opening_angle'] is not None:
                angle_set.add(entry['opening_angle'])

        return {
            'total_entries': len(kv_data),
            'dn_range': sorted(dn_set, key=lambda x: float(x)),
            'pn_range': sorted(pn_set, key=lambda x: float(x)),
            'angle_range': sorted(angle_set),
            'has_data': True
        }