# pages/solenoid_valves.py

import streamlit as st
from solenoid_valves.models import DirectionValve

st.set_page_config(page_title="Каталог пневмораспределителей", layout="wide")
st.title("🔧 Каталог пневмораспределителей")

# Получаем опции фильтров
filter_options = DirectionValve.get_filter_options()

# ==================== СТРОКА 1 ====================
st.markdown("### 🔍 Основные фильтры")
col1, col2, col3 = st.columns(3)

with col1:
    search_text = st.text_input("Поиск по коду", placeholder="Введите код...")

with col2:
    if filter_options.get('brand_id'):
        selected_brand = st.selectbox(
            "Бренд",
            [{'id': None, 'name': 'Все'}] + filter_options['brand_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_brand = None

with col3:
    if filter_options.get('model_line_id'):
        selected_line = st.selectbox(
            "Серия",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_line = None

# ==================== СТРОКА 2 ====================
st.markdown("### ⚙️ Параметры клапана")
col1, col2, col3 = st.columns(3)

with col1:
    if filter_options.get('function_id'):
        selected_function = st.selectbox(
            "Схема (функция)",
            [{'id': None, 'name': 'Все'}] + filter_options['function_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_function = None

with col2:
    if filter_options.get('ip_id'):
        selected_ip = st.selectbox(
            "IP",
            [{'id': None, 'name': 'Все'}] + filter_options['ip_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_ip = None

with col3:
    if filter_options.get('exd_id'):
        selected_exd = st.selectbox(
            "Взрывозащита",
            [{'id': None, 'name': 'Все'}] + filter_options['exd_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_exd = None

# ==================== СТРОКА 3 ====================
col1, col2, col3 = st.columns(3)

with col1:
    if filter_options.get('power_supply_id'):
        selected_power = st.selectbox(
            "Напряжение питания",
            [{'id': None, 'name': 'Все'}] + filter_options['power_supply_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_power = None

with col2:
    kv_min = st.number_input(
        "Kv (м³/ч) ≥",
        value=None,
        placeholder="Не указано",
        step=0.1,
        format="%.2f"
    )

with col3:
    if filter_options.get('body_material_id'):
        selected_body_mat = st.selectbox(
            "Материал корпуса",
            [{'id': None, 'name': 'Все'}] + filter_options['body_material_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_body_mat = None

# ==================== СТРОКА 4 ====================
col1, col2, col3 = st.columns(3)

with col1:
    if filter_options.get('solenoid_body_material_id'):
        selected_solenoid_mat = st.selectbox(
            "Материал соленоида",
            [{'id': None, 'name': 'Все'}] + filter_options['solenoid_body_material_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_solenoid_mat = None

with col2:
    if filter_options.get('pneumatic_connection_id'):
        selected_pneumo = st.selectbox(
            "Пневмоподключение",
            [{'id': None, 'name': 'Все'}] + filter_options['pneumatic_connection_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_pneumo = None

with col3:
    work_temp_min = st.number_input(
        "Мин. температура (≤ °C)",
        value=None,
        placeholder="Не указано",
        step=5
    )

# ==================== СТРОКА 5 ====================
col1, col2, col3 = st.columns(3)

with col1:
    work_temp_max = st.number_input(
        "Макс. температура (≥ °C)",
        value=None,
        placeholder="Не указано",
        step=5
    )

with col2:
    limit = st.number_input("Лимит записей", min_value=1, max_value=1000, value=100)

# ==================== ФОРМИРУЕМ ПАРАМЕТРЫ ====================
params = {'limit': limit}

if search_text:
    params['search'] = search_text

if selected_brand and selected_brand.get('id'):
    params['brand_id'] = selected_brand['id']

if selected_line and selected_line.get('id'):
    params['model_line_id'] = selected_line['id']

if selected_function and selected_function.get('id'):
    params['function_id'] = selected_function['id']

if selected_ip and selected_ip.get('id'):
    params['ip_id'] = selected_ip['id']

if selected_exd and selected_exd.get('id'):
    params['exd_id'] = selected_exd['id']

if selected_power and selected_power.get('id'):
    params['power_supply_id'] = selected_power['id']

if kv_min:
    params['kv'] = kv_min

if selected_body_mat and selected_body_mat.get('id'):
    params['body_material_id'] = selected_body_mat['id']

if selected_solenoid_mat and selected_solenoid_mat.get('id'):
    params['solenoid_body_material_id'] = selected_solenoid_mat['id']

if selected_pneumo and selected_pneumo.get('id'):
    params['pneumatic_connection_id'] = selected_pneumo['id']

if work_temp_min:
    params['work_temp_min'] = work_temp_min

if work_temp_max:
    params['work_temp_max'] = work_temp_max

# ==================== ЗАГРУЖАЕМ ДАННЫЕ ====================
result = DirectionValve.filter_by_params(params)

st.markdown("---")
st.markdown("### 📈 Результаты")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Найдено записей", result['total'])
with col2:
    compat_count = result.get('compatible_total', 0)
    st.metric("Совместимых", compat_count)
with col3:
    st.metric("Загружено", len(result['data']) + len(result.get('compatible_data', [])))

if result.get('filters_applied'):
    st.write(f"**Применённые фильтры:** {result['filters_applied']}")


# ==================== ФУНКЦИЯ ОТРИСОВКИ КАРТОЧКИ ====================
def _render_valve(item, badge=None):
    expander_title = item.get('name', '')
    if item.get('code'):
        expander_title += f" ({item['code']})"

    with st.expander(expander_title):
        if badge:
            st.caption(badge)
        if item.get('description'):
            st.markdown(f"**📝 Описание:** {item['description']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📋 Основное:**")
            st.write(f"**Бренд:** {item['brand']['name'] if item.get('brand') else '-'}")
            st.write(f"**Серия:** {item['model_line']['name'] if item.get('model_line') else '-'}")
            st.write(f"**Схема:** {item['function']['name'] if item.get('function') else '-'}")
            st.write(f"**IP:** {item['ip']['name'] if item.get('ip') else '-'}")
            st.write(f"**Exd:** {item['exd']['name'] if item.get('exd') else '-'}")

        with col2:
            st.markdown("**⚙️ Характеристики:**")
            st.write(f"**Питание:** {item['power_supply']['name'] if item.get('power_supply') else '-'}")
            st.write(f"**Kv:** {item.get('kv', '-')} м³/ч" if item.get('kv') else "**Kv:** -")
            st.write(f"**Материал корпуса:** {item['body_material']['name'] if item.get('body_material') else '-'}")
            st.write(
                f"**Материал соленоида:** {item['solenoid_body_material']['name'] if item.get('solenoid_body_material') else '-'}")
            st.write(
                f"**Пневмоподключение:** {item['pneumatic_connection']['name'] if item.get('pneumatic_connection') else '-'}")
            temp_range = f"{item.get('work_temp_min', '-')}…{item.get('work_temp_max', '-')} °C"
            st.write(f"**Температура:** {temp_range}")


# ==================== ТОЧНЫЕ СОВПАДЕНИЯ ====================
if result['data']:
    st.markdown("---")
    st.markdown("### 🎯 Точные совпадения")
    for item in result['data']:
        _render_valve(item)

# ==================== СОВМЕСТИМЫЕ ====================
if result.get('compatible_data'):
    st.markdown("---")
    st.markdown("### 🔗 Совместимые схемы (например, 3/2 ↔ 5/2)")
    for item in result['compatible_data']:
        _render_valve(item)
