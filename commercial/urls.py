from django.urls import path

from .views import CartQuotationView

urlpatterns = [
    path('quotation/<uuid:cart_id>/', CartQuotationView.as_view(), name='cart_quotation'),
]
