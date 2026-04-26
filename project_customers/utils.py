# project_customers/utils.py
from django.apps import apps
from django.conf import settings
import streamlit as st

def get_current_customer_user(request) :
    """
    Получить ProjectCustomerUser для текущего запроса
    Поддерживает отладку и аутентификацию
    """
    # 1. Пытаемся получить из middleware (если используется)
    customer_user = getattr(request , 'customer_user' , None)
    if customer_user :
        return customer_user

    # 2. Пытаемся получить из сессии
    customer_user_id = request.session.get('customer_user_id')
    if customer_user_id :
        ProjectCustomerUser = apps.get_model('project_customers' , 'ProjectCustomerUser')
        try :
            return ProjectCustomerUser.objects.get(id=customer_user_id)
        except ProjectCustomerUser.DoesNotExist :
            pass

    # 3. Для отладки - возвращаем первого пользователя
    if settings.DEBUG :
        ProjectCustomerUser = apps.get_model('project_customers' , 'ProjectCustomerUser')
        return ProjectCustomerUser.objects.first()

    return None


def get_streamlit_customer_user() :
    """
    Получить ProjectCustomerUser для Streamlit
    Результат кэшируется в st.session_state

    Returns:
        tuple: (customer_user, customer_company) или (None, None)
    """
    # Если в сессии уже есть пользователь - возвращаем его
    if 'customer_user' in st.session_state and 'customer_company' in st.session_state :
        return st.session_state.customer_user , st.session_state.customer_company

    ProjectCustomerUser = apps.get_model('project_customers' , 'ProjectCustomerUser')

    # Берем первого пользователя из БД
    first_user = ProjectCustomerUser.objects.first()

    if first_user :
        # Сохраняем в сессию
        st.session_state.customer_user = first_user
        st.session_state.customer_company = first_user.customer
        return first_user , first_user.customer

    return None , None


def clear_streamlit_customer_user() :
    """
    Очистить кэш пользователя в сессии (при выходе)
    """
    if 'customer_user' in st.session_state :
        del st.session_state.customer_user
    if 'customer_company' in st.session_state :
        del st.session_state.customer_company

def get_customer_user_by_django_user(django_user) :
    """
    Получить ProjectCustomerUser по Django User
    """
    if not django_user or not django_user.is_authenticated :
        return None

    ProjectCustomerUser = apps.get_model('project_customers' , 'ProjectCustomerUser')
    try :
        return ProjectCustomerUser.objects.get(user=django_user)
    except ProjectCustomerUser.DoesNotExist :
        return None


def get_user_template(customer_user) :
    """
    Получить шаблон номера из настроек пользователя
    """
    if not customer_user :
        return "{company_seq}-{user_seq}"

    UserParameter = apps.get_model('project_customers' , 'UserParameter')
    try :
        param = UserParameter.objects.get(
            user=customer_user ,
            code='request_number_template'
        )
        return param.value
    except UserParameter.DoesNotExist :
        return "{company_seq}-{user_seq}"