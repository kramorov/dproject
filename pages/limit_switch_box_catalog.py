# pages/limit_switch_box_catalog.py

import streamlit as st

from pa_controls.models.limit_switch import LimitSwitchBox

st.title("Отладка блоков концевых выключателей")

filter_options = LimitSwitchBox.get_filter_options()

# Фильтры
col1, col2, col3, col4 = st.columns(4)

with col1:
    search_text = st.text_input("Поиск", placeholder="Код или название...")

with col2:
    if filter_options.get('model_lines'):
        selected_line = st.selectbox(
            "Серия",
            [{'id': None, 'name': 'Все'}] + filter_options['model_lines'],
            format_func=lambda x: x['name']
        )

with col3:
    if filter_options.get('model_line_brands'):
        selected_brand = st.selectbox(
            "Бренд",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_brands'],
            format_func=lambda x: x['name']
        )

with col4:
    if filter_options.get('sensor_varieties'):
        selected_sensor = st.selectbox(
            "Тип сенсора",
            [{'id': None, 'name': 'Все'}] + filter_options['sensor_varieties'],
            format_func=lambda x: x['name']
        )

col1, col2, col3, col4 = st.columns(4)

with col1:
    if filter_options.get('points_options'):
        selected_points = st.selectbox(
            "Количество датчиков",
            [{'id': None, 'name': 'Все'}] + filter_options['points_options'],
            format_func=lambda x: x['name']
        )

with col2:
    if filter_options.get('ip_options'):
        selected_ip = st.selectbox(
            "IP",
            [{'id': None, 'name': 'Все'}] + filter_options['ip_options'],
            format_func=lambda x: x['name']
        )

with col3:
    min_temp = st.number_input("Температура от (°C)", value=None, placeholder="Не указано")
    max_temp = st.number_input("Температура до (°C)", value=None, placeholder="Не указано")

with col4:
    st.markdown("### ")


# Дополнительные фильтры для сенсоров
col1, col2, col3, col4 = st.columns(4)

with col1:
    if filter_options.get('signal_type_options'):
        selected_signal_type = st.selectbox(
            "Тип сигнала датчика",
            [{'id': None, 'name': 'Все'}] + filter_options['signal_type_options'],
            format_func=lambda x: x['name']
        )
    else:
        selected_signal_type = None

with col2:
    if filter_options.get('contact_form_options'):
        selected_contact_form = st.selectbox(
            "Форма контактов датчика",
            [{'id': None, 'name': 'Все'}] + filter_options['contact_form_options'],
            format_func=lambda x: x['name']
        )
    else:
        selected_contact_form = None

with col3:
    st.markdown("")
    # Фильтр по конкретному датчику (опционально, если нужно)
        # if filter_options.get('sensor_component_options'):
        #     selected_sensor = st.selectbox(
        #         "Датчик",
        #         [{'id': None, 'name': 'Все'}] + filter_options['sensor_component_options'],
        #         format_func=lambda x: x['name']
        #     )
        # else:
        #     selected_sensor = None

with col4:
    st.markdown("")
# Формируем params
params = {'limit': 100}

if search_text:
    params['search'] = search_text
if selected_line and selected_line.get('id'):
    params['model_line_id'] = selected_line['id']
if selected_brand and selected_brand.get('id'):
    params['model_line_brand_id'] = selected_brand['id']
if selected_sensor and selected_sensor.get('id'):
    params['sensor_variety_id'] = selected_sensor['id']
if selected_points and selected_points.get('id'):
    params['points'] = selected_points['id']
if selected_ip and selected_ip.get('id'):
    params['ip_id'] = selected_ip['id']
if min_temp:
    params['work_temp_min'] = min_temp
if max_temp:
    params['work_temp_max'] = max_temp

if selected_signal_type and selected_signal_type.get('id'):
    params['signal_type_id'] = selected_signal_type['id']
if selected_contact_form and selected_contact_form.get('id'):
    params['contact_form_id'] = selected_contact_form['id']
if selected_sensor and selected_sensor.get('id'):
    params['sensor_component_id'] = selected_sensor['id']

result = LimitSwitchBox.filter_by_params(params)

st.write(f"**Найдено:** {result['total']} | **Загружено:** {len(result['data'])}")

for item in result['data']:
    with st.expander(f"{item['name']} ({item['code']})"):
        st.write(f"**Серия:** {item['model_line']['name'] if item['model_line'] else '-'}")
        st.write(f"**Бренд:** {item['model_line']['brand']['name'] if item.get('model_line') and item['model_line'].get('brand') else '-'}")
        st.write(f"**Тип сенсора:** {item['sensor_variety']['name'] if item['sensor_variety'] else '-'}")
        st.write(f"**Датчиков:** {item['points']}")
        st.write(f"**IP:** {item['ip']['name'] if item['ip'] else '-'}")
        st.write(f"**Температура:** {item['work_temp_min']}...{item['work_temp_max']} °C")
        # st.write(f"**Взрывозащита:** {item['exd_display']}")
        st.write(f"**Датчики:** {item['sensors_names']}")