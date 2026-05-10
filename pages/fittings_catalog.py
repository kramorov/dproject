# pages/fittings_catalog.py

import streamlit as st
from pneumatic_fittings.models import PneumaticFitting

st.set_page_config(page_title="Каталог фитингов", layout="wide")
st.title("🔧 Каталог пневматических фитингов")

# Получаем опции фильтров
filter_options = PneumaticFitting.get_filter_options()

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
    if filter_options.get('fitting_model_line_id'):
        selected_line = st.selectbox(
            "Серия",
            [{'id': None, 'name': 'Все'}] + filter_options['fitting_model_line_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_line = None

# ==================== СТРОКА 2 ====================
st.markdown("### 🔧 Параметры фитинга")
col1, col2, col3 = st.columns(3)

with col1:
    if filter_options.get('fitting_variety_id'):
        selected_variety = st.selectbox(
            "Тип фитинга",
            [{'id': None, 'name': 'Все'}] + filter_options['fitting_variety_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_variety = None

with col2:
    if filter_options.get('body_material_id'):
        selected_body_material = st.selectbox(
            "Материал корпуса",
            [{'id': None, 'name': 'Все'}] + filter_options['body_material_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_body_material = None

with col3:
    if filter_options.get('pipe_material_id'):
        selected_pipe_material = st.selectbox(
            "Материал трубки",
            [{'id': None, 'name': 'Все'}] + filter_options['pipe_material_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_pipe_material = None

# ==================== СТРОКА 3 ====================
col1, col2, col3 = st.columns(3)

with col1:
    if filter_options.get('pipe_diameter'):
        selected_diameter = st.selectbox(
            "Диаметр трубки",
            [{'id': None, 'name': 'Все'}] + filter_options['pipe_diameter'],
            format_func=lambda x: f"{x['name']} мм" if x['id'] is not None else x['name']
        )
    else:
        selected_diameter = None

with col2 :
    if filter_options.get('thread_type_id') :
        selected_thread_type = st.selectbox(
            "Тип резьбы" ,
            [{'id' : None , 'name' : 'Все'}] + filter_options['thread_type_id'] ,
            format_func=lambda x : x['name']
        )
    else :
        selected_thread_type = None

with col3 :
    # Каскад: резьбы фильтруются по выбранному типу
    if selected_thread_type and selected_thread_type.get('id') :
        thread_options = PneumaticFitting.get_cascade_options(
            'thread_type_id' , selected_thread_type['id']
        )
    else :
        thread_options = filter_options.get('thread_id' , [])

    if thread_options :
        selected_thread = st.selectbox(
            "Резьба" ,
            [{'id' : None , 'name' : 'Все'}] + thread_options ,
            format_func=lambda x : x['name']
        )
    else :
        selected_thread = None

    # ==================== СТРОКА 4 ====================
col1, col2, col3 = st.columns(3)

with col1:
    if filter_options.get('thread_inner_outer_id'):
        selected_tio = st.selectbox(
            "Резьба (нар/внут)",
            [{'id': None, 'name': 'Все'}] + filter_options['thread_inner_outer_id'],
            format_func=lambda x: x['name']
        )
    else:
        selected_tio = None

with col2:
    temp_min = st.number_input(
        "Мин. температура (≤ °C)",
        value=None,
        placeholder="Не указано",
        step=5
    )

with col3:
    limit = st.number_input("Лимит записей", min_value=1, max_value=1000, value=100)

# ==================== ФОРМИРУЕМ ПАРАМЕТРЫ ====================
params = {'limit': limit}

if search_text:
    params['search'] = search_text

if selected_brand and selected_brand.get('id'):
    params['brand_id'] = selected_brand['id']

if selected_line and selected_line.get('id'):
    params['fitting_model_line_id'] = selected_line['id']

if selected_variety and selected_variety.get('id'):
    params['fitting_variety_id'] = selected_variety['id']

if selected_body_material and selected_body_material.get('id'):
    params['body_material_id'] = selected_body_material['id']

if selected_pipe_material and selected_pipe_material.get('id'):
    params['pipe_material_id'] = selected_pipe_material['id']

if selected_diameter and selected_diameter.get('id'):
    params['pipe_diameter'] = selected_diameter['id']

if selected_thread and selected_thread.get('id') :
    # COMPATIBLE_CASCADE сам учтёт совместимые типы — thread_type_id не нужен
    params['thread_id'] = selected_thread['id']
elif selected_thread_type and selected_thread_type.get('id') :
    # Только тип, без конкретной резьбы
    params['thread_type_id'] = selected_thread_type['id']

if selected_tio and selected_tio.get('id'):
    params['thread_inner_outer_id'] = selected_tio['id']

if temp_min:
    params['temp_min'] = temp_min

# ==================== ЗАГРУЖАЕМ ДАННЫЕ ====================
result = PneumaticFitting.filter_by_params(params)

st.markdown("---")
st.markdown("### 📈 Результаты")

col1, col2 = st.columns(2)
with col1:
    st.metric("Найдено записей", result['total'])
with col2:
    st.metric("Загружено записей", len(result['data']))

if result.get('filters_applied'):
    st.write(f"**Применённые фильтры:** {result['filters_applied']}")

# ==================== ОТОБРАЖАЕМ КАРТОЧКИ ====================
for item in result['data']:
    expander_title = item['name']
    if item.get('code'):
        expander_title += f" ({item['code']})"
    if item.get('pipe_diameter'):
        expander_title += f" | ⌀{item['pipe_diameter']} мм"

    with st.expander(expander_title):
        if item.get('description'):
            st.markdown(f"**📝 Описание:** {item['description']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📋 Основное:**")
            st.write(f"**Бренд:** {item['brand']['name'] if item.get('brand') else '-'}")
            st.write(f"**Серия:** {item['model_line']['name'] if item.get('model_line') else '-'}")
            st.write(f"**Тип фитинга:** {item['fitting_variety']['name'] if item.get('fitting_variety') else '-'}")
            st.write(f"**Диаметр трубки:** {item.get('pipe_diameter', '-')} мм" if item.get('pipe_diameter') else "**Диаметр трубки:** -")
            # Badge совместимости резьбы
            if selected_thread_type and selected_thread_type.get('id') :
                item_thread = item.get('thread' , {}) or {}
                item_tt = item_thread.get('thread_type' , {}) or {}
                if item_tt.get('id') and item_tt['id'] != selected_thread_type['id'] :
                    st.caption(
                        f"🔗 Совместимая резьба: {item_tt.get('name' , '')} (выбрано: {selected_thread_type['name']})")

        with col2:
            st.markdown("**⚙️ Характеристики:**")
            st.write(f"**Материал корпуса:** {item['body_material']['name'] if item.get('body_material') else '-'}")
            st.write(f"**Материал трубки:** {item['pipe_material']['name'] if item.get('pipe_material') else '-'}")
            st.write(f"**Резьба:** {item['thread']['name'] if item.get('thread') else '-'}")
            st.write(f"**Тип резьбы:** {item['thread_inner_outer']['name'] if item.get('thread_inner_outer') else '-'}")
            temp_range = f"{item.get('temp_min', '-')}…{item.get('temp_max', '-')} °C"
            st.write(f"**Температура:** {temp_range}")

        # Дополнительные параметры если есть
        if item.get('flow_rate') or item.get('operating_pressure'):
            st.markdown("---")
            st.markdown("**📊 Дополнительно:**")
            extras_col1, extras_col2 = st.columns(2)
            with extras_col1:
                if item.get('flow_rate'):
                    st.write(f"**Расход:** {item['flow_rate']} л/мин")
            with extras_col2:
                if item.get('operating_pressure'):
                    st.write(f"**Рабочее давление:** {item['operating_pressure']} бар")
