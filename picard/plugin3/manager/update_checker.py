# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Bob Swift
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from picard import log
from picard.util.thread import run_task


class PluginUpdateChecker:
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager

    def check_for_updates(self):
        log.debug("Checking for %s plugin updates.", len(self.plugin_manager.plugins))
        self.plugin_manager.refresh_registry_and_caches(callback=self._on_registry_refreshed)

    def _on_registry_refreshed(self, success, error):
        if not success:
            log.error('Failed to refresh registry: %s', error)
        else:
            log.debug("Plugin registry and caches refreshed successfully.")
        run_task(
            self._update_checker,
            next_func=self._on_plugin_update_checks_finished,
        )

    def _update_checker(self):
        try:
            # Fetch remote refs for all plugins (for ref selectors)
            self.plugin_manager.refresh_all_plugin_refs()

            # Check for updates (silent - no dialog) - skip fetching since we just did it
            self.plugin_manager.check_updates(skip_fetch=True)

        except Exception as e:
            log.error("Failed to refresh all plugins: %s", e, exc_info=True)

    def _on_plugin_update_checks_finished(self, *args, **kwargs):
        log.debug("Finished checking for plugin updates.")
        self.plugin_manager.refresh_updates_available.emit()
