import streamlit as st
from db_init import init_django

init_django() # Подключаем Django

st.set_page_config(page_title="Pneumatic System", layout="wide")

st.title("🔩 Система управления пневматикой")

st.markdown("""
### Добро пожаловать в MVP интерфейс!
Здесь вы можете тестировать логику работы моделей Django без сложной верстки.

**Доступные разделы:**
1. 📂 **Каталог** — просмотр фитингов в виде карточек.
2. ✍️ **Редактор** — массовое изменение данных (Excel-style).
3. 📚 **Справочники** — управление брендами и производителями.
""")

# Статистика из БД для главной страницы
from pneumatic_fittings.models import PneumaticFitting
total = PneumaticFitting.objects.count()
active = PneumaticFitting.objects.filter(is_active=True).count()

col1, col2 = st.columns(2)
col1.metric("Всего фитингов", total)
col2.metric("Активных", active)

st.markdown("---")

# Кнопка перехода к справочникам
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📚 Перейти к управлению справочниками", width="stretch"):
        st.switch_page("pages/3_brands.py")