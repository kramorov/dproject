# # myapp/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import ModelLineViewSet, ElectricActuatorDataViewSet, CableGlandHolesSetViewSet, WiringDiagramViewSet,\
#     ActualActuatorViewSet, ActualActuatorAPIView
# # ActualActuatorListView
#
# import logging
#
# # Получаем логгер для этого модуля
# logger = logging.getLogger(__name__)
# # Настройка базового логгера
# logging.basicConfig(level=logging.DEBUG)
#
# # Пример записи сообщения
# logger.debug('Это отладочное сообщение')
# logger.info('Это информационное сообщение')
# logging.warning('Это предупреждающее сообщение')
# logging.error('Это сообщение об ошибке')
# logging.critical('Это критическое сообщение')
#
# router = DefaultRouter()
# router.register(r'model-lines', ModelLineViewSet)
# router.register(r'model-data', ElectricActuatorDataViewSet)
# router.register(r'cable-glands-holes-sets', CableGlandHolesSetViewSet)
# router.register(r'wiring-diagrams', WiringDiagramViewSet)
# router.register(r'actual-actuator', ActualActuatorViewSet)
# # router.register(r'actuals-actuator-sellist', ActualActuatorListView)
#
#
# urlpatterns = [
#     path('', include(router.urls)),
#     # CRUD-операции
#     path('actuators/', ActualActuatorAPIView.as_view(), name='actuator-list-create'),
#     path('actual-actuator/<int:pk>/', ActualActuatorAPIView.as_view(), name='actuator-detail-update-delete'),
#     # Копирование записи
#     path('actual-actuator/<int:pk>/copy/', ActualActuatorAPIView.as_view(), name='actuator-copy'),
# ]
