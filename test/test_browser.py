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

    def assert_mb_url_matches(self, url, path, query_args=None):
        parsed_url = urlparse(url)
        expected_host = SERVER
        self.assertEqual(expected_host, parsed_url.netloc, '"%s" hostname does not match "%s"' % (url, expected_host))
        self.assertEqual('https' if PORT == 443 else 'http', parsed_url.scheme)
        self.assertEqual(path, parsed_url.path, '"%s" path does not match "%s"' % (url, path))
        if query_args is not None:
            actual_query_args = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
            self.assertEqual(query_args, actual_query_args)

    def assert_mb_entity_url_matches(self, url, entity, mbid, query_args=None):
        path = '/'.join(('', entity, mbid))
        self.assert_mb_url_matches(url, path, query_args)

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
                result = case['function']("123")
                self.assertTrue(result)
                mock_open.assert_called_once()
                url = mock_open.call_args[0][0]
                query_args = {'tport': '8000'}
                self.assert_mb_entity_url_matches(url, case['entity'], '123', query_args)

    @patch.object(webbrowser2, 'open')
    def test_discid_submission(self, mock_open):
        url = 'https://testmb.org/cdtoc/attach?id=123'
        result = self.lookup.discid_submission(url)
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assertEqual('https://testmb.org/cdtoc/attach?id=123&tport=8000', url)

    @patch.object(webbrowser2, 'open')
    def test_acoustid_lookup(self, mock_open):
        result = self.lookup.acoust_lookup('123')
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assertEqual('https://acoustid.org/track/123', url)

    def test_mbid_lookup_invalid_url(self):
        self.assertFalse(self.lookup.mbid_lookup('noentity:123'))

    def test_mbid_lookup_no_entity(self):
        self.assertFalse(self.lookup.mbid_lookup('F03D09B3-39DC-4083-AFD6-159E3F0D462F'))

    @patch.object(webbrowser2, 'open')
    def test_mbid_lookup_set_type(self, mock_open):
        result = self.lookup.mbid_lookup('bd55aeb7-19d1-4607-a500-14b8479d3fed', 'place')
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assert_mb_entity_url_matches(url, 'place', 'bd55aeb7-19d1-4607-a500-14b8479d3fed')

    @patch.object(webbrowser2, 'open')
    def test_mbid_lookup_matched_callback(self, mock_open):
        mock_matched_callback = Mock()
        result = self.lookup.mbid_lookup('area:F03D09B3-39DC-4083-AFD6-159E3F0D462F', mbid_matched_callback=mock_matched_callback)
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assert_mb_entity_url_matches(url, 'area', 'f03d09b3-39dc-4083-afd6-159e3f0d462f')

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
        for entity in {'area', 'artist', 'instrument', 'label', 'place', 'series', 'url', 'work'}:
            with patch.object(webbrowser2, 'open') as mock_open:
                uri = '%s:%s' % (entity, mbid)
                result = self.lookup.mbid_lookup(uri)
                self.assertTrue(result, 'lookup failed for %s' % uri)
                mock_open.assert_called_once()
                url = mock_open.call_args[0][0]
                self.assert_mb_entity_url_matches(url, entity, mbid)

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

    @patch.object(webbrowser2, 'open')
    def test_tag_lookup(self, mock_open):
        args = {
            'artist': 'Artist',
            'release': 'Release',
            'track': 'Track',
            'tracknum': 'Tracknum',
            'duration': 'Duration',
            'filename': 'Filename',
        }
        result = self.lookup.tag_lookup(**args)
        self.assertTrue(result)
        url = mock_open.call_args[0][0]
        args['tport'] = '8000'
        self.assert_mb_url_matches(url, '/taglookup', args)

    @patch.object(webbrowser2, 'open')
    def test_collection_lookup(self, mock_open):
        result = self.lookup.collection_lookup(123)
        self.assertTrue(result)
        url = mock_open.call_args[0][0]
        self.assert_mb_url_matches(url, '/user/123/collections')

    @patch.object(webbrowser2, 'open')
    def test_search_entity(self, mock_open):
        result = self.lookup.search_entity('foo', 'search:123')
        self.assertTrue(result)
        url = mock_open.call_args[0][0]
        query_args = {
            'type': 'foo',
            'query': 'search:123',
            'limit': '25',
            'tport': '8000',
        }
        self.assert_mb_url_matches(url, '/search/textsearch', query_args)

    @patch.object(webbrowser2, 'open')
    def test_search_entity_advanced(self, mock_open):
        result = self.lookup.search_entity('foo', 'search:123', adv=True)
        self.assertTrue(result)
        url = mock_open.call_args[0][0]
        query_args = {
            'type': 'foo',
            'query': 'search:123',
            'limit': '25',
            'tport': '8000',
            'adv': 'on',
        }
        self.assert_mb_url_matches(url, '/search/textsearch', query_args)

    def test_search_entity_mbid_lookup(self):
        with patch.object(self.lookup, 'mbid_lookup') as mock_lookup:
            entity = 'artist'
            mbid = '4836aa50-a9ae-490a-983b-cfc8efca92de'
            callback = Mock()
            result = self.lookup.search_entity(entity, mbid, mbid_matched_callback=callback)
            self.assertTrue(result)
            mock_lookup.assert_called_once_with(mbid, entity, mbid_matched_callback=callback)
