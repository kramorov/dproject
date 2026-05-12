# pages/filter_regulator_catalog.py

import streamlit as st
from filter_regulator.models import FilterRegulator

st.title("Отладка фильтр-регуляторов")

# Получаем опции фильтров
filter_options = FilterRegulator.get_filter_options()

# ==================== ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ====================
search_text = None
selected_line = None
selected_drain = None
selected_brand = None
selected_thread = None
selected_filter_variety = None
selected_body_material = None
selected_gauge = None
min_filtration = None
max_filtration = None
min_flow = None
max_flow = None
min_work_temp = None
max_work_temp = None
required_min_pressure = None
required_max_pressure = None
max_inlet_pressure = None

# ==================== СТРОКА 1 ====================
st.markdown("### 🔍 Основные фильтры")
col1, col2, col3, col4 = st.columns(4)
# st.write("DEBUG: model_line_brands =", filter_options.get('model_line_brands'))
with col1:
    search_text = st.text_input("Поиск", placeholder="Код или название...")

with col2:
    if filter_options.get('model_line_id'):
        selected_line = st.selectbox(
            "Серия",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_id'],
            format_func=lambda x: x['name']
        )

with col3:
    if filter_options.get('drain_variety_id'):
        selected_drain = st.selectbox(
            "Тип дренажа",
            [{'id': None, 'name': 'Все'}] + filter_options['drain_variety_id'],
            format_func=lambda x: x['name']
        )

with col4:
    if filter_options.get('model_line_brand_id'):
        selected_brand = st.selectbox(
            "Бренд серии",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_brand_id'],
            format_func=lambda x: x['name']
        )

# ==================== СТРОКА 2 ====================
st.markdown("### 🔧 Параметры серии (Model Line)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if filter_options.get('body_thread_id'):
        selected_thread = st.selectbox(
            "Резьба корпуса",
            [{'id': None, 'name': 'Все'}] + filter_options['body_thread_id'],
            format_func=lambda x: x['name']
        )

with col2:
    if filter_options.get('model_line_filter_variety_id'):
        selected_filter_variety = st.selectbox(
            "Разновидность",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_filter_variety_id'],
            format_func=lambda x: x['name']
        )

with col3:
    if filter_options.get('model_line_body_material_id'):
        selected_body_material = st.selectbox(
            "Материал корпуса серии",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_body_material_id'],
            format_func=lambda x: x['name']
        )

with col4:
    st.markdown("### ")

# ==================== СТРОКА 3 (ТЕМПЕРАТУРЫ) ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    min_work_temp = st.number_input(
        "Раб. температура от (°C)",
        value=None,
        placeholder="Не указано"
    )

with col2:
    max_work_temp = st.number_input(
        "Раб. температура до (°C)",
        value=None,
        placeholder="Не указано"
    )

with col3:
    required_min_pressure = st.number_input(  # то, что нужно пользователю (minimum requirement)
        "Требуемое давление от (бар)",
        value=None,
        placeholder="Не указано"
    )

with col4:
    required_max_pressure = st.number_input(  # то, что нужно пользователю (maximum requirement)
        "Требуемое давление до (бар)",
        value=None,
        placeholder="Не указано"
    )

# ==================== СТРОКА 4 (ДАВЛЕНИЯ И ХАРАКТЕРИСТИКИ) ====================
col1, col2, col3 = st.columns(3)

with col1:
    max_inlet_pressure = st.number_input(
        "Макс. входное давление (бар)",
        value=None,
        placeholder="Не указано"
    )

with col2:
    if filter_options.get('gauge_quantity'):
        selected_gauge = st.selectbox(
            "Манометр",
            [{'id': None, 'name': 'Все'}] + filter_options['gauge_quantity'],
            format_func=lambda x: x['name']
        )

with col3:
    st.markdown("### ")

# ==================== СТРОКА 5 (ФИЛЬТРАЦИЯ И РАСХОД) ====================
st.markdown("### ⚙️ Характеристики")
col1, col2 = st.columns(2)

with col1:
    min_filtration = st.number_input(
        "Тонкость фильтрации от (мкм)",
        value=None,
        placeholder="Не указано"
    )
    max_filtration = st.number_input(
        "Тонкость фильтрации до (мкм)",
        value=None,
        placeholder="Не указано"
    )

