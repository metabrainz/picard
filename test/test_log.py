# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021, 2024 Laurent Monin
# Copyright (C) 2021, 2024 Philipp Wolfer
# Copyright (C) 2024 Bob Swift
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


from collections import deque
from dataclasses import dataclass
from pathlib import (
    PurePath,
    PureWindowsPath,
)
import unittest
from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.const.sys import IS_WIN
from picard.debug_opts import DebugOpt
from picard.log import (
    _calculate_bounds,
    name_filter,
)


class MockLogItem:
    def __init__(self, pos=0):
        self.pos = pos


class MockLogItemQueue:
    def __init__(self):
        self._log_queue = deque(maxlen=10)

    def contents(self, prev=-1):
        if not self._log_queue:
            return []
        offset, length = _calculate_bounds(prev, self._log_queue[0].pos, self._log_queue[-1].pos, len(self._log_queue))

        if offset >= 0:
            return (self._log_queue[i] for i in range(offset, length))
            # If offset < 0, there is a discontinuity in the queue positions
            # Use a slower approach to get the new content.
        else:
            return (x for x in self._log_queue if x.pos > prev)

    def push(self, item):
        self._log_queue.append(item)


class LogQueueCommonTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.item_queue = MockLogItemQueue()


class LogQueueBoundsTestCase(LogQueueCommonTest):
    def test_1(self):
        # Common case where the item positions are within the max size of the queue
        # [0,1,2,3,4,5,6,7], len = 8, maxlen = 10, offset = 0
        for i in range(8):
            self.item_queue.push(MockLogItem(i))
        content_list = self.item_queue.contents()
        self.assertListEqual([x.pos for x in content_list], list(range(0, 8)))

    def test_2(self):
        # Common case where the item positions are outside the max size of the queue
        # Which means the positions do not match the index of items in the queue
        # [5,6,7,8,9,10,11,12,13,14], len = 10, offset = len - (last - prev) = 10 - (14-7) = 3
        for i in range(15):
            self.item_queue.push(MockLogItem(i))
        content_list = self.item_queue.contents(7)  # prev value
        self.assertListEqual([x.pos for x in content_list], list(range(8, 15)))

    def test_3(self):
        # Previous case but the previous item (2) was already removed from the queue
        # So we pick the first item in the queue in its place
        # [5,6,7,8,9,10,11,12,13,14], len = 10, maxlen = 10, prev = 5-1 = 4, offset = 0
        for i in range(15):
            self.item_queue.push(MockLogItem(i))
        content_list = self.item_queue.contents(2)
        self.assertListEqual([x.pos for x in content_list], list(range(5, 15)))

    def test_4(self):
        # In case we have only one element but use different prev values
        self.item_queue.push(MockLogItem(10))
        content_list = self.item_queue.contents()  # prev = -1 is smaller than 10, so we update prev from -1 to 10-1 = 9
        self.assertListEqual([x.pos for x in content_list], [10])

        content_list = self.item_queue.contents(2)  # prev = 2 is smaller than 10, so we update prev from 2 to 10-1 = 9
        self.assertListEqual([x.pos for x in content_list], [10])

        content_list = self.item_queue.contents(9)  # prev = 9 is smaller than 10, so we update prev from 9 to 10-1 = 9
        self.assertListEqual([x.pos for x in content_list], [10])

        content_list = self.item_queue.contents(10)  # prev = 10 is equal to 10, so we use it as is
        self.assertListEqual([x.pos for x in content_list], [])

        content_list = self.item_queue.contents(20)  # prev = 20 is bigger than 10, so we use it as is
        self.assertListEqual([x.pos for x in content_list], [])

    def test_5(self):
        # This shouldn't really happen, but here is a test for it
        # In case of a discontinuity e.g. [4,5,11], we have len = 3, prev = 3, last_pos=11,
        #   which results in offset = 3 - (11-4) = -4, which is completely absurd offset, when the correct would be 0
        self.item_queue.push(MockLogItem(4))
        self.item_queue.push(MockLogItem(5))
        self.item_queue.push(MockLogItem(11))
        content_list = self.item_queue.contents(3)
        self.assertListEqual([x.pos for x in content_list], [4, 5, 11])


@dataclass
class FakeRecord:
    pathname: str
    name: str


