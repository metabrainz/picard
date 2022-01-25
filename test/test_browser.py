# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020 Laurent Monin
# Copyright (C) 2019, 2022 Philipp Wolfer
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


from unittest.mock import patch
from urllib.parse import (
    parse_qs,
    urlparse,
)

from test.picardtestcase import PicardTestCase

from picard.browser.filelookup import FileLookup
from picard.util import webbrowser2


SERVER = 'musicbrainz.org'
PORT = 443
LOCAL_PORT = "8000"


class BrowserLookupTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.lookup = FileLookup(None, SERVER, PORT, LOCAL_PORT)

    @patch.object(webbrowser2, 'open')
    def test_entity_lookups(self, mock_open):
        lookups = {
            "recording": {'function': self.lookup.recording_lookup, 'path': 'recording'},
            "track": {'function': self.lookup.track_lookup, 'path': 'track'},
            "album": {'function': self.lookup.album_lookup, 'path': 'release'},
            "work": {'function': self.lookup.work_lookup, 'path': 'work'},
            "artist": {'function': self.lookup.artist_lookup, 'path': 'artist'},
            "albumartist": {'function': self.lookup.artist_lookup, 'path': 'artist'},
            "releasegroup": {'function': self.lookup.release_group_lookup, 'path': 'release-group'},
            "cdtoc": {'function': self.lookup.discid_lookup, 'path': 'cdtoc'},
        }
        for i, type_ in enumerate(lookups):
            lookups[type_]['function']("123")

            url = urlparse(mock_open.call_args[0][0])
            path = url.path.split('/')[1:]
            query_args = parse_qs(url.query)

            self.assertEqual(mock_open.call_count, i + 1)
            self.assertEqual(url.netloc, "%s:%s" % (SERVER, PORT))

            self.assertEqual(lookups[type_]['path'], path[0])
            self.assertEqual("123", path[1])

            self.assertIn('tport', query_args)
            self.assertEqual(query_args['tport'][0], '8000')

    @patch('picard.browser.filelookup.Disc')
    def test_mbid_lookup_cdtoc(self, mock_disc):
        url = 'https://musicbrainz.org/cdtoc/vtlGcbJUaP_IFdBUC10NGIhu2E0-'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        mock_disc.assert_called_once_with(id='vtlGcbJUaP_IFdBUC10NGIhu2E0-')
        instance = mock_disc.return_value
        instance.lookup.assert_called_once()
