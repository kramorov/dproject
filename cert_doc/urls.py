# cert_doc/urls.py
from django.urls import path

from cert_doc.views.admin_copy import CertAdminCopyView
from cert_doc.views.admin_create import CertAdminCreateView
from cert_doc.views.admin_detail import CertAdminDetailView
from cert_doc.views.admin_media_upload import CertMediaUploadView
from cert_doc.views.filters import CertFilterOptionsView

urlpatterns_admin = [
    path('upload-media/', CertMediaUploadView.as_view(), name='cert_media_upload'),
    path('filters/', CertFilterOptionsView.as_view(), name='cert_filter_options'),
    path('', CertAdminCreateView.as_view(), name='cert_admin_create'),
    path('<int:pk>/copy/', CertAdminCopyView.as_view(), name='cert_admin_copy'),
    path('<int:pk>/', CertAdminDetailView.as_view(), name='cert_admin_detail'),
]
