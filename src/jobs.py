"""Durable single-worker jobs with explicit cancellation and no automatic paid retry."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock
from uuid import uuid4
import json
import os
from src import task_store

_executor=ThreadPoolExecutor(max_workers=4, thread_name_prefix='autonovel')
_mutex=Lock();_locks={}
_current=ContextVar('autonovel_job',default=None)
MAX_JOBS=200  # compatibility; durable idempotency records are never evicted


class ProjectBusyError(ValueError): pass
class JobCancelled(ValueError): pass


def _lock_for(project_id):
    with _mutex: return _locks.setdefault(project_id,Lock())


@contextmanager
def project_guard(project_id):
    lock=_lock_for(project_id)
    if not lock.acquire(blocking=False):raise ProjectBusyError('An operation is already running for this project')
    try:yield
    finally:lock.release()


def current_job(): return _current.get() or os.environ.get('AUTONOVEL_TASK_ID')


def child_context():
    job=current_job()
    return {'AUTONOVEL_TASK_ID':job,'AUTONOVEL_TASK_DB':str(task_store.database_path().resolve())} if job else {}


def get_job(job_id): return task_store.read(job_id)


def check_cancelled():
    job_id=current_job()
    job=get_job(job_id) if job_id else None
    if job and job['status'] in {'cancel_requested','cancelled'}:raise JobCancelled('Cancellation requested; remote outcome may be unknown')


def cancel_job(job_id):
    job=get_job(job_id)
    if not job:return None
    if job['status'] in {'queued','running'}:
        job=task_store.update(job_id,status='cancel_requested',cancellation='requested; an already submitted provider call may still be billed')
        task_store.event(job_id,'cancel_requested')
    return job


def list_jobs(project_id=None):
    with task_store.connection() as db:
        task_store.recover(db)
        rows=db.execute('SELECT payload FROM tasks '+('WHERE project=? ' if project_id else '')+'ORDER BY rowid DESC LIMIT 200',(project_id,) if project_id else ())
        return [json.loads(row[0]) for row in rows]


def report_progress(step, progress=None):
    job=current_job()
    if job:
        task_store.update(job,step=step,progress=progress)
        task_store.event(job,'progress',{'step':step,'progress':progress})


def submit_job(project_id, operation, function, idempotency_key=None, serialize=True):
    if idempotency_key and (len(idempotency_key)>128 or not idempotency_key.isascii()):raise ValueError('Invalid idempotency key')
    with task_store.connection() as db:
        db.execute('BEGIN IMMEDIATE');task_store.recover(db)
        if idempotency_key:
            row=db.execute('SELECT * FROM tasks WHERE project=? AND idem=?',(project_id,idempotency_key)).fetchone()
            if row:
                if row['operation']!=operation:raise ValueError('Idempotency key already used for a different operation')
                return json.loads(row['payload'])
        row=db.execute("SELECT * FROM tasks WHERE project=? AND state IN ('queued','running','cancel_requested')",(project_id,)).fetchone()
        if row:
            if row['operation']==operation:return json.loads(row['payload'])
            raise ProjectBusyError('Another task is active for this project')
        job={'id':uuid4().hex,'project_id':project_id,'operation':operation,'idempotency_key':idempotency_key,'status':'queued','created_at':task_store.now(),'started_at':None,'finished_at':None,'result':None,'error':None}
        db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?)',(job['id'],project_id,operation,idempotency_key,'queued',os.getpid(),json.dumps(job)))
    def run():
        token=_current.set(job['id'])
        try:
            check_cancelled();task_store.update(job['id'],status='running',started_at=task_store.now())
            task_store.event(job['id'],'started')
            if serialize:
                with project_guard(project_id):result=function()
            else:result=function()
            check_cancelled()
            state='failed' if isinstance(result,dict) and result.get('returncode',0)!=0 else 'succeeded'
            task_store.update(job['id'],status=state,result=result,finished_at=task_store.now())
            task_store.event(job['id'],state)
        except JobCancelled:
            task_store.update(job['id'],status='cancelled',finished_at=task_store.now(),error='Stopped locally; verify provider outcome before retry')
            task_store.event(job['id'],'cancelled')
        except Exception:
            # Exception bodies may include URLs, keys or full provider content.
            task_store.update(job['id'],status='failed',finished_at=task_store.now(),error='Operation failed; inspect the structured result and local diagnostics')
            task_store.event(job['id'],'failed')
        finally:_current.reset(token)
    _executor.submit(run)
    return job