with col2:
    min_flow = st.number_input(
        "Расход от (л/мин)",
        value=None,
        placeholder="Не указано"
    )
    max_flow = st.number_input(
        "Расход до (л/мин)",
        value=None,
        placeholder="Не указано"
    )

# ==================== ФОРМИРУЕМ ПАРАМЕТРЫ ====================
params = {'limit': 100}

if search_text:
    params['search'] = search_text

# Прямые фильтры
if selected_line and selected_line.get('id'):
    params['model_line_id'] = selected_line['id']

if selected_drain and selected_drain.get('id'):
    params['drain_variety_id'] = selected_drain['id']

if selected_gauge and selected_gauge.get('id') is not None:
    params['gauge_quantity'] = selected_gauge['id']

if min_filtration:
    params['min_filtration_rating'] = min_filtration
if max_filtration:
    params['max_filtration_rating'] = max_filtration

if min_flow:
    params['min_flow_rate'] = min_flow
if max_flow:
    params['max_flow_rate'] = max_flow

# Фильтры по model_line
if selected_brand and selected_brand.get('id'):
    params['model_line_brand_id'] = selected_brand['id']

if selected_thread and selected_thread.get('id'):
    params['body_thread_id'] = selected_thread['id']

if selected_filter_variety and selected_filter_variety.get('id'):
    params['model_line_filter_variety_id'] = selected_filter_variety['id']

if selected_body_material and selected_body_material.get('id'):
    params['model_line_body_material_id'] = selected_body_material['id']

if min_work_temp:
    params['work_temp_min'] = min_work_temp
if max_work_temp:
    params['work_temp_max'] = max_work_temp

if required_min_pressure:
    params['pressure_min'] = required_min_pressure  # оборудование должно иметь давление НЕ ВЫШЕ # user_min - используем max_value_filter
if required_max_pressure:
    params['pressure_max'] = required_max_pressure  # user_max - используем min_value_filter оборудование должно иметь давление НЕ НИЖЕ

if max_inlet_pressure:
    params['pressure_inlet_max'] = max_inlet_pressure

# ==================== ЗАГРУЖАЕМ ДАННЫЕ ====================
result = FilterRegulator.filter_by_params(params)

st.write(f"**Найдено:** {result['total']} | **Загружено:** {len(result['data'])}")

# Отображаем результаты
for item in result['data']:
    with st.expander(f"{item['name']} ({item['code']})"):
        # Основная информация
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Серия:** {item['model_line']['name'] if item['model_line'] else '-'}")
            if item.get('model_line'):
                brand_name = item['model_line'].get('brand', {}).get('name', '-') if isinstance(
                    item['model_line'].get('brand'), dict) else '-'
                st.write(f"**Бренд:** {brand_name}")
            st.write(f"**Тип дренажа:** {item['drain_variety']['name'] if item['drain_variety'] else '-'}")
            st.write(f"**Манометр:** {item.get('gauge_quantity_display', '-')}")

        with col2:
            st.write(f"**Тонкость фильтрации:** {item.get('filtration_rating', '-')} мкм")
            st.write(f"**Расход:** {item.get('flow_rate', '-')} л/мин")
            if item.get('body') and item['body'].get('thread'):
                thread_name = item['body']['thread'].get('name', '-') if isinstance(item['body']['thread'],
                                                                                    dict) else '-'
                st.write(f"**Резьба корпуса:** {thread_name}")

        # Параметры серии
        if item.get('model_line'):
            st.markdown("---")
            st.markdown("**📊 Параметры серии:**")

            col1, col2, col3 = st.columns(3)
            with col1:
                filter_variety_name = item['model_line'].get('filter_variety', {}).get('name', '-') if isinstance(
                    item['model_line'].get('filter_variety'), dict) else '-'
                body_material_name = item['model_line'].get('body_material', {}).get('name', '-') if isinstance(
                    item['model_line'].get('body_material'), dict) else '-'
                st.write(f"**Разновидность:** {filter_variety_name}")
                st.write(f"**Материал корпуса:** {body_material_name}")
            with col2:
                st.write(
                    f"**Температура:** {item['model_line'].get('work_temp_min', '-')}...{item['model_line'].get('work_temp_max', '-')} °C")
            with col3:
                st.write(
                    f"**Давление:** {item['model_line'].get('pressure_min', '-')}...{item['model_line'].get('pressure_max', '-')} бар")
                st.write(f"**Макс. входное давление:** {item['model_line'].get('pressure_inlet_max', '-')} бар")