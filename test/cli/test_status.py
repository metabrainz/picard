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

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.cli.status import ShellStatus
from picard.notification import (
    notifier,
    set_notifier_sink,
)


class ShellStatusTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.status = ShellStatus()

    def test_keeps_the_latest_message(self):
        self.status.set_statusbar_message('first')
        self.status.set_statusbar_message('second')
        self.assertEqual('second', self.status.latest)

    def test_named_placeholders(self):
        self.status.set_statusbar_message('Loading %(id)s', {'id': 'abc'})
        self.assertEqual('Loading abc', self.status.latest)

    def test_positional_placeholders(self):
        self.status.set_statusbar_message('%s of %s', 1, 2)
        self.assertEqual('1 of 2', self.status.latest)

    def test_placeholders_that_do_not_fit_leave_the_message_as_it_is(self):
        self.status.set_statusbar_message('Loading %(id)s', {'other': 'abc'})
        self.assertEqual('Loading %(id)s', self.status.latest)

    def test_empty_message_clears_the_status(self):
        self.status.set_statusbar_message('something')
        self.status.set_statusbar_message('')
        self.assertIsNone(self.status.latest)

    def test_reset_forgets_the_message(self):
        self.status.set_statusbar_message('something')
        self.status.reset()
        self.assertIsNone(self.status.latest)

    def test_message_is_translated_unless_disabled(self):
        translate = MagicMock(side_effect=lambda text: f'<{text}>')
        self.status.set_statusbar_message('hello', translate=translate)
        self.assertEqual('<hello>', self.status.latest)
        self.status.set_statusbar_message('hello', translate=None)
        self.assertEqual('hello', self.status.latest)

    def test_message_is_echoed_untranslated_unless_disabled(self):
        echo = MagicMock()
        self.status.set_statusbar_message('Loading %(id)s', {'id': 'x'}, echo=echo, translate=lambda text: 'other')
        echo.assert_called_once_with('Loading x')
        echo.reset_mock()
        self.status.set_statusbar_message('Loading', echo=None)
        echo.assert_not_called()

    def test_receives_the_notifications_of_the_core(self):
        set_notifier_sink(self.status)
        self.addCleanup(set_notifier_sink, None)
        notifier().status_message('Loading album %(id)s …', {'id': 'x'}, echo=None)
        self.assertEqual('Loading album x …', self.status.latest)
        notifier().set_processing(True)
        notifier().flash_busy()
