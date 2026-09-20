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


import sys
import tracemalloc

from test.picardtestcase import PicardTestCase

from picard.debug_opts import DebugOpt
from picard.util import memprofile


class MemProfileGateTest(PicardTestCase):
    """Verify the DebugOpt.MEMORY gating of the logging entry points."""

    def setUp(self):
        super().setUp()
        # Ensure a clean, isolated registry for each test.
        self._saved_registry = DebugOpt.get_registry()
        DebugOpt.set_registry(set())

    def tearDown(self):
        DebugOpt.set_registry(self._saved_registry)
        super().tearDown()

    def test_memory_snapshot_yields_when_disabled(self):
        # No exception, block runs, nothing raised even though tracing is off.
        ran = False
        with memprofile.memory_snapshot("disabled"):
            ran = True
        self.assertTrue(ran)

    def test_log_object_counts_noop_when_disabled(self):
        # Must not raise and must not run gc / iterate objects meaningfully.
        memprofile.log_object_counts("disabled")

    def test_object_counts_baseline_none_when_disabled(self):
        self.assertIsNone(memprofile.object_counts_baseline())

    def test_object_counts_baseline_returns_counter_when_enabled(self):
        DebugOpt.MEMORY.enabled = True
        baseline = memprofile.object_counts_baseline()
        self.assertIsNotNone(baseline)
        assert baseline is not None  # narrow for type checkers
        self.assertIn('dict', baseline)

    def test_log_object_growth_noop_when_disabled(self):
        # Even with a baseline, disabled means no work / no raise.
        memprofile.log_object_growth("disabled", None)

    def test_log_object_growth_reports_new_objects_when_enabled(self):
        DebugOpt.MEMORY.enabled = True
        baseline = memprofile.object_counts_baseline()
        # Allocate a distinct, retained type so growth is detectable.

        class _GrowthMarker:
            pass

        retained = [_GrowthMarker() for _ in range(20)]
        # Should not raise; the marker type grew by 20 since the baseline.
        memprofile.log_object_growth("grew", baseline, threshold=1)
        self.assertEqual(len(retained), 20)  # keep the list alive until here

    def test_memory_snapshot_starts_tracing_when_enabled(self):
        DebugOpt.MEMORY.enabled = True
        was_tracing = tracemalloc.is_tracing()
        try:
            with memprofile.memory_snapshot("enabled", n=3):
                _ = [object() for _ in range(100)]
            self.assertTrue(tracemalloc.is_tracing())
        finally:
            if not was_tracing and tracemalloc.is_tracing():
                tracemalloc.stop()


class FormatBytesTest(PicardTestCase):
    def test_delegates_to_bytes2human_binary(self):
        # Thin wrapper over bytes2human.binary (l10n disabled); spot-check a
        # few values incl. a negative delta.
        self.assertEqual(memprofile.format_bytes(0), "0 B")
        self.assertEqual(memprofile.format_bytes(1024), "1 KiB")
        self.assertEqual(memprofile.format_bytes(1536), "1.5 KiB")
        self.assertEqual(memprofile.format_bytes(-1024), "-1 KiB")


class ShouldRunThrottleTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self._saved_registry = DebugOpt.get_registry()
        DebugOpt.set_registry(set())
        memprofile.reset_throttles()

    def tearDown(self):
        memprofile.reset_throttles()
        DebugOpt.set_registry(self._saved_registry)
        super().tearDown()

    def test_returns_false_when_disabled(self):
        self.assertFalse(memprofile.should_run("k", 0.0))

    def test_first_call_true_then_throttled(self):
        DebugOpt.MEMORY.enabled = True
        # First call passes; an immediate second call for the same key is
        # throttled by the (large) interval.
        self.assertTrue(memprofile.should_run("k", 1000.0))
        self.assertFalse(memprofile.should_run("k", 1000.0))

    def test_zero_interval_always_runs(self):
        DebugOpt.MEMORY.enabled = True
        self.assertTrue(memprofile.should_run("k", 0.0))
        self.assertTrue(memprofile.should_run("k", 0.0))

    def test_independent_keys(self):
        DebugOpt.MEMORY.enabled = True
        self.assertTrue(memprofile.should_run("a", 1000.0))
        # Different key is tracked separately, so it still passes.
        self.assertTrue(memprofile.should_run("b", 1000.0))

    def test_reset_throttles_clears_state(self):
        DebugOpt.MEMORY.enabled = True
        self.assertTrue(memprofile.should_run("k", 1000.0))
        self.assertFalse(memprofile.should_run("k", 1000.0))
        memprofile.reset_throttles()
        # After reset, the key passes again.
        self.assertTrue(memprofile.should_run("k", 1000.0))


