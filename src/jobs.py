"""Single-process background jobs. Run one server worker; never share project writes."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4
from copy import deepcopy

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="autonovel")
_mutex = Lock()
_jobs = {}
_active = {}
_locks = {}
MAX_JOBS = 200


class ProjectBusyError(ValueError):
    pass


def _lock_for(project_id):
    with _mutex:
        return _locks.setdefault(project_id, Lock())


@contextmanager
def project_guard(project_id):
    lock = _lock_for(project_id)
    if not lock.acquire(blocking=False):
        raise ProjectBusyError("An operation is already running for this project")
    try:
        yield
    finally:
        lock.release()


def get_job(job_id):
    with _mutex:
        job = _jobs.get(job_id)
        return deepcopy(job) if job else None


def submit_job(project_id, operation, function, idempotency_key=None):
    """Return an existing in-flight operation; reject competing project operations."""
    if idempotency_key and (len(idempotency_key) > 128 or not idempotency_key.isascii()):
        raise ValueError("Invalid idempotency key")
    with _mutex:
        if idempotency_key:
            for previous in _jobs.values():
                if previous.get('idempotency_key') == idempotency_key and previous['project_id'] == project_id:
                    if previous['operation'] != operation:
                        raise ValueError("Idempotency key already used for a different operation")
                    return deepcopy(previous)
        existing = _active.get(project_id)
        if existing:
            job = _jobs[existing]
            if job['operation'] == operation:
                return deepcopy(job)
            raise ProjectBusyError("Another operation is running for this project")
        lock = _locks.setdefault(project_id, Lock())
        if not lock.acquire(blocking=False):
            raise ProjectBusyError("Project is being edited")
        job_id = uuid4().hex
        job = dict(id=job_id, project_id=project_id, operation=operation,
                   status="queued", progress="Waiting", result=None, error=None, idempotency_key=idempotency_key,
                   created_at=datetime.now(timezone.utc).isoformat())
        # Bound memory, retaining running tasks.
        for old_id in list(_jobs):
            if len(_jobs) < MAX_JOBS:
                break
            if _jobs[old_id]['status'] in ('succeeded', 'failed'):
                del _jobs[old_id]
        _jobs[job_id] = job
        _active[project_id] = job_id
        initial = deepcopy(job)

    def execute():
        try:
            with _mutex:
                job.update(status="running", progress="Running")
            result = function()
            if isinstance(result, dict) and (result.get('error') or result.get('returncode', 0) != 0):
                raise RuntimeError(result.get('error') or 'Operation failed')
            with _mutex:
                job.update(status="succeeded", progress="Completed", result=result)
        except Exception as exc:
            # Public HTTP errors are authored by our API; provider payloads are not exposed.
            from fastapi import HTTPException
            import logging
            logging.getLogger(__name__).warning("Job %s failed (%s)", job_id, type(exc).__name__)
            message = exc.detail if isinstance(exc, HTTPException) else "Operation failed; inspect server diagnostics and project status"
            with _mutex:
                job.update(status="failed", progress="Failed", error=message)
        finally:
            with _mutex:
                _active.pop(project_id, None)
            lock.release()
    try:
        _executor.submit(execute)
    except Exception:
        with _mutex:
            _active.pop(project_id, None)
            _jobs.pop(job_id, None)
        lock.release()
        raise
    return initial
