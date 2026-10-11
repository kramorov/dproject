"""
Фоновые задачи бэкапа/восстановления (in-process).

Одна тяжёлая задача одновременно (backup/restore/dry-run).
Задача крутится в daemon-потоке, прогресс — в ProgressState,
отмена — threading.Event. Состояние живёт в памяти процесса
(при рестарте сервера задачи теряются — приемлемо для админ-инструмента).
"""
import threading
import time
import uuid

from storage_manager.backup_service import ProgressState

JOBS = {}
_LOCK = threading.RLock()
MAX_FINISHED_AGE = 6 * 3600  # 6 часов — храним завершённые задачи


class Job:
    def __init__(self, kind, params):
        self.id = uuid.uuid4().hex[:10]
        self.kind = kind
        self.params = params
        self.state = 'running'
        self.started_at = time.time()
        self.finished_at = None
        self.error = None
        self.result = None
        self.cancel_event = threading.Event()
        self.progress = ProgressState()

    def to_dict(self):
        d = {
            'id': self.id,
            'kind': self.kind,
            'params': self.params,
            'state': self.state,
            'error': self.error,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
        }
        d.update(self.progress.snapshot())
        if self.result:
            d['result'] = self.result
        return d


def _any_running():
    with _LOCK:
        return any(j.state == 'running' for j in JOBS.values())


def start_job(kind, params, target):
    """
    Запускает фоновую задачу. target(job) — функция, выполняющая работу
    (получает job.progress и job.cancel_event). Возвращает job_id.
    """
    with _LOCK:
        if _any_running():
            raise RuntimeError('Уже выполняется задача — дождитесь её завершения')
        job = Job(kind, params)
        JOBS[job.id] = job

    thread = threading.Thread(target=_run, args=(job, target), daemon=True)
    thread.start()
    return job.id


def _run(job, target):
    try:
        job.result = target(job)
        if job.result and job.result.get('cancelled'):
            job.state = 'cancelled'
        else:
            job.state = 'done'
    except Exception as e:  # noqa: BLE001 — граница потока
        job.state = 'failed'
        job.error = str(e)
        job.progress.log(f'✗ Ошибка: {e}')
    finally:
        job.finished_at = time.time()
        job.progress.finish(job.state)


def get_job(job_id):
    return JOBS.get(job_id)


def cancel_job(job_id) -> bool:
    job = JOBS.get(job_id)
    if not job or job.state != 'running':
        return False
    job.cancel_event.set()
    return True


def list_jobs(limit=20) -> list:
    now = time.time()
    with _LOCK:
        # Подчищаем старые завершённые задачи
        stale = [
            jid for jid, j in JOBS.items()
            if j.state != 'running' and j.finished_at and now - j.finished_at > MAX_FINISHED_AGE
        ]
        for jid in stale:
            del JOBS[jid]
        jobs = sorted(JOBS.values(), key=lambda j: -j.started_at)
        return [j.to_dict() for j in jobs[:limit]]
