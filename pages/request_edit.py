# pages/request_edit.py
import streamlit as st
from datetime import datetime

from clients.models import Company
from db_init import init_django

init_django()

from client_requests.models import ClientRequest , ClientRequestStatus
from project_customers.utils import get_streamlit_customer_user

st.set_page_config(
    page_title="Запрос клиента" ,
    page_icon="📋" ,
    layout="wide"
)


def get_request(request_id) :
    """Получить запрос по ID"""
    try :
        return ClientRequest.objects.get(id=request_id)
    except ClientRequest.DoesNotExist :
        return None


def save_request(request , form_data , is_new=False) :
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

    if is_new :
        # Для новых запросов устанавливаем владельца
        current_user , current_company = get_streamlit_customer_user()
        request.project_customer_user_request_owner = current_user
        request.project_customer_request_owner = current_company
        # Устанавливаем статус "Новый" для новых запросов
        if not request.request_status_id :
            new_status = ClientRequestStatus.get_default_status()
            if new_status :
                request.request_status_id = new_status.id

    request.save()
    return request


def render_request_form(request , is_edit=False , is_new=False) :
    """Рендер формы запроса"""

    # Получаем текущего пользователя для фильтрации
    current_user , _ = get_streamlit_customer_user()
    st.write(f"render_request_form")
    st.markdown("### 📋 Данные запроса")

    # Основная информация
    col1 , col2 = st.columns(2)

    with col1 :
        # Номер заявки
        if is_edit and not is_new :
            st.text_input("Номер заявки" , value=request.code or "" , disabled=True)
        else :
            code = st.text_input("Номер заявки" , value=request.code or "" ,
                                 placeholder="Будет сгенерирован автоматически")

        # Название заявки
        name = st.text_input("Название заявки *" , value=request.name or "")

        # Номер заявки клиента
        client_request_number = st.text_input("Номер заявки клиента" , value=request.client_request_number or "")

        # Конечный заказчик
        end_customer = st.text_input("Конечный заказчик" , value=request.end_customer or "")

    with col2 :
        # Дата запроса
        request_date = st.date_input(
            "Дата запроса *" ,
            value=request.request_date or datetime.now().date()
        )

        # Требуемая дата
        required_by_date = st.date_input(
            "Требуемая дата" ,
            value=request.required_by_date if request.required_by_date else datetime.now().date() ,
            help="Желаемая дата выполнения"
        )

        # Статус (для новых запросов - "Новый")
        statuses = ClientRequestStatus.get_choices()
        status_options = [(s.id , s.name) for s in statuses]

        # Для нового запроса выбираем статус "Новый"
        if is_new :
            default_status = ClientRequestStatus.get_default_status()
            current_status_id = default_status.id if default_status else (
                status_options[0][0] if status_options else None)
        else :
            current_status_id = request.request_status_id if request.request_status_id else (
                status_options[0][0] if status_options else None
            )

        status_id = st.selectbox(
            "Статус" ,
            options=status_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , s in enumerate(status_options) if s[0] == current_status_id) , 0)
        )[0]

    # Компании и ответственные
    st.markdown("### 🏢 Клиент")
    col1 , col2 = st.columns(2)

    with col1 :

        # Получаем компании для выпадающего списка
        company_choices = Company.get_choices(owner_user=current_user)
        company_options = [(0 , "— Выберите —")] + [(c['id'] , c['name']) for c in company_choices]
        current_company_id = request.request_from_client_company_id if request.request_from_client_company_id else 0
        company_id = st.selectbox(
            "Компания клиента" ,
            options=company_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , c in enumerate(company_options) if c[0] == current_company_id) , 0) ,
            key="company_select"
        )[0]

    with col2 :
        # Ответственное лицо
        st.markdown("### 👤 Ответственное лицо")

        person_choices = Company.get_person_choices(
            company_id=company_id if company_id != 0 else None ,
            owner_user=current_user
        )
        is_disabled = (company_id == 0)

        # Если есть только один сотрудник, автоматически выбираем его
        if len(person_choices) == 1 and not is_disabled :
            default_person_id = person_choices[0]['id']
        else :
            default_person_id = request.request_responsible_person_id if request.request_responsible_person_id else 0

        person_options = [(0 , "— Не выбрано —")] + [(p['id'] , p['name']) for p in person_choices]

        responsible_person_id = st.selectbox(
            "Ответственное лицо" ,
            options=person_options ,
            format_func=lambda x : x[1] ,
            index=next((i for i , p in enumerate(person_options) if p[0] == default_person_id) , 0) ,
            disabled=is_disabled
        )[0]

    # Текст запроса
    st.markdown("### 📝 Текст запроса")
    request_text = st.text_area(
        "Текст запроса" ,
        value=request.request_text or "" ,
        height=150
    )

    # Внутренние заметки
    internal_notes = st.text_area(
        "Внутренние заметки" ,
        value=request.internal_notes or "" ,
        height=100 ,
        help="Заметки для внутреннего использования"
    )

    # Интеграции
    st.markdown("### 🔌 Интеграции")
    col1 , col2 = st.columns(2)

    with col1 :
        orders_1c = st.text_input("Заказы в 1С" , value=request.orders_1c or "" , placeholder="Номера через запятую")

    with col2 :
        bitrix_deal_id = st.text_input("ID сделки в Битрикс24" , value=request.bitrix_deal_id or "")

    # Кнопки
    col1 , col2 , col3 = st.columns([1 , 1 , 1])

    with col1 :
        if st.button("💾 Сохранить" , use_container_width=True) :
            form_data = {
                'name' : name ,
                'code' : code if is_new or not is_edit else request.code ,
                'client_request_number' : client_request_number ,
                'end_customer' : end_customer ,
                'status_id' : status_id if status_id != 0 else None ,
                'company_id' : company_id if company_id != 0 else None ,
                'responsible_person_id' : responsible_person_id if responsible_person_id != 0 else None ,
                'request_text' : request_text ,
                'request_date' : request_date ,
                'required_by_date' : required_by_date if required_by_date else None ,
                'internal_notes' : internal_notes ,
                'orders_1c' : orders_1c ,
                'bitrix_deal_id' : bitrix_deal_id ,
            }
            return form_data , True

    with col2 :
        if st.button("🔙 Назад к списку" , use_container_width=True) :
            st.switch_page("pages/request_list.py")

    with col3 :
        if is_edit and not is_new and st.button("🗑 Удалить" , use_container_width=True) :
            return None , 'delete'

    return None , False


