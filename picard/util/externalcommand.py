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

"""Discover and run external command-line programs.

This module provides an asynchronous way to run external command-line programs,
built on :class:`~PyQt6.QtCore.QProcess`:

* :class:`ExternalCommand` — a single asynchronous command.
* :class:`ExternalCommandRunner` — a bounded pool of commands with cancellation.

Running external programs this way keeps the UI responsive, supports a
concurrency limit and cancellation, and reports results on the main thread.

The important cross-platform and correctness details are handled once:

* stdout and stderr are captured as UTF-8 text, with undecodable bytes replaced.
* The exit code is always available; a command may declare which non-zero exit
  codes are acceptable (``ok_returncodes``), so programs like ``fpcalc`` that
  use a non-zero code to signal a recoverable condition are handled cleanly.
* On a failure the program's own stdout/stderr are carried on the error, so a
  caller never loses the diagnostic.

:func:`find_executable` is re-exported from :mod:`picard.util` for discovery.
"""

from __future__ import annotations

from collections import deque
from collections.abc import (
    Callable,
    Iterable,
)
from dataclasses import dataclass

from PyQt6 import QtCore

from picard import log

# Re-exported so callers can import discovery and execution helpers from a
# single module. find_executable handles Windows executable-extension expansion
# and frozen-build lookup.
from picard.util import find_executable


__all__ = [
    'CommandError',
    'CommandResult',
    'ExternalCommand',
    'ExternalCommandRunner',
    'find_executable',
]


@dataclass(frozen=True)
class CommandResult:
    """Outcome of an external command that finished and ran to completion.

    A result is produced when the process exits with code ``0`` or with one of
    the caller's declared ``ok_returncodes``. Inspect :attr:`returncode` to tell
    an exact-success (``0``) from an accepted non-zero exit.

    Attributes:
        args: The argument vector that was executed.
        returncode: The process exit code.
        stdout: Captured standard output as text.
        stderr: Captured standard error as text.
    """

    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class CommandError(Exception):
    """Raised or reported when an external command fails.

    This covers failure to start the process (executable not found), a timeout,
    or an exit with a code that is neither ``0`` nor an accepted
    ``ok_returncodes`` value. The captured ``stdout`` and ``stderr`` are
    included so callers can surface the program's own error message.

    Attributes:
        args_list: The argument vector that was executed.
        returncode: The process exit code, or ``None`` if the process could not
            be started or did not produce an exit code.
        stdout: Captured standard output as text (may be empty).
        stderr: Captured standard error as text (may be empty).
    """

    def __init__(
        self,
        message: str,
        *,
        args_list: tuple[str, ...] = (),
        returncode: int | None = None,
        stdout: str = '',
        stderr: str = '',
    ):
        super().__init__(message)
        self.args_list = args_list
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _decode(data: bytes) -> str:
    """Decode captured QProcess output as UTF-8, replacing undecodable bytes."""
    return bytes(data).decode('utf-8', errors='replace')


def _is_accepted(returncode: int, ok_returncodes: Iterable[int]) -> bool:
    """Return True if the exit code counts as success."""
    return returncode == 0 or returncode in set(ok_returncodes)


def _non_zero_message(args: tuple[str, ...], returncode: int, stderr: str) -> str:
    """Build a readable error message for an unacceptable exit code."""
    detail = f": {stderr.strip()}" if stderr.strip() else ""
    return f"{args[0]!r} returned non-zero exit code ({returncode}){detail}"


SuccessCallback = Callable[[CommandResult], None]
ErrorCallback = Callable[[CommandError], None]


