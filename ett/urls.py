from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EttStringView, EttDocumentViewSet

router = DefaultRouter()
router.register(r'ett-documents', EttDocumentViewSet)  # Регистрируем наш viewset

urlpatterns = [
    path('', include(router.urls)),  # Подключаем роутер
    path('decode/' , EttStringView.as_view() , name='ett_decode') ,
]
