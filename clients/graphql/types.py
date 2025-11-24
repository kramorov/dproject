import graphene
from graphene_django import DjangoObjectType
from clients.models import (Company, CompanyPerson)


class CompanyType(DjangoObjectType):
    class Meta:
        model = Company
        fields = (
            'id',
            'symbolic_code',
            'company_name'
        )

    verbose_names = graphene.Field(
        graphene.JSONString,
        description="Verbose names for fields"
    )
    help_texts = graphene.Field(
        graphene.JSONString,
        description="Help texts for fields"
    )

    def resolve_verbose_names(self, info):
        return {
            field.name: field.verbose_name
            for field in self._meta.fields
            if hasattr(field, 'verbose_name')
        }

    def resolve_help_texts(self, info):
        return {
            field.name: field.help_text
            for field in self._meta.fields
            if hasattr(field, 'help_text') and field.help_text
        }

class CompanyPersonType(DjangoObjectType):
    class Meta:
        model = CompanyPerson
        fields = (
            'id',
            'symbolic_code',
            'employee_company',
            'phone_number_office',
            'phone_number_cell',
            'person_email'
        )
clientsModelsTypes = [CompanyType,CompanyPersonType]