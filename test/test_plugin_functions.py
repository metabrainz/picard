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


from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.plugin import (
    PluginFunctions,
    _log_processor_error,
)


class TestLogProcessorError(PicardTestCase):
    """Tests for the _log_processor_error context manager."""

    @patch('picard.plugin.log')
    def test_logs_exception_with_module_and_name(self, mock_log):
        def bad_func():
            raise ValueError("something went wrong")

        with _log_processor_error('track_metadata_processors', bad_func):
            bad_func()

        mock_log.error.assert_called_once()
        args = mock_log.error.call_args
        formatted = args[0][0] % args[0][1:]
        self.assertIn('track_metadata_processors', formatted)
        self.assertIn('bad_func', formatted)
        self.assertTrue(args[1].get('exc_info'))

    @patch('picard.plugin.log')
    def test_no_log_on_success(self, mock_log):
        with _log_processor_error('album_metadata_processors', lambda: None):
            pass

        mock_log.error.assert_not_called()

    def test_does_not_catch_keyboard_interrupt(self):
        """SystemExit and KeyboardInterrupt must propagate."""
        with self.assertRaises(KeyboardInterrupt):
            with _log_processor_error('track_metadata_processors', lambda: None):
                raise KeyboardInterrupt


class TestPluginFunctionsRun(PicardTestCase):
    """Tests for PluginFunctions.run() error isolation (PICARD-3393)."""

    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'plugins3_exec_order': {}})
        self.pf = PluginFunctions(label='track_metadata_processors')

    def test_run_executes_all_functions(self):
        results = []

        def func_a(x):
            results.append('a')

        def func_b(x):
            results.append('b')

        self.pf.register('test_module', func_a)
        self.pf.register('test_module', func_b)
        self.pf.run('arg')
        self.assertEqual(results, ['a', 'b'])

    def test_run_continues_after_exception(self):
        """A failing function must not prevent subsequent functions from running."""
        results = []

        def func_good_before(x):
            results.append('before')

        def func_bad(x):
            raise TypeError("wrong number of arguments")

        def func_good_after(x):
            results.append('after')

        self.pf.register('test_module', func_good_before)
        self.pf.register('test_module', func_bad)
        self.pf.register('test_module', func_good_after)
        self.pf.run('arg')
        self.assertEqual(results, ['before', 'after'])

    @patch('picard.plugin.log')
    def test_run_logs_exception(self, mock_log):
        """A failing function should be logged with an error."""

        def func_bad(x):
            raise ValueError("something went wrong")

        self.pf.register('test_module', func_bad)
        self.pf.run('arg')
        mock_log.error.assert_called_once()
        args = mock_log.error.call_args
        self.assertTrue(args[1].get('exc_info'))

    def test_run_with_no_functions(self):
        """run() with no registered functions should be a no-op."""
        self.pf.run('arg')  # Should not raise

    def test_run_multiple_failures_all_logged(self):
        """Multiple failing functions should all be logged independently."""
        results = []

        def func_bad_1(x):
            raise TypeError("bad 1")

        def func_good(x):
            results.append('good')

        def func_bad_2(x):
            raise RuntimeError("bad 2")

        self.pf.register('test_module', func_bad_1)
        self.pf.register('test_module', func_good)
        self.pf.register('test_module', func_bad_2)

        with patch('picard.plugin.log') as mock_log:
            self.pf.run('arg')

        self.assertEqual(results, ['good'])
        self.assertEqual(mock_log.error.call_count, 2)

    def test_run_works_for_non_metadata_processors(self):
        """Error isolation works for all processor types, not just metadata."""
        pf = PluginFunctions(label='file_post_load_processors')
        results = []

        def func_bad(f):
            raise RuntimeError("plugin crash")

        def func_good(f):
            results.append('loaded')

        pf.register('test_module', func_bad)
        pf.register('test_module', func_good)
        pf.run('file')
        self.assertEqual(results, ['loaded'])
