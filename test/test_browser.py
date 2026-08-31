# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2022, 2025-2026 Laurent Monin
# Copyright (C) 2019, 2022, 2024-2025 Philipp Wolfer
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


from io import BytesIO
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)
from urllib.parse import (
    parse_qs,
    urlparse,
)

from test.picardtestcase import PicardTestCase

from picard.browser.filelookup import FileLookup
from picard.browser.server import (
    RequestHandler,
    clean_header,
)
from picard.const import METABRAINZ_OAUTH_SCOPES
from picard.oauth import OAuthInvalidStateError
from picard.util import webbrowser2


SERVER = 'musicbrainz.org'
PORT = 443
LOCAL_PORT = "8000"


class BrowserLookupTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.browser.filelookup')
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
        result = self.lookup.mbid_lookup(
            'area:F03D09B3-39DC-4083-AFD6-159E3F0D462F', mbid_matched_callback=mock_matched_callback
        )
        self.assertTrue(result)
        mock_open.assert_called_once()
        url = mock_open.call_args[0][0]
        self.assert_mb_entity_url_matches(url, 'area', 'f03d09b3-39dc-4083-afd6-159e3f0d462f')

    def test_mbid_lookup_release(self):
        self.tagger.load_album = MagicMock()
        url = 'https://musicbrainz.org/release/60dbf818-3058-41b9-bb53-25dbdb9d9bad'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        self.tagger.load_album.assert_called_once_with('60dbf818-3058-41b9-bb53-25dbdb9d9bad')

    def test_mbid_lookup_recording(self):
        self.tagger.load_nat = MagicMock()
        url = 'https://musicbrainz.org/recording/511f3a33-ded8-4dc7-92d2-b913ec420dfc'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        self.tagger.load_nat.assert_called_once_with('511f3a33-ded8-4dc7-92d2-b913ec420dfc')

    @patch('picard.browser.filelookup.AlbumSearchDialog')
    def test_mbid_lookup_release_group(self, mock_dialog):
        url = 'https://musicbrainz.org/release-group/168615bf-f841-49f7-ac98-36a4eb25479c'
        result = self.lookup.mbid_lookup(url)
        self.assertTrue(result)
        mock_dialog.show_releasegroup_search.assert_called_once_with('168615bf-f841-49f7-ac98-36a4eb25479c')

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
        self.set_config_values({'query_limit': 25})
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
        self.set_config_values({'query_limit': 25})
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

    @patch.object(webbrowser2, 'open')
    def test_search_entity_mbid_lookup_force_browser(self, mock_open):
        self.set_config_values({'query_limit': 25})
        with patch.object(self.lookup, 'mbid_lookup') as mock_lookup:
            entity = 'artist'
            mbid = '4836aa50-a9ae-490a-983b-cfc8efca92de'
            callback = Mock()
            result = self.lookup.search_entity(entity, mbid, mbid_matched_callback=callback, force_browser=True)
            self.assertTrue(result)
            mock_lookup.assert_not_called()
            url = mock_open.call_args[0][0]
            query_args = {
                'type': entity,
                'query': mbid,
                'limit': '25',
                'tport': '8000',
            }
            self.assert_mb_url_matches(url, '/search/textsearch', query_args)


class BrowserIntegrationTest(PicardTestCase):
    def test_clean_header(self):
        bad_header = "foo\nSome-Header: bar"
        self.assertEqual("fooSome-Header bar", clean_header(bad_header))


