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


from unittest.mock import (
    Mock,
    patch,
)
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

    def assert_mbid_url_matches(self, url, entity, mbid, expected_query_args=None):
        url = urlparse(url)
        path = url.path.split('/')[1:]
        query_args = parse_qs(url.query)

        self.assertEqual(url.netloc, "%s:%s" % (SERVER, PORT))

        self.assertEqual(entity, path[0])
        self.assertEqual(mbid, path[1])

        if expected_query_args:
            for key, value in expected_query_args.items():
                self.assertIn(key, query_args)
                self.assertEqual(value, query_args['tport'][0])


    def test_entity_lookups(self):
        lookups = (
            {'function': self.lookup.recording_lookup, 'entity': 'recording'},
            {'function': self.lookup.track_lookup, 'entity': 'track'},
            {'function': self.lookup.album_lookup, 'entity': 'release'},
            {'function': self.lookup.work_lookup, 'entity': 'work'},
            {'function': self.lookup.artist_lookup, 'entity': 'artist'},
            {'function': self.lookup.artist_lookup, 'entity': 'artist'},
            {'function': self.lookup.release_group_lookup, 'entity': 'release-group'},
            {'function': self.lookup.discid_lookup, 'entity': 'cdtoc'},
        )
        for case in lookups:
            with patch.object(webbrowser2, 'open') as mock_open:
                case['function']("123")
                mock_open.assert_called_once()
                url = mock_open.call_args[0][0]
                query_args = {'tport': '8000'}
                self.assert_mbid_url_matches(url, case['entity'], '123', query_args)

    def test_mbid_lookup_invalid_url(self):
        self.assertFalse(self.lookup.mbid_lookup('noentity:123'))

    def test_mbid_lookup_no_entity(self):
        self.assertFalse(self.lookup.mbid_lookup('F03D09B3-39DC-4083-AFD6-159E3F0D462F'))

    @patch.object(webbrowser2, 'open')
    def test_mbid_lookup_set_type(self, mock_open):
        result = self.lookup.mbid_lookup('bd55aeb7-19d1-4607-a500-14b8479d3fed', 'place')
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args.args[0]
        self.assert_mbid_url_matches(url, 'place', 'bd55aeb7-19d1-4607-a500-14b8479d3fed')

    @patch.object(webbrowser2, 'open')
    def test_mbid_lookup_matched_callback(self, mock_open):
        mock_matched_callback = Mock()
        result = self.lookup.mbid_lookup('area:F03D09B3-39DC-4083-AFD6-159E3F0D462F', mbid_matched_callback=mock_matched_callback)
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args.args[0]
        self.assert_mbid_url_matches(url, 'area', 'f03d09b3-39dc-4083-afd6-159e3f0d462f')

    @patch('PyQt5.QtCore.QObject.tagger')
    def test_mbid_lookup_release(self, mock_tagger):
        url = 'https://musicbrainz.org/release/60dbf818-3058-41b9-bb53-25dbdb9d9bad'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        mock_tagger.load_album.assert_called_once_with('60dbf818-3058-41b9-bb53-25dbdb9d9bad')

    @patch('PyQt5.QtCore.QObject.tagger')
    def test_mbid_lookup_recording(self, mock_tagger):
        url = 'https://musicbrainz.org/recording/511f3a33-ded8-4dc7-92d2-b913ec420dfc'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        mock_tagger.load_nat.assert_called_once_with('511f3a33-ded8-4dc7-92d2-b913ec420dfc')

    @patch('PyQt5.QtCore.QObject.tagger')
    @patch('picard.browser.filelookup.AlbumSearchDialog')
    def test_mbid_lookup_release_group(self, mock_dialog, mock_tagger):
        url = 'https://musicbrainz.org/release-group/168615bf-f841-49f7-ac98-36a4eb25479c'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        mock_dialog.assert_called_once_with(mock_tagger.window, force_advanced_search=True)
        instance = mock_dialog.return_value
        instance.search.assert_called_once_with('rgid:168615bf-f841-49f7-ac98-36a4eb25479c')
        instance.exec_.assert_called_once()

    def test_mbid_lookup_browser_fallback(self):
        mbid = '4836aa50-a9ae-490a-983b-cfc8efca92de'
        for entity in {'area', 'artist', 'label', 'url', 'work'}:
            with patch.object(webbrowser2, 'open') as mock_open:
                uri = '%s:%s' % (entity, mbid)
                result = self.lookup.mbid_lookup(uri)
                self.assertTrue(result, 'lookup failed for %s' % uri)
                mock_open.assert_called_once()
                url = mock_open.call_args.args[0]
                self.assert_mbid_url_matches(url, entity, mbid)

    @patch.object(webbrowser2, 'open')
    def test_mbid_lookup_browser_fallback_disabled(self, mock_open):
        url = 'https://musicbrainz.org/artist/4836aa50-a9ae-490a-983b-cfc8efca92de'
        result = self.lookup.mbid_lookup(url, browser_fallback=False)
        self.assertFalse(result)
        mock_open.assert_not_called()

    @patch('picard.browser.filelookup.Disc')
    def test_mbid_lookup_cdtoc(self, mock_disc):
        url = 'https://musicbrainz.org/cdtoc/vtlGcbJUaP_IFdBUC10NGIhu2E0-'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        mock_disc.assert_called_once_with(id='vtlGcbJUaP_IFdBUC10NGIhu2E0-')
        instance = mock_disc.return_value
        instance.lookup.assert_called_once()
