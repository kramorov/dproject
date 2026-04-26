from django.db import models
from django.utils.translation import gettext_lazy as _

from project_customers.models import ProjectCustomer
from project_customers.utils import get_streamlit_customer_user
import logging
logger = logging.getLogger(__name__)

class Company(models.Model) :
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Название") ,
                            help_text=_("Рабочее название компании")
                            )
    full_name = models.CharField(max_length=500 , blank=True , null=True ,
                                 verbose_name=_("Название компании для документов") ,
                                 help_text=_('Официальное название компании (для документов)'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код компании"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание компании'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    # Наша компания (владелец аккаунта) - для быстрой фильтрации
    project_customer_request_owner = models.ForeignKey(
        'project_customers.ProjectCustomer' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='owned_project_customer' ,
        verbose_name=_("Владелец заявки") ,
        help_text=_("Наша компания, которая обрабатывает запрос")
    )

    # Пользователь-владелец (закрепленный менеджер) - для быстрой фильтрации
    # В дальнейшем заменить на список прав доступа
    project_customer_user_request_owner = models.ForeignKey(
        'project_customers.ProjectCustomerUser' ,
        on_delete=models.SET_NULL ,
        null=True , blank=True ,
        related_name='owned_project_customer_user' ,
        verbose_name=_("Владелец (пользователь)") ,
        help_text=_("Пользователь, создавший заявку")
    )
    # Партнер в 1С
    partner_1c = models.TextField(
        blank=True , null=True ,
        verbose_name=_("ID в 1С") ,
        help_text=_("Идентификатор партнера ID партнера в 1С")
    )

    # Партнер в Битрикс24
    bitrix_id = models.CharField(
        max_length=50 ,
        blank=True , null=True ,
        verbose_name=_("ID в Битрикс24") ,
        help_text=_("Идентификатор партнера в Битрикс24")
    )

    class Meta :
        verbose_name = 'Компания'  # Единственное число
        verbose_name_plural = 'Компании'  # Множественное число

    def __str__(self) :
        return self.name

    @classmethod
    def get_for_user(cls , filters=None) :
        """
        Получить компании для пользователя
        """
        # Получаем пользователя из filters или из сессии
        customer_user = filters.pop('customer_user' , None) if filters else None

        if customer_user is None :
            customer_user , customer_company = get_streamlit_customer_user()
        else :
            customer_company = customer_user.customer

        if not customer_user :
            return cls.objects.none()

        # Фильтр по владельцу
        queryset = cls.objects.filter(
            project_customer_request_owner=customer_company
        ).select_related(
            'project_customer_request_owner' ,
            'project_customer_user_request_owner'
        ).order_by('sorting_order' , 'name')

        if filters :
            if filters.get('name') :
                queryset = queryset.filter(name__icontains=filters['name'])
            if filters.get('code') :
                queryset = queryset.filter(code__icontains=filters['code'])
            if filters.get('is_active') is not None :
                queryset = queryset.filter(is_active=filters['is_active'])
            if filters.get('person_id') :
                queryset = queryset.filter(employee_company__id=filters['person_id'])

        return queryset

    @classmethod
    def get_choices(cls , owner_user=None) :
        """
        Получить список компаний для выпадающего списка
        """
        # Получаем пользователя
        if owner_user :
            customer_user = owner_user
            project_customer = owner_user.customer  # Это должен быть ProjectCustomer
        else :
            customer_user , project_customer = get_streamlit_customer_user()

        # if not customer_user or not project_customer :
        #     logger.error(
        #         f"No customer_user or project_customer found. customer_user: {customer_user}, project_customer: {project_customer}")
        #     return []
        #
        # logger.error(f"get_choices - project_customer: {project_customer} (type: {type(project_customer)})")

        companies = cls.objects.filter(
            project_customer_request_owner=project_customer ,
            is_active=True
        ).order_by('name')

        # logger.error(f"Found {companies.count()} companies")

        return [{'id' : c.id , 'name' : c.name} for c in companies]

    @classmethod
    def get_person_choices(cls , company_id=None , owner_user=None) :
        """
        Получить список сотрудников компании для выпадающего списка
        """
        # Получаем пользователя
        if owner_user :
            customer_user = owner_user
            project_customer = owner_user.customer
        else :
            customer_user , project_customer = get_streamlit_customer_user()

        if not customer_user or not project_customer :
            logger.error(f"No customer_user or project_customer found Company.get_person_choices")
            return []

        # logger.error(f"get_person_choices - company_id: {company_id}")
        # logger.error(f"project_customer: {project_customer} (type: {type(project_customer)})")

        # Базовый фильтр по владельцу
        persons = CompanyPerson.objects.filter(
            employee_company__project_customer_request_owner=project_customer ,
            is_active=True
        )

        # logger.error(f"Total persons (by owner): {persons.count()}")

        if company_id :
            persons = persons.filter(employee_company_id=company_id)
            # logger.error(f"After filter by company_id={company_id}: {persons.count()}")
        # else :
            # logger.error("No company_id filter applied")

        persons = persons.order_by('name')

        # Возвращаем ID как строки для единообразия
        persons_list = [{'id' : str(p.id) , 'name' : p.name} for p in persons]
        # logger.error(f"Final persons list with IDs (as strings): {persons_list}")

        return persons_list

class CompanyPerson(models.Model) :
    name = models.CharField(max_length=100 , blank=True , null=True ,
                            verbose_name=_("Сотрудник") ,
                            help_text=_("Рабочее название сотрудника для выбора в списке")
                            )
    full_name = models.CharField(max_length=500 , blank=True , null=True , verbose_name=_("ФИО") ,
                                 help_text=_('ФИО сотрудника'))
    code = models.CharField(max_length=50 , blank=True , null=True , verbose_name=_("Код") ,
                            help_text=_("Код сотрудника"))
    description = models.TextField(blank=True , verbose_name=_("Описание") ,
                                   help_text=_('Текстовое описание сотрудника'))
    sorting_order = models.IntegerField(default=0 , verbose_name=_("Порядок сортировки") ,
                                        help_text=_('Порядок сортировки в списке'))
    is_active = models.BooleanField(default=True , verbose_name=_("Активно") ,
                                    help_text=_('Активно свойство или нет'))
    # Контактное лицо в 1С
    partner_1c = models.TextField(
        blank=True , null=True ,
        verbose_name=_("ID в 1С") ,
        help_text=_("Идентификатор партнера ID партнера в 1С")
    )

    # Контактное лицо в Битрикс24
    bitrix_id = models.CharField(
        max_length=50 ,
        blank=True , null=True ,
        verbose_name=_("ID в Битрикс24") ,
        help_text=_("Идентификатор контактного лица в Битрикс24")
    )
    employee_company = models.ForeignKey(Company , on_delete=models.CASCADE , related_name='employee_company' ,
                                         help_text='Компания сотрудника')
    phone_number_office = models.CharField(max_length=50 , blank=True , null=True ,
                                           help_text='Телефон сотрудника офисный (городской)')
    phone_number_cell = models.CharField(max_length=50 , blank=True , null=True ,
                                         help_text='Телефон сотрудника сотовый')
    person_email = models.EmailField(max_length=255 , blank=True , null=True , help_text='Email сотрудника')

    class Meta :
        verbose_name = 'Ответственный сотрудник клиента'  # Единственное число
        verbose_name_plural = 'Ответственные сотрудники клиентов'  # Множественное число

    def __str__(self) :
        return self.name

    def get_full_name(self) :
        """Получить полное ФИО"""
        return self.full_name
