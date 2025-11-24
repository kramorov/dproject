import graphene
# from graphene_django_filter import AdvancedDjangoFilterConnectionField, AdvancedFilterSet

from .types import CompanyType, CompanyPersonType
from clients.models import Company, CompanyPerson

class Query(graphene.ObjectType):
    # Запросы для Company
    company_company = graphene.Field(
        CompanyType,
        id=graphene.ID(required=True),
        description="Получение одной компании по ID"
    )
    company_all_companies = graphene.List(
        CompanyType,
        description="Список всех компаний"
    )
    company_companies_by_code = graphene.List(
        CompanyType,
        code=graphene.String(),
        description="Фильтрация компаний по коду"
    )

    # Запросы для CompanyPerson (исправлены имена полей)
    company_company_person = graphene.Field(
        CompanyPersonType,
        id=graphene.ID(required=True),
        description="Получение одного сотрудника по ID company_person"
    )
    company_all_company_persons = graphene.List(
        CompanyPersonType,
        description="Список всех сотрудников компании all_company_persons"
    )
    company_persons_by_company = graphene.List(
        CompanyPersonType,
        company_id=graphene.ID(required=True),
        description="Сотрудники конкретной компании persons_by_company"
    )

    # Резолверы для Company
    def resolve_company_company(self, info, id):
        return Company.objects.get(pk=id)

    def resolve_company_all_companies(self, info):
        return Company.objects.all()

    def resolve_company_companies_by_code(self, info, code=None):
        queryset = Company.objects.all()
        if code:
            queryset = queryset.filter(symbolic_code__icontains=code)
        return queryset

    # Резолверы для CompanyPerson (исправлены имена методов)
    def resolve_company_company_person(self, info, id):
        return CompanyPerson.objects.get(pk=id)

    def resolve_company_all_company_persons(self, info):
        return CompanyPerson.objects.select_related('employee_company').all()

    def resolve_company_persons_by_company(self, info, company_id):
        return CompanyPerson.objects.filter(employee_company__id=company_id)

# Создание схемы
# schema = graphene.Schema(query=Query)