class RequestHandlerAuthTest(PicardTestCase):
    """Tests for PICARD-3398: Pending request stuck if authentication gets cancelled."""

    def setUp(self):
        super().setUp()
        self.set_config_values({'server_host': 'musicbrainz.org'})
        self.callback = MagicMock()
        self.oauth_manager = MagicMock()
        self.oauth_manager.verify_state.return_value = self.callback
        self.tagger.webservice.oauth_manager = self.oauth_manager
        self.patch_tagger_instance('picard.browser.server')

    def _make_handler(self, path):
        """Create a RequestHandler instance without starting a real HTTP server."""
        handler = RequestHandler.__new__(RequestHandler)
        handler.server_version = 'Test'
        handler.sys_version = ''
        handler.path = path
        handler.headers = {'origin': None}
        handler.wfile = BytesIO()
        handler.requestline = f'GET {path} HTTP/1.1'
        handler.command = 'GET'
        handler.request_version = 'HTTP/1.1'
        handler.responses = {}
        handler.client_address = ('127.0.0.1', 0)
        return handler

    @patch('picard.browser.server.to_main')
    def test_auth_cancelled_calls_callback(self, mock_to_main):
        """When auth is cancelled (error=access_denied), the callback should be
        called with successful=False so pending requests are released."""
        handler = self._make_handler('/auth?error=access_denied&state=valid_state')

        handler._handle_get()

        self.oauth_manager.verify_state.assert_called_once_with('valid_state')
        mock_to_main.assert_called_once_with(self.callback, successful=False, error_msg='access_denied')
        response = handler.wfile.getvalue()
        self.assertIn(b'Authentication cancelled', response)
        self.assertIn(b'<!doctype html>', response)

    @patch('picard.browser.server.to_main')
    def test_auth_cancelled_with_error_description(self, mock_to_main):
        """When auth error includes error_description, it should be in the callback."""
        handler = self._make_handler(
            '/auth?error=access_denied&error_description=The+user+denied+the+request&state=valid_state'
        )

        handler._handle_get()

        mock_to_main.assert_called_once_with(self.callback, successful=False, error_msg='The user denied the request')

    @patch('picard.browser.server.to_main')
    def test_auth_success_still_works(self, mock_to_main):
        """Ensure normal auth success flow is not broken."""
        handler = self._make_handler('/auth?code=auth_code_123&state=valid_state')

        handler._handle_get()

        self.oauth_manager.verify_state.assert_called_once_with('valid_state')
        mock_to_main.assert_called_once()
        self.callback.assert_not_called()
        # The code exchange must request the same prefixed scopes as the
        # authorization request; a mismatch yields a token without the
        # expected permissions (e.g. collection access fails with 401).
        self.assertEqual(mock_to_main.call_args.kwargs['scopes'], METABRAINZ_OAUTH_SCOPES)
        self.assertIn('musicbrainz:collection', mock_to_main.call_args.kwargs['scopes'])
        response = handler.wfile.getvalue()
        self.assertIn(b'Authentication successful', response)
        self.assertIn(b'<!doctype html>', response)

    def test_auth_invalid_state(self):
        """An invalid state should return 400 regardless of code or error."""
        self.oauth_manager.verify_state.side_effect = OAuthInvalidStateError()
        for path in (
            '/auth?code=auth_code_123&state=bad',
            '/auth?error=access_denied&state=bad',
        ):
            with self.subTest(path=path):
                self.oauth_manager.verify_state.reset_mock()
                handler = self._make_handler(path)

                handler._handle_get()

                self.oauth_manager.verify_state.assert_called_once_with('bad')
                self.callback.assert_not_called()
                response = handler.wfile.getvalue()
                self.assertIn(b'400', response)
                self.assertIn(b'<!doctype html>', response)
                self.assertIn(b'Authentication error', response)

    def test_auth_no_code_no_error(self):
        """When auth has neither code nor error, return 400 with a styled page."""
        handler = self._make_handler('/auth?state=valid_state')

        handler._handle_get()

        response = handler.wfile.getvalue()
        self.assertIn(b'400', response)
        self.assertIn(b'<!doctype html>', response)
        self.assertIn(b'Authentication error', response)

    def test_favicon_serves_svg_logo(self):
        """The browser's implicit /favicon.ico request is served the Picard logo."""
        handler = self._make_handler('/favicon.ico')

        handler._handle_get()

        response = handler.wfile.getvalue()
        self.assertIn(b'200', response)
        self.assertIn(b'image/svg+xml', response)
        self.assertIn(b'<svg', response)
