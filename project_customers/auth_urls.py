from django.urls import path
from project_customers.views.auth import LoginView, LogoutView, CurrentUserView
from project_customers.views.api_keys import ApiKeyListView, ApiKeyDetailView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('me/', CurrentUserView.as_view(), name='auth_me'),
    path('api-keys/', ApiKeyListView.as_view(), name='api_keys_list'),
    path('api-keys/<int:pk>/', ApiKeyDetailView.as_view(), name='api_keys_detail'),
]
