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

from test.picardtestcase import PicardTestCase

from picard.plugin3.asyncops.callbacks import (
    OperationResult,
    ProgressUpdate,
)


class TestAsyncopsCallbacks(PicardTestCase):
    def test_operation_result_success(self):
        """Test OperationResult for successful operation."""
        result = OperationResult(success=True, result='test_value')
        self.assertTrue(result.success)
        self.assertEqual(result.result, 'test_value')
        self.assertIsNone(result.error)
        self.assertEqual(result.error_message, '')

    def test_operation_result_error(self):
        """Test OperationResult for failed operation."""
        error = ValueError('test error')
        result = OperationResult(success=False, error=error, error_message='test error')
        self.assertFalse(result.success)
        self.assertIsNone(result.result)
        self.assertEqual(result.error, error)
        self.assertEqual(result.error_message, 'test error')

    def test_progress_update_basic(self):
        """Test ProgressUpdate with basic fields."""
        update = ProgressUpdate(operation='install', message='Installing...', percent=50)
        self.assertEqual(update.operation, 'install')
        self.assertEqual(update.message, 'Installing...')
        self.assertEqual(update.percent, 50)
        self.assertIsNone(update.plugin_id)
        self.assertEqual(update.current, 0)
        self.assertEqual(update.total, 0)

    def test_progress_update_full(self):
        """Test ProgressUpdate with all fields."""
        update = ProgressUpdate(
            operation='update_all', plugin_id='test-plugin', percent=75, message='Updating...', current=3, total=4
        )
        self.assertEqual(update.operation, 'update_all')
        self.assertEqual(update.plugin_id, 'test-plugin')
        self.assertEqual(update.percent, 75)
        self.assertEqual(update.message, 'Updating...')
        self.assertEqual(update.current, 3)
        self.assertEqual(update.total, 4)
