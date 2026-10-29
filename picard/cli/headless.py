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

"""Headless application object for running the tagging core without a GUI.

The GUI ``Tagger`` is a ``QApplication`` that both provides the long-lived
services and dispatches background-thread callbacks (via its ``event()``
override handling ``ProxyToMainEvent``). The headless ``picard-cli`` runs on a
bare ``QCoreApplication`` that has neither, so the tagging pipeline's
thread-pool callbacks would never be delivered and service lookups would fail.

``HeadlessTagger`` is a small ``QCoreApplication`` subclass that provides the
subset of the ``Tagger`` surface the file load/save pipeline needs:

- the long-lived services (``webservice``, ``mb_api``, ``format_registry``,
  ``acoustidmanager``, ``isrc_submit_manager``, ``acoustid_client``),
- the thread pools (``thread_pool``, ``priority_thread_pool``,
  ``save_thread_pool``),
- the small amount of save/stop bookkeeping the ``File`` save path reads
  (``stopping``, ``files``, ``_saving_files_count``,
  ``_saving_dirty_image_parents``, ``flush_saving_image_parents``),
- delivery of ``ProxyToMainEvent`` so thread-pool callbacks run on the main
  thread.

It installs itself as the services provider (see :mod:`picard.services`) so
core code reaching services via ``services()`` transparently uses it.

This object intentionally holds no GUI, no session/registry orchestration and
no album/cluster state beyond ``files`` — it is scoped to the file tag
read/write pipeline. Broader headless tagging (album loading, matching) is a
later step.
"""

import time

from PyQt6 import QtCore

from picard import (
    log,
    set_tagger_provider,
)
from picard.config import (
    get_config,
    setup_config,
)
from picard.config_upgrade import run_config_upgrades
from picard.formats import DEFAULT_FORMATS
from picard.formats.registry import FormatRegistry
from picard.options import init_options
from picard.services import set_services_provider
from picard.util import thread


