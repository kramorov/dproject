# pages/request_edit.py
import streamlit as st
from datetime import datetime

from clients.models import Company
from db_init import init_django

init_django()

from client_requests.models import ClientRequest, ClientRequestStatus, ClientRequestItem, RequestItemType
from project_customers.utils import get_streamlit_customer_user

st.set_page_config(
    page_title="Редактирование запроса клиента",
    page_icon="✏️",
    layout="wide"
)


def get_request(request_id):
    """Получить запрос по ID"""
    try:
        return ClientRequest.objects.get(id=request_id)
    except ClientRequest.DoesNotExist:
        return None


def get_request_items(request_id):
    """Получить все позиции запроса"""
    return ClientRequestItem.objects.filter(
        request_parent_id=request_id,
        is_current=True,
        status='active'
    ).order_by('item_no')


def delete_request_item(item_id):
    """Удалить позицию запроса (мягкое удаление)"""
    try:
        item = ClientRequestItem.objects.get(id=item_id)
        item.is_current = False
        item.status = 'deleted'
        item.save()
        return True
    except ClientRequestItem.DoesNotExist:
        return False


def save_request(request, form_data):
    """Сохранить изменения запроса"""
    request.name = form_data.get('name')
    request.client_request_number = form_data.get('client_request_number')
    request.end_customer = form_data.get('end_customer')
    request.request_status_id = form_data.get('status_id')
    request.request_from_client_company_id = form_data.get('company_id')
    request.request_responsible_person_id = form_data.get('responsible_person_id')
    request.request_text = form_data.get('request_text')
    request.request_date = form_data.get('request_date')
    request.required_by_date = form_data.get('required_by_date')
    request.internal_notes = form_data.get('internal_notes')
    request.orders_1c = form_data.get('orders_1c')
    request.bitrix_deal_id = form_data.get('bitrix_deal_id')
    request.save()
    return request


def save_new_item(request_id, item_type_id, request_line_ol, request_line_text):
    """Создать новую позицию"""

    # Создаем позицию
    item = ClientRequestItem.objects.create_new_item(
        request_parent_id=request_id,

        request_line_ol=request_line_ol,
        request_line_text=request_line_text,
    )
    return item


def update_item(item_id, item_type_id, request_line_ol, request_line_text):
    """Обновить существующую позицию"""
    item = ClientRequestItem.objects.get(id=item_id)
    item.item_type_id = item_type_id
    item.request_line_ol = request_line_ol
    item.request_line_text = request_line_text
    item.save()
    return item


def render_item_form(request_id):
    """Упрощенная форма для быстрого создания позиции"""

    with st.form("simple_item_form", clear_on_submit=True):
        st.markdown("#### ➕ Новая позиция")

        col1, col2 = st.columns(2)

        with col1:
            # Тип позиции (обязательно)
            item_types = RequestItemType.objects.all()
            type_options = [(None, "— Выберите тип —")] + [(t.id, t.name) for t in item_types]
            item_type_id = st.selectbox(
                "Тип позиции *",
                options=type_options,
                format_func=lambda x: x[1],
                index=0
            )[0]

        with col2:
            # Текст ОЛ
            request_line_ol = st.text_area("Номер ОЛ, например ОЛ-002 *", height=80)

        request_line_text = st.text_area("Текст позиции *", height=80)

        col3, col4 = st.columns(2)

        with col3:
            submitted = st.form_submit_button("💾 Создать", use_container_width=True, type="primary")

        with col4:
            cancelled = st.form_submit_button("❌ Отмена", use_container_width=True)

        if submitted:
            # Валидация
            if not item_type_id:
                st.error("❌ Выберите тип позиции")
                return
            if not request_line_text:
                st.error("❌ Введите текст позиции")
                return

            # Создаем позицию через метод модели
            item = ClientRequestItem.create_new_item(
                request_parent_id=request_id,
                item_type_id=item_type_id,
                request_line_text=request_line_text,
                request_line_ol=request_line_ol
            )
            st.success(f"✅ Позиция {item.item_no} создана!")

            # Скрываем форму и перезагружаем страницу
            st.session_state.show_item_form = False
            st.rerun()

        if cancelled:
            # Скрываем форму
            st.session_state.show_item_form = False
            st.rerun()

def render_request_item_card(item):
    """Рендер карточки позиции запроса"""

    # Получаем тип подбора для отображения
    item_type_name = ""
    if item.item_type_id:
        try:
            item_type = RequestItemType.objects.get(id=item.item_type_id)
            item_type_name = item_type.name
        except:
            item_type_name = "Тип не найден"

    with st.container(border=True):
        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            ol_value = item.request_line_ol or "не указан"
            text_preview = item.request_line_text or "не указан"
            if len(text_preview) > 80:
                text_preview = text_preview[:80] + "..."

            st.markdown(f"**Позиция {item.item_no}**")
            st.caption(f"📄 ОЛ: {ol_value} | 🏷️ Тип: {item_type_name}")
            st.caption(f"📝 {text_preview}")

        with col2:
            if st.button("✏️ Редактировать", key=f"edit_{item.id}", use_container_width=True):
                st.session_state.edit_item_id = item.id
                st.session_state.edit_item_request_id = item.request_parent_id
                st.switch_page("pages/request_item_edit.py")

        with col3:
            if st.button("🗑️ Удалить", key=f"del_{item.id}", use_container_width=True):
                if delete_request_item(item.id):
                    st.success(f"Позиция {item.item_no} удалена")
                    st.rerun()
                else:
                    st.error("Ошибка при удалении")


