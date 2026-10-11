"""
API админ-страницы «Бэкап хранилища» (Cloud.ru ↔ локальный диск).

  GET  backups/                       — список локальных бэкапов (по manifest.json)
  GET  backups/<folder>/manifest/     — полный manifest.json бэкапа
  POST backup/start/                  — запустить бэкап (фоново)  {prefix?}
  POST backup/dry-run/                — dry-run бэкапа (фоново)   {prefix?}
  POST restore/start/                 — запустить восстановление (фоново) {folder, overwrite?, dry_run?}
  GET  jobs/                          — список задач (с прогрессом и журналом)
  GET  jobs/<job_id>/                 — состояние одной задачи
  POST jobs/<job_id>/cancel/          — отменить задачу

Доступ: SectionAccessPermission(required_section='admin_section')
(тот же контракт, что у админки медиабиблиотеки).
"""
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from project_customers.permissions import SectionAccessPermission

from storage_manager import backup_service
from storage_manager import jobs


class StorageAdminBaseView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'


class StorageBackupsListView(StorageAdminBaseView):
    """GET backups/ — список локальных бэкапов."""

    def get(self, request):
        return Response({'backups': backup_service.list_backups()})


class StorageManifestView(StorageAdminBaseView):
    """GET backups/<folder>/manifest/ — полный manifest.json бэкапа."""

    def get(self, request, folder):
        try:
            manifest = backup_service.load_manifest(folder)
        except (ValueError, FileNotFoundError) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response({'folder': folder, 'manifest': manifest})


class StorageBackupStartView(StorageAdminBaseView):
    """POST backup/start/ — полный бэкап Cloud.ru → диск (фоново)."""

    def post(self, request):
        prefix = str(request.data.get('prefix', '') or '').strip()
        if any(ch in prefix for ch in ('\\', '..')):
            return Response({'error': 'Некорректный префикс'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            job_id = jobs.start_job('backup', {'prefix': prefix}, lambda j: backup_service.run_backup(
                prefix=prefix, progress=j.progress, cancel_event=j.cancel_event))
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response({'job_id': job_id}, status=status.HTTP_202_ACCEPTED)


class StorageBackupDryRunView(StorageAdminBaseView):
    """POST backup/dry-run/ — листинг Cloud.ru без скачивания (фоново)."""

    def post(self, request):
        prefix = str(request.data.get('prefix', '') or '').strip()
        if any(ch in prefix for ch in ('\\', '..')):
            return Response({'error': 'Некорректный префикс'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            job_id = jobs.start_job('backup_dry_run', {'prefix': prefix},
                                    lambda j: backup_service.run_backup(
                                        prefix=prefix, dry_run=True,
                                        progress=j.progress, cancel_event=j.cancel_event))
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response({'job_id': job_id}, status=status.HTTP_202_ACCEPTED)


class StorageRestoreStartView(StorageAdminBaseView):
    """POST restore/start/ — восстановление из локального бэкапа в Cloud.ru (фоново)."""

    def post(self, request):
        folder = str(request.data.get('folder', '') or '').strip()
        overwrite = bool(request.data.get('overwrite', False))
        dry_run = bool(request.data.get('dry_run', False))
        try:
            manifest = backup_service.load_manifest(folder)
        except (ValueError, FileNotFoundError) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        manifest_path = os.path.join(backup_service.BACKUP_ROOT, folder, 'manifest.json')
        try:
            job_id = jobs.start_job('restore', {'folder': folder, 'overwrite': overwrite, 'dry_run': dry_run},
                                    lambda j: backup_service.run_restore(
                                        manifest_path=manifest_path, overwrite=overwrite,
                                        dry_run=dry_run, progress=j.progress,
                                        cancel_event=j.cancel_event))
        except RuntimeError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        return Response({'job_id': job_id}, status=status.HTTP_202_ACCEPTED)


class StorageJobsListView(StorageAdminBaseView):
    """GET jobs/ — список задач (последние сверху)."""

    def get(self, request):
        return Response({'jobs': jobs.list_jobs()})


class StorageJobStatusView(StorageAdminBaseView):
    """GET jobs/<job_id>/ — состояние задачи с прогрессом и журналом."""

    def get(self, request, job_id):
        job = jobs.get_job(job_id)
        if not job:
            return Response({'error': 'Задача не найдена'}, status=status.HTTP_404_NOT_FOUND)
        return Response(job.to_dict())


class StorageJobCancelView(StorageAdminBaseView):
    """POST jobs/<job_id>/cancel/ — отменить задачу."""

    def post(self, request, job_id):
        ok = jobs.cancel_job(job_id)
        if not ok:
            return Response({'error': 'Задача не найдена или уже завершена'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({'ok': True})
