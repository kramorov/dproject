from rest_framework import generics
from clients.models import Company, CompanyPerson
from .serializers import CompanySerializer, CompanyPersonSerializer


# 1. Получение списка всех Company CompanyList: Это вьюха для получения списка всех компаний. Она использует
# ListAPIView, который автоматически обрабатывает GET-запросы и возвращает список всех объектов Company.
class CompanyList(generics.ListAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


# 2. Получение Company по pk CompanyDetail: Это вьюха для получения деталей конкретной компании по её pk (primary
# key). Она использует RetrieveAPIView, который обрабатывает GET-запросы и возвращает один объект Company.
class CompanyDetail(generics.RetrieveAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


# 3. Получение списка всех CompanyPerson CompanyPersonList:
# Это вьюха для получения списка всех сотрудников компаний.
# Она использует ListAPIView для возврата всех объектов CompanyPerson.
class CompanyPersonList(generics.ListAPIView):
    queryset = CompanyPerson.objects.all()
    serializer_class = CompanyPersonSerializer


# 4. Получение CompanyPerson по pk CompanyPersonDetail: Это вьюха для получения деталей конкретного сотрудника
# компании по его pk. Она использует RetrieveAPIView для возврата одного объекта CompanyPerson.
class CompanyPersonDetail(generics.RetrieveAPIView):
    queryset = CompanyPerson.objects.all()
    serializer_class = CompanyPersonSerializer


# 5. Получение списка CompanyPerson, у которых Company == SelectedCompany CompanyPersonByCompanyList: Это вьюха для
# получения списка сотрудников, которые работают в конкретной компании. Она использует ListAPIView, но переопределяет
# метод get_queryset, чтобы фильтровать сотрудников по company_id, который передается в URL
class CompanyPersonByCompanyList(generics.ListAPIView):
    serializer_class = CompanyPersonSerializer

    def get_queryset(self):
        company_id = self.kwargs['company_id']
        return CompanyPerson.objects.filter(company_id=company_id)
