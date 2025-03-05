from django.urls import path
from .views import CompanyList, CompanyDetail, CompanyPersonList, CompanyPersonDetail, CompanyPersonByCompanyList

urlpatterns = [
    path('companies-list/', CompanyList.as_view(), name='company-list'),
    path('company-detail/<int:pk>/', CompanyDetail.as_view(), name='company-detail'),
    path('company-persons/', CompanyPersonList.as_view(), name='companyperson-list'),
    path('company-person-detail/<int:pk>/', CompanyPersonDetail.as_view(), name='companyperson-detail'),
    path('company/<int:company_id>/company-persons/', CompanyPersonByCompanyList.as_view(), name='companyperson-by-company-list'),
]