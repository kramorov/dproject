from django.urls import path
from project_customers.views.admin_customers import (
    CustomerAdminView, CustomerUserAdminView, CustomerKeyAdminView,
)

urlpatterns = [
    path('customers/', CustomerAdminView.as_view(), name='admin_customers_list'),
    path('customers/<int:pk>/', CustomerAdminView.as_view(), name='admin_customers_detail'),
    path('customers/<int:cid>/users/', CustomerUserAdminView.as_view(), name='admin_customers_users'),
    path('customers/<int:cid>/keys/', CustomerKeyAdminView.as_view(), name='admin_customers_keys'),
]
