# main_page.py
import warnings

warnings.filterwarnings("ignore" , message="Model '.*' was already registered")

import streamlit as st
from db_init import init_django
from datetime import datetime
from pathlib import Path

# Инициализируем Django ДО импорта моделей
init_django()

# Теперь можно импортировать модели
from pneumatic_fittings.models import PneumaticFitting

st.set_page_config(
    page_title="Pneumatic System" ,
    page_icon="🔩" ,
    layout="wide" ,
    initial_sidebar_state="expanded"
)

# ==================== ОПРЕДЕЛЕНИЕ СТРАНИЦ ДЛЯ st.navigation ====================

# Определяем страницы с полными путями
PAGES = {
    "fittings" : st.Page(
        "pages/fittings_catalog.py" ,
        title="Фитинги" ,
        icon="🔧" ,
        default=False
    ) ,
    "pneumatic_actuators" : st.Page(
        "pages/pa_selection.py" ,
        title="Пневмоприводы" ,
        icon="⚙️" ,
        default=False
    ) ,
    "client_requests" : st.Page(
        "pages/request_list.py" ,
        title="Запросы клиентов" ,
        icon="📋" ,
        default=False
    ) ,
}


# ==================== ФУНКЦИИ ДЛЯ КУРСОВ ВАЛЮТ ====================

def get_currency_rates() :
    """
    Получить курсы валют с ЦБ РФ
    Позже здесь будет реальный API запрос
    """
    # TODO: Реализовать запрос к API ЦБ РФ
    return {
        "USD" : 92.50 ,
        "EUR" : 99.80 ,
        "CNY" : 12.75 ,
        "updated_at" : datetime.now().strftime("%d.%m.%Y")
    }


def render_currency_block():
    """Рендер блока с курсами валют в правом верхнем углу"""
    rates = get_currency_rates()

    currency_html = f"""
    <div style="
        background-color: rgba(240, 242, 246, 0.9);
        padding: 8px 15px;
        border-radius: 20px;
        text-align: right;
        font-size: 14px;
        font-family: monospace;
        color: #262730;
        backdrop-filter: blur(4px);
    ">
        <span style="font-weight: bold;">📅 {rates['updated_at']}</span><br>
        <span>💵 USD: {rates['USD']:.2f}</span>&nbsp;&nbsp;
        <span>💶 EUR: {rates['EUR']:.2f}</span>&nbsp;&nbsp;
        <span>💴 CNY: {rates['CNY']:.2f}</span>
    </div>
    """
    return currency_html


def render_stats() :
    """Рендер статистики"""
    total_fittings = PneumaticFitting.objects.count()
    active_fittings = PneumaticFitting.objects.filter(is_active=True).count()

    col1 , col2 , col3 , col4 = st.columns(4)
    with col1 :
        st.metric("🔧 Всего фитингов" , total_fittings)
    with col2 :
        st.metric("✅ Активных фитингов" , active_fittings)
    with col3 :
        st.metric("🏭 Производителей" , 0)
    with col4 :
        st.metric("🏷️ Брендов" , 0)


def render_main_sections() :
    """Рендер плиток разделов на главной странице"""
    st.markdown("### 📦 Разделы системы")

    # Разбиваем на строки по 2 колонки
    pages_list = list(PAGES.items())

    for i in range(0 , len(pages_list) , 2) :
        cols = st.columns(2)
        for j in range(2) :
            idx = i + j
            if idx < len(pages_list) :
                section_key , page = pages_list[idx]

                with cols[j] :
                    icon = page.icon or "📄"
                    title = page.title

                    card_html = f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 10px 0;
                        background-color: white;
                        text-align: center;
                    ">
                        <div style="font-size: 48px;">{icon}</div>
                        <div style="font-size: 18px; font-weight: bold; margin-top: 10px;">{title}</div>
                    </div>
                    """
                    st.markdown(card_html , unsafe_allow_html=True)

                    if st.button(f"Перейти в раздел {title}" , key=f"main_{section_key}" , use_container_width=True) :
                        st.switch_page(page._callable)


# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================

def main() :
    """Главная функция страницы"""

    # Верхняя строка с курсами валют
    header_col1 , header_col2 = st.columns([4 , 1])
    with header_col1 :
        st.markdown("# 🔩 Система управления пневматикой")
    with header_col2 :
        currency_html = render_currency_block()
        st.markdown(currency_html , unsafe_allow_html=True)

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

    # Навигация в сайдбаре с помощью st.navigation
    with st.sidebar :
        st.markdown("---")

        # Используем st.navigation для навигации
        # Создаем список страниц для навигации
        nav_pages = list(PAGES.values())

        # Добавляем заглушки для разделов в разработке
        nav_pages.append(
            st.Page(
                "main_page.py" ,
                title="Электроприводы (в разработке)" ,
                icon="⚡" ,
                url_path="electric_actuators"
            )
        )
        nav_pages.append(
            st.Page(
                "main_page.py" ,
                title="Кабельные вводы (в разработке)" ,
                icon="🔌" ,
                url_path="cable_glands"
            )
        )

        # Создаем навигацию
        pg = st.navigation(nav_pages)

        st.markdown("---")
        st.caption(f"Версия 1.0.0\n{datetime.now().strftime('%d.%m.%Y %H:%M')}")

    # Запускаем выбранную страницу
    pg.run()


if __name__ == "__main__" :
    main()