#pages/pneumatic_actuators/pa_selection.py
# Подбор пневматического привода

# pages/pa_selection.py

import streamlit as st
from db_init import init_django
from decimal import Decimal

init_django()

# Импортируем обработчик напрямую (без API!)
from pneumatic_actuators.actuator_selector_handler import (
    get_initial_data ,
    get_filtered_model_line_items ,
    get_actuator_options
)

st.set_page_config(page_title="Подбор пневматического привода" , layout="wide")
st.title("🔧 Подбор пневматического привода")


def init_session_state() :
    """Инициализация session state"""
    # Параметры арматуры
    if 'dn_id' not in st.session_state :
        st.session_state.dn_id = None
    if 'pn_id' not in st.session_state :
        st.session_state.pn_id = None
    if 'mounting_plate_id' not in st.session_state :
        st.session_state.mounting_plate_id = None
    if 'stem_id' not in st.session_state :
        st.session_state.stem_id = None

    # Моменты
    if 'torque_without_safety' not in st.session_state :
        st.session_state.torque_without_safety = Decimal('0')
    if 'safety_factor' not in st.session_state :
        st.session_state.safety_factor = Decimal('1.3')
    if 'torque_with_safety' not in st.session_state :
        st.session_state.torque_with_safety = Decimal('0')

    # Требования к приводу
    if 'model_line_id' not in st.session_state :
        st.session_state.model_line_id = None
    if 'model_line_item_id' not in st.session_state :
        st.session_state.model_line_item_id = None
    if 'actuator_variety_id' not in st.session_state :
        st.session_state.actuator_variety_id = None
    if 'actuator_variety_code' not in st.session_state :
        st.session_state.actuator_variety_code = None
    if 'safety_position_id' not in st.session_state :
        st.session_state.safety_position_id = None
    if 'ip_id' not in st.session_state :
        st.session_state.ip_id = None
    if 'exd_id' not in st.session_state :
        st.session_state.exd_id = None
    if 'coating_id' not in st.session_state :
        st.session_state.coating_id = None
    if 'hand_wheel_id' not in st.session_state :
        st.session_state.hand_wheel_id = None
    if 'temp_min' not in st.session_state :
        st.session_state.temp_min = 0
    if 'temp_max' not in st.session_state :
        st.session_state.temp_max = 0

    # Кэш для опций
    if 'options_cache' not in st.session_state :
        st.session_state.options_cache = {}


def load_initial_data() :
    """Загружает начальные данные (с кэшированием)"""
    if 'initial_data' not in st.session_state :
        st.session_state.initial_data = get_initial_data()
    return st.session_state.initial_data


def load_actuator_options() :
    """Загружает опции для привода на основе выбранных model_line/model_line_item"""
    cache_key = f"options_{st.session_state.model_line_id}_{st.session_state.model_line_item_id}"

    if cache_key not in st.session_state.options_cache :
        st.session_state.options_cache[cache_key] = get_actuator_options(
            model_line_id=st.session_state.model_line_id ,
            model_line_item_id=st.session_state.model_line_item_id
        )

    return st.session_state.options_cache[cache_key]


