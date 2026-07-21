# project_customers/utils.py
from django.apps import apps
from django.conf import settings

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
        ProjectCustomer = apps.get_model('project_customers' , 'ProjectCustomer')
        archimed = ProjectCustomer.objects.filter(name__icontains='Архимед').first()
        if archimed:
            return ProjectCustomerUser.objects.filter(customer=archimed).first()
        return ProjectCustomerUser.objects.first()

    return None


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