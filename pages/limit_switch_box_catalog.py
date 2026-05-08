# pages/limit_switch_box_catalog.py

import streamlit as st

from pa_controls.models.limit_switch import LimitSwitchBox
from params.models import ExdOption

st.title("Отладка блоков концевых выключателей")

# Получаем опции фильтров (автоматически из FILTER_DEFINITIONS)
filter_options = LimitSwitchBox.get_filter_options()

# Получаем иерархическую структуру Exd
exd_structure = ExdOption.get_structured_choices()

# ==================== ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ====================
search_text = None
selected_line = None
selected_brand = None
selected_sensor = None
selected_points = None
selected_ip = None
min_temp = None
max_temp = None
selected_signal_type = None
selected_contact_form = None
selected_method = None
selected_type = None
selected_temp = None
selected_group = None

# ==================== СТРОКА 1 ====================
col1, col2, col3, col4 = st.columns(4)

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
    if filter_options.get('model_line_brand_id'):
        selected_brand = st.selectbox(
            "Бренд",
            [{'id': None, 'name': 'Все'}] + filter_options['model_line_brand_id'],
            format_func=lambda x: x['name']
        )

with col4:
    if filter_options.get('sensor_variety_id'):
        selected_sensor = st.selectbox(
            "Тип сенсора",
            [{'id': None, 'name': 'Все'}] + filter_options['sensor_variety_id'],
            format_func=lambda x: x['name']
        )

# ==================== СТРОКА 2 ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    if filter_options.get('points'):
        selected_points = st.selectbox(
            "Количество датчиков",
            [{'id': None, 'name': 'Все'}] + filter_options['points'],
            format_func=lambda x: x['name']
        )

with col2:
    if filter_options.get('ip_id'):
        selected_ip = st.selectbox(
            "IP",
            [{'id': None, 'name': 'Все'}] + filter_options['ip_id'],
            format_func=lambda x: x['name']
        )

with col3:
    min_temp = st.number_input("Температура от (°C)", value=None, placeholder="Не указано")

with col4:
    max_temp = st.number_input("Температура до (°C)", value=None, placeholder="Не указано")

# ==================== СТРОКА 3 (ДАТЧИКИ) ====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    if filter_options.get('signal_type_id'):
        selected_signal_type = st.selectbox(
            "Тип сигнала датчика",
            [{'id': None, 'name': 'Все'}] + filter_options['signal_type_id'],
            format_func=lambda x: x['name']
        )

with col2:
    if filter_options.get('contact_form_id'):
        selected_contact_form = st.selectbox(
            "Форма контактов датчика",
            [{'id': None, 'name': 'Все'}] + filter_options['contact_form_id'],
            format_func=lambda x: x['name']
        )

with col3:
    st.markdown("")

with col4:
    st.markdown("")

# ==================== СТРОКА 4 (ВЗРЫВОЗАЩИТА) ====================
st.markdown("### 💥 Взрывозащита")

col1, col2, col3,col4 = st.columns(4)
with col1:
    methods = exd_structure.get('methods', [])

    method_list = [{'id': None, 'name': 'Все методы', 'description': ''}] + methods

    selected_method = st.selectbox(
        "Метод взрывозащиты",
        options=method_list,
        format_func=lambda x: x['name'],
        key="exd_method"
    )

    # Извлекаем ID (число или None)
    selected_method_id = selected_method['id'] if selected_method and selected_method.get('id') else None

    if selected_method_id:
        st.caption(f"📖 {selected_method['description']}")
# with col1:
#     methods = exd_structure.get('methods', [])
#     method_options = {None: "Все методы"}
#     for m in methods:
#         # method_options[m['id']] = f"Ex {m['code']} - {m['name']}"
#         method_options[m['id']] = f"{m['name']}"
#
#     selected_method = st.selectbox(
#         "Метод взрывозащиты",
#         options=list(method_options.keys()),
#         format_func=lambda x: method_options.get(x, "Все"),
#         key="exd_method"
#     )
#     # Опционально: показывать тип группы (газ/пыль)
#     if selected_method:
#         method = next((g for g in method_options if g['id'] == selected_method), None)
#         if method:
#             st.caption(f" { method['description']}")

