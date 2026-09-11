# cable_glands/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cable_glands.api.views_constructor import CableGlandConstructorViewSet
from cable_glands.catalog.views_list import CableGlandCatalogView
from cable_glands.catalog.views_filters import CableGlandFilterOptionsView
from cable_glands.catalog.views_engineer import CableGlandEngineerView
from cable_glands.catalog.views_engineer_filters import CableGlandEngineerFilterOptionsView
from cable_glands.catalog.views_quickselect import CableGlandQuickSelectView
from cable_glands.catalog.views_meta import CableGlandMetaView
from cable_glands.catalog.views_detail import CableGlandDetailView
from cable_glands.catalog.views_sections import CableGlandSectionView

router = DefaultRouter()
router.register(r'constructor', CableGlandConstructorViewSet, basename='cg-constructor')

urlpatterns = [
    path('', include(router.urls)),
    path('catalog/', CableGlandCatalogView.as_view(), name='cable_glands_catalog'),
    path('catalog/<int:pk>/', CableGlandDetailView.as_view(), name='cable_glands_detail'),
    path('sections/', CableGlandSectionView.as_view(), name='cable_glands_sections'),
    path('filters/', CableGlandFilterOptionsView.as_view(), name='cable_glands_filters'),
    path('engineer/', CableGlandEngineerView.as_view(), name='cable_glands_engineer'),
    path('engineer/filters/', CableGlandEngineerFilterOptionsView.as_view(), name='cable_glands_engineer_filters'),
    path('quickselect/', CableGlandQuickSelectView.as_view(), name='cable_glands_quickselect'),
    path('meta/', CableGlandMetaView.as_view(), name='cable_glands_meta'),
]