class ExternalCommand(QtCore.QObject):
    """A single external command executed asynchronously via QProcess.

    The command is started with :meth:`start`; exactly one of the supplied
    callbacks is invoked on the main thread when it finishes. Output is captured
    and decoded as UTF-8. Use :meth:`cancel` to kill a running command. An
    optional ``timeout`` (seconds) kills the command and reports a
    :class:`CommandError` if it runs too long.

    Prefer :class:`ExternalCommandRunner` when running many commands, as it adds
    a concurrency limit and group cancellation.
    """

    def __init__(
        self,
        args: list[str] | tuple[str, ...],
        *,
        parent: QtCore.QObject | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        ok_returncodes: Iterable[int] = (),
        timeout: float | None = None,
    ):
        super().__init__(parent)
        if not args:
            raise ValueError("args must contain at least the executable")
        self._args = tuple(args)
        self._cwd = cwd
        self._env = env
        self._ok_returncodes = tuple(ok_returncodes)
        self._timeout = timeout
        self._on_success: SuccessCallback | None = None
        self._on_error: ErrorCallback | None = None
        self._process: QtCore.QProcess | None = None
        self._timer: QtCore.QTimer | None = None
        self._finished = False

    @property
    def args(self) -> tuple[str, ...]:
        return self._args

    def start(self, on_success: SuccessCallback, on_error: ErrorCallback) -> None:
        """Start the command. Callbacks run on the main thread when it ends."""
        self._on_success = on_success
        self._on_error = on_error

        process = QtCore.QProcess(self)
        self._process = process
        if self._cwd:
            process.setWorkingDirectory(self._cwd)
        if self._env is not None:
            environment = QtCore.QProcessEnvironment()
            for key, value in self._env.items():
                environment.insert(key, value)
            process.setProcessEnvironment(environment)
        process.finished.connect(self._on_process_finished)
        process.errorOccurred.connect(self._on_process_error)

        program = self._args[0]
        arguments = list(self._args[1:])
        log.debug("Running external command: %r %r", program, arguments)
        process.start(program, arguments)

        if self._timeout is not None:
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self._on_timeout)
            timer.start(int(self._timeout * 1000))
            self._timer = timer

    def _stop_timer(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def _on_timeout(self) -> None:
        if self._finished:
            return
        self._finished = True
        self._timer = None
        stdout, stderr = self._read_output()
        if self._process is not None and self._process.state() != QtCore.QProcess.ProcessState.NotRunning:
            self._process.kill()
        self._deliver_error(
            CommandError(
                f"Command timed out after {self._timeout}s: {self._args[0]!r}",
                args_list=self._args,
                stdout=stdout,
                stderr=stderr,
            )
        )

    def cancel(self) -> None:
        """Kill the running command. No callback is invoked after cancelling."""
        self._finished = True
        self._stop_timer()
        if self._process is not None and self._process.state() != QtCore.QProcess.ProcessState.NotRunning:
            self._process.kill()

    def _read_output(self) -> tuple[str, str]:
        assert self._process is not None
        stdout = _decode(self._process.readAllStandardOutput().data())
        stderr = _decode(self._process.readAllStandardError().data())
        return stdout, stderr

    def _on_process_finished(self, exit_code: int, exit_status: QtCore.QProcess.ExitStatus) -> None:
        if self._finished:
            return
        self._finished = True
        self._stop_timer()
        stdout, stderr = self._read_output()

        if exit_status != QtCore.QProcess.ExitStatus.NormalExit:
            self._deliver_error(
                CommandError(
                    f"{self._args[0]!r} crashed",
                    args_list=self._args,
                    returncode=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                )
            )
            return

        if not _is_accepted(exit_code, self._ok_returncodes):
            self._deliver_error(
                CommandError(
                    _non_zero_message(self._args, exit_code, stderr),
                    args_list=self._args,
                    returncode=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                )
            )
            return

        result = CommandResult(args=self._args, returncode=exit_code, stdout=stdout, stderr=stderr)
        if self._on_success is not None:
            self._on_success(result)

    def _on_process_error(self, error: QtCore.QProcess.ProcessError) -> None:
        if self._finished:
            return
        # FailedToStart arrives before/without finished(); other errors (e.g.
        # Crashed) are also reported by finished() and handled there.
        if error != QtCore.QProcess.ProcessError.FailedToStart:
            return
        self._finished = True
        self._stop_timer()
        message = self._process.errorString() if self._process is not None else "failed to start"
        self._deliver_error(
            CommandError(
                f"Failed to run {self._args[0]!r}: {message}",
                args_list=self._args,
            )
        )

    def _deliver_error(self, error: CommandError) -> None:
        log.error(
            "External command failed: %r (code=%r): %s",
            self._args,
            error.returncode,
            error.stderr.strip() or error,
        )
        if self._on_error is not None:
            self._on_error(error)


class ExternalCommandRunner(QtCore.QObject):
    """Run external commands asynchronously with a bounded concurrency limit.

    Commands submitted with :meth:`run` are queued and started as slots free up,
    never exceeding ``max_concurrent`` running at once. Each command reports to
    its own success/error callback on the main thread. Use :meth:`cancel` to
    cancel commands matching a predicate (both queued and running).
    """

    def __init__(self, max_concurrent: int = 1, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._max_concurrent = max(1, int(max_concurrent))
        self._queue: deque[tuple[ExternalCommand, SuccessCallback, ErrorCallback, object]] = deque()
        self._running: dict[ExternalCommand, object] = {}

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    def set_max_concurrent(self, value: int) -> None:
        self._max_concurrent = max(1, int(value))
        self._pump()

    def run(
        self,
        args: list[str] | tuple[str, ...],
        on_success: SuccessCallback,
        on_error: ErrorCallback,
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        ok_returncodes: Iterable[int] = (),
        timeout: float | None = None,
        key: object = None,
    ) -> ExternalCommand:
        """Queue a command to run. Returns the created :class:`ExternalCommand`.

        Args:
            args: The argument vector (executable first).
            on_success: Called on the main thread with a :class:`CommandResult`.
            on_error: Called on the main thread with a :class:`CommandError`.
            cwd: Optional working directory.
            env: Optional environment mapping.
            ok_returncodes: Non-zero exit codes to accept as success.
            timeout: Optional timeout in seconds; the command is killed and
                reported as a :class:`CommandError` if it runs longer.
            key: Optional opaque value used by :meth:`cancel` to select which
                commands to cancel (e.g. the file a command is working on).

        Returns:
            ExternalCommand: The command object (already queued; may not have
            started yet if the concurrency limit is reached).
        """
        command = ExternalCommand(
            args,
            parent=self,
            cwd=cwd,
            env=env,
            ok_returncodes=ok_returncodes,
            timeout=timeout,
        )
        self._queue.append((command, on_success, on_error, key))
        self._pump()
        return command

    def cancel(self, predicate: Callable[[object], bool]) -> None:
        """Cancel queued and running commands whose ``key`` matches ``predicate``."""
        remaining: deque[tuple[ExternalCommand, SuccessCallback, ErrorCallback, object]] = deque()
        for entry in self._queue:
            command, _on_success, _on_error, key = entry
            if predicate(key):
                command.cancel()
            else:
                remaining.append(entry)
        self._queue = remaining
        for command, key in list(self._running.items()):
            if predicate(key):
                command.cancel()
                self._running.pop(command, None)
        self._pump()

    def cancel_all(self) -> None:
        """Cancel every queued and running command."""
        for command, _on_success, _on_error, _key in self._queue:
            command.cancel()
        self._queue.clear()
        for command in list(self._running):
            command.cancel()
        self._running.clear()

    def _pump(self) -> None:
        while self._queue and len(self._running) < self._max_concurrent:
            command, on_success, on_error, key = self._queue.popleft()
            self._running[command] = key
            command.start(
                self._wrap_success(command, on_success),
                self._wrap_error(command, on_error),
            )

    def _wrap_success(self, command: ExternalCommand, on_success: SuccessCallback) -> SuccessCallback:
        def _wrapped(result: CommandResult) -> None:
            self._complete(command)
            on_success(result)

        return _wrapped

    def _wrap_error(self, command: ExternalCommand, on_error: ErrorCallback) -> ErrorCallback:
        def _wrapped(error: CommandError) -> None:
            self._complete(command)
            on_error(error)

        return _wrapped

    def _complete(self, command: ExternalCommand) -> None:
        self._running.pop(command, None)
        self._pump()