def render_actuator_requirements() :
    """Рендер блока требований к приводу"""
    st.markdown("### 🔧 Требования к приводу")

    initial_data = load_initial_data()

    # Серия моделей
    model_lines = initial_data.get('model_lines' , [])
    model_line_options = {0 : "Выберите серию"}
    for ml in model_lines :
        model_line_options[ml['id']] = f"{ml['name']} ({ml['code']})" if ml.get('code') else ml['name']

    model_line_id = st.selectbox(
        "Серия моделей" ,
        options=list(model_line_options.keys()) ,
        format_func=lambda x : model_line_options.get(x , "Выберите") ,
        key="model_line_select"
    )

    if model_line_id != st.session_state.model_line_id :
        st.session_state.model_line_id = model_line_id
        st.session_state.model_line_item_id = None
        # Очищаем кэш опций при смене серии
        st.session_state.options_cache = {}
        st.rerun()

    # Вид пневмопривода (загружаем из кэша или обработчика)
    actuator_options = load_actuator_options()
    actuator_varieties = actuator_options.get('actuator_varieties' , [])

    variety_options = {0 : "Выберите вид привода"}
    for av in actuator_varieties :
        variety_options[av['id']] = f"{av['name']} ({av['code']})"

    actuator_variety_id = st.selectbox(
        "Вид пневмопривода" ,
        options=list(variety_options.keys()) ,
        format_func=lambda x : variety_options.get(x , "Выберите") ,
        key="actuator_variety_select"
    )

    # Сохраняем код выбранного вида привода
    if actuator_variety_id != st.session_state.actuator_variety_id :
        st.session_state.actuator_variety_id = actuator_variety_id
        for av in actuator_varieties :
            if av['id'] == actuator_variety_id :
                st.session_state.actuator_variety_code = av.get('code')
                break
        st.session_state.model_line_item_id = None
        # Очищаем кэш опций
        st.session_state.options_cache = {}
        st.rerun()

    # Модель в серии (зависит от серии и вида привода)
    model_items = get_filtered_model_line_items(
        model_line_id=st.session_state.model_line_id if st.session_state.model_line_id != 0 else None ,
        actuator_variety_code=st.session_state.actuator_variety_code
    )

    model_item_options = {0 : "Выберите модель"}
    for mi in model_items :
        model_item_options[mi['id']] = f"{mi['name']} ({mi['code']})" if mi.get('code') else mi['name']

    model_line_item_id = st.selectbox(
        "Модель в серии" ,
        options=list(model_item_options.keys()) ,
        format_func=lambda x : model_item_options.get(x , "Выберите") ,
        key="model_line_item_select"
    )

    if model_line_item_id != st.session_state.model_line_item_id :
        st.session_state.model_line_item_id = model_line_item_id
        # Очищаем кэш опций при смене модели
        st.session_state.options_cache = {}
        st.rerun()

    # Получаем актуальные опции (с учетом выбранной модели)
    actuator_options = load_actuator_options()

    # Положение безопасности (NO/NC)
    safety_positions = actuator_options.get('safety_positions' , [])
    safety_options = {0 : "Выберите положение безопасности"}
    for sp in safety_positions :
        safety_options[sp['id']] = sp['name']

    safety_position_id = st.selectbox(
        "NO/NC (положение безопасности)" ,
        options=list(safety_options.keys()) ,
        format_func=lambda x : safety_options.get(x , "Выберите") ,
        key="safety_position_select"
    )
    st.session_state.safety_position_id = safety_position_id if safety_position_id != 0 else None

    # IP защита
    ip_options_list = actuator_options.get('ip_options' , [])
    ip_options = {0 : "Выберите IP"}
    for ip_opt in ip_options_list :
        ip_options[ip_opt['id']] = ip_opt['name']

    ip_id = st.selectbox(
        "IP защита" ,
        options=list(ip_options.keys()) ,
        format_func=lambda x : ip_options.get(x , "Выберите") ,
        key="ip_select"
    )
    st.session_state.ip_id = ip_id if ip_id != 0 else None

    # Exd взрывозащита
    exd_options_list = actuator_options.get('exd_options' , [])
    exd_options = {0 : "Выберите Exd"}
    for exd_opt in exd_options_list :
        exd_options[exd_opt['id']] = exd_opt['name']

    exd_id = st.selectbox(
        "Exd взрывозащита" ,
        options=list(exd_options.keys()) ,
        format_func=lambda x : exd_options.get(x , "Выберите") ,
        key="exd_select"
    )
    st.session_state.exd_id = exd_id if exd_id != 0 else None

    # Покрытие корпуса
    coating_options_list = actuator_options.get('coating_options' , [])
    coating_options = {0 : "Выберите покрытие"}
    for coat in coating_options_list :
        coating_options[coat['id']] = coat['name']

    coating_id = st.selectbox(
        "Покрытие корпуса" ,
        options=list(coating_options.keys()) ,
        format_func=lambda x : coating_options.get(x , "Выберите") ,
        key="coating_select"
    )
    st.session_state.coating_id = coating_id if coating_id != 0 else None

    # Ручной дублер
    hand_wheel_options_list = actuator_options.get('hand_wheel_options' , [])
    hand_wheel_options = {0 : "Выберите ручной дублер"}
    for hw in hand_wheel_options_list :
        hand_wheel_options[hw['id']] = hw['name']

    hand_wheel_id = st.selectbox(
        "Ручной дублер" ,
        options=list(hand_wheel_options.keys()) ,
        format_func=lambda x : hand_wheel_options.get(x , "Выберите") ,
        key="hand_wheel_select"
    )
    st.session_state.hand_wheel_id = hand_wheel_id if hand_wheel_id != 0 else None

    # Температура
    col1 , col2 = st.columns(2)
    with col1 :
        temp_min = st.number_input(
            "Минимальная температура (°C)" ,
            value=st.session_state.temp_min ,
            step=5 ,
            min_value=-70 ,
            max_value=300 ,
            key="temp_min_input"
        )
        st.session_state.temp_min = temp_min

    with col2 :
        temp_max = st.number_input(
            "Максимальная температура (°C)" ,
            value=st.session_state.temp_max ,
            step=5 ,
            min_value=-70 ,
            max_value=300 ,
            key="temp_max_input"
        )
        st.session_state.temp_max = temp_max


