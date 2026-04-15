# pages/fittings_catalog.py

import streamlit as st
from db_init import init_django

init_django()

from pneumatic_fittings.models import PneumaticFitting

st.set_page_config(page_title="Каталог фитингов", layout="wide")
st.title("🔧 Каталог пневматических фитингов")


def init_session_state():
    """Инициализация session state"""
    if 'filters_applied' not in st.session_state:
        st.session_state.filters_applied = False
    if 'filter_result' not in st.session_state:
        st.session_state.filter_result = None
    if 'filter_options' not in st.session_state:
        st.session_state.filter_options = PneumaticFitting.get_filter_options()

    # Инициализируем значения фильтров
    if 'filter_code' not in st.session_state:
        st.session_state.filter_code = ""
    if 'filter_brand' not in st.session_state:
        st.session_state.filter_brand = 0
    if 'filter_model_line' not in st.session_state:
        st.session_state.filter_model_line = 0


def render_filters():
    """Рендер фильтров на главной странице"""
    st.markdown("### 🔍 Фильтры")

    # Получаем опции для фильтров
    options = st.session_state.filter_options

    # Строка 1: Поиск по коду, бренд, серия
    col1, col2, col3 = st.columns(3)

    with col1:
        code = st.text_input(
            "Поиск по коду",
            value=st.session_state.filter_code,
            placeholder="Введите код...",
            key="filter_code"
        )

    with col2:
        brand_options = {0: "Все бренды"}
        for b in options.get('brands', []):
            brand_options[b['id']] = b['name']

        brand_id = st.selectbox(
            "Бренд",
            options=list(brand_options.keys()),
            format_func=lambda x: brand_options.get(x, "Все"),
            key="filter_brand"
        )

    with col3:
        model_options = {0: "Все серии"}
        for ml in options.get('model_lines', []):
            model_options[ml['id']] = ml['name']

        model_line_id = st.selectbox(
            "Серия",
            options=list(model_options.keys()),
            format_func=lambda x: model_options.get(x, "Все"),
            key="filter_model_line"
        )

    # Строка 2: Тип фитинга, тип резьбы, резьба
    col1, col2, col3 = st.columns(3)

    with col1:
        variety_options = {0: "Все типы"}
        for v in options.get('varieties', []):
            variety_options[v['id']] = v['name']

        variety_id = st.selectbox(
            "Тип фитинга",
            options=list(variety_options.keys()),
            format_func=lambda x: variety_options.get(x, "Все"),
            key="filter_variety"
        )

    with col2:
        # Фильтр по типу резьбы
        thread_type_options = {0: "Все типы резьб"}
        for tt in options.get('thread_types', []):
            thread_type_options[tt['id']] = tt['name']

        thread_type_id = st.selectbox(
            "Тип резьбы",
            options=list(thread_type_options.keys()),
            format_func=lambda x: thread_type_options[x],
            key="filter_thread_type"
        )

        # Получаем отфильтрованные резьбы
        threads = PneumaticFitting.get_filtered_threads(
            thread_type_id if thread_type_id != 0 else None
        )

    with col3:
        thread_options = {0: "Все резьбы"}
        for t in threads:
            thread_options[t['id']] = t['name']

        thread_id = st.selectbox(
            "Резьба",
            options=list(thread_options.keys()),
            format_func=lambda x: thread_options[x],
            key="filter_thread"
        )

    # Строка 3: Тип резьбы (наружная/внутренняя), материал корпуса, материал трубки
    col1, col2, col3 = st.columns(3)

    with col1:
        tio_options = {0: "Все"}
        for tio in options.get('thread_inner_outers', []):
            tio_options[tio['id']] = tio['name']

        thread_inner_outer_id = st.selectbox(
            "Тип резьбы (нар/внут)",
            options=list(tio_options.keys()),
            format_func=lambda x: tio_options.get(x, "Все"),
            key="filter_tio"
        )

    with col2:
        body_material_options = {0: "Все материалы"}
        for bm in options.get('body_materials', []):
            body_material_options[bm['id']] = bm['name']

        body_material_id = st.selectbox(
            "Материал корпуса",
            options=list(body_material_options.keys()),
            format_func=lambda x: body_material_options.get(x, "Все"),
            key="filter_body_material"
        )

    with col3:
        pipe_material_options = {0: "Все материалы"}
        for pm in options.get('pipe_materials', []):
            pipe_material_options[pm['id']] = pm['name']

        pipe_material_id = st.selectbox(
            "Материал трубки",
            options=list(pipe_material_options.keys()),
            format_func=lambda x: pipe_material_options.get(x, "Все"),
            key="filter_pipe_material"
        )

    # Строка 4: Диаметр трубки, температура, активность
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        diameter_options = {0: "Все диаметры"}
        for d in options.get('pipe_diameters', []):
            diameter_options[d['id']] = f"{d['name']} мм"

        pipe_diameter = st.selectbox(
            "Диаметр трубки (мм)",
            options=list(diameter_options.keys()),
            format_func=lambda x: diameter_options.get(x, "Все"),
            key="filter_pipe_diameter"
        )

    with col2:
        temp_min = st.number_input(
            "Мин. температура (≤ °C)",
            value=None,
            placeholder="Не выше",
            step=5,
            key="filter_temp_min"
        )

    with col3:
        is_active = st.checkbox("Только активные", value=True, key="filter_active")

    with col4:
        st.markdown("### ")
        apply_btn = st.button("🔍 Применить", use_container_width=True, key="apply_filters")

    # Строка 5: Кнопка сброса
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        reset_btn = st.button("🗑 Сбросить все фильтры", use_container_width=True)

    # Сбор параметров фильтрации
    filters = {
        'code': code if code else None,
        'temp_min': temp_min if temp_min else None,
        'brand_id': brand_id if brand_id != 0 else None,
        'fitting_model_line_id': model_line_id if model_line_id != 0 else None,
        'fitting_variety_id': variety_id if variety_id != 0 else None,
        'body_material_id': body_material_id if body_material_id != 0 else None,
        'pipe_material_id': pipe_material_id if pipe_material_id != 0 else None,
        'pipe_diameter': pipe_diameter if pipe_diameter != 0 else None,
        'thread_type_id': thread_type_id if thread_type_id != 0 else None,
        'thread_id': thread_id if thread_id != 0 else None,
        'thread_inner_outer_id': thread_inner_outer_id if thread_inner_outer_id != 0 else None,
        'is_active': is_active
    }

    return filters, apply_btn, reset_btn


