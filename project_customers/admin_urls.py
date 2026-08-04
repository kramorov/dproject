from django.urls import path
from project_customers.views.admin_customers import (
    CustomerAdminView, CustomerUserAdminView, CustomerKeyAdminView,
)
from project_customers.views.admin_permissions import (
    SiteSectionListView, PermissionMatrixView, SystemGroupListView, ObjectRegistryView,
)

urlpatterns = [
    path('customers/', CustomerAdminView.as_view(), name='admin_customers_list'),
    path('customers/<int:pk>/', CustomerAdminView.as_view(), name='admin_customers_detail'),
    path('customers/<int:cid>/users/', CustomerUserAdminView.as_view(), name='admin_customers_users'),
    path('customers/<int:cid>/keys/', CustomerKeyAdminView.as_view(), name='admin_customers_keys'),
    path('customers/<int:cid>/permission-matrix/', PermissionMatrixView.as_view(), name='admin_permission_matrix'),
    path('site-sections/', SiteSectionListView.as_view(), name='admin_site_sections_list'),
    path('site-sections/<str:code>/', SiteSectionListView.as_view(), name='admin_site_sections_detail'),
    path('system-groups/', SystemGroupListView.as_view(), name='admin_system_groups_list'),
    path('system-groups/<int:group_id>/', SystemGroupListView.as_view(), name='admin_system_groups_detail'),
    path('object-registry/', ObjectRegistryView.as_view(), name='admin_object_registry'),
]
