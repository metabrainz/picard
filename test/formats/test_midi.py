# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
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


from picard.formats import midi

from .common import (
    TAGS,
    CommonTests,
)


class MIDITest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.mid'
    expected_info = {
        'length': 127997,
        '~format': 'Standard MIDI File'
    }
    unexpected_info = ['~video']

    def test_supports_tag(self):
        for tag in TAGS:
            self.assertFalse(midi.MIDIFile.supports_tag(tag))