@unittest.skipIf(IS_WIN, "Posix test")
@patch('picard.log.picard_module_path', PurePath('/path1/path2'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('/user/picard/plugins'))
class NameFilterTestRel(PicardTestCase):

    def test_1(self):
        record = FakeRecord(name=None, pathname='/path1/path2/module/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'module/file')

    def test_2(self):
        record = FakeRecord(name=None, pathname='/path1/path2/module/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'module')

    def test_3(self):
        record = FakeRecord(name=None, pathname='/path1/path2/module/subpath/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'module/subpath/file')

    def test_4(self):
        record = FakeRecord(name=None, pathname='')
        with self.assertRaises(ValueError):
            name_filter(record)

    def test_5(self):
        record = FakeRecord(name=None, pathname='/path1/path2/__init__/module/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '__init__/module')

    def test_plugin_path_long_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='/user/picard/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/user/picard/plugins/plugin')

    def test_plugin_path_long_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='/user/picard/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/user/picard/plugins/plugin.zip/xxx')

    def test_plugin_path_short_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/user/picard/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins/plugin')

    def test_plugin_path_short_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/user/picard/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins/plugin.zip/xxx')

    def test_plugin_path_short_3(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/user/picard/plugins/myplugin.zip/myplugin.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins/myplugin.zip')

    def test_plugin_path_short_4(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/user/picard/plugins/myplugin.zip/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins/myplugin.zip')


@unittest.skipIf(IS_WIN, "Posix test")
@patch('picard.log.picard_module_path', PurePath('/picard'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('/user/picard/plugins/'))
class NameFilterTestAbs(PicardTestCase):

    def test_1(self):
        record = FakeRecord(name=None, pathname='/path/module/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path/module/file')

    def test_2(self):
        record = FakeRecord(name=None, pathname='/path/module/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path/module')

    def test_3(self):
        record = FakeRecord(name=None, pathname='/path/module/subpath/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path/module/subpath/file')

    def test_4(self):
        record = FakeRecord(name=None, pathname='')
        with self.assertRaises(ValueError):
            name_filter(record)

    def test_plugin_path_long_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/plugin')

    def test_plugin_path_long_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/plugin.zip/xxx')

    def test_plugin_path_long_3(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/plugin.zip/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/plugin.zip')

    def test_plugin_path_short_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/plugin')

    def test_plugin_path_short_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/plugin.zip/xxx')

    def test_plugin_path_short_3(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/myplugin.zip/myplugin.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/myplugin.zip')

    def test_plugin_path_short_4(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='/path1/path2/plugins/myplugin.zip/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path1/path2/plugins/myplugin.zip')


@unittest.skipIf(IS_WIN, "Posix test")
@patch('picard.log.picard_module_path', PurePath('/path1/path2/'))  # incorrect, but testing anyway
@patch('picard.log.USER_PLUGIN_DIR', PurePath('/user/picard/plugins'))
class NameFilterTestEndingSlash(PicardTestCase):

    def test_1(self):
        record = FakeRecord(name=None, pathname='/path3/module/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '/path3/module/file')


@unittest.skipUnless(IS_WIN, "Windows test")
@patch('picard.log.picard_module_path', PureWindowsPath('C:\\path1\\path2'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('C:\\user\\picard\\plugins'))
class NameFilterTestRelWin(PicardTestCase):

    def test_1(self):
        record = FakeRecord(name=None, pathname='C:/path1/path2/module/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'module\\file')

    def test_2(self):
        record = FakeRecord(name=None, pathname='C:/path1/path2/module/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'module')

    def test_3(self):
        record = FakeRecord(name=None, pathname='C:/path1/path2/module/subpath/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'module\\subpath\\file')

    def test_4(self):
        record = FakeRecord(name=None, pathname='')
        with self.assertRaises(ValueError):
            name_filter(record)

    def test_5(self):
        record = FakeRecord(name=None, pathname='C:/path1/path2/__init__/module/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '__init__\\module')

    def test_plugin_path_long_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='C:/user/picard/plugins/path3/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\user\\picard\\plugins\\path3\\plugins\\plugin')

    def test_plugin_path_long_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='C:/user/picard/plugins/path3/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\user\\picard\\plugins\\path3\\plugins\\plugin.zip\\xxx')

    def test_plugin_path_short_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/user/picard/plugins/path3/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins\\path3\\plugins\\plugin')

    def test_plugin_path_short_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/user/picard/plugins/path3/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins\\path3\\plugins\\plugin.zip\\xxx')

    def test_plugin_path_short_3(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/user/picard/plugins/path3/plugins/myplugin.zip/myplugin.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins\\path3\\plugins\\myplugin.zip')

    def test_plugin_path_short_4(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/user/picard/plugins/path3/plugins/myplugin.zip/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, 'plugins\\path3\\plugins\\myplugin.zip')


@unittest.skipUnless(IS_WIN, "Windows test")
@patch('picard.log.picard_module_path', PureWindowsPath('C:\\picard'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('C:\\user\\picard\\plugins'))
class NameFilterTestAbsWin(PicardTestCase):

    def test_1(self):
        record = FakeRecord(name=None, pathname='C:/path/module/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path\\module\\file')

    def test_2(self):
        record = FakeRecord(name=None, pathname='C:/path/module/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path\\module')

    def test_3(self):
        record = FakeRecord(name=None, pathname='C:/path/module/subpath/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path\\module\\subpath\\file')

    def test_4(self):
        record = FakeRecord(name=None, pathname='')
        with self.assertRaises(ValueError):
            name_filter(record)

    def test_plugin_path_long_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='C:/path1/path2/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path1\\path2\\plugins\\plugin')

    def test_plugin_path_long_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        record = FakeRecord(name=None, pathname='C:/path1/path2/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path1\\path2\\plugins\\plugin.zip\\xxx')

    def test_plugin_path_short_1(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/path1/path2/plugins/plugin.zip')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path1\\path2\\plugins\\plugin')

    def test_plugin_path_short_2(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/path1/path2/plugins/plugin.zip/xxx.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path1\\path2\\plugins\\plugin.zip\\xxx')

    def test_plugin_path_short_3(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/path1/path2/plugins/myplugin.zip/myplugin.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path1\\path2\\plugins\\myplugin.zip')

    def test_plugin_path_short_4(self):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        record = FakeRecord(name=None, pathname='C:/path1/path2/plugins/myplugin.zip/__init__.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path1\\path2\\plugins\\myplugin.zip')


@unittest.skipUnless(IS_WIN, "Windows test")
@patch('picard.log.picard_module_path', PureWindowsPath('C:\\path1\\path2\\'))  # incorrect, but testing anyway
@patch('picard.log.USER_PLUGIN_DIR', PurePath('C:\\user\\picard\\plugins'))
class NameFilterTestEndingSlashWin(PicardTestCase):

    def test_1(self):
        record = FakeRecord(name=None, pathname='C:/path3/module/file.py')
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, '\\path3\\module\\file')
