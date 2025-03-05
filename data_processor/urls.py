# text_processor/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TextInputViewSet, IndexView, HelloView, StringProcessorView, ETTView

# Создаем экземпляр роутера
router = DefaultRouter()
router.register(r'action', TextInputViewSet, basename='text-input')
# router.register(r'process', StringProcessorView.as_view(), basename='process-string')

urlpatterns = [
    path('index/', IndexView.as_view(), name='index'),  # Главная страница
    path('hello/', HelloView.as_view(), name='hello'),
    path('ett/', ETTView.as_view(), name='ett_decode'),
    # path('text/', StringProcessorView.as_view()),
]
