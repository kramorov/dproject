# pages/client_requests/request_list.py
import streamlit as st
import pandas as pd
from datetime import datetime

from client_requests.models import ClientRequest, ClientRequestStatus
from project_customers.utils import get_streamlit_customer_user

st.set_page_config(
    page_title="Запросы клиентов",
    page_icon="📋",
    layout="wide"
)

def render_filters():
    """Рендер фильтров"""
    # current_user, current_user_company = get_current_user()

    with st.expander("🔍 Фильтры", expanded=False):
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

        with col1:
            code = st.text_input(
                "📄 Номер заявки", placeholder="Поиск по номеру...", key="filter_code"
            )

        with col2:
            client_request_number = st.text_input(
                "🏷️ Номер заявки клиента", placeholder="Поиск по номеру клиента...",
                key="filter_client_request_number"
            )

        with col3:
            name = st.text_input(
                "📝 Название заявки", placeholder="Поиск по названию...",
                key="filter_name"
            )

        with col4:
            statuses = ClientRequestStatus.get_choices()
            status_options = {0: "Все статусы"}
            for s in statuses:
                status_options[s.id] = s.name
            status_id = st.selectbox(
                "📊 Статус",
                options=list(status_options.keys()),
                format_func=lambda x: status_options[x],
                key="filter_status"
            )
            status_id = None if status_id == 0 else status_id

        with col5:
            companies = ClientRequest.get_company_choices()
            company_options = {0: "Все компании"}
            for c in companies :
                company_options[c['id']] = c['name']
            company_id = st.selectbox(
                "🏢 Компания клиента",
                options=list(company_options.keys()),
                format_func=lambda x: company_options[x],
                key="filter_company"
            )
            company_id = None if company_id == 0 else company_id

        with col6:
            st.markdown("### ")
            apply_filters = st.button("🔍 Применить фильтры", width='stretch')

    return {
        'code': code if code else None,
        'client_request_number': client_request_number if client_request_number else None,
        'name': name if name else None,
        'status_id': status_id,
        'company_id': company_id,
    }, apply_filters


def render_create_form() :
    """Рендер формы создания"""
    current_user , current_user_company = get_streamlit_customer_user()

    with st.form("create_request_form") :
        st.markdown("### ➕ Новый запрос клиента (page request_list)")

        col1 , col2 = st.columns(2)
        with col1 :
            statuses = ClientRequestStatus.get_choices()
            status_options = [(0 , "— Выберите —")] + [(s.id , s.name) for s in statuses]
            status_id = st.selectbox(
                "Статус" , options=status_options , format_func=lambda x : x[1]
            )[0]

            from clients.models import Company
            companies = Company.objects.all().order_by('name')  # убрали is_active
            company_options = [(0 , "— Выберите —")] + [(c.id , c.name) for c in companies]
            company_id = st.selectbox(
                "Компания клиента" , options=company_options , format_func=lambda x : x[1]
            )[0]

        with col2 :
            request_date = st.date_input("Дата запроса" , value=datetime.now().date())
            name = st.text_input("Название заявки" , placeholder="Краткое название")
            client_request_number = st.text_input("Номер заявки клиента" , placeholder="Номер в системе клиента")

        request_text = st.text_area("Текст запроса" , height=150)
        internal_notes = st.text_area("Внутренние заметки" , height=80)

        col1 , col2 = st.columns(2)
        with col1 :
            submitted = st.form_submit_button("✅ Создать" , use_container_width=True)
        with col2 :
            cancelled = st.form_submit_button("❌ Отмена" , use_container_width=True)

        if submitted :
            if status_id == 0 :
                status_id = None
            if company_id == 0 :
                company_id = None

            # Создаем новый запрос
            request = ClientRequest(
                request_date=request_date ,
                request_from_client_company_id=company_id ,
                request_status_id=status_id ,
                name=name or None ,
                client_request_number=client_request_number or None ,
                request_text=request_text or None ,
                internal_notes=internal_notes or None ,
                project_customer_user_request_owner=current_user ,
                project_customer_request_owner=current_user_company if current_user_company else None
            )
            request.save()

            st.success(f"✅ Запрос {request.code} создан!")
            # Очищаем флаг ДО перехода
            if 'create_new_request' in st.session_state:
                del st.session_state.create_new_request
            # Переходим на страницу редактирования
            st.session_state.edit_request_id = request.id
            st.session_state.create_new_request = False
            st.switch_page("pages/request_edit.py")

        if cancelled :
            st.session_state.create_new_request = False
            st.rerun()


