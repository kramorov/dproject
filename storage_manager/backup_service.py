"""
Общий сервис бэкапа/восстановления Cloud.ru.

Один код на два входа:
  - management-команды: backup_cloudru / restore_cloudru (прогресс → stdout);
  - API админ-страницы «Бэкап хранилища» (прогресс → ProgressState для polling).

Прогресс передаётся через объект ProgressState (потокобезопасный):
  start(phase, total) → set(**счётчики) → log(text) → finish(phase).
"""
import json
import os
import re
import threading
import time
from collections import deque
from datetime import datetime, timezone

from storage_manager.storage_backends.cloudru import CloudRuStorage

BACKUP_ROOT = os.path.join('backups', 'cloudru')
FOLDER_RE = re.compile(r'^[A-Za-z0-9._\-]+$')


def fmt_size(size_bytes: int) -> str:
    for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
        if size_bytes < 1024:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.1f} ПБ'


class ProgressState:
    """Потокобезопасное состояние задачи: фазы, счётчики, журнал."""

    def __init__(self):
        self._lock = threading.Lock()
        self.phase = 'queued'
        self.current = 0
        self.total = 0
        self.processed = 0      # скачано (backup) / залито (restore)
        self.skipped = 0
        self.failed = 0
        self.bytes = 0
        self.speed = 0
        self.elapsed = 0.0
        self.started_at = None
        self.finished_at = None
        self._logs = deque(maxlen=300)
        self._start_time = None

    def start(self, phase, total=0):
        with self._lock:
            self.phase = phase
            self.total = total
            self.current = 0
            if self._start_time is None:
                self._start_time = time.time()
                self.started_at = time.time()

    def set(self, **kw):
        with self._lock:
            for k, v in kw.items():
                if hasattr(self, k):
                    setattr(self, k, v)
            if self._start_time:
                self.elapsed = time.time() - self._start_time

    def log(self, text):
        with self._lock:
            self._logs.append(text)

    def finish(self, phase):
        with self._lock:
            self.phase = phase
            self.finished_at = time.time()
            if self._start_time:
                self.elapsed = time.time() - self._start_time

    def snapshot(self):
        with self._lock:
            pct = 0.0
            if self.total:
                pct = round(min(self.current, self.total) / self.total * 100, 1)
            return {
                'phase': self.phase,
                'current': self.current,
                'total': self.total,
                'processed': self.processed,
                'skipped': self.skipped,
                'failed': self.failed,
                'bytes': self.bytes,
                'speed': round(self.speed, 0),
                'elapsed': round(self.elapsed, 1),
                'percent': pct,
                'started_at': self.started_at,
                'finished_at': self.finished_at,
                'logs': list(self._logs),
            }


def get_storage() -> CloudRuStorage:
    return CloudRuStorage()


def list_cloud_objects(prefix='', page_size=1000, progress=None):
    """Листинг всех объектов бакета Cloud.ru (пагинация list_objects_v2)."""
    storage = get_storage()
    s3 = storage.s3_admin
    objects = []
    token = None
    while True:
        kw = {'Bucket': storage.bucket_name, 'MaxKeys': page_size}
        if prefix:
            kw['Prefix'] = prefix
        if token:
            kw['ContinuationToken'] = token
        resp = s3.list_objects_v2(**kw)
        for obj in resp.get('Contents', []):
            objects.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'etag': obj.get('ETag', ''),
                'last_modified': obj['LastModified'].isoformat(),
            })
        if progress is not None:
            progress.set(current=len(objects))
        if resp.get('IsTruncated'):
            token = resp.get('NextContinuationToken')
        else:
            break
    return objects


