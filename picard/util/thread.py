# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018, 2020-2025 Laurent Monin
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020, 2022, 2026 Philipp Wolfer
# Copyright (C) 2022 Bob Swift
# Copyright (C) 2022 skelly37
# Copyright (C) 2024 Giorgio Fontanive
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections.abc import Callable
from functools import partial
import sys
import threading
import time
import traceback
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
)

from PyQt6.QtCore import (
    QCoreApplication,
    QEvent,
    QRunnable,
    QThreadPool,
    QTimer,
)

from picard import (
    log,
    tagger_instance,
)
from picard.debug_opts import DebugOpt


P = ParamSpec('P')
R = TypeVar('R')


class Callback(Protocol[R]):
    def __call__(self, result: R | None = None, error: BaseException | None = None) -> None: ...


class ProxyToMainEvent(QEvent):
    def __init__(self, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs):
        super().__init__(QEvent.Type.User)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.func(*self.args, **self.kwargs)


class TaskCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def decrement(self):
        with self.lock:
            self.count -= 1
            if self.count == 0:
                self.condition.notify_all()

    def increment(self):
        with self.lock:
            self.count += 1

    def wait_for_tasks(self):
        with self.lock:
            while self.count > 0:
                self.condition.wait()


class Runnable(QRunnable):
    def __init__(
        self,
        func: Callable[[], R],
        next_func: Callback[R],
        task_counter: TaskCounter | None = None,
        traceback: bool = True,
    ):
        super().__init__()
        self.func = func
        self.next_func = next_func
        self.task_counter = task_counter
        self.traceback = traceback

    def run(self):
        try:
            result = self.func()
        except BaseException:
            if self.traceback:
                log.error(traceback.format_exc())
            to_main(self.next_func, error=sys.exc_info()[1])
        else:
            to_main(self.next_func, result=result)
        finally:
            if self.task_counter:
                self.task_counter.decrement()


def run_task(
    func: Callable[[], R],
    next_func: Callback[R] | None = None,
    priority: int = 0,
    thread_pool: QThreadPool | None = None,
    task_counter: TaskCounter | None = None,
    traceback: bool = True,
) -> None:
    """Schedules func to be run on a separate thread

    Args:
        func: Function to run on a separate thread.
        next_func: Callback function to run after the thread has been completed.
          The callback will be run on the main thread.
        priority: Priority for the run queue's order of execution.
        thread_pool: Instance of QThreadPool to run this task.
        task_counter: Instance of TaskCounter to count the number of tasks currently running.
        traceback: If set to true the stack trace will be logged to the error log
          if an exception was raised.
    """

    def _no_operation(*args, **kwargs):
        return

    if not next_func:
        next_func = _no_operation

    if task_counter:
        task_counter.increment()

    if not thread_pool:
        thread_pool = tagger_instance().thread_pool
    thread_pool.start(Runnable(func, next_func, task_counter, traceback), priority)


def to_main(func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> None:
    QCoreApplication.postEvent(QCoreApplication.instance(), ProxyToMainEvent(func, *args, **kwargs))


def to_main_with_blocking(func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> None:
    """Executes a command as a user-defined event, and waits until the event has
    closed before returning.  Note that any new threads started while processing
    the event will not be considered when releasing the blocking of the function.

    Args:
        func: Function to run.
    """
    _task = ProxyToMainEvent(func, *args, **kwargs)
    QCoreApplication.postEvent(QCoreApplication.instance(), _task)

    while True:
        try:
            if not _task.isAccepted():
                break
        except Exception:
            break
        time.sleep(0.01)


_BATCH_TIME_BUDGET = 0.050  # 50ms per batch (~20 yields/sec)


def process_in_batches(
    items: list[R],
    process_func: Callable[[R], Any],
    label: str,
    time_budget: float | None = None,
    on_complete: Callable[[], Any] | None = None,
) -> None:
    """Process ``items`` with a time budget, yielding to the event loop between batches.

    Pops items from the front of ``items`` and calls ``process_func`` on each,
    for up to ``time_budget`` seconds, then reschedules itself via
    ``QTimer.singleShot(0, ...)`` so the event loop can run between batches. When
    ``items`` is empty, ``on_complete`` (if given) is invoked.

    This keeps a frontend responsive while applying a large batch of changes on
    the main thread. It relies only on the Qt event loop (``QTimer``), so it
    works under any ``QCoreApplication`` — the GUI as well as the headless
    application — not just the GUI. ``items`` is mutated (drained) in place.

    Args:
        items: List of items to process. Items are popped from the front.
        process_func: Callable that processes a single item.
        label: Label for debug timing output.
        time_budget: Max seconds per batch, must be positive. Defaults to 50 ms.
        on_complete: Optional callable invoked once all items are processed.

    Raises:
        ValueError: if ``time_budget`` is zero or negative (no item could ever
            be processed, so the batches would reschedule forever).
    """
    if time_budget is None:
        time_budget = _BATCH_TIME_BUDGET
    elif time_budget <= 0:
        raise ValueError(f"time_budget must be positive, got {time_budget!r}")
    deadline = time.perf_counter() + time_budget
    count = 0
    while items and time.perf_counter() < deadline:
        process_func(items.pop(0))
        count += 1
    log.debug_if(DebugOpt.TIMINGS, "%s: %d items, %d remaining", label, count, len(items))
    if items:
        QTimer.singleShot(0, partial(process_in_batches, items, process_func, label, time_budget, on_complete))
    elif on_complete:
        on_complete()
