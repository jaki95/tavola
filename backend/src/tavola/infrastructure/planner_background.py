from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


class InProcessPlannerBackgroundRunner:
    """Run one planner task at a time for the local demonstrator backend."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="planner")
        self._lock = Lock()
        self._busy = False

    def try_acquire(self) -> bool:
        with self._lock:
            if self._busy:
                return False
            self._busy = True
            return True

    def submit(self, task: Callable[[], None]) -> None:
        self._executor.submit(self._run_and_release, task)

    def release(self) -> None:
        with self._lock:
            self._busy = False

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _run_and_release(self, task: Callable[[], None]) -> None:
        try:
            task()
        finally:
            self.release()
