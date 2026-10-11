from django.urls import path

from storage_manager import views

app_name = 'storage_manager'

urlpatterns = [
    path('backups/', views.StorageBackupsListView.as_view(), name='storage_backups'),
    path('backups/<str:folder>/manifest/', views.StorageManifestView.as_view(), name='storage_manifest'),
    path('backup/start/', views.StorageBackupStartView.as_view(), name='storage_backup_start'),
    path('backup/dry-run/', views.StorageBackupDryRunView.as_view(), name='storage_backup_dry_run'),
    path('restore/start/', views.StorageRestoreStartView.as_view(), name='storage_restore_start'),
    path('jobs/', views.StorageJobsListView.as_view(), name='storage_jobs'),
    path('jobs/<str:job_id>/', views.StorageJobStatusView.as_view(), name='storage_job_status'),
    path('jobs/<str:job_id>/cancel/', views.StorageJobCancelView.as_view(), name='storage_job_cancel'),
]
