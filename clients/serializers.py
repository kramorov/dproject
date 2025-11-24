from rest_framework.serializers import ModelSerializer, SerializerMethodField

from clients.models import CompanyPerson, Company
from djangoProject1.common_models.abstract_serializers import FormDataSerializer


class CompanySerializer(FormDataSerializer):
    employees = SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id',
            'symbolic_code',
            'company_name',
            'employees'
        ]

    def get_employees(self, obj):
        # Получаем всех сотрудников компании через related_name
        employees = obj.employee_company.all()
        return CompanyPersonSerializer(employees, many=True).data

class CompanyPersonSerializer(FormDataSerializer):
    class Meta:
        model = CompanyPerson
        fields = '__all__'
        depth = 2

