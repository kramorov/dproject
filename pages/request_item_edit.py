# pages/request_item_edit.py
import streamlit as st
from client_requests.models import RequestItemType, ClientRequestItem
from project_customers.utils import get_streamlit_customer_user

st.set_page_config(
    page_title="Редактирование позиции",
    page_icon="✏️",
    layout="wide"
)

def get_item(item_id):
    """Получить позицию по ID"""
    try:
        return ClientRequestItem.objects.get(id=item_id)
    except ClientRequestItem.DoesNotExist:
        return None


def save_item_update(item, form_data, changed_by):
    """Сохранить изменения позиции (создавая новую версию)"""

    # Собираем обновленные поля
    updated_fields = {
        'item_type_id': form_data.get('item_type_id'),
        'request_line_ol': form_data.get('request_line_ol', ''),
        'request_line_text': form_data.get('request_line_text', '')
    }

    # Создаем новую версию
    change_comment = form_data.get('change_comment', f"Редактирование позиции {item.item_no}")
    new_item = item.create_new_version(
        change_comment=change_comment,
        changed_by=changed_by,
        **updated_fields
    )
    return new_item


def save_new_item(request_id, form_data):
    """Создать новую позицию"""
    item = ClientRequestItem.create_new_item(
        request_parent_id=request_id,
        item_type_id=form_data.get('item_type_id'),
        request_line_ol=form_data.get('request_line_ol', ''),
        request_line_text=form_data.get('request_line_text', '')
    )
    return item


def render_request_item_form(item=None, request_id=None, is_new=False):
    """Рендер формы редактирования позиции запроса"""

    # Заголовок формы
    if is_new:
        st.markdown("### ➕ Новая позиция")
        item_no = None
        current_type_id = None
        request_line_ol = ""
        request_line_text = ""
    else:
        st.markdown(f"### ✏️ Редактирование позиции {item.item_no}")
        item_no = item.item_no
        current_type_id = item.item_type_id
        request_line_ol = item.request_line_ol or ""
        request_line_text = item.request_line_text or ""

    with st.form("item_edit_form"):
        # Номер позиции (только для чтения при редактировании)
        if not is_new:
            st.text_input("Номер позиции", value=item_no, disabled=True)

        # Номер опросного листа
        request_line_ol = st.text_input(
            "Номер опросного листа (ОЛ)",
            value=request_line_ol,
            placeholder="Например: ОЛ-001",
            help="Номер опросного листа для этой позиции"
        )

        # Тип подбора
        item_types = RequestItemType.get_choices()
        type_options = [(None, "— Выберите тип подбора —")] + [(t.id, t.name) for t in item_types]

        type_id = st.selectbox(
            "Тип подбора *",
            options=type_options,
            format_func=lambda x: x[1],
            index=next((i for i, t in enumerate(type_options) if t[0] == current_type_id), 0),
            help="Выберите что нужно подобрать для этой позиции"
        )[0]

        # Показываем описание выбранного типа
        if type_id:
            selected_type = next((t for t in item_types if t.id == type_id), None)
            if selected_type and selected_type.description:
                st.info(f"📌 {selected_type.description}")

                # Показываем что будет подбираться
                requirements = []
                if selected_type.need_valve_selection:
                    requirements.append("🔧 Арматура")
                if selected_type.need_pneumatic_actuator_selection:
                    requirements.append("💨 Пневмопривод")
                if selected_type.need_electric_actuator_selection:
                    requirements.append("⚡ Электропривод")
                if selected_type.need_mounting_kit:
                    requirements.append("🔩 Монтажный комплект")
                if selected_type.need_fittings:
                    requirements.append("🔗 Фитинги")
                if selected_type.need_positioner:
                    requirements.append("🎯 Позиционер")
                if selected_type.need_air_preparation:
                    requirements.append("💨 Пневмоподготовка")

                if requirements:
                    st.caption(f"**Требуется подобрать:** {', '.join(requirements)}")

        # Исходный текст запроса
        request_line_text = st.text_area(
            "Исходный текст запроса *",
            value=request_line_text,
            height=200,
            placeholder="Введите подробное описание требований по этой позиции...",
            help="Детальное описание того, что требуется подобрать"
        )

        # Комментарий к изменению (только для редактирования)
        change_comment = ""
        if not is_new:
            change_comment = st.text_area(
                "Комментарий к изменению",
                placeholder="Опишите, что изменилось в этой версии...",
                help="Объясните причину изменения позиции"
            )

        # Кнопки
        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("✅ Сохранить", use_container_width=True, type="primary")

        with col2:
            cancelled = st.form_submit_button("❌ Отмена", use_container_width=True)

        if submitted:
            # Валидация
            if not type_id:
                st.error("❌ Выберите тип позиции")
                return None, False
            if not request_line_text or not request_line_text.strip():
                st.error("❌ Введите текст позиции")
                return None, False

            form_data = {
                'item_type_id': type_id,
                'request_line_ol': request_line_ol,
                'request_line_text': request_line_text,
                'change_comment': change_comment
            }
            return form_data, True

        if cancelled:
            return None, 'cancelled'

    return None, False


