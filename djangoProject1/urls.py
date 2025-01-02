# myproject/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('params.urls')),  # Включаем URL-ы из приложения myapp
]
