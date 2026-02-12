# price/urls.py
from django.urls import path
from .views import update_exchange_rates

app_name = 'price'

urlpatterns = [
    path('cbr-update/', update_exchange_rates, name='cbr-update'),
]