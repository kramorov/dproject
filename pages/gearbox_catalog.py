# debug_gearbox.py
import streamlit as st
from gearbox.models import GearBox

st.title("Отладка редукторов")

# Получаем опции фильтров
filter_options = GearBox.get_filter_options()

# ==================== СТРОКА 1 ====================
st.markdown("### 🔍 Фильтры")
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Поиск по коду/названию
    search_text = st.text_input("Поиск", placeholder="Код или название...")

with col2:
    # Фильтр по максимальному рабочему моменту
    min_work_torque = st.number_input(
        "Рабочий момент от (Нм)",
        value=None,
        placeholder="Не указано",
        step=10.0
    )

with col3:
    # Фильтр по минимальной температуре
    temp_min = st.number_input(
        "Температура от (°С)",
        value=None,
        placeholder="Не указано",
        step=5
    )

with col4:
    # Фильтр по IP
    if filter_options.get('ip_options'):
        selected_ip = st.selectbox(
            "IP",
            [{'id': None, 'name': 'Все'}] + filter_options['ip_options'],
            format_func=lambda x: x['name']
        )
    else:
        selected_ip = None

# ==================== СТРОКА 2 ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Фильтр по серии
    if filter_options.get('model_lines'):
        selected_line = st.selectbox(
            "Серия",
            [{'id': None, 'name': 'Все'}] + filter_options['model_lines'],
            format_func=lambda x: x['name']
        )
    else:
        selected_line = None

with col2:
    # Фильтр по корпусу
    if filter_options.get('bodies'):
        selected_body = st.selectbox(
            "Корпус",
            [{'id': None, 'name': 'Все'}] + filter_options['bodies'],
            format_func=lambda x: x['name']
        )
    else:
        selected_body = None

with col3:
    # Фильтр по максимальной температуре
    temp_max = st.number_input(
        "Температура до (°С)",
        value=None,
        placeholder="Не указано",
        step=5
    )

with col4:
    # Фильтр по монтажной площадке
    if filter_options.get('mounting_plate_top_options'):
        selected_plate = st.selectbox(
            "Монтажная площадка",
            [{'id': None, 'name': 'Все'}] + filter_options['mounting_plate_top_options'],
            format_func=lambda x: x['name']
        )
    else:
        selected_plate = None

# ==================== ПАРАМЕТРЫ ЗАГРУЗКИ ====================
st.markdown("### 📊 Параметры")
col1, col2 = st.columns(2)

with col1:
    limit = st.number_input("Лимит записей", min_value=1, max_value=1000, value=50)

with col2:
    show_full_details = st.checkbox("Все детали", value=False)

# ==================== ФОРМИРУЕМ ПАРАМЕТРЫ ====================
params = {'limit': limit}

if search_text:
    params['search'] = search_text

if min_work_torque:
    params['min_work_torque'] = min_work_torque

if temp_min:
    params['temp_min'] = temp_min

if temp_max:
    params['temp_max'] = temp_max

if selected_ip and selected_ip.get('id'):
    params['ip_id'] = selected_ip['id']

if selected_line and selected_line.get('id'):
    params['model_line_id'] = selected_line['id']

if selected_body and selected_body.get('id'):
    params['body_id'] = selected_body['id']

if selected_plate and selected_plate.get('id'):
    params['mounting_plate_top_id'] = selected_plate['id']

# ==================== ЗАГРУЖАЕМ ДАННЫЕ ====================
result = GearBox.filter_by_params(params)

st.markdown("---")
st.markdown("### 📈 Результаты")

col1, col2 = st.columns(2)
with col1:
    st.metric("Найдено записей", result['total'])
with col2:
    st.metric("Загружено записей", len(result['data']))

if result['filters_applied']:
    st.write(f"**Примененные фильтры:** {result['filters_applied']}")

# ==================== ОТОБРАЖАЕМ КАРТОЧКИ ====================
for item in result['data']:
    expander_title = f"{item['name']} ({item['code']})"

    # Добавляем рабочий момент в заголовок если есть
    if item.get('body') and item['body'].get('max_work_torque'):
        expander_title += f" | {item['body']['max_work_torque']} Нм"

    with st.expander(expander_title):
        # Описание
        if item.get('description'):
            st.markdown(f"**📝 Описание:** {item['description']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📋 Основное:**")
            st.write(f"**Серия:** {item['model_line']['name'] if item['model_line'] else '-'}")
            st.write(f"**Корпус:** {item['body']['name'] if item['body'] else '-'}")
            st.write(f"**Температура:** {item['work_temp_min']}...{item['work_temp_max']} °C")
            st.write(f"**IP:** {item['ip']['name'] if item['ip'] else '-'}")

        with col2:
            if item.get('body'):
                st.markdown("**⚙️ Корпус:**")
                st.write(f"**Рабочий момент:** {item['body'].get('max_work_torque', '-')} Нм")

                # Монтажные площадки
                if item['body'].get('mounting_plate_top'):
                    plates = ", ".join([p['name'] for p in item['body']['mounting_plate_top']])
                    st.write(f"**Площадки:** {plates}")

        # Детальная информация о корпусе
        if show_full_details and item.get('body'):
            st.markdown("---")
            st.markdown("**🔧 Детали корпуса:**")

            body = item['body']

            # Характеристики корпуса
            cols = st.columns(2)
            with cols[0]:
                if body.get('reduction_ratio'):
                    st.write(f"**Передаточное число:** {body['reduction_ratio']}")
                if body.get('efficiency'):
                    st.write(f"**КПД:** {body['efficiency']:.1%}" if body[
                                                                         'efficiency'] < 1 else f"**КПД:** {body['efficiency']}")
                if body.get('max_input_torque'):
                    st.write(f"**Входной момент:** {body['max_input_torque']} Нм")
                if body.get('handwheel_diameter'):
                    st.write(f"**Диаметр штурвала:** {body['handwheel_diameter']} мм")

            with cols[1]:
                if body.get('weight'):
                    st.write(f"**Вес:** {body['weight']} кг")
                if body.get('material'):
                    st.write(f"**Материал:** {body['material']}")

            # Присоединительные размеры
            if body.get('mounting_plate_top'):
                st.markdown("**Монтажные площадки (сверху):**")
                for plate in body['mounting_plate_top']:
                    st.write(f"  - {plate['name']}")

            if body.get('mounting_plate_bottom'):
                st.markdown("**Монтажные площадки (снизу):**")
                for plate in body['mounting_plate_bottom']:
                    st.write(f"  - {plate['name']}")