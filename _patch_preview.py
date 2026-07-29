import re
path = r'pneumatic_actuators/api/views_constructor.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        # -- Технические --
        tech_fields = []
        t_order = 1
        for key, label, value in [
            ('pressure', 'Давление мин/макс', f"{body.min_pressure_bar} - {body.max_pressure_bar} бар" if body and body.min_pressure_bar else ''),
            ('air_usage', 'Расход воздуха', f"открытие {body.air_usage_open} л, закрытие {body.air_usage_close} л" if body and (body.air_usage_open or body.air_usage_close) else ''),
        ]:
            if value:
                tech_fields.append({'key': key, 'label': label, 'value': str(value), 'type': 'text', 'order': t_order})
                t_order += 1
        # Присоединение к арматуре
        t_order += 1
        tech_fields.append({'key': 'attachment', 'label': 'Присоединение к арматуре', 'value': '', 'type': 'text', 'order': t_order})
        st_order = t_order * 100 + 1
        for key, label, value in [
            ('stem', 'Шток', body.stem_info_display if body else ''),
            ('mounting', 'Монтажные площадки', body.mounting_plate_display if body else ''),
        ]:
            if value:
                tech_fields.append({'key': key, 'label': label, 'value': str(value), 'type': 'text', 'order': st_order})
                st_order += 1
        # Подключения корпуса
        st_order += 1
        tech_fields.append({'key': 'connections', 'label': 'Подключения корпуса', 'value': '', 'type': 'text', 'order': st_order})
        conn_order = st_order * 100 + 1
        for key, label, value in [
            ('thread_in', 'Пневмовход', str(body.thread_in) if body and body.thread_in else ''),
            ('thread_out', 'Пневмовыход', str(body.thread_out) if body and body.thread_out else ''),
            ('pneumatic_conn', 'Типы пневмоподключений', ', '.join(str(c) for c in body.pneumatic_connection.all()) if body and body.pneumatic_connection.exists() else ''),
        ]:
            if value:
                tech_fields.append({'key': key, 'label': label, 'value': str(value), 'type': 'text', 'order': conn_order})
                conn_order += 1
        # Вес
        if body and body.weight_spring:
            conn_order += 1
            tech_fields.append({'key': 'weight', 'label': 'Вес', 'value': f"{body.weight_spring} кг", 'type': 'number', 'order': conn_order})'''

new = '''        # -- Технические (разбито на подгруппы) --
        # Основные параметры
        basic_tech = []
        t_order = 1
        for key, label, value in [
            ('pressure', 'Давление мин/макс', f"{body.min_pressure_bar} - {body.max_pressure_bar} бар" if body and body.min_pressure_bar else ''),
            ('air_usage', 'Расход воздуха', f"открытие {body.air_usage_open} л, закрытие {body.air_usage_close} л" if body and (body.air_usage_open or body.air_usage_close) else ''),
        ]:
            if value:
                basic_tech.append({'key': key, 'label': label, 'value': str(value), 'type': 'text', 'order': t_order})
                t_order += 1
        # Присоединение к арматуре
        attachment = []
        a_order = 1
        for key, label, value in [
            ('stem', 'Шток', body.stem_info_display if body else ''),
            ('mounting', 'Монтажные площадки', body.mounting_plate_display if body else ''),
        ]:
            if value:
                attachment.append({'key': key, 'label': label, 'value': str(value), 'type': 'text', 'order': a_order})
                a_order += 1
        # Подключения корпуса
        connections = []
        c_order = 1
        for key, label, value in [
            ('thread_in', 'Пневмовход', str(body.thread_in) if body and body.thread_in else ''),
            ('thread_out', 'Пневмовыход', str(body.thread_out) if body and body.thread_out else ''),
            ('pneumatic_conn', 'Типы пневмоподключений', ', '.join(str(c) for c in body.pneumatic_connection.all()) if body and body.pneumatic_connection.exists() else ''),
        ]:
            if value:
                connections.append({'key': key, 'label': label, 'value': str(value), 'type': 'text', 'order': c_order})
                c_order += 1
        # Вес
        weight_fields = []
        if body and body.weight_spring:
            weight_fields.append({'key': 'weight', 'label': 'Вес', 'value': f"{body.weight_spring} кг", 'type': 'number', 'order': 1})

        # Собираем группы
        data['sections'] = [s for s in data.get('sections', []) if s['key'] != 'specs']
        groups = [
            {'key': 'general', 'title': 'Основные', 'order': 1, 'fields': general_fields},
            {'key': 'options', 'title': 'Выбранные опции', 'order': 2, 'fields': option_fields},
            {'key': 'tech_basic', 'title': 'Технические', 'order': 3, 'fields': basic_tech},
        ]
        if attachment:
            groups.append({'key': 'attachment', 'title': 'Присоединение к арматуре', 'order': 4, 'fields': attachment})
        if connections:
            groups.append({'key': 'connections', 'title': 'Подключения корпуса', 'order': 5, 'fields': connections})
        if weight_fields:
            groups.append({'key': 'weight_group', 'title': 'Вес', 'order': 6, 'fields': weight_fields})
        data['sections'].insert(1, {
            'key': 'specs', 'title': 'Характеристики', 'type': 'specs', 'order': 1,
            'groups': groups,
        })

        return Response(data)'''

# Find and replace
idx = content.find(old)
if idx >= 0:
    content = content[:idx] + new + content[idx+len(old):]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK')
else:
    print('NOT FOUND')
