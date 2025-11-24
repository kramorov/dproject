# urls.py
from django.urls import path
from .views import CSVImportView, ImportHistoryView

urlpatterns = [
    path('api/procurement/import-csv/', CSVImportView.as_view(), name='import-csv'),
    path('api/procurement/import-history/', ImportHistoryView.as_view(), name='import-history'),
]