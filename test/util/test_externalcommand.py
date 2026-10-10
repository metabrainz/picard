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

from PyQt6.QtTest import QTest

from test.picardtestcase import PicardTestCase

from picard.util.externalcommand import (
    CommandError,
    CommandResult,
    ExternalCommand,
    ExternalCommandRunner,
    find_executable,
)


def _py(code: str) -> list[str]:
    """Build an argv that runs the given Python snippet with this interpreter."""
    return [sys.executable, "-c", code]


# --------------------------------------------------------------------------- #
# Data / discovery layer (no Qt)
# --------------------------------------------------------------------------- #


class FindExecutableTest(PicardTestCase):
    def test_finds_python(self):
        self.assertIsNotNone(find_executable(sys.executable))

    def test_returns_none_for_missing(self):
        self.assertIsNone(find_executable("definitely-not-a-real-command-xyz"))

    def test_skips_empty_and_falls_back(self):
        self.assertIsNotNone(find_executable("", "definitely-not-a-real-command-xyz", sys.executable))


# --------------------------------------------------------------------------- #
# Qt layer (QProcess)
# --------------------------------------------------------------------------- #


class _Collector:
    """Collects success/error callbacks and counts total completions."""

    def __init__(self):
        self.results: list[CommandResult] = []
        self.errors: list[CommandError] = []

    @property
    def total(self) -> int:
        return len(self.results) + len(self.errors)

    def on_success(self, result: CommandResult) -> None:
        self.results.append(result)

    def on_error(self, error: CommandError) -> None:
        self.errors.append(error)


class ExternalCommandQtTestBase(PicardTestCase):
    """Base providing a QCoreApplication and an event-loop wait helper."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from PyQt6.QtCore import QCoreApplication

        cls.app = QCoreApplication.instance()
        if cls.app is None:
            cls.app = QCoreApplication([])

    def _wait_for(self, condition, timeout_ms: int = 5000) -> None:
        elapsed = 0
        step = 20
        while not condition() and elapsed < timeout_ms:
            QTest.qWait(step)
            elapsed += step
        self.assertTrue(condition(), "timed out waiting for condition")


class ExternalCommandTest(ExternalCommandQtTestBase):
    def test_success(self):
        collector = _Collector()
        cmd = ExternalCommand(_py("print('hi')"))
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.results), 1)
        self.assertEqual(collector.results[0].stdout.strip(), "hi")

    def test_accepted_non_zero(self):
        collector = _Collector()
        cmd = ExternalCommand(
            _py("import sys; print('partial'); sys.exit(3)"),
            ok_returncodes=(3,),
        )
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.results), 1)
        self.assertEqual(collector.results[0].returncode, 3)
        self.assertEqual(collector.results[0].stdout.strip(), "partial")

    def test_failure_reports_error_with_output(self):
        collector = _Collector()
        cmd = ExternalCommand(_py("import sys; print('bad', file=sys.stderr); sys.exit(1)"))
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.errors), 1)
        self.assertEqual(collector.errors[0].returncode, 1)
        self.assertIn("bad", collector.errors[0].stderr)

    def test_failed_to_start(self):
        collector = _Collector()
        cmd = ExternalCommand(["definitely-not-a-real-command-xyz"])
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.errors), 1)
        self.assertIsNone(collector.errors[0].returncode)

    def test_empty_args_raises(self):
        with self.assertRaises(ValueError):
            ExternalCommand([])

    def test_timeout_fires(self):
        collector = _Collector()
        cmd = ExternalCommand(_py("import time; time.sleep(5)"), timeout=0.2)
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.errors), 1)
        self.assertIn("timed out", str(collector.errors[0]).lower())

    def test_timeout_not_fired_on_fast_command(self):
        collector = _Collector()
        # Generous timeout that must not fire for a quick command.
        cmd = ExternalCommand(_py("print('quick')"), timeout=5)
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.results), 1)
        self.assertEqual(collector.results[0].stdout.strip(), "quick")
        # The timer must have been stopped on normal completion.
        self.assertIsNone(cmd._timer)

    def test_no_timeout_by_default(self):
        cmd = ExternalCommand(_py("print('x')"))
        collector = _Collector()
        cmd.start(collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 1)
        self.assertEqual(len(collector.results), 1)
        self.assertIsNone(cmd._timer)


class ExternalCommandRunnerTest(ExternalCommandQtTestBase):
    def test_runs_all_commands(self):
        collector = _Collector()
        runner = ExternalCommandRunner(max_concurrent=2)
        for i in range(5):
            runner.run(_py(f"print({i})"), collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 5)
        self.assertEqual(len(collector.results), 5)
        outputs = sorted(r.stdout.strip() for r in collector.results)
        self.assertEqual(outputs, ["0", "1", "2", "3", "4"])

    def test_respects_concurrency_limit(self):
        # Each command records concurrent count via a shared marker directory.
        marker_dir = self.mktmpdir()
        # Script: create a unique file, sleep, count files present, print peak.
        script = (
            "import os, sys, time, uuid\n"
            f"d = {marker_dir!r}\n"
            "p = os.path.join(d, uuid.uuid4().hex)\n"
            "open(p, 'w').close()\n"
            "time.sleep(0.3)\n"
            "print(len(os.listdir(d)))\n"
            "os.remove(p)\n"
        )
        collector = _Collector()
        runner = ExternalCommandRunner(max_concurrent=2)
        for _ in range(4):
            runner.run(_py(script), collector.on_success, collector.on_error)
        self._wait_for(lambda: collector.total == 4, timeout_ms=10000)
        self.assertEqual(len(collector.results), 4)
        peak = max(int(r.stdout.strip()) for r in collector.results)
        self.assertLessEqual(peak, 2, "concurrency limit exceeded")

    def test_cancel_by_key_prevents_queued_start(self):
        collector = _Collector()
        # max_concurrent=1 so later entries stay queued while the first runs.
        runner = ExternalCommandRunner(max_concurrent=1)
        runner.run(
            _py("import time; time.sleep(0.4); print('a')"), collector.on_success, collector.on_error, key="keep"
        )
        runner.run(_py("print('b')"), collector.on_success, collector.on_error, key="drop")
        runner.run(_py("print('c')"), collector.on_success, collector.on_error, key="drop")
        # Cancel the queued "drop" commands before they start.
        runner.cancel(lambda k: k == "drop")
        self._wait_for(lambda: collector.total >= 1)
        # Give any erroneously-started commands a chance to report.
        QTest.qWait(300)
        outputs = [r.stdout.strip() for r in collector.results]
        self.assertIn("a", outputs)
        self.assertNotIn("b", outputs)
        self.assertNotIn("c", outputs)

    def test_cancel_all_prevents_queued_start(self):
        collector = _Collector()
        runner = ExternalCommandRunner(max_concurrent=1)
        runner.run(_py("import time; time.sleep(0.3); print('a')"), collector.on_success, collector.on_error)
        runner.run(_py("print('b')"), collector.on_success, collector.on_error)
        runner.run(_py("print('c')"), collector.on_success, collector.on_error)
        runner.cancel_all()
        # Nothing more should start; let any erroneous starts report.
        QTest.qWait(400)
        outputs = [r.stdout.strip() for r in collector.results]
        self.assertNotIn("b", outputs)
        self.assertNotIn("c", outputs)