def main() :
    # Определяем режим
    is_new = st.session_state.get('create_new_request' , False)
    request_id = st.session_state.get('view_request_id') or st.session_state.get('edit_request_id')
    is_edit = 'edit_request_id' in st.session_state

    # Создание нового запроса
    if is_new :
        st.title("➕ Новый запрос клиента")

        # Создаем пустой объект запроса
        request = ClientRequest()
        request.request_date = datetime.now().date()

        # Рендер формы
        st.write(f"➕ Новый запрос клиента")
        form_data , saved = render_request_form(request , is_edit=False , is_new=True)

        if saved and form_data :
            request = save_request(request , form_data , is_new=True)
            st.success(f"✅ Запрос {request.code} успешно создан!")
            # Очищаем session_state
            if 'create_new_request' in st.session_state :
                del st.session_state.create_new_request
            st.switch_page("pages/request_list.py")

        if st.button("🔙 Отмена") :
            if 'create_new_request' in st.session_state :
                del st.session_state.create_new_request
            st.switch_page("pages/request_list.py")
        return

    # Просмотр/редактирование существующего
    if not request_id :
        st.error("❌ Запрос не найден")
        if st.button("🔙 Вернуться к списку") :
            st.switch_page("pages/request_list.py")
        return

    # Получаем запрос
    request = get_request(request_id)

    if not request :
        st.error("❌ Запрос не найден")
        if st.button("🔙 Вернуться к списку") :
            st.switch_page("pages/request_list.py")
        return

    # Заголовок
    if is_edit :
        st.title(f"✏️ Редактирование запроса {request.code or ''}")
    else :
        st.title(f"📋 Просмотр запроса {request.code or ''}")

    # Рендер формы
    print("✏️ Редактирование запроса")
    form_data , saved = render_request_form(request , is_edit=is_edit , is_new=False)

    if saved and form_data :
        request = save_request(request , form_data)
        st.success(f"✅ Запрос {request.code} успешно сохранен!")
        st.rerun()

    if saved == 'delete' :
        request_id = request.id
        request.delete()
        st.success(f"✅ Запрос удален!")
        # Очищаем session_state
        if 'view_request_id' in st.session_state :
            del st.session_state.view_request_id
        if 'edit_request_id' in st.session_state :
            del st.session_state.edit_request_id
        st.switch_page("pages/request_list.py")


if __name__ == "__main__" :
    main()