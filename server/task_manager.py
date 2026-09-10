import json
import os
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests

from utils.logger import logger

INTERRUPTED_MSG = "进程中断，任务未完成"


class AvatarTask:
    def __init__(self, task_id, model_type, avatar_id, params, notify_url=None):
        self.task_id = task_id
        self.model_type = model_type
        self.avatar_id = avatar_id
        self.params = params or {}
        self.status = "pending"  # pending, running, completed, failed
        self.progress = 0
        self.error_msg = ""
        self.notify_url = notify_url
        self.start_time = time.time()
        self.end_time = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "model_type": self.model_type,
            "avatar_id": self.avatar_id,
            "status": self.status,
            "progress": self.progress,
            "error_msg": self.error_msg,
            "notify_url": self.notify_url,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": (self.end_time or time.time()) - self.start_time
        }


class TaskManager:
    def __init__(self, max_workers=1):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}
        self.lock = threading.Lock()
        self._store_path = None
        self._store_lock = threading.Lock()

    def attach_store(self, db_path: str):
        self._store_path = db_path
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._fail_interrupted()
        self._load()

    def add_task(self, model_type, avatar_id, params, task_id=None, notify_url=None, run=True):
        if task_id is None:
            task_id = str(uuid.uuid4())

        task = AvatarTask(task_id, model_type, avatar_id, params, notify_url)
        with self.lock:
            self.tasks[task_id] = task
        self._persist(task)

        self._notify(task)
        if run:
            self.executor.submit(self._run_task, task_id)
        return task_id

    def get_task(self, task_id):
        with self.lock:
            return self.tasks.get(task_id)

    def delete_task(self, task_id):
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False, "Task not found"

            if task.status != "pending":
                return False, f"Task is in {task.status} state, cannot delete"

            del self.tasks[task_id]
        self._delete_row(task_id)
        return True, "Task deleted"

    def list_tasks(self):
        with self.lock:
            return sorted([task.to_dict() for task in self.tasks.values()], key=lambda x: x['start_time'], reverse=True)

    def persist_task(self, task):
        self._persist(task)

    def _run_task(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return

        task.status = "running"
        self._persist(task)
        self._notify(task)
        logger.info(f"Starting task {task_id} for model {task.model_type}, avatar {task.avatar_id}")

        try:
            def progress_callback(p):
                task.progress = p
                self._persist(task)

            if task.model_type == "musetalk":
                from avatars.musetalk.genavatar import generate_avatar
                generate_avatar(
                    video_path=task.params['video_path'],
                    avatar_id=task.avatar_id,
                    save_path=task.params.get('save_path', './data/avatars'),
                    bbox_shift=task.params.get('bbox_shift', 0),
                    extra_margin=task.params.get('extra_margin', 10),
                    parsing_mode=task.params.get('parsing_mode', 'jaw'),
                    version=task.params.get('version', 'v15'),
                    progress_callback=progress_callback
                )
            elif task.model_type == "wav2lip":
                from avatars.wav2lip.genavatar import generate_avatar
                generate_avatar(
                    video_path=task.params['video_path'],
                    avatar_id=task.avatar_id,
                    save_path=task.params.get('save_path', './data/avatars'),
                    img_size=task.params.get('img_size', 96),
                    pads=task.params.get('pads', [0, 10, 0, 0]),
                    nosmooth=task.params.get('nosmooth', False),
                    face_det_batch_size=task.params.get('face_det_batch_size', 16),
                    progress_callback=progress_callback
                )
            else:
                raise ValueError(f"Unsupported model type: {task.model_type}")

            task.status = "completed"
            task.progress = 100
            self._persist(task)
            self._notify(task)
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            task.status = "failed"
            task.error_msg = str(e)
            self._persist(task)
            self._notify(task)
            logger.error(f"Task {task_id} failed: {e}")
        finally:
            task.end_time = time.time()
            self._persist(task)
            on_status = getattr(self, "on_status", None)
            if on_status:
                try:
                    on_status(task)
                except Exception as e:
                    logger.error(f"Task {task_id} status hook failed: {e}")

    def _notify(self, task):
        if not task.notify_url:
            return

        try:
            payload = task.to_dict()
            logger.info(f"Sending notification for task {task.task_id} to {task.notify_url}")
            requests.post(task.notify_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send notification for task {task.task_id}: {e}")

    def _conn(self):
        conn = sqlite3.connect(self._store_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _fail_interrupted(self):
        if not self._store_path:
            return
        now = time.time()
        with self._store_lock:
            conn = self._conn()
            try:
                conn.execute(
                    """
                    UPDATE avatar_tasks
                    SET status = 'failed', error_msg = ?, end_time = ?
                    WHERE status IN ('pending', 'running')
                    """,
                    (INTERRUPTED_MSG, now),
                )
                conn.commit()
            finally:
                conn.close()

    def _load(self):
        loaded = {}
        if not self._store_path:
            with self.lock:
                self.tasks = {}
            return
        with self._store_lock:
            conn = self._conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM avatar_tasks ORDER BY start_time DESC"
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []
            finally:
                conn.close()
        for row in rows:
            try:
                params = json.loads(row["params"] or "{}")
            except Exception:
                params = {}
            task = AvatarTask(
                row["task_id"],
                row["model_type"],
                row["avatar_id"],
                params,
                row["notify_url"],
            )
            task.status = row["status"]
            task.progress = row["progress"] or 0
            task.error_msg = row["error_msg"] or ""
            task.start_time = row["start_time"]
            task.end_time = row["end_time"]
            loaded[task.task_id] = task
        with self.lock:
            self.tasks = loaded

    def _persist(self, task):
        if not self._store_path:
            return
        with self._store_lock:
            conn = self._conn()
            try:
                conn.execute(
                    """
                    INSERT INTO avatar_tasks (
                        task_id, model_type, avatar_id, params, status, progress,
                        error_msg, notify_url, start_time, end_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        model_type = excluded.model_type,
                        avatar_id = excluded.avatar_id,
                        params = excluded.params,
                        status = excluded.status,
                        progress = excluded.progress,
                        error_msg = excluded.error_msg,
                        notify_url = excluded.notify_url,
                        start_time = excluded.start_time,
                        end_time = excluded.end_time
                    """,
                    (
                        task.task_id,
                        task.model_type,
                        task.avatar_id,
                        json.dumps(task.params or {}),
                        task.status,
                        int(task.progress or 0),
                        task.error_msg or "",
                        task.notify_url,
                        task.start_time,
                        task.end_time,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def _delete_row(self, task_id):
        if not self._store_path:
            return
        with self._store_lock:
            conn = self._conn()
            try:
                conn.execute("DELETE FROM avatar_tasks WHERE task_id = ?", (task_id,))
                conn.commit()
            finally:
                conn.close()


task_manager = TaskManager()
