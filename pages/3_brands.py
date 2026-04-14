# pages/3_brands.py

import streamlit as st
from db_init import init_django
import pandas as pd

init_django()

from producers.models import Brands , Producer

st.set_page_config(page_title="Справочники" , layout="wide")
st.title("📚 Управление справочниками")


# ==================== ВСПЛЫВАЮЩИЕ ОКНА (DIALOGS) ====================

@st.dialog("➕ Добавить новый бренд")
def dialog_add_brand() :
    """Диалог добавления нового бренда"""
    with st.form("add_brand_form") :
        col1 , col2 = st.columns(2)
        with col1 :
            name = st.text_input("Название *")
            code = st.text_input("Код")
        with col2 :
            sorting_order = st.number_input("Сортировка" , value=0)
            is_active = st.checkbox("Активен" , value=True)

        description = st.text_area("Описание" , height=100)

        col1 , col2 , col3 = st.columns([1 , 1 , 1])
        with col2 :
            submitted = st.form_submit_button("💾 Создать" , use_container_width=True)

        if submitted :
            if name :
                Brands.create_from_dict({
                    'name' : name ,
                    'code' : code if code else None ,
                    'description' : description ,
                    'sorting_order' : sorting_order ,
                    'is_active' : is_active
                })
                st.success(f"Бренд '{name}' создан!")
                st.rerun()
            else :
                st.error("Название обязательно!")


@st.dialog("➕ Добавить бренд производителю")
def dialog_add_brand_to_producer(producer_id: int , producer_name: str) :
    """Диалог добавления существующего бренда производителю"""
    all_brands = Brands.get_all(active_only=True)
    existing_brands = Producer.get_by_id(producer_id).brands.all()
    existing_ids = [b.id for b in existing_brands]

    available_brands = [b for b in all_brands if b.id not in existing_ids]

    if not available_brands :
        st.info("Все доступные бренды уже добавлены этому производителю")
        if st.button("Закрыть") :
            st.rerun()
        return

    with st.form(f"add_brand_to_producer_form") :
        st.write(f"Производитель: **{producer_name}**")

        selected_brand_ids = st.multiselect(
            "Выберите бренды для добавления" ,
            options=[b.id for b in available_brands] ,
            format_func=lambda x : next((f"{b.name} ({b.code or '-'})" for b in available_brands if b.id == x) , str(x))
        )

        col1 , col2 , col3 = st.columns([1 , 1 , 1])
        with col2 :
            submitted = st.form_submit_button("➕ Добавить" , use_container_width=True)

        if submitted and selected_brand_ids :
            producer = Producer.get_by_id(producer_id)
            current_ids = [b.id for b in producer.brands.all()]
            producer.brands.set(current_ids + selected_brand_ids)
            st.success(f"Добавлено {len(selected_brand_ids)} брендов")
            st.rerun()


@st.dialog("➕ Добавить нового производителя")
def dialog_add_producer() :
    """Диалог добавления нового производителя"""
    all_brands = {b.id : f"{b.name} ({b.code or '-'})" for b in Brands.get_all(active_only=True)}

    with st.form("add_producer_form") :
        col1 , col2 = st.columns(2)
        with col1 :
            name = st.text_input("Название *")
            code = st.text_input("Код")
            organization = st.text_input("Организация")
        with col2 :
            sorting_order = st.number_input("Сортировка" , value=0)
            is_active = st.checkbox("Активен" , value=True)

        description = st.text_area("Описание" , height=80)

        selected_brands = st.multiselect(
            "Бренды" ,
            options=list(all_brands.keys()) ,
            format_func=lambda x : all_brands.get(x , str(x))
        )

        col1 , col2 , col3 = st.columns([1 , 1 , 1])
        with col2 :
            submitted = st.form_submit_button("💾 Создать" , use_container_width=True)

        if submitted :
            if name :
                Producer.create_from_dict({
                    'name' : name ,
                    'code' : code if code else None ,
                    'organization' : organization if organization else None ,
                    'description' : description ,
                    'sorting_order' : sorting_order ,
                    'is_active' : is_active ,
                    'brands_ids' : selected_brands
                })
                st.success(f"Производитель '{name}' создан!")
                st.rerun()
            else :
                st.error("Название обязательно!")