def run_backup(*, prefix='', output_dir=None, dry_run=False, manifest_only=False,
               page_size=1000, progress=None, cancel_event=None) -> dict:
    """
    Полный бэкап Cloud.ru на локальный диск.

    dry_run=True — только листинг (файлы не скачиваются, manifest не пишется).
    manifest_only=True — только manifest.json без скачивания файлов.
    Возвращает stats-dict.
    """
    storage = get_storage()
    s3 = storage.s3_admin
    bucket = storage.bucket_name
    if not output_dir:
        output_dir = os.path.join(BACKUP_ROOT, datetime.now().strftime('%Y-%m-%d'))

    def cancelled():
        return cancel_event is not None and cancel_event.is_set()

    if progress is not None:
        progress.start('listing')
        progress.log(f'Бакет: {bucket}')
        progress.log(f'Endpoint: {storage.endpoint_url}')
        progress.log(f'Префикс: {prefix or "(все)"}')
        progress.log(f'Папка бэкапа: {output_dir}')
        progress.log('Получаю список объектов...')

    objects = list_cloud_objects(prefix=prefix, page_size=page_size, progress=progress)
    total_size = sum(o['size'] for o in objects)

    if progress is not None:
        progress.log(f'Всего объектов: {len(objects)}, общий размер: {fmt_size(total_size)}')

    if not objects:
        if progress is not None:
            progress.log('Нет объектов для бэкапа.')
            progress.finish('done')
        return {
            'bucket': bucket, 'endpoint': storage.endpoint_url, 'prefix': prefix,
            'output_dir': output_dir, 'total_objects': 0, 'total_size_bytes': 0,
            'downloaded': 0, 'skipped': 0, 'failed': 0, 'bytes': 0,
            'dry_run': dry_run, 'manifest_only': manifest_only, 'cancelled': False,
        }

    manifest = {
        'backup_date': datetime.now(timezone.utc).isoformat(),
        'bucket': bucket,
        'endpoint': storage.endpoint_url,
        'prefix': prefix,
        'total_objects': len(objects),
        'total_size_bytes': total_size,
        'files': objects,
    }
    manifest_path = None

    # Manifest пишется только при реальном бэкапе (не в dry-run)
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
        manifest_path = os.path.join(output_dir, 'manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        if progress is not None:
            progress.log(f'Manifest сохранён: {manifest_path}')

    downloaded = 0
    skipped = 0
    failed = 0
    downloaded_bytes = 0
    start_time = time.time()

    if progress is not None:
        progress.start('downloading', len(objects))

    if manifest_only:
        if progress is not None:
            progress.set(current=len(objects), processed=0, skipped=0, failed=0, bytes=0)
            progress.finish('done')
        return {
            'bucket': bucket, 'endpoint': storage.endpoint_url, 'prefix': prefix,
            'output_dir': output_dir, 'manifest_path': manifest_path,
            'total_objects': len(objects), 'total_size_bytes': total_size,
            'downloaded': 0, 'skipped': 0, 'failed': 0, 'bytes': 0,
            'dry_run': False, 'manifest_only': True, 'cancelled': False,
        }

    if dry_run:
        downloaded = len(objects)
        downloaded_bytes = total_size
        if progress is not None:
            progress.set(current=len(objects), processed=downloaded,
                         bytes=downloaded_bytes, skipped=0, failed=0)
            progress.finish('done')
        return {
            'bucket': bucket, 'endpoint': storage.endpoint_url, 'prefix': prefix,
            'output_dir': output_dir, 'total_objects': len(objects),
            'total_size_bytes': total_size, 'downloaded': downloaded,
            'skipped': skipped, 'failed': failed, 'bytes': downloaded_bytes,
            'dry_run': True, 'manifest_only': False, 'cancelled': False,
            'sample_keys': [o['key'] for o in objects[:20]],
        }

    for i, obj in enumerate(objects):
        if cancelled():
            if progress is not None:
                progress.log('Отменено пользователем.')
                progress.finish('cancelled')
            return {
                'bucket': bucket, 'endpoint': storage.endpoint_url, 'prefix': prefix,
                'output_dir': output_dir, 'manifest_path': manifest_path,
                'total_objects': len(objects), 'total_size_bytes': total_size,
                'downloaded': downloaded, 'skipped': skipped, 'failed': failed,
                'bytes': downloaded_bytes, 'dry_run': False, 'manifest_only': False,
                'cancelled': True,
            }

        key = obj['key']
        size = obj['size']
        local_path = os.path.join(output_dir, key)

        # Пропускаем если файл уже существует и размер совпадает
        if os.path.exists(local_path) and os.path.getsize(local_path) == size:
            skipped += 1
        else:
            try:
                local_dir = os.path.dirname(local_path)
                os.makedirs(local_dir, exist_ok=True)
                s3.download_file(bucket, key, local_path)
                actual_size = os.path.getsize(local_path)
                if actual_size != size and progress is not None:
                    progress.log(f'⚠ Размер не совпадает: {key} (ожидалось {size}, получено {actual_size})')
                downloaded += 1
                downloaded_bytes += size
            except Exception as e:
                failed += 1
                if progress is not None:
                    progress.log(f'✗ Ошибка: {key} — {e}')

        if progress is not None:
            elapsed = time.time() - start_time
            speed = downloaded_bytes / elapsed if elapsed > 0 else 0
            progress.set(current=i + 1, processed=downloaded, skipped=skipped,
                         failed=failed, bytes=downloaded_bytes, speed=speed)
            if (i + 1) % 50 == 0 or (i + 1) == len(objects):
                pct = (i + 1) / len(objects) * 100
                progress.log(
                    f'[{i + 1}/{len(objects)}] {pct:.0f}% | '
                    f'скачано: {downloaded}, пропущено: {skipped}, ошибок: {failed} | '
                    f'{fmt_size(downloaded_bytes)} @ {fmt_size(int(speed))}/c'
                )

    if progress is not None:
        progress.finish('done')
    return {
        'bucket': bucket, 'endpoint': storage.endpoint_url, 'prefix': prefix,
        'output_dir': output_dir, 'manifest_path': manifest_path,
        'total_objects': len(objects), 'total_size_bytes': total_size,
        'downloaded': downloaded, 'skipped': skipped, 'failed': failed,
        'bytes': downloaded_bytes, 'dry_run': False, 'manifest_only': False,
        'cancelled': False,
    }


def run_restore(*, manifest_path, overwrite=False, dry_run=False, prefix='',
                progress=None, cancel_event=None) -> dict:
    """
    Восстановление файлов из локального бэкапа (manifest.json) в бакет Cloud.ru.

    По умолчанию пропускает существующие в облаке файлы того же размера.
    dry_run=True — только проверка локальных файлов и подсчёт, без заливки.
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    backup_dir = os.path.dirname(os.path.abspath(manifest_path))
    all_files = manifest.get('files', [])
    if prefix:
        all_files = [obj for obj in all_files if obj['key'].startswith(prefix)]

    storage = get_storage()
    s3 = storage.s3_admin
    bucket = storage.bucket_name

    def cancelled():
        return cancel_event is not None and cancel_event.is_set()

    if progress is not None:
        progress.start('uploading', len(all_files))
        progress.log(f'Manifest: {manifest_path}')
        progress.log(f'Бакет: {bucket}')
        progress.log(f'Дата бэкапа: {manifest.get("backup_date", "неизвестна")}')
        progress.log(f'Папка бэкапа: {backup_dir}')
        progress.log(f'Файлов к восстановлению: {len(all_files)}')
        if dry_run:
            progress.log('DRY RUN — файлы НЕ заливаются')

    if not all_files:
        if progress is not None:
            progress.log('Нет файлов для восстановления.')
            progress.finish('done')
        return {
            'bucket': bucket, 'manifest_path': manifest_path,
            'total': 0, 'uploaded': 0, 'skipped': 0, 'failed': 0, 'bytes': 0,
            'dry_run': dry_run, 'overwrite': overwrite, 'cancelled': False,
        }

    uploaded = 0
    skipped = 0
    failed = 0
    uploaded_bytes = 0
    start_time = time.time()

    for i, obj in enumerate(all_files):
        if cancelled():
            if progress is not None:
                progress.log('Отменено пользователем.')
                progress.finish('cancelled')
            return {
                'bucket': bucket, 'manifest_path': manifest_path,
                'total': len(all_files), 'uploaded': uploaded, 'skipped': skipped,
                'failed': failed, 'bytes': uploaded_bytes,
                'dry_run': dry_run, 'overwrite': overwrite, 'cancelled': True,
            }

        key = obj['key']
        local_path = os.path.join(backup_dir, key)

        if not os.path.exists(local_path):
            failed += 1
            if progress is not None:
                progress.log(f'✗ Файл отсутствует локально: {key}')
        else:
            local_size = os.path.getsize(local_path)
            skip_file = False
            # Проверяем существование в облаке (только при реальной заливке)
            if not overwrite and not dry_run:
                try:
                    resp = s3.head_object(Bucket=bucket, Key=key)
                    cloud_size = resp['ContentLength']
                    if cloud_size == local_size:
                        skipped += 1
                        skip_file = True
                    elif progress is not None:
                        progress.log(
                            f'Размер отличается: {key} (локально {local_size}, облако {cloud_size}) — перезаливаю'
                        )
                except Exception:
                    pass  # файла нет в облаке — заливаем

            if not skip_file:
                if dry_run:
                    uploaded += 1
                    uploaded_bytes += local_size
                else:
                    try:
                        s3.upload_file(local_path, bucket, key)
                        uploaded += 1
                        uploaded_bytes += local_size
                    except Exception as e:
                        failed += 1
                        if progress is not None:
                            progress.log(f'✗ Ошибка заливки: {key} — {e}')

        if progress is not None:
            elapsed = time.time() - start_time
            speed = uploaded_bytes / elapsed if elapsed > 0 else 0
            progress.set(current=i + 1, processed=uploaded, skipped=skipped,
                         failed=failed, bytes=uploaded_bytes, speed=speed)
            if (i + 1) % 50 == 0 or (i + 1) == len(all_files):
                pct = (i + 1) / len(all_files) * 100
                progress.log(
                    f'[{i + 1}/{len(all_files)}] {pct:.0f}% | '
                    f'залито: {uploaded}, пропущено: {skipped}, ошибок: {failed} | '
                    f'{fmt_size(uploaded_bytes)} @ {fmt_size(int(speed))}/c'
                )

    if progress is not None:
        progress.finish('done')
    return {
        'bucket': bucket, 'manifest_path': manifest_path,
        'total': len(all_files), 'uploaded': uploaded, 'skipped': skipped,
        'failed': failed, 'bytes': uploaded_bytes,
        'dry_run': dry_run, 'overwrite': overwrite, 'cancelled': False,
    }


def list_backups() -> list:
    """Список локальных бэкапов (по manifest.json в backups/cloudru/*). Новые сверху."""
    entries = []
    if not os.path.isdir(BACKUP_ROOT):
        return entries
    for name in sorted(os.listdir(BACKUP_ROOT), reverse=True):
        if not FOLDER_RE.fullmatch(name):
            continue
        dir_path = os.path.join(BACKUP_ROOT, name)
        if not os.path.isdir(dir_path):
            continue
        manifest_path = os.path.join(dir_path, 'manifest.json')
        if not os.path.isfile(manifest_path):
            continue
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                m = json.load(f)
            entries.append({
                'folder': name,
                'path': dir_path,
                'backup_date': m.get('backup_date', ''),
                'bucket': m.get('bucket', ''),
                'prefix': m.get('prefix', ''),
                'total_objects': m.get('total_objects', len(m.get('files', []))),
                'total_size_bytes': m.get('total_size_bytes', 0),
            })
        except Exception:
            continue
    return entries


def load_manifest(folder: str) -> dict:
    """Полный manifest.json бэкапа. folder — имя подкаталога backups/cloudru (без путей)."""
    if not FOLDER_RE.fullmatch(folder):
        raise ValueError('Некорректное имя папки бэкапа')
    manifest_path = os.path.join(BACKUP_ROOT, folder, 'manifest.json')
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f'Манифест не найден: {manifest_path}')
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)
