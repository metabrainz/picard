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

from PyQt6 import QtCore

from picard import log
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

    def __init__(self, argv, config_file=None):
        super().__init__(argv)
        self.stopping = False
        self.exit_cleanup = []

        # File registry (filename -> File), as read by the save path.
        self.files = {}

        # Batch-save bookkeeping read by File._saving_finished.
        self._saving_files_count = 0
        self._saving_dirty_image_parents = set()

        # Config must be set up before the services (WebService reads config).
        # Mirror minimal_init(): register options, load config, migrate
        # non-interactively (headless must not block on an upgrade dialog).
        init_options()
        setup_config(app=self, filename=config_file)
        run_config_upgrades(get_config(), interactive=False)

        self._init_threads()
        self._init_services()

        set_services_provider(self)

    # --- services -----------------------------------------------------------

    def _init_services(self):
        # Imported here to avoid pulling the web service into CLI commands that
        # do not need it, and to mirror the GUI Tagger's lazy service setup.
        from picard.acoustid import AcoustIDClient
        from picard.acoustid.manager import AcoustIDManager
        from picard.isrcsubmit import ISRCSubmitManager
        from picard.webservice import WebService
        from picard.webservice.api_helpers import (
            AcoustIdAPIHelper,
            MBAPIHelper,
        )

        self.webservice = WebService()
        self.register_cleanup(self.webservice.stop)
        self.mb_api = MBAPIHelper(self.webservice)

        self.format_registry = FormatRegistry(self)
        for file_format in DEFAULT_FORMATS:
            self.format_registry.register(file_format)

        acoustid_api = AcoustIdAPIHelper(self.webservice)
        self.acoustid_client = AcoustIDClient(acoustid_api)
        self.acoustid_client.init()
        self.register_cleanup(self.acoustid_client.done)
        self.acoustidmanager = AcoustIDManager(acoustid_api)
        self.isrc_submit_manager = ISRCSubmitManager(self.mb_api)

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
