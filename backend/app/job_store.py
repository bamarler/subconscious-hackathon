import threading
import time
import uuid
from dataclasses import dataclass, field

from .models import PipelineEvent

JOB_TTL_SECONDS = 30 * 60  # 30 minutes


@dataclass
class Job:
    id: str
    status: str  # pending | running | completed | error
    created_at: float
    events: list[PipelineEvent] = field(default_factory=list)
    current_step: int = 0
    error: str | None = None
    _notify: threading.Event = field(default_factory=threading.Event)

    def append_event(self, event: PipelineEvent) -> None:
        self.events.append(event)
        self.current_step = event.step
        if event.status == "error":
            self.status = "error"
            self.error = event.error
        if event.step == 3 and event.status == "completed":
            self.status = "completed"
        # Pulse: wake any SSE listeners waiting for new events
        self._notify.set()
        self._notify.clear()


_store: dict[str, Job] = {}
_lock = threading.Lock()


def create_job() -> Job:
    _cleanup_old_jobs()
    job_id = uuid.uuid4().hex[:12]
    job = Job(id=job_id, status="pending", created_at=time.time())
    with _lock:
        _store[job_id] = job
    return job


def get_job(job_id: str) -> Job | None:
    with _lock:
        return _store.get(job_id)


def _cleanup_old_jobs() -> None:
    now = time.time()
    with _lock:
        expired = [k for k, v in _store.items() if now - v.created_at > JOB_TTL_SECONDS]
        for k in expired:
            del _store[k]
