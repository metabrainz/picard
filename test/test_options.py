# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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

from picard.config import Option
from picard.i18n import N_
from picard.options import get_option_title


class OptionsUtilitiesTest(PicardTestCase):

    def test_option_titles(self):
        # Add test option settings
        if ('setting', 'test_option_with_title') not in Option.registry:
            Option('setting', 'test_option_with_title', None, title=N_('Test option with title'))
        if ('setting', 'test_option_without_title') not in Option.registry:
            Option('setting', 'test_option_without_title', None)

        # Invalid option name
        self.assertEqual(get_option_title('invalid_option'), None)

        # No title assigned to the option
        self.assertEqual(get_option_title('test_option_without_title'), "No title for setting 'test_option_without_title'")

        # Title assigned to the option
        self.assertEqual(get_option_title('test_option_with_title'), 'Test option with title')
