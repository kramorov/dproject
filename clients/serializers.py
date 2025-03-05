from rest_framework.serializers import ModelSerializer

from clients.models import CompanyPerson, Company


class CompanySerializer(ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class CompanyPersonSerializer(ModelSerializer):
    class Meta:
        model = CompanyPerson
        fields = '__all__'
        depth = 2