def main() :
    init_session_state()

    # Параметры арматуры
    st.markdown("### 📋 Параметры арматуры")

    initial_data = load_initial_data()

    col1 , col2 = st.columns(2)

    with col1 :
        dn_list = initial_data.get('dn_varieties' , [])
        dn_options = {0 : "Выберите DN"}
        for dn in dn_list :
            dn_options[dn['id']] = dn['name']
        dn_id = st.selectbox(
            "DN" ,
            options=list(dn_options.keys()) ,
            format_func=lambda x : dn_options.get(x , "Выберите") ,
            key="dn_select"
        )
        st.session_state.dn_id = dn_id if dn_id != 0 else None

    with col2 :
        pn_list = initial_data.get('pn_varieties' , [])
        pn_options = {0 : "Выберите PN"}
        for pn in pn_list :
            pn_options[pn['id']] = pn['name']
        pn_id = st.selectbox(
            "PN" ,
            options=list(pn_options.keys()) ,
            format_func=lambda x : pn_options.get(x , "Выберите") ,
            key="pn_select"
        )
        st.session_state.pn_id = pn_id if pn_id != 0 else None

    col1 , col2 = st.columns(2)

    with col1 :
        plate_list = initial_data.get('mounting_plates' , [])
        plate_options = {0 : "Выберите монтажную площадку"}
        for plate in plate_list :
            plate_options[plate['id']] = plate['name']
        plate_id = st.selectbox(
            "Монтажная площадка" ,
            options=list(plate_options.keys()) ,
            format_func=lambda x : plate_options.get(x , "Выберите") ,
            key="plate_select"
        )
        st.session_state.mounting_plate_id = plate_id if plate_id != 0 else None

    with col2 :
        stem_list = initial_data.get('stem_sizes' , [])
        stem_options = {0 : "Выберите шток"}
        for stem in stem_list :
            stem_options[stem['id']] = stem['name']
        stem_id = st.selectbox(
            "Шток" ,
            options=list(stem_options.keys()) ,
            format_func=lambda x : stem_options.get(x , "Выберите") ,
            key="stem_select"
        )
        st.session_state.stem_id = stem_id if stem_id != 0 else None

    # Моменты
    st.markdown("### ⚙️ Расчет момента")

    col1 , col2 , col3 = st.columns(3)

    with col1 :
        torque_without_safety = st.number_input(
            "Момент без запаса (Нм)" ,
            value=float(st.session_state.torque_without_safety) ,
            step=0.1 ,
            format="%.1f" ,
            key="torque_without_safety_input"
        )
        if Decimal(str(torque_without_safety)) != st.session_state.torque_without_safety :
            st.session_state.torque_without_safety = Decimal(str(torque_without_safety))
            st.session_state.torque_with_safety = st.session_state.torque_without_safety * st.session_state.safety_factor
            st.rerun()

    with col2 :
        safety_factor = st.number_input(
            "Коэффициент запаса" ,
            value=float(st.session_state.safety_factor) ,
            step=0.1 ,
            format="%.2f" ,
            min_value=1.0 ,
            max_value=5.0 ,
            key="safety_factor_input"
        )
        if Decimal(str(safety_factor)) != st.session_state.safety_factor :
            st.session_state.safety_factor = Decimal(str(safety_factor))
            st.session_state.torque_with_safety = st.session_state.torque_without_safety * st.session_state.safety_factor
            st.rerun()

    with col3 :
        torque_with_safety = st.number_input(
            "Момент с запасом (Нм)" ,
            value=float(st.session_state.torque_with_safety) ,
            step=0.1 ,
            format="%.1f" ,
            key="torque_with_safety_input"
        )
        if Decimal(str(torque_with_safety)) != st.session_state.torque_with_safety :
            st.session_state.torque_with_safety = Decimal(str(torque_with_safety))
            if st.session_state.safety_factor != 0 :
                st.session_state.torque_without_safety = st.session_state.torque_with_safety / st.session_state.safety_factor
            st.rerun()

    # Требования к приводу
    render_actuator_requirements()

    # Кнопки
    st.markdown("---")
    col1 , col2 , col3 , col4 = st.columns(4)

    with col2 :
        search_btn = st.button("🔍 Подобрать привод" , use_container_width=True)

    with col3 :
        reset_btn = st.button("🗑 Очистить фильтры" , use_container_width=True)

    if reset_btn :
        for key in st.session_state.keys() :
            if key not in ['torque_without_safety' , 'safety_factor' , 'torque_with_safety'] :
                if 'id' in key :
                    st.session_state[key] = None
                elif 'temp' in key :
                    st.session_state[key] = 0
                elif 'code' in key :
                    st.session_state[key] = None
        st.session_state.options_cache = {}
        st.rerun()

    if search_btn :
        with st.spinner("Поиск подходящего привода...") :
            # Здесь будет поиск
            st.info("Функция поиска будет добавлена позже")


if __name__ == "__main__" :
    main()