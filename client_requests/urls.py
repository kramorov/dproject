from django.urls import path, include
from rest_framework.routers import DefaultRouter

# from client_request import views
from .views import ClientRequestItemView, ClientRequestEditAdd, ClientRequestTypeAPIView, ClientRequestTypeAPIListView, \
  ClientRequestAPIView, ClientRequestsAPIListView, ClientRequestItemAPIView, ClientRequestItemListView, \
  ElectricActuatorRequirementAPIView, ElectricActuatorRequirementAPIListView,  \
   ClientRequestLinesOnly_List, ClientRequestsStatusList

router = DefaultRouter()
router.register(r'client-requests', ClientRequestEditAdd, basename='clientrequests')


urlpatterns = [

  path('clientrequesttype/<int:pk>/', ClientRequestTypeAPIView.as_view()),
  path('clientrequesttypelist/', ClientRequestTypeAPIListView.as_view()),
  # Получить структуру: GET /api/client-requests/structure/
  path('request/structure/', ClientRequestAPIView.as_view(), name='client-request-structure'),

  # CRUD операции: /api/client-requests/<pk>/
  path('request/<int:pk>/', ClientRequestAPIView.as_view(), name='client-request-detail'),
  path('clientrequestlist/', ClientRequestsAPIListView.as_view(), name='request-list'), #Развернутый (со свойствами список заказов клиентов)
  path('clientrequestlist/<int:pk>/', ClientRequestsAPIListView.as_view(), name='client-request-detail'),    # Развернутый (со свойствами список заказов клиентов)
  path('client-requests-status/', ClientRequestsStatusList.as_view()),
  # Развернутый (со свойствами список заказов клиентов)
  path('client-request-lines-list/',ClientRequestItemAPIView.as_view()), #Получение списка строк по id запроса клиента
  path('clientrequestitemlist/', ClientRequestItemListView.as_view()),
  path('client-request-items/', ClientRequestLinesOnly_List.as_view(), name='client-request-items'),

  path('electricactuatorrequirement/<int:pk>/', ElectricActuatorRequirementAPIView.as_view()),
  path('electricactuatorrequirementlist/', ElectricActuatorRequirementAPIListView.as_view()),

  # path('valverequirement/<int:pk>/', ValveRequirementAPIView.as_view()),
  # path('valverequirementlist/', ValveRequirementAPIListView.as_view()),

]
