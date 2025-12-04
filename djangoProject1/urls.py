#djangoProject1/urls.py
"""djangoProject12 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.template.defaulttags import url
from django.urls import path, include
from data_processor.views import StringProcessorView
from .views import GetUrlByNameAPIView
from graphene_django.views import GraphQLView
from .graphql_api.schema import schema  # Импорт вашей GraphQL-схемы
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static
from core.views import UniversalAPIView

urlpatterns = [
    path('api/get-url/<str:name>/', GetUrlByNameAPIView.as_view(), name='get_url_by_name'),
    path('admin/', admin.site.urls),
    path('api/core/', include('core.urls')),  # Универсальный API - ТОЛЬКО ЭТОТ
    # path('api/params/', include('params.urls')),  # Включаем URL-ы из приложения params
    # path('api/producers/', include('producers.urls')),  # Включаем URL-ы из приложения producers
    # path('api/electric_actuators/', include('electric_actuators.urls')),  # Включаем URL-ы из приложения electric_actuators
    # path('data/', include('data_processor.urls')),  # Включаем URL-ы из приложения electric_actuators
    # path('api/process-string-with-model-name/', StringProcessorView.as_view(), name='process_string'),
    # path('cg/', include('cable_glands.urls')),
    # path('ett/', include('ett.urls')),
    # path('api/valve-data/', include('valve_data.urls')),
    # path('api/clients/', include('clients.urls')),
    # path('api/client_requests/', include('client_requests.urls')),
    path('api/pneumatic_actuators/', include('pneumatic_actuators.urls')),
    # GraphQL
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += [url(r'^i18n/', include('django.conf.urls.i18n'))]