@st.dialog("✏️ Редактировать бренд")
def dialog_edit_brand(brand_id: int) :
    """Диалог редактирования бренда"""
    brand = Brands.get_by_id(brand_id)
    if not brand :
        st.error("Бренд не найден")
        return

    with st.form(f"edit_brand_form_{brand_id}") :
        col1 , col2 = st.columns(2)
        with col1 :
            name = st.text_input("Название *" , value=brand.name)
            code = st.text_input("Код" , value=brand.code or "")
        with col2 :
            sorting_order = st.number_input("Сортировка" , value=brand.sorting_order)
            is_active = st.checkbox("Активен" , value=brand.is_active)

        description = st.text_area("Описание" , value=brand.description or "" , height=100)

        col1 , col2 , col3 = st.columns([1 , 1 , 1])
        with col2 :
            submitted = st.form_submit_button("💾 Сохранить" , use_container_width=True)

        if submitted :
            if name :
                brand.update_from_dict({
                    'name' : name ,
                    'code' : code if code else None ,
                    'description' : description ,
                    'sorting_order' : sorting_order ,
                    'is_active' : is_active
                })
                st.success(f"Бренд '{name}' сохранен!")
                st.rerun()
            else :
                st.error("Название обязательно!")


@st.dialog("✏️ Редактировать производителя")
def dialog_edit_producer(producer_id: int) :
    """Диалог редактирования производителя"""
    producer = Producer.get_by_id(producer_id)
    if not producer :
        st.error("Производитель не найден")
        return

    all_brands = {b.id : f"{b.name} ({b.code or '-'})" for b in Brands.get_all(active_only=True)}
    current_brands = [b.id for b in producer.brands.all()]

    with st.form(f"edit_producer_form_{producer_id}") :
        col1 , col2 = st.columns(2)
        with col1 :
            name = st.text_input("Название *" , value=producer.name)
            code = st.text_input("Код" , value=producer.code or "")
            organization = st.text_input("Организация" , value=producer.organization or "")
        with col2 :
            sorting_order = st.number_input("Сортировка" , value=producer.sorting_order)
            is_active = st.checkbox("Активен" , value=producer.is_active)

        description = st.text_area("Описание" , value=producer.description or "" , height=80)

        selected_brands = st.multiselect(
            "Бренды" ,
            options=list(all_brands.keys()) ,
            default=current_brands ,
            format_func=lambda x : all_brands.get(x , str(x))
        )

        col1 , col2 , col3 = st.columns([1 , 1 , 1])
        with col2 :
            submitted = st.form_submit_button("💾 Сохранить" , use_container_width=True)

        if submitted :
            if name :
                producer.update_from_dict({
                    'name' : name ,
                    'code' : code if code else None ,
                    'organization' : organization if organization else None ,
                    'description' : description ,
                    'sorting_order' : sorting_order ,
                    'is_active' : is_active ,
                    'brands_ids' : selected_brands
                })
                st.success(f"Производитель '{name}' сохранен!")
                st.rerun()
            else :
                st.error("Название обязательно!")


# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

def render_brands_editor() :
    """Редактор брендов"""
    st.header("🏷️ Бренды")

    # Кнопка добавления
    col1 , col2 , col3 = st.columns([1 , 6 , 1])
    with col1 :
        if st.button("➕ Добавить бренд" , use_container_width=True) :
            dialog_add_brand()

    # Таблица брендов
    brands = Brands.get_all()

    if brands :
        data = []
        for b in brands :
            data.append({
                "ID" : b.id ,
                "Название" : b.name ,
                "Код" : b.code or "-" ,
                "Сортировка" : b.sorting_order ,
                "Активен" : "✅" if b.is_active else "❌"
            })

        df = pd.DataFrame(data)
        st.dataframe(df , use_container_width=True , hide_index=True)

        # Кнопки действий для каждого бренда
        st.subheader("⚙️ Действия с брендами")
        cols = st.columns(min(len(brands) , 4))

        for idx , brand in enumerate(brands) :
            col_idx = idx % 4
            with cols[col_idx] :
                if st.button(f"✏️ {brand.name}" , key=f"edit_btn_{brand.id}") :
                    dialog_edit_brand(brand.id)


