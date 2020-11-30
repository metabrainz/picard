# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020 Philipp Wolfer
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

from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.ui.mainwindow import IgnoreSelectionContext


class IgnoreSelectionContextTest(PicardTestCase):

    def test_enter_exit(self):
        context = IgnoreSelectionContext()
        self.assertFalse(context)
        with context:
            self.assertTrue(context)
        self.assertFalse(context)

    def test_run_onexit(self):
        onexit = Mock()
        context = IgnoreSelectionContext(onexit=onexit)
        with context:
            onexit.assert_not_called()
        onexit.assert_called_once_with()

    def test_nested_with(self):
        context = IgnoreSelectionContext()
        with context:
            with context:
                self.assertTrue(context)
            self.assertTrue(context)
        self.assertFalse(context)
