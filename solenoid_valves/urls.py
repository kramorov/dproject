# solenoid_valves/urls.py
from django.urls import path
from solenoid_valves.catalog.views_list import SolenoidValvesCatalogView
from solenoid_valves.catalog.views_filters import SolenoidValvesFilterOptionsView
from solenoid_valves.catalog.views_engineer import SolenoidValvesEngineerView
from solenoid_valves.catalog.views_engineer_filters import SolenoidValvesEngineerFilterOptionsView
from solenoid_valves.catalog.views_quickselect import SolenoidValvesQuickSelectView
from solenoid_valves.catalog.views_meta import SolenoidValvesMetaView

urlpatterns = [
    path('catalog/', SolenoidValvesCatalogView.as_view(), name='solenoid_valves_catalog'),
    path('filters/', SolenoidValvesFilterOptionsView.as_view(), name='solenoid_valves_filters'),
    path('engineer/', SolenoidValvesEngineerView.as_view(), name='solenoid_valves_engineer'),
    path('engineer/filters/', SolenoidValvesEngineerFilterOptionsView.as_view(), name='solenoid_valves_engineer_filters'),
    path('quickselect/', SolenoidValvesQuickSelectView.as_view(), name='solenoid_valves_quickselect'),
    path('meta/', SolenoidValvesMetaView.as_view(), name='solenoid_valves_meta'),
]
