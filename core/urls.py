#core/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import UniversalAPIView, DebugAPIView, ExdStructureView, ExdParseView, ExdCompatibleView
from .climate_views import ClimateStructureView, ClimateParseView
from .ref_views import SectionsView, AllowedAppsView, BrandsView, DjangoUsersView

urlpatterns = [
    path('', csrf_exempt(UniversalAPIView.as_view()), name='universal_api'),
    path('debug/', DebugAPIView.as_view(), name='debug_api'),
    path('exd/structure/', ExdStructureView.as_view(), name='exd_structure'),
    path('exd/parse/', ExdParseView.as_view(), name='exd_parse'),
    path('exd/compatible/', ExdCompatibleView.as_view(), name='exd_compatible'),
    path('climate/structure/', ClimateStructureView.as_view(), name='climate_structure'),
    path('climate/parse/', ClimateParseView.as_view(), name='climate_parse'),
    path('sections/', SectionsView.as_view(), name='sections'),
    path('allowed-apps/', AllowedAppsView.as_view(), name='allowed_apps'),
    path('brands/', BrandsView.as_view(), name='brands'),
    path('django-users/', DjangoUsersView.as_view(), name='django_users'),
]