def render_simple_fitting_card(fitting: dict):
    """Рендер простой карточки фитинга (только description)"""
    description = fitting.get('description', '')
    if not description:
        description = '—'

    is_active = fitting.get('is_active', True)
    bg_color = '#fef9e6' if not is_active else '#fff'
    border_color = '#ffcccc' if not is_active else '#e0e0e0'

    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            background-color: {bg_color};
        ">
            <div style="font-size: 14px; color: #444; line-height: 1.4;">
                {description}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_results():
    """Рендер результатов поиска"""
    if not st.session_state.filters_applied:
        st.info("👆 Используйте фильтры выше для поиска фитингов")
        return

    result = st.session_state.filter_result

    if not result or not result.get('data'):
        st.warning("😕 Ничего не найдено. Попробуйте изменить критерии поиска.")
        return

    data = result['data']
    for fitting in data:
        render_simple_fitting_card(fitting)

def main():
    """Главная функция страницы"""
    init_session_state()

    filters, apply_btn, reset_btn = render_filters()

    if apply_btn:
        with st.spinner("Поиск..."):
            clean_filters = {k: v for k, v in filters.items() if v is not None and v != ''}
            # Сохраняем фильтры в query_params
            st.query_params.update(clean_filters)
            st.session_state.filter_result = PneumaticFitting.filter_by_params(clean_filters)
            st.session_state.filters_applied = True
            st.rerun()

    if reset_btn:
        # Очищаем query_params - это автоматически сбросит все виджеты
        # Сбрасываем session_state
        st.session_state.filter_code = ""
        st.session_state.filter_brand = 0
        st.session_state.filter_model_line = 0
        st.session_state.filter_variety = 0
        st.session_state.filter_thread_type = 0
        st.session_state.filter_thread = 0
        st.session_state.filter_tio = 0
        st.session_state.filter_body_material = 0
        st.session_state.filter_pipe_material = 0
        st.session_state.filter_pipe_diameter = 0
        st.session_state.filter_temp_min = None
        st.session_state.filter_active = True

        st.session_state.filter_result = None
        st.session_state.filters_applied = False
        st.rerun()

    st.markdown("---")
    render_results()


if __name__ == "__main__":
    main()