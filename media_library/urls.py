# media_library/urls.py
"""
URL-ы медиабиблиотеки — два входа:

  api/admin/media/   — админка (upload, edit, delete)
  api/media/         — публичная раздача (download, preview)
"""
from django.urls import path

from media_library.views.admin_copy import MediaAdminCopyView
from media_library.views.admin_detail import MediaAdminDetailView
from media_library.views.admin_recreate_preview import MediaAdminRecreatePreviewView
from media_library.views.admin_upload import MediaAdminUploadView
from media_library.views.download import MediaDownloadView
from media_library.views.filters import MediaFilterOptionsView
from media_library.views.preview import MediaPreviewView


# ── Админские эндпоинты ──────────────────────────────
urlpatterns_admin = [
    path('filters/', MediaFilterOptionsView.as_view(), name='media_admin_filters'),
    path('upload/', MediaAdminUploadView.as_view(), name='media_admin_upload'),
    path('<int:pk>/copy/', MediaAdminCopyView.as_view(), name='media_admin_copy'),
    path('<int:pk>/recreate-preview/', MediaAdminRecreatePreviewView.as_view(), name='media_admin_recreate_preview'),
    path('<int:pk>/', MediaAdminDetailView.as_view(), name='media_admin_detail'),
]

# ── Публичные эндпоинты ──────────────────────────────
urlpatterns_public = [
    path('<int:pk>/download/', MediaDownloadView.as_view(), name='media_download'),
    path('<int:pk>/view/', MediaPreviewView.as_view(), name='media_view'),
]