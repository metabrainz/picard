# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025 Laurent Monin
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

"""Async registry operations."""

import json

from PyQt6.QtCore import QCoreApplication

from picard.plugin3.asyncops.callbacks import OperationResult
from picard.plugin3.registry import PluginRegistry


class AsyncPluginRegistry:
    """Async wrapper for PluginRegistry operations."""

    def __init__(self, registry: PluginRegistry):
        self._registry = registry
        self._tagger = QCoreApplication.instance()

    def fetch_registry(self, callback, use_cache=True):
        """Fetch registry asynchronously using WebService.

        Args:
            callback: Called with OperationResult on completion
            use_cache: Whether to use cached registry
        """
        # Check cache first
        if use_cache and self._registry.is_registry_loaded():
            callback(OperationResult(success=True, result=self._registry.get_raw_registry_data()))
            return

        def _on_response(data, reply, error):
            if error:
                callback(OperationResult(success=False, error=error, error_message=str(error)))
            else:
                try:
                    registry_data = json.loads(data)
                    self._registry.set_raw_registry_data(registry_data)
                    callback(OperationResult(success=True, result=registry_data))
                except json.JSONDecodeError as e:
                    callback(OperationResult(success=False, error=e, error_message=f'Invalid JSON: {e}'))

        # Use Picard's WebService for async HTTP
        self._tagger.webservice.get_url(
            url=self._registry.registry_url, handler=_on_response, parse_response_type='json'
        )

    def search_plugins(self, query=None, category=None, trust_level=None):
        """Search plugins (synchronous - fast operation)."""
        return self._registry.list_plugins(query=query, category=category, trust_level=trust_level)
