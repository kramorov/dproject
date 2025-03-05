from django.urls import path, include
from rest_framework.routers import DefaultRouter

# from client_request import views
from .views import ClientRequestItemView, ClientRequestEditAdd, ClientRequestTypeAPIView, ClientRequestTypeAPIListView, \
  ClientRequestAPIView, ClientRequestAPIListView, ClientRequestItemAPIView, ClientRequestItemListView, \
  ElectricActuatorRequirementAPIView, ElectricActuatorRequirementAPIListView, ValveRequirementAPIView, \
  ValveRequirementAPIListView

router = DefaultRouter()
router.register(r'client-requests', ClientRequestEditAdd, basename='clientrequest')

urlpatterns = [

  path('clientrequesttype/<int:pk>/', ClientRequestTypeAPIView.as_view()),
  path('clientrequesttypelist/', ClientRequestTypeAPIListView.as_view()),

  path('clientrequest/<int:pk>/', ClientRequestAPIView.as_view()),
  path('clientrequestlist/', ClientRequestAPIListView.as_view()), #Развернутый (со свойствами список заказов клиентов)

  path('client-request-lines-list/',ClientRequestItemAPIView.as_view()), #Получение списка строк по id запроса клиента
  path('clientrequestitemlist/', ClientRequestItemListView.as_view()),
  path('client-request-items/', ClientRequestItemView.as_view(), name='client-request-items'),

  path('electricactuatorrequirement/<int:pk>/', ElectricActuatorRequirementAPIView.as_view()),
  path('electricactuatorrequirementlist/', ElectricActuatorRequirementAPIListView.as_view()),

  path('valverequirement/<int:pk>/', ValveRequirementAPIView.as_view()),
  path('valverequirementlist/', ValveRequirementAPIListView.as_view()),

]
