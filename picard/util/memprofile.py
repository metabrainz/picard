# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""Generic, opt-in memory profiling helpers.

Every facility is gated behind ``DebugOpt.MEMORY`` and is a near-zero-overhead
no-op (a single boolean check) when that option is disabled, so calls may be
left in production code paths. Enable at runtime with ``--debug-opts=memory``.

The helpers rely only on the Python standard library (``tracemalloc``, ``gc``,
``sys``) and make no assumptions about Picard's own data structures.

Public helpers:
  - ``memory_snapshot(label)``: tracemalloc allocation diff around a block.
  - ``object_counts_baseline()`` + ``log_object_growth(label, baseline)``:
    report which live object types grew since a baseline (leak hunting).
  - ``log_object_counts(label)``: absolute snapshot of live object types.
  - ``deep_getsizeof(obj)`` + ``format_bytes(n)``: retained-size estimate.
  - ``MemorySampler(label, track_objects=...)``: background RSS/traced curve
    over time, optionally with periodic per-type growth.
  - ``should_run(key, min_interval)``: throttle for summaries in tight loops.
"""

from collections import Counter
from collections.abc import Generator
from contextlib import contextmanager
import gc
import sys
import threading
import time
import tracemalloc

from picard import log
from picard.debug_opts import DebugOpt
from picard.util import bytes2human


# Number of frames tracemalloc keeps per allocation. More frames give better
# attribution at the cost of memory/CPU while tracing.
_TRACEMALLOC_FRAMES = 25

# Default number of top entries to log in snapshot diffs / object counts.
_DEFAULT_TOP = 10

# Container types whose elements are walked by deep_getsizeof().
_CONTAINER_TYPES = (list, tuple, set, frozenset)


def _type_counts() -> 'Counter[str]':
    """Count live objects by type name. Shared by the count/growth helpers."""
    return Counter(type(obj).__name__ for obj in gc.get_objects())


def _ensure_tracing() -> bool:
    """Start ``tracemalloc`` if the MEMORY option is enabled and not already running.

    Returns True if tracing is active after the call, False otherwise. Safe to
    call repeatedly; only starts tracing once.
    """
    if not DebugOpt.MEMORY.enabled:
        return False
    if not tracemalloc.is_tracing():
        tracemalloc.start(_TRACEMALLOC_FRAMES)
        log.debug("memprofile: tracemalloc started with %d frames", _TRACEMALLOC_FRAMES)
    return True


def format_bytes(num: float) -> str:
    """Human-readable binary byte size for logs (e.g. ``1.5 KiB``).

    Wraps :func:`picard.util.bytes2human.binary` with l10n disabled so log
    output stays stable and locale-independent. Provided so profiling call
    sites have a single formatting entry point without importing bytes2human.
    """
    return bytes2human.binary(int(num), scale=1, l10n=False)


# Per-key timestamps for should_run(), used to rate-limit summaries emitted
# from tight loops (e.g. once per loaded album during a bulk load).
_last_run: dict[str, float] = {}


def should_run(key: str, min_interval: float) -> bool:
    """Return True at most once per ``min_interval`` seconds for a given key.

    A lightweight, generic throttle so a summary called from a hot loop (per
    album, per file, ...) only emits occasionally instead of on every
    iteration. Always returns False when the MEMORY option is disabled, so
    callers can guard expensive summary work with a single call.

    Args:
        key: Identifies the throttled call site (independent keys are tracked
            separately).
        min_interval: Minimum seconds between two True results for this key.
    """
    if not DebugOpt.MEMORY.enabled:
        return False
    now = time.perf_counter()
    last = _last_run.get(key)
    if last is not None and now - last < min_interval:
        return False
    _last_run[key] = now
    return True


def reset_throttles() -> None:
    """Forget all should_run() timestamps (mainly for tests)."""
    _last_run.clear()


@contextmanager
def memory_snapshot(label: str, *, n: int | None = None, top: int = _DEFAULT_TOP) -> Generator[None]:
    """Diff traced memory allocations around a block and log the top allocators.

    When ``DebugOpt.MEMORY`` is disabled this is a near-zero-overhead no-op.

    Args:
        label: Human-readable name for the profiled block.
        n: Optional workload size (e.g. number of objects) logged alongside the
            result so growth can be compared across runs.
        top: Number of top allocating source lines to log.
    """
    if not _ensure_tracing():
        yield
        return

    snapshot_before = tracemalloc.take_snapshot()
    current_before, _peak_before = tracemalloc.get_traced_memory()
    t0 = time.perf_counter_ns()

    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
        current_after, peak_after = tracemalloc.get_traced_memory()
        snapshot_after = tracemalloc.take_snapshot()

        net = current_after - current_before
        suffix = f" (n={n})" if n is not None else ""
        log.debug(
            "memprofile[%s]%s: net=%s peak=%s elapsed=%.1f ms",
            label,
            suffix,
            format_bytes(net),
            format_bytes(peak_after),
            elapsed_ms,
        )

        stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        log.debug("memprofile[%s]: top %d allocating lines:", label, top)
        for stat in stats[:top]:
            log.debug("  %s", stat)


def log_object_counts(label: str, *, top: int = _DEFAULT_TOP, collect: bool = True) -> None:
    """Log the most common live object types, for retention / leak detection.

    Call after an operation (and across repeated operations) to see which types
    keep growing. No-op when the option is disabled.

    Args:
        label: Context label for the log line.
        top: Number of most common types to log.
        collect: Run ``gc.collect()`` first so only genuinely retained objects
            are counted.
    """
    if not DebugOpt.MEMORY.enabled:
        return
    if collect:
        gc.collect()
    counts = _type_counts()
    log.debug("memprofile[%s]: top %d live object types:", label, top)
    for name, count in counts.most_common(top):
        log.debug("  %6d  %s", count, name)


def object_counts_baseline() -> 'Counter[str] | None':
    """Return a snapshot of live object-type counts, or None when disabled.

    Pass the result to :func:`log_object_growth` after an operation to log only
    the types that grew, which is far more useful for leak-hunting than two
    separate absolute dumps.
    """
    if not DebugOpt.MEMORY.enabled:
        return None
    gc.collect()
    return _type_counts()


def log_object_growth(
    label: str,
    baseline: 'Counter[str] | None',
    *,
    top: int = _DEFAULT_TOP,
    threshold: int = 1,
) -> None:
    """Log the object types that grew the most since ``baseline``.

    ``baseline`` comes from :func:`object_counts_baseline`. Only types whose
    net growth is at least ``threshold`` are reported, newest-heaviest first,
    so the output is a single concise line pointing at what accumulated.
    No-op when disabled or when ``baseline`` is None.
    """
    if not DebugOpt.MEMORY.enabled or baseline is None:
        return
    gc.collect()
    counts = _type_counts()
    deltas = {
        name: counts[name] - baseline.get(name, 0)
        for name in counts
        if counts[name] - baseline.get(name, 0) >= threshold
    }
    if not deltas:
        log.debug("memprofile[%s]: no net object growth", label)
        return
    grown = sorted(deltas.items(), key=lambda kv: kv[1], reverse=True)[:top]
    summary = ', '.join(f"{name} +{delta}" for name, delta in grown)
    log.debug("memprofile[%s]: object growth: %s", label, summary)


def deep_getsizeof(obj: object, _seen: set[int] | None = None) -> int:
    """Recursively estimate the retained size of an object, in bytes.

    Follows dict/list/tuple/set/frozenset containers and ``__dict__`` /
    ``__slots__`` attributes, deduplicating by id so shared references are
    counted once. This is an estimate (it cannot see C-level buffers it does not
    know about) but is useful for comparing the relative cost of data structures
    at scale.

    This function runs regardless of the MEMORY option so it can be unit-tested
    and reused; call it from a gated call site.
    """
    if _seen is None:
        _seen = set()
    obj_id = id(obj)
    if obj_id in _seen:
        return 0
    _seen.add(obj_id)

    size = sys.getsizeof(obj)

    # Bytes-like and str already account for their full payload in getsizeof().
    if isinstance(obj, (str, bytes, bytearray)):
        return size

    if isinstance(obj, dict):
        for key, value in obj.items():
            size += deep_getsizeof(key, _seen)
            size += deep_getsizeof(value, _seen)
    elif isinstance(obj, _CONTAINER_TYPES):
        for item in obj:
            size += deep_getsizeof(item, _seen)

    obj_dict = getattr(obj, '__dict__', None)
    if obj_dict:
        size += deep_getsizeof(obj_dict, _seen)

    slots = getattr(obj, '__slots__', None)
    if slots:
        if isinstance(slots, str):
            slots = (slots,)
        for slot in slots:
            try:
                value = getattr(obj, slot)
            except AttributeError:
                continue
            size += deep_getsizeof(value, _seen)

    return size


class MemorySampler:
    """Background thread sampling process memory over time.

    Produces a memory-over-time curve without any external profiler. Uses
    ``tracemalloc`` for Python-traced memory and, when available, ``psutil`` or
    :func:`resource.getrusage` for process RSS. Does nothing when the MEMORY
    option is disabled.

    When ``track_objects`` is True, the sampler also periodically logs the
    object types whose live instance count grew the most since the previous
    object scan. This turns the sampler into a leak locator for long
    operations: a type that climbs monotonically across scans is the
    accumulating one.

    To keep the log readable and avoid distorting what it measures, the sampler
    is deliberately quiet:
      - ``interval`` defaults to 2 s (the RSS/traced curve line cadence),
      - object scans run only every ``object_every`` samples (default 5, so
        ~every 10 s), because ``gc.get_objects()`` is expensive,
      - growth is only logged for types exceeding ``growth_threshold``.

    Usable as a context manager::

        with MemorySampler(label="bulk save", track_objects=True):
            do_long_operation()
    """

    def __init__(
        self,
        interval: float = 2.0,
        label: str = "sampler",
        *,
        track_objects: bool = False,
        top_growth: int = 8,
        object_every: int = 5,
        growth_threshold: int = 50,
    ):
        self.interval = interval
        self.label = label
        self.track_objects = track_objects
        self.top_growth = top_growth
        self.object_every = max(1, object_every)
        self.growth_threshold = growth_threshold
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._prev_counts: dict[str, int] | None = None
        self._sample_index = 0

    @staticmethod
    def _rss_bytes() -> int | None:
        """Best-effort resident set size in bytes, or None if unavailable."""
        try:
            import psutil  # ty: ignore[unresolved-import]  # optional dependency

            return psutil.Process().memory_info().rss
        except ImportError:
            pass
        try:
            import resource

            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # Linux reports KiB, macOS reports bytes.
            if sys.platform == 'darwin':
                return usage
            return usage * 1024
        except (ImportError, ValueError):
            return None

    def _log_object_growth(self) -> None:
        """Log the object types that grew most since the previous object scan.

        Only types whose growth exceeds ``growth_threshold`` are reported, so
        transient churn does not flood the log; a monotonic climber will keep
        appearing across scans.
        """
        counts = _type_counts()
        if self._prev_counts is not None:
            deltas = {
                name: counts[name] - self._prev_counts.get(name, 0)
                for name in counts
                if counts[name] - self._prev_counts.get(name, 0) >= self.growth_threshold
            }
            if deltas:
                top = sorted(deltas.items(), key=lambda kv: kv[1], reverse=True)[: self.top_growth]
                summary = ', '.join(f"{name} +{delta}" for name, delta in top)
                log.debug("memprofile[%s]: object growth: %s", self.label, summary)
        self._prev_counts = counts

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            traced = ""
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                traced = f"traced={format_bytes(current)} peak={format_bytes(peak)}"
            rss = self._rss_bytes()
            rss_str = format_bytes(rss) if rss is not None else "n/a"
            log.debug("memprofile[%s]: rss=%s %s", self.label, rss_str, traced)
            if self.track_objects and self._sample_index % self.object_every == 0:
                self._log_object_growth()
            self._sample_index += 1

    def start(self) -> None:
        if not DebugOpt.MEMORY.enabled:
            return
        _ensure_tracing()
        if self._thread is not None:
            return
        self._prev_counts = None
        self._sample_index = 0
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="MemorySampler", daemon=True)
        self._thread.start()
        log.debug(
            "memprofile[%s]: sampler started (interval=%.2fs, track_objects=%s)",
            self.label,
            self.interval,
            self.track_objects,
        )

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=self.interval * 2)
        self._thread = None
        log.debug("memprofile[%s]: sampler stopped", self.label)

    def __enter__(self) -> 'MemorySampler':
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()