def render_producers_editor() :
    """Редактор производителей"""
    st.header("🏭 Производители")

    # Кнопка добавления
    col1 , col2 , col3 = st.columns([1 , 6 , 1])
    with col1 :
        if st.button("➕ Добавить производителя" , use_container_width=True) :
            dialog_add_producer()

    # Таблица производителей
    producers = Producer.get_all()

    if producers :
        for producer in producers :
            with st.expander(f"🏭 **{producer.name}**" , expanded=False) :
                # Основная информация в колонках
                col1 , col2 , col3 , col4 = st.columns(4)
                with col1 :
                    st.write("**Код:**")
                    st.write(producer.code or "-")
                with col2 :
                    st.write("**Организация:**")
                    st.write(producer.organization or "-")
                with col3 :
                    st.write("**Сортировка:**")
                    st.write(producer.sorting_order)
                with col4 :
                    st.write("**Статус:**")
                    st.write("✅ Активен" if producer.is_active else "❌ Неактивен")

                if producer.description :
                    st.write("**Описание:**")
                    st.write(producer.description)

                st.markdown("---")

                # Бренды производителя (в подвале)
                st.write("**🏷️ Бренды производителя:**")
                brands_list = list(producer.brands.all())

                if brands_list :
                    # Отображаем бренды в виде чипсов/карточек
                    brand_cols = st.columns(min(len(brands_list) , 5))
                    for idx , brand in enumerate(brands_list) :
                        col_idx = idx % 5
                        with brand_cols[col_idx] :
                            st.markdown(f"""
                            <div style="
                                background-color: #f0f2f6;
                                padding: 5px 10px;
                                border-radius: 20px;
                                text-align: center;
                                margin: 5px 0;
                            ">
                                <b>{brand.name}</b><br>
                                <small>{brand.code or '-'}</small>
                            </div>
                            """ , unsafe_allow_html=True)
                else :
                    st.info("Нет добавленных брендов")

                # Кнопки действий
                st.markdown("---")
                col1 , col2 , col3 , col4 = st.columns(4)
                with col1 :
                    if st.button("✏️ Редактировать" , key=f"edit_prod_{producer.id}" , use_container_width=True) :
                        dialog_edit_producer(producer.id)
                with col2 :
                    if st.button("➕ Добавить бренд" , key=f"add_brand_to_{producer.id}" , use_container_width=True) :
                        dialog_add_brand_to_producer(producer.id , producer.name)
                with col3 :
                    if st.button("📋 Дублировать" , key=f"duplicate_prod_{producer.id}" , use_container_width=True) :
                        # Создание дубликата
                        duplicate = producer
                        duplicate.pk = None
                        duplicate.name = f"{producer.name} (копия)"
                        duplicate.save()
                        # Копируем связи
                        duplicate.brands.set([b.id for b in producer.brands.all()])
                        st.success(f"Создан дубликат: {duplicate.name}")
                        st.rerun()
                with col4 :
                    if st.button("🗑️ Деактивировать" , key=f"deactivate_prod_{producer.id}" ,
                                 use_container_width=True) :
                        producer.is_active = False
                        producer.save()
                        st.success(f"Производитель '{producer.name}' деактивирован")
                        st.rerun()


def main() :
    """Главная функция страницы"""
    tab1 , tab2 = st.tabs(["🏷️ Бренды" , "🏭 Производители"])

    with tab1 :
        render_brands_editor()

    with tab2 :
        render_producers_editor()


if __name__ == "__main__" :
    main()