class DeepGetSizeofTest(PicardTestCase):
    """deep_getsizeof is pure and runs regardless of the MEMORY option."""

    def test_scalar(self):
        self.assertEqual(memprofile.deep_getsizeof(123), sys.getsizeof(123))

    def test_str_not_double_counted(self):
        s = "hello world"
        self.assertEqual(memprofile.deep_getsizeof(s), sys.getsizeof(s))

    def test_dict_includes_keys_and_values(self):
        d = {'a': "x", 'b': "y"}
        size = memprofile.deep_getsizeof(d)
        self.assertGreater(size, sys.getsizeof(d))

    def test_nested_container(self):
        nested = [[1, 2, 3], {'k': [4, 5]}, (6, 7)]
        size = memprofile.deep_getsizeof(nested)
        self.assertGreater(size, sys.getsizeof(nested))

    def test_shared_reference_counted_once(self):
        shared = ['x' * 1000]
        # Two references to the same list must not be double-counted.
        one = memprofile.deep_getsizeof([shared])
        two = memprofile.deep_getsizeof([shared, shared])
        # The second container adds only one extra slot, not another full copy.
        self.assertLess(two - one, memprofile.deep_getsizeof(shared))

    def test_cycle_is_handled(self):
        a: dict = {}
        a['self'] = a
        # Must terminate and not recurse infinitely.
        self.assertGreater(memprofile.deep_getsizeof(a), 0)

    def test_object_with_dict(self):
        class Thing:
            def __init__(self):
                self.payload = "z" * 500

        size = memprofile.deep_getsizeof(Thing())
        self.assertGreater(size, 500)

    def test_object_with_slots(self):
        class Slotted:
            __slots__ = ('payload',)

            def __init__(self):
                self.payload = "z" * 500

        size = memprofile.deep_getsizeof(Slotted())
        self.assertGreater(size, 500)

    def test_object_with_unset_slot(self):
        class Slotted:
            __slots__ = ('a', 'b')

            def __init__(self):
                self.a = 1
                # b intentionally left unset

        # Must not raise on the unset slot.
        self.assertGreater(memprofile.deep_getsizeof(Slotted()), 0)


class MemorySamplerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self._saved_registry = DebugOpt.get_registry()
        DebugOpt.set_registry(set())

    def tearDown(self):
        DebugOpt.set_registry(self._saved_registry)
        super().tearDown()

    def test_start_is_noop_when_disabled(self):
        sampler = memprofile.MemorySampler(interval=0.01)
        sampler.start()
        self.assertIsNone(sampler._thread)
        # stop() must be safe even if never started.
        sampler.stop()

    def test_context_manager_noop_when_disabled(self):
        with memprofile.MemorySampler(interval=0.01) as sampler:
            self.assertIsNone(sampler._thread)

    def test_rss_bytes_returns_int_or_none(self):
        rss = memprofile.MemorySampler._rss_bytes()
        self.assertTrue(rss is None or isinstance(rss, int))

    def test_start_stop_when_enabled(self):
        DebugOpt.MEMORY.enabled = True
        was_tracing = tracemalloc.is_tracing()
        sampler = memprofile.MemorySampler(interval=0.01, label="test")
        try:
            sampler.start()
            self.assertIsNotNone(sampler._thread)
            sampler.stop()
            self.assertIsNone(sampler._thread)
        finally:
            sampler.stop()
            if not was_tracing and tracemalloc.is_tracing():
                tracemalloc.stop()

    def test_type_counts_returns_counter(self):
        counts = memprofile._type_counts()
        self.assertIsInstance(counts, dict)
        # 'dict' objects certainly exist in a running interpreter.
        self.assertIn('dict', counts)

    def test_log_object_growth_sets_prev_counts(self):
        DebugOpt.MEMORY.enabled = True
        sampler = memprofile.MemorySampler(track_objects=True)
        # First call establishes the baseline (no growth logged).
        self.assertIsNone(sampler._prev_counts)
        sampler._log_object_growth()
        self.assertIsNotNone(sampler._prev_counts)
        # Second call diffs against the baseline without raising.
        sampler._log_object_growth()

    def test_track_objects_start_stop_when_enabled(self):
        DebugOpt.MEMORY.enabled = True
        was_tracing = tracemalloc.is_tracing()
        sampler = memprofile.MemorySampler(interval=0.01, label="test", track_objects=True)
        try:
            sampler.start()
            self.assertIsNotNone(sampler._thread)
            sampler.stop()
            self.assertIsNone(sampler._thread)
        finally:
            sampler.stop()
            if not was_tracing and tracemalloc.is_tracing():
                tracemalloc.stop()
