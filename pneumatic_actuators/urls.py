# pneumatic_actuators/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import OptionAPIView, SelectorAPIView
from .api.views_constructor import ConstructorViewSet
from .api.views_item import PneumaticActuatorItemListView, PneumaticActuatorItemDetailView

router = DefaultRouter()
router.register(r'constructor', ConstructorViewSet, basename='constructor')

urlpatterns = [
    path('items/', PneumaticActuatorItemListView.as_view(), name='pa_item_list'),
    path('items/<int:pk>/', PneumaticActuatorItemDetailView.as_view(), name='pa_item_detail'),
    path('options/', OptionAPIView.as_view(), name='get_options'),
    path('selector/initial-data/', SelectorAPIView.as_view(), name='selector_initial_data'),
    path('selector/search/', SelectorAPIView.as_view(), name='selector_search'),
    path('', include(router.urls)),
]
