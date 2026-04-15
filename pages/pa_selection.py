#pages/pneumatic_actuators/pa_selection.py
# Подбор пневматического привода


import streamlit as st
from db_init import init_django
from decimal import Decimal

init_django()

from params.models import DnVariety , PnVariety , MountingPlateTypes , StemSize
from pneumatic_actuators.models import PneumaticActuatorModelLine , PneumaticActuatorModelLineItem , \
    PneumaticActuatorVariety
from pneumatic_actuators.models.pa_options import (PneumaticSafetyPositionOption ,
    PneumaticIpOption , PneumaticExdOption , PneumaticBodyCoatingOption , PneumaticHandWheelOption
)

st.set_page_config(page_title="Подбор пневматического привода" , layout="wide")
st.title("🔧 Подбор пневматического привода")


def init_session_state() :
    """Инициализация session state"""
    # Параметры арматуры
    if 'valve_type' not in st.session_state :
        st.session_state.valve_type = None
    if 'dn' not in st.session_state :
        st.session_state.dn = None
    if 'pn' not in st.session_state :
        st.session_state.pn = None
    if 'mounting_plate' not in st.session_state :
        st.session_state.mounting_plate = None
    if 'stem' not in st.session_state :
        st.session_state.stem = None

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


def load_model_line_items() :
    """Загрузить модели для выбранной серии и вида привода"""
    return PneumaticActuatorModelLineItem.get_for_select(
        model_line_id=st.session_state.model_line_id ,
        actuator_variety_code=st.session_state.get('actuator_variety_code')
    )


def load_safety_positions() :
    """Загрузить положения безопасности для выбранной модели"""
    return PneumaticSafetyPositionOption.get_for_select(
        model_line_item_id=st.session_state.model_line_item_id
    )


def render_actuator_requirements() :
    """Рендер блока требований к приводу"""
    st.markdown("### 🔧 Требования к приводу")

    # Серия моделей
    model_lines = PneumaticActuatorModelLine.get_for_select()
    model_line_options = {0 : "Выберите серию"}
    for ml in model_lines :
        model_line_options[ml['id']] = f"{ml['name']} ({ml['code']})" if ml['code'] else ml['name']

    model_line_id = st.selectbox(
        "Серия моделей" ,
        options=list(model_line_options.keys()) ,
        format_func=lambda x : model_line_options.get(x , "Выберите") ,
        key="model_line_select"
    )

    # При изменении серии обновляем список моделей
    if model_line_id != st.session_state.model_line_id :
        st.session_state.model_line_id = model_line_id
        st.session_state.model_line_item_id = None
        st.rerun()

    # Вид пневмопривода (DA/SR)
    actuator_varieties = PneumaticActuatorVariety.get_for_select()
    variety_options = {0 : "Выберите вид привода"}
    for av in actuator_varieties :
        variety_options[av['id']] = f"{av['name']} ({av['code']})"

    actuator_variety_id = st.selectbox(
        "Вид пневмопривода" ,
        options=list(variety_options.keys()) ,
        format_func=lambda x : variety_options.get(x , "Выберите") ,
        key="actuator_variety_select"
    )

    if actuator_variety_id != st.session_state.actuator_variety_id :
        st.session_state.actuator_variety_id = actuator_variety_id
        # Сохраняем код для фильтрации моделей
        for av in actuator_varieties :
            if av['id'] == actuator_variety_id :
                st.session_state.actuator_variety_code = av['code']
                break
        st.session_state.model_line_item_id = None
        st.rerun()

    # Модель в серии (зависит от серии и вида привода)
    model_items = load_model_line_items()
    model_item_options = {0 : "Выберите модель"}
    for mi in model_items :
        model_item_options[mi['id']] = f"{mi['name']} ({mi['code']})" if mi['code'] else mi['name']

    model_line_item_id = st.selectbox(
        "Модель в серии" ,
        options=list(model_item_options.keys()) ,
        format_func=lambda x : model_item_options.get(x , "Выберите") ,
        key="model_line_item_select"
    )

    if model_line_item_id != st.session_state.model_line_item_id :
        st.session_state.model_line_item_id = model_line_item_id
        st.rerun()

    # NO/NC (положение безопасности)
    safety_positions = load_safety_positions()
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
    ip_options_list = PneumaticIpOption.get_for_select(model_line_id=st.session_state.model_line_id)
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
    exd_options_list = PneumaticExdOption.get_for_select(model_line_id=st.session_state.model_line_id)
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
    coating_options_list = PneumaticBodyCoatingOption.get_for_select(model_line_id=st.session_state.model_line_id)
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
    hand_wheel_options_list = PneumaticHandWheelOption.get_for_select(model_line_id=st.session_state.model_line_id)
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


