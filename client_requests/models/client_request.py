# client_requests/models/client_request.py
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import re
from django.utils import timezone

from clients.models import Company , CompanyPerson
from djangoProject1.common_models.abstract_models import CreatedAtMixin , UpdatedAtMixin
from project_customers.utils import get_user_template # Исправить потом код этой функции на аутентификацию


class ClientRequest(CreatedAtMixin , UpdatedAtMixin) :
    """
    Запрос клиента (основная модель)
    """
    id = models.UUIDField(
        primary_key=True ,
        default=uuid.uuid4 ,
        editable=False
    )

    request_number = models.CharField(
        max_length=50 ,
        unique=True ,
        verbose_name=_("Номер заявки") ,
        help_text=_("Уникальный номер заявки (генерируется автоматически)")
    )

    client_request_number = models.CharField(
        max_length=100 ,
        blank=True , null=True ,
        verbose_name=_("Номер заявки клиента") ,
        help_text=_("Номер заявки в системе клиента (если предоставлен)")
    )

    symbolic_code = models.CharField(
        max_length=100 ,
        blank=True , null=True ,
        verbose_name=_("Название заявки") ,
        help_text=_("Краткое название для идентификации")
    )

    end_customer = models.CharField(
        max_length=200 ,
        blank=True , null=True ,
        verbose_name=_("Конечный заказчик") ,
        help_text=_("Название конечного заказчика")
    )

    request_status = models.ForeignKey(
        'ClientRequestStatus' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Статус запроса")
    )

    request_from_client_company = models.ForeignKey(
        Company ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Компания клиента")
    )

    request_responsible_person = models.ForeignKey(
        CompanyPerson ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        verbose_name=_("Ответственное лицо")
    )

    request_text = models.TextField(
        blank=True , null=True ,
        verbose_name=_("Текст запроса")
    )

    request_date = models.DateField(
        verbose_name=_("Дата запроса") ,
        help_text=_("Дата поступления запроса")
    )

    required_by_date = models.DateField(
        null=True , blank=True ,
        verbose_name=_("Требуемая дата")
    )

    internal_notes = models.TextField(
        blank=True ,
        verbose_name=_("Внутренние заметки")
    )
    # Заказы в 1С
    onec_orders = models.TextField(
        blank=True , null=True ,
        verbose_name=_("Заказы в 1С") ,
        help_text=_("Номера заказов в 1С (можно несколько, разделитель - запятая)")
    )

    # Сделка в Битрикс24
    bitrix_deal_id = models.CharField(
        max_length=50 ,
        blank=True , null=True ,
        verbose_name=_("ID сделки в Битрикс24") ,
        help_text=_("Идентификатор сделки в Битрикс24")
    )
    class Meta :
        verbose_name = _("Запрос клиента")
        verbose_name_plural = _("Запросы клиентов")
        ordering = ['-request_date' , 'request_number']

    created_by = models.ForeignKey(
        'project_customers.ProjectCustomerUser' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='created_requests' ,
        verbose_name=_("Кем создано") ,
        help_text=_("Пользователь, создавший заявку")
    )

    # Наша компания (владелец заявки) - для быстрой фильтрации
    project_customer_request_owner = models.ForeignKey(
        'project_customers.ProjectCustomer' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='owned_requests' ,
        verbose_name=_("Владелец заявки") ,
        help_text=_("Наша компания, которая обрабатывает запрос")
    )

    # Пользователь-владелец (кто создал) - для быстрой фильтрации
    project_customer_user_request_owner = models.ForeignKey(
        'project_customers.ProjectCustomerUser' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='owned_requests' ,
        verbose_name=_("Владелец (пользователь)") ,
        help_text=_("Пользователь, создавший заявку")
    )

    def __str__(self) :
        if self.symbolic_code :
            return f"{self.request_number} - {self.symbolic_code}"
        return self.request_number

    def save(self , *args , **kwargs) :
        """Переопределяем save для автоматической генерации номера"""
        # Генерируем номер только если его еще нет
        if not self.request_number :
            self.request_number = self.generate_request_number()
        super().save(*args , **kwargs)

    def generate_request_number(self) :
        """
        Генерация номера заявки
        """
        from .request_number_counter import RequestNumberCounter

        print("\n" + "=" * 60)
        print("=== generate_request_number called ===")
        print(f"  request_from_client_company: {self.request_from_client_company}")
        print(f"  created_by: {self.created_by}")

        template = self._get_number_template()
        print(f"  template: {template}")

        company_number = None
        user_number = None

        if self.project_customer_request_owner and self.project_customer_user_request_owner:
            print("  ✅ Вызываем get_next_numbers...")
            company_number , user_number = RequestNumberCounter.get_next_numbers(
                project_customer=self.project_customer_request_owner ,
                project_customer_user=self.project_customer_user_request_owner
            )
            print(f"  Результат: company_number={company_number}, user_number={user_number}")
        else :
            print("  ❌ Пропускаем: отсутствует компания или пользователь")
            if not self.project_customer_request_owner :
                print("     - нет компании")
            if not self.project_customer_user_request_owner :
                print("     - нет пользователя")

        result = self._render_template(template , company_number , user_number)
        print(f"  Итоговый номер: {result}")
        print("=" * 60 + "\n")

        return result

    def _get_number_template(self) :
        """
        Получить шаблон номера из настроек пользователя
        """
        from project_customers.models import get_user_parameter

        print("\n" + "=" * 60)
        print("=== _get_number_template called ===")

        user_profile = getattr(self , 'project_customer_user_request_owner' , None)
        print(f"  user_profile (project_customer_user_request_owner): {user_profile}")

        if user_profile :
            print(f"  Пользователь найден: {user_profile.get_full_name()}")
            template = get_user_parameter(
                user_profile ,
                'request_number_template' ,
                default_value="{company_seq}-{user_seq}"
            )
            print(f"  Шаблон из настроек: {template}")
        else :
            print(f"  Пользователь не найден, используем шаблон по умолчанию")
            template = "{company_seq}-{user_seq}"
            print(f"  Шаблон по умолчанию: {template}")

        print(f"  Возвращаем: {template}")
        print("=" * 60 + "\n")

        return template

    def _render_template(self , template , company_number , user_number) :
        """
        Рендеринг шаблона номера
        """
        now = timezone.now()

        context = {
            'year' : now.strftime('%Y') ,
            'year_short' : now.strftime('%y') ,
            'month' : now.strftime('%m') ,
            'day' : now.strftime('%d') ,
            'company_seq' : company_number or '' ,
            'user_seq' : user_number or '' ,
        }

        result = template
        # Простая замена
        for key , value in context.items() :
            result = result.replace(f'{{{key}}}' , str(value))

        # Форматирование чисел {company_seq:05d}
        pattern = r'\{(company_seq|user_seq):(\d+)d\}'

        def replace(match) :
            var_name = match.group(1)
            width = int(match.group(2))
            val = context.get(var_name , 0)
            if isinstance(val , int) :
                return str(val).zfill(width)
            return str(val).zfill(width) if val else '0' * width

        result = re.sub(pattern , replace , result)

        return result

    def get_absolute_url(self) :
        return reverse('client_requests:detail' , args=[str(self.id)])

    def get_current_items(self) :
        """Получить все актуальные версии позиций"""
        return self.request_lines.filter(is_current=True , status='active').order_by('item_no')

    def get_current_snapshot(self) :
        """Получить текущий утвержденный снапшот"""
        return self.snapshots.filter(is_approved=True).first()