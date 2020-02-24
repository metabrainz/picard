# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Philipp Wolfer
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


from .common import (
    REPLAYGAIN_TAGS,
    TAGS,
    CommonTests,
    skipUnlessTestfile,
)


class WAVTest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.wav'
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }
    unexpected_info = ['~video']

    def setUp(self):
        super().setUp()
        self.unsupported_tags = {**TAGS, **REPLAYGAIN_TAGS}

    @skipUnlessTestfile
    def test_unsupported_tags(self):
        self._test_unsupported_tags(self.unsupported_tags)