def render_torque_block() :
    """Рендер блока расчета момента"""
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


def render_buttons() :
    """Рендер кнопок"""
    st.markdown("---")

    col1 , col2 , col3 , col4 = st.columns(4)

    with col2 :
        search_btn = st.button("🔍 Подобрать привод" , use_container_width=True)

    with col3 :
        reset_btn = st.button("🗑 Очистить фильтры" , use_container_width=True)

    return search_btn , reset_btn


def reset_filters() :
    """Сбросить все фильтры"""
    st.session_state.model_line_id = None
    st.session_state.model_line_item_id = None
    st.session_state.actuator_variety_id = None
    st.session_state.safety_position_id = None
    st.session_state.ip_id = None
    st.session_state.exd_id = None
    st.session_state.coating_id = None
    st.session_state.hand_wheel_id = None
    st.session_state.temp_min = 0
    st.session_state.temp_max = 0
    st.session_state.torque_without_safety = Decimal('0')
    st.session_state.safety_factor = Decimal('1.3')
    st.session_state.torque_with_safety = Decimal('0')


def main() :
    """Главная функция страницы"""
    init_session_state()

    # Параметры арматуры
    st.markdown("### 📋 Параметры арматуры")

    col1 , col2 = st.columns(2)

    with col1 :
        # Тип арматуры (заглушка, позже добавим реальные данные)
        valve_type = st.selectbox(
            "Тип арматуры" ,
            options=["Выберите тип" , "Шаровой кран" , "Дисковый затвор" , "Задвижка"] ,
            key="valve_type_select"
        )
        st.session_state.valve_type = valve_type if valve_type != "Выберите тип" else None

        dn_options = {0 : "Выберите DN"}
        for dn in DnVariety.objects.filter(is_active=True) :
            dn_options[dn.id] = dn.name
        dn_id = st.selectbox(
            "DN" ,
            options=list(dn_options.keys()) ,
            format_func=lambda x : dn_options.get(x , "Выберите") ,
            key="dn_select"
        )
        st.session_state.dn = dn_id if dn_id != 0 else None

    with col2 :
        pn_options = {0 : "Выберите PN"}
        for pn in PnVariety.objects.filter(is_active=True) :
            pn_options[pn.id] = pn.name
        pn_id = st.selectbox(
            "PN" ,
            options=list(pn_options.keys()) ,
            format_func=lambda x : pn_options.get(x , "Выберите") ,
            key="pn_select"
        )
        st.session_state.pn = pn_id if pn_id != 0 else None

        plate_options = {0 : "Выберите монтажную площадку"}
        for plate in MountingPlateTypes.objects.filter(is_active=True) :
            plate_options[plate.id] = plate.name
        plate_id = st.selectbox(
            "Монтажная площадка" ,
            options=list(plate_options.keys()) ,
            format_func=lambda x : plate_options.get(x , "Выберите") ,
            key="plate_select"
        )
        st.session_state.mounting_plate = plate_id if plate_id != 0 else None

    # Моменты
    render_torque_block()

    # Требования к приводу
    render_actuator_requirements()

    # Кнопки
    search_btn , reset_btn = render_buttons()

    if reset_btn :
        reset_filters()
        st.rerun()

    if search_btn :
        with st.spinner("Поиск подходящего привода...") :
            # TODO: здесь будет обращение к БД для подбора привода
            st.info("🔧 Функция подбора привода будет добавлена позже")
            st.json({
                "torque_without_safety" : float(st.session_state.torque_without_safety) ,
                "safety_factor" : float(st.session_state.safety_factor) ,
                "torque_with_safety" : float(st.session_state.torque_with_safety) ,
                "model_line_id" : st.session_state.model_line_id ,
                "model_line_item_id" : st.session_state.model_line_item_id ,
                "actuator_variety_id" : st.session_state.actuator_variety_id ,
                "safety_position_id" : st.session_state.safety_position_id ,
                "ip_id" : st.session_state.ip_id ,
                "exd_id" : st.session_state.exd_id ,
                "coating_id" : st.session_state.coating_id ,
                "hand_wheel_id" : st.session_state.hand_wheel_id ,
                "temp_min" : st.session_state.temp_min ,
                "temp_max" : st.session_state.temp_max ,
            })


if __name__ == "__main__" :
    main()