def render_items_list(request):
    """Рендер списка позиций"""
    st.markdown("### 📦 Позиции запроса")

    # Кнопка добавления
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("➕ Добавить позицию", use_container_width=True, type="primary"):
            st.session_state.show_item_form = True
    # ПОКАЗЫВАЕМ ФОРМУ, ЕСЛИ НУЖНО (вот это добавить)
    if st.session_state.get('show_item_form', False):
        render_item_form(request.id)
        st.markdown("---")  # разделитель
    # Получаем и отображаем позиции
    items = get_request_items(request.id)

    if not items:
        st.info("💡 Нет добавленных позиций. Нажмите 'Добавить позицию'")
        return

    for item in items:
        render_request_item_card(item)

def render_edit_form(request):
    """Рендер формы редактирования запроса"""

    current_user, _ = get_streamlit_customer_user()

    st.markdown("### 📋 Данные запроса")

    # Основная информация
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Номер заявки", value=request.code or "", disabled=True)
        name = st.text_input("Название заявки *", value=request.name or "")
        client_request_number = st.text_input("Номер заявки клиента", value=request.client_request_number or "")
        end_customer = st.text_input("Конечный заказчик", value=request.end_customer or "")

    with col2:
        request_date = st.date_input(
            "Дата запроса *",
            value=request.request_date or datetime.now().date()
        )
        required_by_date = st.date_input(
            "Требуемая дата",
            value=request.required_by_date if request.required_by_date else datetime.now().date(),
            help="Желаемая дата выполнения"
        )

        statuses = ClientRequestStatus.get_choices()
        status_options = [(s.id, s.name) for s in statuses]
        current_status_id = request.request_status_id if request.request_status_id else (
            status_options[0][0] if status_options else None)
        status_id = st.selectbox(
            "Статус",
            options=status_options,
            format_func=lambda x: x[1],
            index=next((i for i, s in enumerate(status_options) if s[0] == current_status_id), 0)
        )[0]

    # Компании и ответственные
    st.markdown("### 🏢 Клиент")
    col1, col2 = st.columns(2)

    with col1:
        company_choices = Company.get_choices(owner_user=None)
        company_options = [(0, "— Выберите —")] + [(c['id'], c['name']) for c in company_choices]
        current_company_id = request.request_from_client_company_id if request.request_from_client_company_id else 0
        company_id = st.selectbox(
            "Компания клиента",
            options=company_options,
            format_func=lambda x: x[1],
            index=next((i for i, c in enumerate(company_options) if c[0] == current_company_id), 0),
            key="company_select"
        )[0]

    with col2:
        st.markdown("### 👤 Ответственное лицо")
        person_choices = Company.get_person_choices(
            company_id=company_id if company_id != 0 else None,
            owner_user=current_user
        )
        is_disabled = (company_id == 0)

        if len(person_choices) == 1 and not is_disabled:
            default_person_id = person_choices[0]['id']
        else:
            default_person_id = request.request_responsible_person_id if request.request_responsible_person_id else 0

        person_options = [(0, "— Не выбрано —")] + [(p['id'], p['name']) for p in person_choices]
        responsible_person_id = st.selectbox(
            "Ответственное лицо",
            options=person_options,
            format_func=lambda x: x[1],
            index=next((i for i, p in enumerate(person_options) if p[0] == default_person_id), 0),
            disabled=is_disabled
        )[0]

    # Текст запроса
    st.markdown("### 📝 Текст запроса")
    request_text = st.text_area("Текст запроса", value=request.request_text or "", height=150)

    # Позиции запроса
    render_items_list(request)

    # Внутренние заметки
    st.markdown("### 📝 Внутренние заметки")
    internal_notes = st.text_area(
        "Внутренние заметки",
        value=request.internal_notes or "",
        height=100,
        help="Заметки для внутреннего использования"
    )

    # Интеграции
    st.markdown("### 🔌 Интеграции")
    col1, col2 = st.columns(2)
    with col1:
        orders_1c = st.text_input("Заказы в 1С", value=request.orders_1c or "", placeholder="Номера через запятую")
    with col2:
        bitrix_deal_id = st.text_input("ID сделки в Битрикс24", value=request.bitrix_deal_id or "")

    # Кнопки
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Сохранить запрос", use_container_width=True, type="primary"):
            form_data = {
                'name': name,
                'client_request_number': client_request_number,
                'end_customer': end_customer,
                'status_id': status_id if status_id != 0 else None,
                'company_id': company_id if company_id != 0 else None,
                'responsible_person_id': responsible_person_id if responsible_person_id != 0 else None,
                'request_text': request_text,
                'request_date': request_date,
                'required_by_date': required_by_date if required_by_date else None,
                'internal_notes': internal_notes,
                'orders_1c': orders_1c,
                'bitrix_deal_id': bitrix_deal_id,
            }
            return form_data, True

    with col2:
        if st.button("🔙 Назад к списку", use_container_width=True):
            st.switch_page("pages/request_list.py")

    return None, False


def main():
    # Получаем ID запроса из session_state
    request_id = st.session_state.get('edit_request_id')

    # Если нет ID - показываем ошибку и кнопку возврата
    if not request_id:
        st.error("❌ Не выбран запрос для редактирования")
        if st.button("🔙 Вернуться к списку"):
            st.switch_page("pages/request_list.py")
        return

    # Получаем запрос
    request = get_request(request_id)
    if not request:
        st.error(f"❌ Запрос с ID={request_id} не найден")
        if st.button("🔙 Вернуться к списку"):
            st.switch_page("pages/request_list.py")
        return

    st.title(f"✏️ Редактирование запроса {request.code or ''}")

    # Рендер формы редактирования
    form_data, saved = render_edit_form(request)

    if saved and form_data:
        request = save_request(request, form_data)
        st.success(f"✅ Запрос {request.code} успешно сохранен!")
        st.rerun()


if __name__ == "__main__":
    main()