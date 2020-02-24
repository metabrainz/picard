# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018, 2020 Laurent Monin
# Copyright (C) 2014 Michael Wiencek
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Wieland Hoffmann
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


import os.path

from test.picardtestcase import (
    PicardTestCase,
    load_test_json,
)

from picard import config
from picard.i18n import setup_gettext
from picard.releasegroup import ReleaseGroup


settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": False
}


class ReleaseTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        # we are using temporary locales for tests
        self.tmp_path = self.mktmpdir()
        self.localedir = os.path.join(self.tmp_path, 'locale')
        setup_gettext(self.localedir, 'C')

    def test_1(self):
        config.setting = settings.copy()
        rlist = load_test_json('release_group_2.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Jewel Case / special')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / special')
        self.assertEqual(r.versions[2]['name'],
                         '5 / 2009 / GB / CD / label A / cat 123 / Digipak / specialx')

    def test_2(self):
        config.setting = settings.copy()
        rlist = load_test_json('release_group_3.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123 / special A')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2011 / FR / CD / label A / cat 123')

    def test_3(self):
        config.setting = settings.copy()
        rlist = load_test_json('release_group_4.json')
        r = ReleaseGroup(1)
        r._parse_versions(rlist)
        self.assertEqual(r.versions[0]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / 0123456789')
        self.assertEqual(r.versions[1]['name'],
                         '5 / 2009 / FR / CD / label A / cat 123 / [no barcode]')
