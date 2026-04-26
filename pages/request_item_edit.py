# pages/request_item_edit.py
import streamlit as st
from datetime import datetime
from client_requests.models import RequestItemType
from clients.models import CompanyPerson
from project_customers.utils import get_streamlit_customer_user

def render_request_item_form(item_data , item_index , is_new=False) :
    """Рендер формы редактирования позиции запроса"""

    # Заголовок формы
    if is_new :
        st.markdown("### ➕ Новая позиция")
    else :
        st.markdown(f"### ✏️ Редактирование позиции {item_data.get('item_no' , '')}")

    # Получаем текущего пользователя
    current_user , _ = get_streamlit_customer_user()

    # Основная информация в колонках
    col1 , col2 = st.columns(2)
    with st.container(border=True) :
        with col1 :
            # Номер позиции (только для чтения при редактировании)
            if is_new :
                item_no = st.number_input(
                    "Номер позиции" ,
                    min_value=1 ,
                    value=item_data.get('item_no' , 1) ,
                    step=1 ,
                    help="Порядковый номер позиции в заявке"
                )
            else :
                st.text_input(
                    "Номер позиции" ,
                    value=item_data.get('item_no' , '') ,
                    disabled=True
                )
                item_no = item_data.get('item_no')

        with col2 :
            # Номер опросного листа
            request_line_ol = st.text_input(
                "Номер опросного листа (ОЛ)" ,
                value=item_data.get('request_line_ol' , '') ,
                placeholder="Например: ОЛ-001" ,
                help="Номер опросного листа для этой позиции"
            )

        # Тип подбора
        item_types = RequestItemType.get_choices()
        type_options = [(None , "— Выберите тип подбора —")] + [(t.id , t.name) for t in item_types]

        current_type_id = item_data.get('item_type_id')
        type_id = st.selectbox(
            "Тип подбора *" ,
            options=type_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , t in enumerate(type_options) if t[0] == current_type_id) , 0) ,
            help="Выберите что нужно подобрать для этой позиции"
        )[0]

        # Показываем описание выбранного типа
        if type_id :
            selected_type = next((t for t in item_types if t.id == type_id) , None)
            if selected_type and selected_type.description :
                st.info(f"📌 {selected_type.description}")

                # Показываем что будет подбираться
                requirements = []
                if selected_type.need_valve_selection :
                    requirements.append("🔧 Арматура")
                if selected_type.need_pneumatic_actuator_selection :
                    requirements.append("💨 Пневмопривод")
                if selected_type.need_electric_actuator_selection :
                    requirements.append("⚡ Электропривод")
                if selected_type.need_mounting_kit :
                    requirements.append("🔩 Монтажный комплект")
                if selected_type.need_fittings :
                    requirements.append("🔗 Фитинги")
                if selected_type.need_positioner :
                    requirements.append("🎯 Позиционер")
                if selected_type.need_air_preparation :
                    requirements.append("💨 Пневмоподготовка")

                if requirements :
                    st.caption(f"**Требуется подобрать:** {', '.join(requirements)}")

        # Исходный текст запроса
        request_line_text = st.text_area(
            "Исходный текст запроса" ,
            value=item_data.get('request_line_text' , '') ,
            height=200 ,
            placeholder="Введите подробное описание требований по этой позиции..." ,
            help="Детальное описание того, что требуется подобрать"
        )

        # Кнопки
        col1 , col2 , col3 = st.columns([1 , 1 , 2])

        with col1 :
            if st.button("✅ Сохранить" , use_container_width=True , type="primary") :
                return {
                    'item_no' : item_no ,
                    'item_type_id' : type_id ,
                    'request_line_ol' : request_line_ol ,
                    'request_line_text' : request_line_text ,
                    'index' : item_index
                } , True

        with col2 :
            if st.button("❌ Отмена" , use_container_width=True) :
                return None , False

    return None , False


def main() :
    """Основная функция для редактирования позиции"""

    # Получаем данные из session_state
    if 'edit_item_data' not in st.session_state :
        st.error("Данные позиции не найдены")
        if st.button("🔙 Вернуться") :
            st.switch_page("pages/request_edit.py")
        return

    item_data = st.session_state.edit_item_data
    item_index = st.session_state.get('edit_item_index' , -1)
    is_new = st.session_state.get('is_new_item' , False)

    # Рендер формы
    result , saved = render_request_item_form(item_data , item_index , is_new)

    if saved and result :
        # Сохраняем результат в session_state для возврата
        st.session_state.edit_item_result = result
        st.session_state.edit_item_saved = True
        st.switch_page("pages/request_edit.py")

    # Кнопка возврата без сохранения
    if st.button("🔙 Вернуться к списку позиций") :
        st.switch_page("pages/request_edit.py")


if __name__ == "__main__" :
    st.set_page_config(
        page_title="Редактирование позиции" ,
        page_icon="✏️" ,
        layout="wide"
    )
    main()