with col2:
    type_list = [{'id': None, 'name': 'Все типы', 'code': ''}]
    if selected_method_id:
        method = next((m for m in methods if m['id'] == selected_method_id), None)
        if method and method.get('types'):
            for t in method['types']:
                type_list.append({
                    'id': t['id'],
                    'name': f"Ex {t['code']} - {t['name']}",
                    'code': t['code']
                })

    selected_type = st.selectbox(
        "Тип взрывозащиты",
        options=type_list,
        format_func=lambda x: x['name'],
        key="exd_type"
    )

    selected_type_id = selected_type['id'] if selected_type and selected_type.get('id') else None
with col3:
    # Группы (объединенные газ и пыль)
    groups = exd_structure.get('groups', [])

    group_list = [{'id': None, 'name': 'Все группы', 'code': ''}] + [
        {'id': g['id'], 'name': g['code'], 'code': g['code'], 'group_type': g['group_type']}
        for g in groups
    ]

    selected_group = st.selectbox(
        "Группа взрывоопасной среды",
        options=group_list,
        format_func=lambda x: x['name'],
        key="exd_group"
    )

    selected_group_id = selected_group['id'] if selected_group and selected_group.get('id') else None

    # Опционально: показывать тип группы (газ/пыль)
    if selected_group:
        group = next((g for g in groups if g['id'] == selected_group), None)
        if group:
            st.caption(f"Тип: {'Газ' if group['group_type'] == 'GAS' else 'Пыль'}")

with col4:
    temp_classes = exd_structure.get('temperature_classes', [])

    temp_list = [{'id': None, 'name': 'Все классы', 'code': ''}] + [
        {'id': t['id'], 'name': f"{t['code']} ({t['max_temp']}°C)", 'code': t['code']}
        for t in temp_classes
    ]

    selected_temp = st.selectbox(
        "Температурный класс",
        options=temp_list,
        format_func=lambda x: x['name'],
        key="exd_temp"
    )

    selected_temp_id = selected_temp['id'] if selected_temp and selected_temp.get('id') else None
# ==================== ФОРМИРУЕМ ПАРАМЕТРЫ ====================
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

if selected_group:
    params['exd_group_id'] = selected_group
# ==================== ФИЛЬТРАЦИЯ ПО EXD ====================
# Получаем совместимые ID ExdOption по выбранным параметрам
compatible_exd_ids = ExdOption.get_compatible_ids_by_components(
    method_id=selected_method_id,  # ← число или None
    type_id=selected_type_id,      # ← число или None
    group_id=selected_group_id,    # ← число или None
    temp_id=selected_temp_id       # ← число или None
)

if compatible_exd_ids:
    params['exd_id'] = list(compatible_exd_ids)
elif selected_method or selected_type or selected_group  or selected_temp:
    # Если выбраны фильтры взрывозащиты, но совместимых нет
    st.warning("⚠️ Нет записей, соответствующих выбранным параметрам взрывозащиты")
    st.stop()  # Останавливаем выполнение, показываем пустой результат
print("=" * 50)
print("DEBUG: Final params before filter_by_params:")
for key, value in params.items():
    print(f"  {key}: {value}")
print("=" * 50)
# ==================== ЗАГРУЖАЕМ ДАННЫЕ ====================
result = LimitSwitchBox.filter_by_params(params)

st.write(f"**Найдено:** {result['total']} | **Загружено:** {len(result['data'])}")

# ==================== ОТОБРАЖАЕМ РЕЗУЛЬТАТЫ ====================
for item in result['data']:
    with st.expander(f"{item['name']} ({item['code']})"):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Серия:** {item['model_line']['name'] if item['model_line'] else '-'}")
            st.write(
                f"**Бренд:** {item['model_line']['brand']['name'] if item.get('model_line') and item['model_line'].get('brand') else '-'}")
            st.write(f"**Тип сенсора:** {item['sensor_variety']['name'] if item['sensor_variety'] else '-'}")
            st.write(f"**Датчиков:** {item['points']}")

        with col2:
            st.write(f"**IP:** {item['ip']['name'] if item['ip'] else '-'}")
            st.write(f"**Температура:** {item['work_temp_min']}...{item['work_temp_max']} °C")
            if item.get('primary_sensor'):
                st.write(f"**Тип сигнала:** {item['primary_sensor'].get('signal_type', {}).get('name', '-')}")
                st.write(f"**Форма контактов:** {item['primary_sensor'].get('contact_form', {}).get('name', '-')}")

        if item.get('exd'):
            exd_names = [exd.get('name', '') for exd in item['exd']]
            st.write(f"**Взрывозащита:** {', '.join(exd_names)}")

        st.write(f"**Датчики:** {item.get('sensors_names', '-')}")