def main():
    """Основная функция для редактирования позиции"""

    # Определяем режим
    is_new = st.session_state.get('create_new_item', False)
    item_id = st.session_state.get('edit_item_id')
    request_id = st.session_state.get('new_item_request_id') or st.session_state.get('edit_item_request_id')

    # Получаем текущего пользователя
    current_user, _ = get_streamlit_customer_user()

    # Режим создания новой позиции
    if is_new:
        if not request_id:
            st.error("❌ ID запроса не указан")
            if st.button("🔙 Вернуться"):
                st.switch_page("pages/request_edit.py")
            return

        st.title("➕ Новая позиция запроса")

        # Рендер формы
        form_data, result = render_request_item_form(is_new=True, request_id=request_id)

        if result and form_data:
            # Создаем позицию
            item = save_new_item(request_id, form_data)
            st.success(f"✅ Позиция {item.item_no} создана!")

            # Очищаем session_state
            if 'create_new_item' in st.session_state:
                del st.session_state.create_new_item
            if 'new_item_request_id' in st.session_state:
                del st.session_state.new_item_request_id

            st.switch_page("pages/request_edit.py")

        elif result == 'cancelled':
            if 'create_new_item' in st.session_state:
                del st.session_state.create_new_item
            if 'new_item_request_id' in st.session_state:
                del st.session_state.new_item_request_id
            st.switch_page("pages/request_edit.py")

        return

    # Режим редактирования существующей позиции
    if item_id:
        item = get_item(item_id)
        if not item:
            st.error("❌ Позиция не найдена")
            if st.button("🔙 Вернуться"):
                st.switch_page("pages/request_edit.py")
            return

        st.title(f"✏️ Редактирование позиции {item.item_no}")

        # Рендер формы
        form_data, result = render_request_item_form(item=item, is_new=False)

        if result and form_data:
            # Создаем новую версию с изменениями
            new_item = save_item_update(item, form_data, current_user)
            st.success(f"✅ Позиция {new_item.item_no} обновлена (версия {new_item.version})!")

            # Очищаем session_state
            if 'edit_item_id' in st.session_state:
                del st.session_state.edit_item_id
            if 'edit_item_request_id' in st.session_state:
                del st.session_state.edit_item_request_id

            st.switch_page("pages/request_edit.py")

        elif result == 'cancelled':
            if 'edit_item_id' in st.session_state:
                del st.session_state.edit_item_id
            if 'edit_item_request_id' in st.session_state:
                del st.session_state.edit_item_request_id
            st.switch_page("pages/request_edit.py")

        return

    # Если ни один режим не определен
    st.error("❌ Неизвестный режим")
    if st.button("🔙 Вернуться"):
        st.switch_page("pages/request_edit.py")


if __name__ == "__main__":
    main()