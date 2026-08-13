# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Picard Team
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

import logging
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import load_plugin_manifest

from picard.debug_opts import DebugOpt
from picard.plugin3.api import (
    DebugOpt as ApiDebugOpt,
    PluginApi,
    PluginLogger,
)
from picard.plugin3.api_impl import PluginLogger as ImplPluginLogger


class TestPluginLoggerExports(PicardTestCase):
    """Test that DebugOpt and PluginLogger are properly exported from the API."""

    def test_debug_opt_exported(self):
        """DebugOpt should be importable from picard.plugin3.api."""
        self.assertIs(ApiDebugOpt, DebugOpt)

    def test_plugin_logger_exported(self):
        """PluginLogger should be importable from picard.plugin3.api."""
        self.assertIs(PluginLogger, ImplPluginLogger)


class TestPluginLogger(PicardTestCase):
    """Test PluginLogger wrapper class."""

    def setUp(self):
        super().setUp()
        self._underlying = logging.getLogger('test.plugin.myplugin')
        self._logger = ImplPluginLogger(self._underlying)

    def test_delegates_standard_methods(self):
        """Standard logging methods should delegate to the underlying logger."""
        with patch.object(self._underlying, 'debug') as mock_debug:
            self._logger.debug("test %s", "msg")
            mock_debug.assert_called_once_with("test %s", "msg", stacklevel=2)

        with patch.object(self._underlying, 'info') as mock_info:
            self._logger.info("info %s", "msg")
            mock_info.assert_called_once_with("info %s", "msg", stacklevel=2)

        with patch.object(self._underlying, 'warning') as mock_warning:
            self._logger.warning("warn %s", "msg")
            mock_warning.assert_called_once_with("warn %s", "msg", stacklevel=2)

    def test_delegates_attributes(self):
        """Attributes like name should be delegated to the underlying logger."""
        self.assertEqual(self._logger.name, 'test.plugin.myplugin')

    def test_debug_if_enabled(self):
        """debug_if should log when the debug option is enabled."""
        DebugOpt.PLUGIN_DEVELOPMENT.enabled = True
        try:
            with patch('picard.log.main_logger'):
                result = self._logger.debug_if(DebugOpt.PLUGIN_DEVELOPMENT, "test %s", "value")
                self.assertTrue(result)
        finally:
            DebugOpt.PLUGIN_DEVELOPMENT.enabled = False

    def test_debug_if_disabled(self):
        """debug_if should not log when the debug option is disabled."""
        DebugOpt.PLUGIN_DEVELOPMENT.enabled = False
        with patch('picard.log.main_logger') as mock_main:
            result = self._logger.debug_if(DebugOpt.PLUGIN_DEVELOPMENT, "test %s", "value")
            self.assertFalse(result)
            mock_main.debug.assert_not_called()

    def test_debug_if_guard_pattern(self):
        """debug_if should work as a block guard (walrus operator pattern)."""
        DebugOpt.PLUGIN_DEVELOPMENT.enabled = True
        try:
            if dbg := self._logger.debug_if(DebugOpt.PLUGIN_DEVELOPMENT):
                self.assertTrue(dbg)
                # Should be callable
                dbg("item: %r", "test")
        finally:
            DebugOpt.PLUGIN_DEVELOPMENT.enabled = False

    def test_debug_if_guard_disabled(self):
        """debug_if guard should be falsy when disabled."""
        DebugOpt.PLUGIN_DEVELOPMENT.enabled = False
        result = self._logger.debug_if(DebugOpt.PLUGIN_DEVELOPMENT)
        self.assertFalse(result)
        # No-op logger should still be callable without error
        result("should not crash: %s", "test")

    def test_debug_if_msg_func(self):
        """debug_if should support msg_func for lazy formatting."""
        DebugOpt.PLUGIN_DEVELOPMENT.enabled = True
        expensive_called = False

        def expensive():
            nonlocal expensive_called
            expensive_called = True
            return "expensive result"

        try:
            with patch('picard.log.main_logger'):
                self._logger.debug_if(
                    DebugOpt.PLUGIN_DEVELOPMENT,
                    msg_func=lambda: "Result: %s" % expensive(),
                )
                self.assertTrue(expensive_called)
        finally:
            DebugOpt.PLUGIN_DEVELOPMENT.enabled = False

    def test_debug_if_msg_func_not_called_when_disabled(self):
        """msg_func should not be called when the debug option is disabled."""
        DebugOpt.PLUGIN_DEVELOPMENT.enabled = False
        expensive_called = False

        def expensive():
            nonlocal expensive_called
            expensive_called = True
            return "expensive result"

        self._logger.debug_if(
            DebugOpt.PLUGIN_DEVELOPMENT,
            msg_func=lambda: "Result: %s" % expensive(),
        )
        self.assertFalse(expensive_called)


class TestPluginApiLogger(PicardTestCase):
    """Test that PluginApi.logger returns a PluginLogger."""

    def test_logger_is_plugin_logger(self):
        """api.logger should return a PluginLogger instance."""
        api = PluginApi(load_plugin_manifest('example'), Mock(), Mock(), Mock())
        self.assertIsInstance(api.logger, ImplPluginLogger)

    def test_logger_has_debug_if(self):
        """api.logger should have a debug_if method."""
        api = PluginApi(load_plugin_manifest('example'), Mock(), Mock(), Mock())
        self.assertTrue(hasattr(api.logger, 'debug_if'))
        self.assertTrue(callable(api.logger.debug_if))
