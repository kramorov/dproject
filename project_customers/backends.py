"""
CustomerBackend — аутентификация пользователей клиента по логину + пароль.

1:1 связка: ProjectCustomerUser.user → Django User (персональный для каждого).
Django User используется только для аутентификации и сессии.
Все права — через system_groups + org_roles.
"""
from datetime import date

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.utils.timezone import now


class CustomerBackend(ModelBackend):
    """
    Аутентификация клиентского пользователя по login.

    Связка 1:1: ProjectCustomerUser.user → Django User.
    Идентификация конкретного человека — через customer_user_id в сессии.
    """

    def authenticate(self, request, login=None, password=None, **kwargs):
        if login is None or password is None:
            return None

        from project_customers.models.user import ProjectCustomerUser

        try:
            customer_user = ProjectCustomerUser.objects.select_related(
                'customer', 'user'
            ).get(login=login, is_active=True)
        except ProjectCustomerUser.DoesNotExist:
            return None

        if not customer_user.check_password(password):
            return None

        customer = customer_user.customer
        if not customer.is_active:
            return None
        if customer.access_until and customer.access_until < date.today():
            return None

        django_user = customer_user.user
        if django_user is None:
            return None
        if not django_user.is_active:
            return None

        # Обновляем last_login в профиле клиента
        customer_user.last_login = now()
        customer_user.save(update_fields=['last_login'])

        # Сохраняем ID пользователя клиента в сессии
        if request:
            request.session['customer_user_id'] = customer_user.id

        return django_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
