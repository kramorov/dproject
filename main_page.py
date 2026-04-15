# main_page.py
import warnings
warnings.filterwarnings("ignore", message="Model '.*' was already registered")

import streamlit as st
from db_init import init_django
from datetime import datetime

# Инициализируем Django ДО импорта моделей
init_django()

# Теперь можно импортировать модели
from pneumatic_fittings.models import PneumaticFitting

st.set_page_config(
    page_title="Pneumatic System",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== КОНФИГУРАЦИЯ РАЗДЕЛОВ ====================

# Словарь разделов для ГЛАВНОЙ СТРАНИЦЫ (плитки)
MAIN_SECTIONS = {
    "fittings": {
        "title": "Фитинги",
        "icon": "🔧",
        "description": "Пневматические фитинги, штуцеры, переходники",
        "page": "pages/fittings_catalog.py",
        "enabled": True,
        "order": 1
    },
    "pneumatic_actuators": {
        "title": "Пневмоприводы",
        "icon": "⚙️",
        "description": "Пневматические приводы и актуаторы",
        "page": 'pages/pa_selection.py',
        "enabled": True,
        "order": 2
    },
    "electric_actuators": {
        "title": "Электроприводы",
        "icon": "⚡",
        "description": "Электрические приводы и исполнительные механизмы",
        "page": None,
        "enabled": True,
        "order": 3
    },
    "cable_glands": {
        "title": "Кабельные вводы",
        "icon": "🔌",
        "description": "Кабельные вводы и аксессуары",
        "page": None,
        "enabled": True,
        "order": 4
    },
    "hand_wheels": {
        "title": "Ручные дублеры",
        "icon": "🖐️",
        "description": "Ручные дублеры и механизмы управления",
        "page": None,
        "enabled": True,
        "order": 5
    },
    "valves": {
        "title": "Арматура",
        "icon": "🚰",
        "description": "Трубопроводная арматура",
        "page": None,
        "enabled": True,
        "order": 6
    },
    "prices": {
        "title": "Цены",
        "icon": "💰",
        "description": "Прайс-листы и цены на продукцию",
        "page": None,
        "enabled": True,
        "order": 7
    }
}

# Словарь разделов для САЙДБАРА (навигация)
SIDEBAR_SECTIONS = {
    "fittings": {
        "title": "Фитинги",
        "icon": "🔧",
        "page": "pages/fittings_catalog.py",
        "enabled": True,
        "order": 1
    },
    "pneumatic_actuators": {
        "title": "Пневмоприводы",
        "icon": "⚙️",
        "page": 'pages/pa_selection.py',
        "enabled": True,
        "order": 2
    },
    "electric_actuators": {
        "title": "Электроприводы",
        "icon": "⚡",
        "page": None,
        "enabled": True,
        "order": 3
    },
    "cable_glands": {
        "title": "Кабельные вводы",
        "icon": "🔌",
        "page": None,
        "enabled": True,
        "order": 4
    }
}

# Сортировка по order
MAIN_SECTIONS = dict(sorted(MAIN_SECTIONS.items(), key=lambda x: x[1]["order"]))
SIDEBAR_SECTIONS = dict(sorted(SIDEBAR_SECTIONS.items(), key=lambda x: x[1]["order"]))


# ==================== ФУНКЦИИ ДЛЯ КУРСОВ ВАЛЮТ ====================

def get_currency_rates():
    """
    Получить курсы валют с ЦБ РФ
    Позже здесь будет реальный API запрос
    """
    # TODO: Реализовать запрос к API ЦБ РФ
    # Пока возвращаем заглушки
    return {
        "USD": 92.50,
        "EUR": 99.80,
        "CNY": 12.75,
        "updated_at": datetime.now().strftime("%d.%m.%Y")
    }


def render_currency_block():
    """Рендер блока с курсами валют в правом верхнем углу"""
    rates = get_currency_rates()

    # Создаем HTML для отображения курсов
    currency_html = f"""
    <div style="
        background-color: #f0f2f6;
        padding: 8px 15px;
        border-radius: 20px;
        text-align: right;
        font-size: 14px;
        font-family: monospace;
    ">
        <span style="font-weight: bold;">📅 {rates['updated_at']}</span><br>
        <span>💵 USD: {rates['USD']:.2f}</span>&nbsp;&nbsp;
        <span>💶 EUR: {rates['EUR']:.2f}</span>&nbsp;&nbsp;
        <span>💴 CNY: {rates['CNY']:.2f}</span>
    </div>
    """

    return currency_html


def render_sidebar():
    """Рендер бокового меню"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60?text=Pneumatic+System", width='stretch')
        st.markdown("---")

        st.markdown("### 📂 Навигация")

        for section_key, section in SIDEBAR_SECTIONS.items():
            if not section.get("enabled", True):
                continue

            icon = section.get("icon", "📄")
            title = section["title"]

            # Проверяем, есть ли страница для перехода
            if section.get("page") and section["page"] is not None:
                if st.button(f"{icon} {title}", key=f"sidebar_{section_key}", width='stretch'):
                    st.switch_page(section["page"])
            else:
                # Неактивная кнопка
                st.button(f"{icon} {title} 🚧", key=f"sidebar_{section_key}_disabled",
                          disabled=True, width='stretch',
                          help="Раздел в разработке")

        st.markdown("---")
        st.caption(f"Версия 1.0.0\n{datetime.now().strftime('%d.%m.%Y %H:%M')}")


def render_main_sections():
    """Рендер плиток разделов на главной странице"""
    st.markdown("### 📦 Разделы системы")

    # Разбиваем на строки по 3 колонки
    sections_list = list(MAIN_SECTIONS.items())

    for i in range(0, len(sections_list), 3):
        cols = st.columns(3)
        for j in range(3):
            idx = i + j
            if idx < len(sections_list):
                section_key, section = sections_list[idx]

                if not section.get("enabled", True):
                    continue

                with cols[j]:
                    icon = section.get("icon", "📄")
                    title = section["title"]
                    description = section.get("description", "")

                    if section.get("page") and section["page"] is not None:
                        # Активная карточка с переходом
                        card_html = f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 12px;
                            padding: 20px;
                            margin: 10px 0;
                            background-color: white;
                            cursor: pointer;
                            transition: all 0.3s ease;
                            text-align: center;
                        ">
                            <div style="font-size: 48px;">{icon}</div>
                            <div style="font-size: 18px; font-weight: bold; margin-top: 10px;">{title}</div>
                            <div style="font-size: 13px; color: #666; margin-top: 8px;">{description}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)

                        if st.button(f"Перейти в раздел {title}", key=f"main_{section_key}", width='stretch'):
                            st.switch_page(section["page"])
                    else:
                        # Неактивная карточка
                        card_html = f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 12px;
                            padding: 20px;
                            margin: 10px 0;
                            background-color: #f9f9f9;
                            text-align: center;
                            opacity: 0.6;
                        ">
                            <div style="font-size: 48px;">{icon}</div>
                            <div style="font-size: 18px; font-weight: bold; margin-top: 10px;">{title}</div>
                            <div style="font-size: 13px; color: #666; margin-top: 8px;">{description}</div>
                            <div style="font-size: 11px; color: #999; margin-top: 8px;">🚧 В разработке</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)


def render_stats():
    """Рендер статистики"""
    from pneumatic_fittings.models import PneumaticFitting

    total_fittings = PneumaticFitting.objects.count()
    active_fittings = PneumaticFitting.objects.filter(is_active=True).count()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔧 Всего фитингов", total_fittings)
    with col2:
        st.metric("✅ Активных фитингов", active_fittings)
    with col3:
        st.metric("🏭 Производителей", 0)  # TODO: добавить подсчет
    with col4:
        st.metric("🏷️ Брендов", 0)  # TODO: добавить подсчет


# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================

def main():
    """Главная функция страницы"""

    # Верхняя строка с курсами валют
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown("# 🔩 Система управления пневматикой")
    with header_col2:
        currency_html = render_currency_block()
        st.markdown(currency_html, unsafe_allow_html=True)

    st.markdown("---")

    # Приветствие
    st.markdown("""
    ### Добро пожаловать в MVP интерфейс!
    Здесь вы можете тестировать логику работы моделей Django без сложной верстки.
    """)

    # Статистика
    render_stats()

    st.markdown("---")

    # Плитки разделов
    render_main_sections()

    # Сайдбар
    render_sidebar()


if __name__ == "__main__":
    main()