# media_library/urls.py
"""
URL-ы медиабиблиотеки — два входа:

  api/admin/media/   — админка (upload, edit, delete)
  api/media/         — публичная раздача (download, preview)
"""
from django.urls import path
from .views import (
    MediaAdminUploadView,
    MediaAdminDetailView,
    MediaAdminCopyView,
    MediaDownloadView,
    MediaPreviewView,
)

# ── Админские эндпоинты ──────────────────────────────
urlpatterns_admin = [
    path('upload/', MediaAdminUploadView.as_view(), name='media_admin_upload'),
    path('<int:pk>/copy/', MediaAdminCopyView.as_view(), name='media_admin_copy'),
    path('<int:pk>/', MediaAdminDetailView.as_view(), name='media_admin_detail'),
]

# ── Публичные эндпоинты ──────────────────────────────
urlpatterns_public = [
    path('<int:pk>/download/', MediaDownloadView.as_view(), name='media_download'),
    path('<int:pk>/view/', MediaPreviewView.as_view(), name='media_view'),
]
