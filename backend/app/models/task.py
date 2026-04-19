"""任务状态管理（内存单例）"""

import uuid
import threading
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

TASK_TTL = timedelta(hours=1)  # 完成/失败任务保留时长
MAX_TASKS = 500                 # 全局任务字典上限，防止内存无限增长


def _now():
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    message: str = ""
    result: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class TaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._task_lock = threading.Lock()
        return cls._instance

    def create_task(self, task_type: str, metadata: Optional[Dict] = None) -> str:
        self._cleanup_expired()
        task_id = str(uuid.uuid4())
        now = _now()
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        with self._task_lock:
            self._tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._task_lock:
            return self._tasks.get(task_id)

    def find_active_task(self, task_type: str, persona_id: int) -> Optional[Task]:
        """查找指定类型和 persona_id 的 PENDING/PROCESSING 任务（线程安全）。"""
        active_statuses = (TaskStatus.PENDING, TaskStatus.PROCESSING)
        with self._task_lock:
            for task in self._tasks.values():
                if (task.task_type == task_type
                        and task.status in active_statuses
                        and task.metadata.get('persona_id') == persona_id):
                    return task
        return None

    def update_task(self, task_id: str, **kwargs):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                task.updated_at = _now()
                for k, v in kwargs.items():
                    if v is not None and hasattr(task, k):
                        setattr(task, k, v)

    def complete_task(self, task_id: str, result: Dict):
        self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="任务完成",
            result=result
        )

    def fail_task(self, task_id: str, error: str):
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="任务失败",
            error=error
        )

    def _cleanup_expired(self):
        """清理已完成/失败超过 TTL 的任务；若仍超过 MAX_TASKS，按 updated_at 淘汰最旧的。"""
        cutoff = _now() - TASK_TTL
        with self._task_lock:
            # 1. 清理过期任务
            expired = [
                tid for tid, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                and t.updated_at < cutoff
            ]
            for tid in expired:
                del self._tasks[tid]

            # 2. 若总量仍超限，按 updated_at 淘汰最旧的已完成/失败任务
            if len(self._tasks) > MAX_TASKS:
                done = sorted(
                    [(tid, t.updated_at) for tid, t in self._tasks.items()
                     if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)],
                    key=lambda x: x[1]
                )
                for tid, _ in done[:len(self._tasks) - MAX_TASKS]:
                    del self._tasks[tid]