class HeadlessTagger(QtCore.QCoreApplication):
    """A minimal, GUI-less application object for the tagging core."""

    # Signals the tagging core emits on the application object. The GUI Tagger
    # declares the same signals; headless has no listeners by default, but the
    # signals must exist for File state transitions / load completion to emit.
    tagger_stats_changed = QtCore.pyqtSignal()
    file_loaded = QtCore.pyqtSignal(object)

    def __init__(self, argv, config_file=None):
        super().__init__(argv)
        self.stopping = False
        self.exit_cleanup = []

        # File registry (filename -> File), as read by the save path.
        self.files = {}

        # Batch-save bookkeeping read by File._saving_finished.
        self._saving_files_count = 0
        self._saving_dirty_image_parents = set()

        # Services are created lazily (see the properties below) so a command
        # that needs none (e.g. profiles) pays for none, and one that needs only
        # the web service (e.g. plugins) does not spin up the format registry or
        # the AcoustID client. Backing fields start unset.
        self._webservice = None
        self._mb_api = None
        self._format_registry = None
        self._acoustid_api = None
        self._acoustid_client = None
        self._acoustidmanager = None
        self._isrc_submit_manager = None

        # Config must be set up before any service (WebService reads config).
        # Mirror minimal_init(): register options, load config, migrate
        # non-interactively (headless must not block on an upgrade dialog).
        init_options()
        setup_config(app=self, filename=config_file)
        run_config_upgrades(get_config(), interactive=False)

        self._init_threads()

        # Make this object discoverable to core code that reaches the running
        # application via tagger_instance() (e.g. File state bookkeeping), and
        # as the services provider for services().
        set_services_provider(self)
        set_tagger_provider(self)

    # --- services (lazy) ----------------------------------------------------
    #
    # Each service is built on first access and cached. services() delegates by
    # attribute name, so these lazy properties are transparent to core code.
    # Cleanup for a service is registered when (and only when) it is created.

    @property
    def webservice(self):
        if self._webservice is None:
            from picard.webservice import WebService

            self._webservice = WebService()
            self.register_cleanup(self._webservice.stop)
        return self._webservice

    @property
    def mb_api(self):
        if self._mb_api is None:
            from picard.webservice.api_helpers import MBAPIHelper

            self._mb_api = MBAPIHelper(self.webservice)
        return self._mb_api

    @property
    def format_registry(self):
        if self._format_registry is None:
            self._format_registry = FormatRegistry(self)
            for file_format in DEFAULT_FORMATS:
                self._format_registry.register(file_format)
        return self._format_registry

    @property
    def _acoustid_api_helper(self):
        if self._acoustid_api is None:
            from picard.webservice.api_helpers import AcoustIdAPIHelper

            self._acoustid_api = AcoustIdAPIHelper(self.webservice)
        return self._acoustid_api

    @property
    def acoustid_client(self):
        if self._acoustid_client is None:
            from picard.acoustid import AcoustIDClient

            client = AcoustIDClient(self._acoustid_api_helper)
            client.init()
            self.register_cleanup(client.done)
            self._acoustid_client = client
        return self._acoustid_client

    @property
    def acoustidmanager(self):
        if self._acoustidmanager is None:
            from picard.acoustid.manager import AcoustIDManager

            self._acoustidmanager = AcoustIDManager(self._acoustid_api_helper)
        return self._acoustidmanager

    @property
    def isrc_submit_manager(self):
        if self._isrc_submit_manager is None:
            from picard.isrcsubmit import ISRCSubmitManager

            self._isrc_submit_manager = ISRCSubmitManager(self.mb_api)
        return self._isrc_submit_manager

    # --- threads ------------------------------------------------------------

    def _init_threads(self):
        self.thread_pool = QtCore.QThreadPool(self)
        self.register_cleanup(self.thread_pool.waitForDone)
        self.thread_pool.setMaxThreadCount(max(2, QtCore.QThread.idealThreadCount()))

        self.priority_thread_pool = QtCore.QThreadPool(self)
        self.register_cleanup(self.priority_thread_pool.waitForDone)
        self.priority_thread_pool.setMaxThreadCount(1)

        # Separate single-threaded pool for file saving, matching the GUI
        # Tagger (avoids races in File._save_and_rename).
        self.save_thread_pool = QtCore.QThreadPool(self)
        self.register_cleanup(self.save_thread_pool.waitForDone)
        self.save_thread_pool.setMaxThreadCount(1)

    # --- event delivery -----------------------------------------------------

    def event(self, a0: 'QtCore.QEvent | None') -> bool:
        # Background tasks post their completion callback as a ProxyToMainEvent
        # (see picard.util.thread.to_main). Run it on the main thread. Unlike
        # the GUI, there is no UI-responsiveness concern, so run it directly.
        if isinstance(a0, thread.ProxyToMainEvent):
            a0.run()
            return True
        return super().event(a0)

    # --- event loop driver --------------------------------------------------

    def _has_pending_work(self) -> bool:
        """True while background work is still in flight.

        Covers the work the tag load/save pipeline produces: active thread-pool
        tasks and pending web requests. AcoustID fingerprinting is not part of
        tag read/write and is not driven here.

        Reads the web service via the backing field so that merely draining the
        event loop never forces the (lazy) web service to be created.
        """
        pending_requests = self._webservice.num_pending_web_requests if self._webservice is not None else 0
        return bool(
            self.thread_pool.activeThreadCount()
            or self.priority_thread_pool.activeThreadCount()
            or self.save_thread_pool.activeThreadCount()
            or pending_requests
        )

    def run_until_idle(self, timeout: float | None = None, interval: float = 0.02) -> bool:
        """Pump the Qt event loop until all background work has drained.

        File load/save and web requests run on background threads (or the Qt
        network stack) and deliver their results as events on the main thread
        (ProxyToMainEvent / queued signals). Headless code must therefore pump
        the event loop for that work to progress and complete.

        Args:
            timeout: Maximum seconds to wait, or None to wait indefinitely.
            interval: Max seconds each processEvents() call may block waiting
                for new events.

        Returns:
            True if work drained, False if the timeout elapsed first.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        interval_ms = max(1, int(interval * 1000))
        while True:
            # Dispatch any already-queued events (callbacks, signals), waiting
            # briefly for more so we don't busy-spin while threads run.
            self.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, interval_ms)
            if not self._has_pending_work():
                # Drain any final queued callbacks produced by the last task.
                self.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False

    # --- save bookkeeping ---------------------------------------------------

    def flush_saving_image_parents(self):
        """Rebuild deferred cover-art image aggregation for a completed batch.

        Mirrors Tagger.flush_saving_image_parents. For standalone files (no
        album/cluster parent) the set stays empty and this is a no-op.
        """
        parents = self._saving_dirty_image_parents
        if not parents:
            return
        self._saving_dirty_image_parents = set()
        for parent in parents:
            parent.update_metadata_images()

    # --- lifecycle ----------------------------------------------------------

    def register_cleanup(self, func):
        self.exit_cleanup.append(func)

    def run_cleanup(self):
        for f in reversed(self.exit_cleanup):
            try:
                f()
            except Exception:
                log.error("Headless cleanup step failed", exc_info=True)
        self.exit_cleanup = []
        # Clear the providers we installed so a later app/test starts clean.
        set_services_provider(None)
        set_tagger_provider(None)