def render_request_card(req) :
    """Рендер одной карточки запроса (компактная версия)"""
    with st.container() :
        # Заголовки
        col1 , col2 , col3 , col4 , col5 , col6 = st.columns([2 , 2 , 2 , 3 , 2 , 1])

        with col1 :
            st.markdown("**Статус**")
        with col2 :
            st.markdown("**Дата**")
        with col3 :
            st.markdown("**Номер**")
        with col4 :
            st.markdown("**Название заявки клиента**")
        with col5 :
            st.markdown("**Компания клиента**")
        with col6 :
            st.markdown("**Действия**")

        # Значения
        col1 , col2 , col3 , col4 , col5 , col6 = st.columns([2 , 2 , 2 , 3 , 2 , 1])

        with col1 :
            st.markdown(f"**{req.request_status.name if req.request_status else '-'}**")

        with col2 :
            st.write(req.request_date.strftime('%d.%m.%Y') if req.request_date else '-')

        with col3 :
            st.write(f"{req.code or '-'}")

        with col4 :
            st.write(f"{str(req.client_request_number) or '-'}")

        with col5 :
            st.write(f"{str(req.request_from_client_company) if req.request_from_client_company else '-'}")

        with col6 :
            col_btn1 , col_btn2 = st.columns(2)
            with col_btn1 :
                if st.button("👁️" , key=f"view_{req.id}" , help="Просмотр") :
                    st.session_state.view_request_id = req.id
                    st.switch_page("pages/request_edit.py")
            with col_btn2 :
                if st.button("✏️" , key=f"edit_{req.id}" , help="Редактировать") :
                    st.session_state.edit_request_id = req.id
                    st.switch_page("pages/request_edit.py")

        st.divider()

    return None , None

def render_request_table(requests):
    """Рендер таблицы запросов
    name: Тест шаблон
        code: RQ-К-0005
        client_request_number: 12345
        end_customer: fdghbfrdb
        request_status: 1
        request_from_client_company: 1
        request_responsible_person: 1
        request_text: sdcvasdcadsc
        request_date: 2026-04-26
        required_by_date: None
        internal_notes:
        orders_1c:
        bitrix_deal_id: None
        created_by: None
        project_customer_request_owner: 1
        project_customer_user_request_owner: 1
    """
    """Список запросов клиентов постранично"""
    if not requests.exists() :
        st.info("📭 Нет запросов, соответствующих критериям")
        return None , None

    # Пагинация
    items_per_page = 10
    total_items = requests.count()
    total_pages = (total_items + items_per_page - 1) // items_per_page

    if total_pages > 1 :
        col1 , col2 , col3 = st.columns([1 , 2 , 1])
        with col2 :
            page = st.number_input("Страница" , min_value=1 , max_value=total_pages , value=1 , step=1)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        requests_page = requests[start :end]
    else :
        requests_page = requests

    for req in requests_page :
        action , req_id = render_request_card(req)
        if action == 'view' :
            return req_id , None
        elif action == 'edit' :
            return None , req_id

    return None , None

#
# def render_stats(requests):
#     """Рендер статистики"""
#     total = requests.count()
#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("📊 Всего запросов", total)


def render_create_button():
    """Рендер кнопки создания"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Создать запрос", width='stretch'):
            st.session_state.create_new_request = True


def main():
    st.title("📋 Запросы клиентов")

    # current_user , current_user_company = get_streamlit_customer_user()
    # if not current_user:
    #     st.error("❌ Пользователь не найден")
    #     return

    render_create_button()

    if st.session_state.get('create_new_request', False):
        render_create_form()
        return

    filters, apply_filters = render_filters()

    if apply_filters or 'requests' not in st.session_state:
        st.session_state.requests_list = ClientRequest.get_for_user(filters)
    # result = ClientRequest.get_for_user(filters)
    # if result.exists() :
    #     obj = result.first()
    #     from django.forms.models import model_to_dict
    #     data = model_to_dict(obj)
    #     for key , value in data.items() :
    #         print(f"{key}: {value}")
    requests_list = st.session_state.requests_list
    # render_stats(requests_list)

    st.markdown("---")
    view_id , edit_id = render_request_table(requests_list)

    if view_id :
        st.session_state.view_request_id = view_id
        st.info(f"Просмотр запроса {view_id} (в разработке)")
        # st.switch_page("pages/client_requests/request_detail.py")

    if edit_id :
        st.session_state.edit_request_id = edit_id
        st.info(f"Редактирование запроса {edit_id} (в разработке)")
        # st.switch_page("pages/client_requests/request_edit.py") # раскомментировать когда будет страница деталей

if __name__ == "__main__":
    main()