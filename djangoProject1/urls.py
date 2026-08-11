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
from django.urls import path, include, re_path

# from media_library.urls import urlpatterns_public
from .views import GetUrlByNameAPIView
from graphene_django.views import GraphQLView
from .graphql_api.schema import schema  # Импорт вашей GraphQL-схемы
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static
from core.views import UniversalAPIView
from media_library.urls import urlpatterns_admin as media_admin_urls, urlpatterns_public
from cert_doc.urls import urlpatterns_admin as cert_admin_urls
from price.urls import urlpatterns_admin as price_admin_urls
from django.views.generic import TemplateView

urlpatterns = [
    path('api/get-url/<str:name>/', GetUrlByNameAPIView.as_view(), name='get_url_by_name'),
    path('admin/', admin.site.urls),
    path('api/core/', include('core.urls')),  # Универсальный API - ТОЛЬКО ЭТОТ
path('api/test/', UniversalAPIView.as_view(), name='test_api'),  # Прямой маршрут
    # path('api/params/', include('params.urls')),  # Включаем URL-ы из приложения params
    # path('api/producers/', include('producers.urls')),  # Включаем URL-ы из приложения producers
    # path('api/electric_actuators/', include('electric_actuators.urls')),  # Включаем URL-ы из приложения electric_actuators
    # path('data/', include('data_processor.urls')),  # Включаем URL-ы из приложения electric_actuators
    # path('api/process-string-with-model-name/', StringProcessorView.as_view(), name='process_string'),
    # path('cg/', include('cable_glands.urls')),
    # path('ett/', include('ett.urls')),
    # path('api/valve-data/', include('valve_data.urls')),
    # path('api/clients/', include('clients.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/client_requests/', include('client_requests.urls')),
    path('api/configurator/', include('configurator.urls')),
    path('api/pneumatic_actuators/', include('pneumatic_actuators.urls')),
    path('api/ai-assistant/', include('ai_assistant.urls')),
    path('api/electric_actuators/', include('electric_actuators.urls')),
    path('api/gearbox/', include('gearbox.urls')),
    path('api/solenoid-valves/', include('solenoid_valves.urls')),
    path('api/pneumatic-fittings/', include('pneumatic_fittings.urls')),
    path('api/filter-regulator/', include('filter_regulator.urls')),
    path('api/pa-controls/', include('pa_controls.urls')),
    path('api/image-processor/', include('image_processor.urls')),
    path('api/svg-converter/', include('svg_converter.urls')),
    path('api/features/', include('features.urls')),
    path('api/admin/media/', include(media_admin_urls)),
    path('api/admin/certs/', include(cert_admin_urls)),
    path('api/admin/prices/', include(price_admin_urls)),
    path('api/admin/sku/', include('sku.urls')),
    path('api/admin/', include('project_customers.admin_urls')),
    path('api/auth/', include('project_customers.auth_urls')),
    path('api/media/', include(urlpatterns_public)),
    # GraphQL
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]
# SPA catch-all: serve index.html for all non-API/non-admin/non-static paths
urlpatterns += [re_path(r'^(?!api/|admin/|static/|media/|graphql/).*$', TemplateView.as_view(template_name='index.html'))]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += [url(r'^i18n/', include('django.conf.urls.i18n'))]