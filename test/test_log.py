# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021, 2024 Philipp Wolfer
# Copyright (C) 2021-2022, 2024-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections import deque
from dataclasses import dataclass
from pathlib import (
    PurePath,
    PureWindowsPath,
)
import unittest
from unittest.mock import patch

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

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


class NameFilterTestCase(PicardTestCase):
    """Shared helpers for `name_filter` tests.

    `DebugOpt` keeps enabled options in a registry shared by the whole
    process. Each test gets a fresh one so that setting `PLUGIN_FULLPATH`
    cannot leak into tests that do not set it themselves.
    """

    def setUp(self):
        super().setUp()
        original_registry = DebugOpt.get_registry()
        DebugOpt.set_registry(set())
        self.addCleanup(DebugOpt.set_registry, original_registry)

    def assert_record_name(self, pathname, expected_name):
        record = FakeRecord(name=None, pathname=pathname)
        self.assertTrue(name_filter(record))
        self.assertEqual(record.name, expected_name)

    def assert_empty_pathname_raises(self):
        record = FakeRecord(name=None, pathname='')
        with self.assertRaises(ValueError):
            name_filter(record)


@unittest.skipIf(IS_WIN, "Posix test")
@patch('picard.log.picard_module_path', PurePath('/path1/path2'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('/user/picard/plugins'))
class NameFilterTestRel(NameFilterTestCase):
    @subtest_cases(
        "pathname,expected_name",
        [
            ('/path1/path2/module/file.py', 'module/file'),
            ('/path1/path2/module/__init__.py', 'module'),
            ('/path1/path2/module/subpath/file.py', 'module/subpath/file'),
            ('/path1/path2/__init__/module/__init__.py', '__init__/module'),
        ],
    )
    def test_module_paths(self, pathname, expected_name):
        self.assert_record_name(pathname, expected_name)

    def test_empty_pathname(self):
        self.assert_empty_pathname_raises()

    @subtest_cases(
        "pathname,expected_name",
        [
            ('/user/picard/plugins/plugin.zip', '/user/picard/plugins/plugin'),
            ('/user/picard/plugins/plugin.zip/xxx.py', '/user/picard/plugins/plugin.zip/xxx'),
        ],
    )
    def test_plugin_paths_fullpath(self, pathname, expected_name):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        self.assert_record_name(pathname, expected_name)

    @subtest_cases(
        "pathname,expected_name",
        [
            ('/user/picard/plugins/plugin.zip', 'plugins/plugin'),
            ('/user/picard/plugins/plugin.zip/xxx.py', 'plugins/plugin.zip/xxx'),
            ('/user/picard/plugins/myplugin.zip/myplugin.py', 'plugins/myplugin.zip'),
            ('/user/picard/plugins/myplugin.zip/__init__.py', 'plugins/myplugin.zip'),
        ],
    )
    def test_plugin_paths_short(self, pathname, expected_name):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        self.assert_record_name(pathname, expected_name)


@unittest.skipIf(IS_WIN, "Posix test")
@patch('picard.log.picard_module_path', PurePath('/picard'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('/user/picard/plugins/'))
class NameFilterTestAbs(NameFilterTestCase):
    @subtest_cases(
        "pathname,expected_name",
        [
            ('/path/module/file.py', '/path/module/file'),
            ('/path/module/__init__.py', '/path/module'),
            ('/path/module/subpath/file.py', '/path/module/subpath/file'),
        ],
    )
    def test_module_paths(self, pathname, expected_name):
        self.assert_record_name(pathname, expected_name)

    def test_empty_pathname(self):
        self.assert_empty_pathname_raises()

    @subtest_cases(
        "pathname,expected_name",
        [
            ('/path1/path2/plugins/plugin.zip', '/path1/path2/plugins/plugin'),
            ('/path1/path2/plugins/plugin.zip/xxx.py', '/path1/path2/plugins/plugin.zip/xxx'),
            ('/path1/path2/plugins/plugin.zip/__init__.py', '/path1/path2/plugins/plugin.zip'),
        ],
    )
    def test_plugin_paths_fullpath(self, pathname, expected_name):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        self.assert_record_name(pathname, expected_name)

    @subtest_cases(
        "pathname,expected_name",
        [
            ('/path1/path2/plugins/plugin.zip', '/path1/path2/plugins/plugin'),
            ('/path1/path2/plugins/plugin.zip/xxx.py', '/path1/path2/plugins/plugin.zip/xxx'),
            ('/path1/path2/plugins/myplugin.zip/myplugin.py', '/path1/path2/plugins/myplugin.zip'),
            ('/path1/path2/plugins/myplugin.zip/__init__.py', '/path1/path2/plugins/myplugin.zip'),
        ],
    )
    def test_plugin_paths_short(self, pathname, expected_name):
        # These paths are outside USER_PLUGIN_DIR, so PLUGIN_FULLPATH has no effect
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        self.assert_record_name(pathname, expected_name)


@unittest.skipIf(IS_WIN, "Posix test")
@patch('picard.log.picard_module_path', PurePath('/path1/path2/'))  # incorrect, but testing anyway
@patch('picard.log.USER_PLUGIN_DIR', PurePath('/user/picard/plugins'))
class NameFilterTestEndingSlash(NameFilterTestCase):
    def test_module_path(self):
        self.assert_record_name('/path3/module/file.py', '/path3/module/file')


@unittest.skipUnless(IS_WIN, "Windows test")
@patch('picard.log.picard_module_path', PureWindowsPath('C:\\path1\\path2'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('C:\\user\\picard\\plugins'))
class NameFilterTestRelWin(NameFilterTestCase):
    @subtest_cases(
        "pathname,expected_name",
        [
            ('C:/path1/path2/module/file.py', 'module\\file'),
            ('C:/path1/path2/module/__init__.py', 'module'),
            ('C:/path1/path2/module/subpath/file.py', 'module\\subpath\\file'),
            ('C:/path1/path2/__init__/module/__init__.py', '__init__\\module'),
        ],
    )
    def test_module_paths(self, pathname, expected_name):
        self.assert_record_name(pathname, expected_name)

    def test_empty_pathname(self):
        self.assert_empty_pathname_raises()

    @subtest_cases(
        "pathname,expected_name",
        [
            ('C:/user/picard/plugins/path3/plugins/plugin.zip', '\\user\\picard\\plugins\\path3\\plugins\\plugin'),
            (
                'C:/user/picard/plugins/path3/plugins/plugin.zip/xxx.py',
                '\\user\\picard\\plugins\\path3\\plugins\\plugin.zip\\xxx',
            ),
        ],
    )
    def test_plugin_paths_fullpath(self, pathname, expected_name):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        self.assert_record_name(pathname, expected_name)

    @subtest_cases(
        "pathname,expected_name",
        [
            ('C:/user/picard/plugins/path3/plugins/plugin.zip', 'plugins\\path3\\plugins\\plugin'),
            ('C:/user/picard/plugins/path3/plugins/plugin.zip/xxx.py', 'plugins\\path3\\plugins\\plugin.zip\\xxx'),
            ('C:/user/picard/plugins/path3/plugins/myplugin.zip/myplugin.py', 'plugins\\path3\\plugins\\myplugin.zip'),
            ('C:/user/picard/plugins/path3/plugins/myplugin.zip/__init__.py', 'plugins\\path3\\plugins\\myplugin.zip'),
        ],
    )
    def test_plugin_paths_short(self, pathname, expected_name):
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        self.assert_record_name(pathname, expected_name)


@unittest.skipUnless(IS_WIN, "Windows test")
@patch('picard.log.picard_module_path', PureWindowsPath('C:\\picard'))
@patch('picard.log.USER_PLUGIN_DIR', PurePath('C:\\user\\picard\\plugins'))
class NameFilterTestAbsWin(NameFilterTestCase):
    @subtest_cases(
        "pathname,expected_name",
        [
            ('C:/path/module/file.py', '\\path\\module\\file'),
            ('C:/path/module/__init__.py', '\\path\\module'),
            ('C:/path/module/subpath/file.py', '\\path\\module\\subpath\\file'),
        ],
    )
    def test_module_paths(self, pathname, expected_name):
        self.assert_record_name(pathname, expected_name)

    def test_empty_pathname(self):
        self.assert_empty_pathname_raises()

    @subtest_cases(
        "pathname,expected_name",
        [
            ('C:/path1/path2/plugins/plugin.zip', '\\path1\\path2\\plugins\\plugin'),
            ('C:/path1/path2/plugins/plugin.zip/xxx.py', '\\path1\\path2\\plugins\\plugin.zip\\xxx'),
        ],
    )
    def test_plugin_paths_fullpath(self, pathname, expected_name):
        DebugOpt.PLUGIN_FULLPATH.enabled = True
        self.assert_record_name(pathname, expected_name)

    @subtest_cases(
        "pathname,expected_name",
        [
            ('C:/path1/path2/plugins/plugin.zip', '\\path1\\path2\\plugins\\plugin'),
            ('C:/path1/path2/plugins/plugin.zip/xxx.py', '\\path1\\path2\\plugins\\plugin.zip\\xxx'),
            ('C:/path1/path2/plugins/myplugin.zip/myplugin.py', '\\path1\\path2\\plugins\\myplugin.zip'),
            ('C:/path1/path2/plugins/myplugin.zip/__init__.py', '\\path1\\path2\\plugins\\myplugin.zip'),
        ],
    )
    def test_plugin_paths_short(self, pathname, expected_name):
        # These paths are outside USER_PLUGIN_DIR, so PLUGIN_FULLPATH has no effect
        DebugOpt.PLUGIN_FULLPATH.enabled = False
        self.assert_record_name(pathname, expected_name)


@unittest.skipUnless(IS_WIN, "Windows test")
@patch('picard.log.picard_module_path', PureWindowsPath('C:\\path1\\path2\\'))  # incorrect, but testing anyway
@patch('picard.log.USER_PLUGIN_DIR', PurePath('C:\\user\\picard\\plugins'))
class NameFilterTestEndingSlashWin(NameFilterTestCase):
    def test_module_path(self):
        self.assert_record_name('C:/path3/module/file.py', '\\path3\\module\\file')


class StateChangeLoggerTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        from picard.log import StateChangeLogger

        self.logged_messages = []
        self.logger = StateChangeLogger(
            lambda msg, **kwargs: self.logged_messages.append(msg),
            {
                True: "Enabled",
                False: "Disabled",
            },
        )

    def test_first_update_logs(self):
        changed = self.logger.update(False)
        self.assertTrue(changed)
        self.assertEqual(self.logged_messages, ["Disabled"])

    def test_same_value_does_not_log(self):
        self.logger.update(False)
        self.logged_messages.clear()
        changed = self.logger.update(False)
        self.assertFalse(changed)
        self.assertEqual(self.logged_messages, [])

    def test_change_logs_new_message(self):
        self.logger.update(False)
        self.logged_messages.clear()
        changed = self.logger.update(True)
        self.assertTrue(changed)
        self.assertEqual(self.logged_messages, ["Enabled"])

    def test_multiple_changes(self):
        self.logger.update(False)
        self.logger.update(True)
        self.logger.update(True)
        self.logger.update(False)
        self.assertEqual(self.logged_messages, ["Disabled", "Enabled", "Disabled"])

    def test_value_not_in_messages_is_silent(self):
        from picard.log import StateChangeLogger

        logger = StateChangeLogger(
            lambda msg, **kwargs: self.logged_messages.append(msg),
            {True: "On"},
        )
        changed = logger.update(False)
        self.assertTrue(changed)
        self.assertEqual(self.logged_messages, [])

    def test_callable_messages(self):
        from picard.log import StateChangeLogger

        logger = StateChangeLogger(
            lambda msg, **kwargs: self.logged_messages.append(msg),
            lambda v: "Value is %s" % v,
        )
        logger.update("hello")
        logger.update("hello")
        logger.update("world")
        self.assertEqual(self.logged_messages, ["Value is hello", "Value is world"])

    def test_callable_messages_returns_none(self):
        from picard.log import StateChangeLogger

        logger = StateChangeLogger(
            lambda msg, **kwargs: self.logged_messages.append(msg),
            lambda v: "Set to %s" % v if v else None,
        )
        changed = logger.update("")
        self.assertTrue(changed)
        self.assertEqual(self.logged_messages, [])
