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

from unittest.mock import patch
from urllib.parse import (
    parse_qs,
    urlparse,
)
import webbrowser

from test.cli.engine.helpers import EngineCommandTestCase
from test.cli.engine.test_metadata_edit_command import _file

from picard.album import (
    Album,
    NatAlbum,
)
from picard.cluster import Cluster
from picard.track import Track


_RELEASE = '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d'
_RECORDING = '2a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d'


class _BrowseTestCase(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values(setting={'server_host': 'musicbrainz.org', 'server_port': 443})

    def _url(self, line):
        result = self.run_command(line)
        self.assertTrue(result.ok, result.error)
        (item,) = result.items
        return item.data.get('url')


class UrlCommandTest(_BrowseTestCase):
    def test_album_has_the_page_of_its_release(self):
        self.wks.albums[_RELEASE] = Album(_RELEASE)
        self.run_command('ls')
        self.assertEqual(f'https://musicbrainz.org/release/{_RELEASE}', self._url('url a1'))

    def test_server_of_the_configuration_is_used(self):
        self.set_config_values(setting={'server_host': 'mb.example.org', 'server_port': 8000})
        self.wks.albums[_RELEASE] = Album(_RELEASE)
        self.run_command('ls')
        self.assertEqual(f'http://mb.example.org:8000/release/{_RELEASE}', self._url('url a1'))

    def test_no_port_of_the_browser_integration_is_added(self):
        self.wks.albums[_RELEASE] = Album(_RELEASE)
        self.run_command('ls')
        self.assertNotIn('tport', self._url('url a1'))

    def test_matched_file_has_the_page_of_its_recording(self):
        _file(self.wks, 'a.flac', {'musicbrainz_recordingid': _RECORDING})
        self.run_command('ls')
        self.assertEqual(f'https://musicbrainz.org/recording/{_RECORDING}', self._url('url f1'))

    def test_file_that_is_not_matched_has_the_tag_lookup(self):
        _file(self.wks, 'dir/a.flac', {'artist': 'Band', 'album': 'LP', 'title': 'Song', 'tracknumber': '3'})
        self.run_command('ls')
        parsed = urlparse(self._url('url f1'))
        self.assertEqual('/taglookup', parsed.path)
        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        self.assertEqual(
            {'artist': 'Band', 'release': 'LP', 'track': 'Song', 'tracknum': '3', 'filename': 'a.flac'},
            {key: query[key] for key in ('artist', 'release', 'track', 'tracknum', 'filename')},
        )

    def test_cluster_has_the_tag_lookup(self):
        cluster = Cluster('Some Album', 'Some Artist')
        cluster.add_files([_file(self.wks, 'a.flac')])
        self.wks.clusters.append(cluster)
        self.run_command('ls')
        parsed = urlparse(self._url('url c1'))
        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        self.assertEqual('/taglookup', parsed.path)
        self.assertEqual(('Some Artist', 'Some Album'), (query['artist'], query['release']))

    def test_what_has_no_page_is_unsupported(self):
        self.wks.albums['nats'] = NatAlbum()
        self.run_command('ls')
        result = self.run_command('url a1')
        self.assertEqual(['unsupported'], [item.status for item in result.items])
        self.assertNotIn('url', result.items[0].data)

    def test_track_has_the_page_of_its_recording(self):
        album = Album(_RELEASE)
        track = Track(_RECORDING, album)
        album.tracks.append(track)
        self.wks.albums[_RELEASE] = album
        self.run_command('ls')
        handle = self.session.handle_for(track)
        self.assertEqual(f'https://musicbrainz.org/recording/{_RECORDING}', self._url(f'url {handle}'))

    def test_musicbrainz_references_are_accepted(self):
        for text in (f'release:{_RELEASE}', f'https://musicbrainz.org/release/{_RELEASE}'):
            with self.subTest(text=text):
                self.assertEqual(f'https://musicbrainz.org/release/{_RELEASE}', self._url(f'url {text}'))

    def test_several_targets_in_order(self):
        self.wks.albums[_RELEASE] = Album(_RELEASE)
        self.run_command('ls')
        result = self.run_command(f'url a1 recording:{_RECORDING}')
        self.assertEqual(
            [f'https://musicbrainz.org/recording/{_RECORDING}', f'https://musicbrainz.org/release/{_RELEASE}'],
            sorted(item.data['url'] for item in result.items),
        )

    def test_unresolved_is_reported(self):
        self.assertEqual(['a9'], self.run_command('url a9').unresolved)

    def test_usage(self):
        result = self.run_command('url')
        self.assertFalse(result.ok)
        self.assertIn('usage', result.error)


class OpenCommandTest(_BrowseTestCase):
    def setUp(self):
        super().setUp()
        self.wks.albums[_RELEASE] = Album(_RELEASE)
        self.run_command('ls')
        patcher = patch('picard.cli.engine.builtins.browse.webbrowser.open', return_value=True)
        self.open = patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_page_is_opened(self):
        result = self.run_command('open a1')
        self.open.assert_called_once_with(f'https://musicbrainz.org/release/{_RELEASE}')
        self.assertEqual(['opened'], [item.status for item in result.items])
        self.assertEqual('', result.message)

    def test_a_browser_that_cannot_be_started_is_reported(self):
        for failure in ({'return_value': False}, {'side_effect': webbrowser.Error('no browser')}):
            with self.subTest(failure=failure):
                self.open.configure_mock(**{'return_value': True, 'side_effect': None})
                self.open.configure_mock(**failure)
                result = self.run_command('open a1')
                self.assertTrue(result.ok)
                self.assertEqual(['open_failed'], [item.status for item in result.items])
                self.assertIn('no web browser', result.message)
                self.assertIn(_RELEASE, result.items[0].data['url'])

    def test_what_has_no_page_is_not_opened(self):
        self.wks.albums['nats'] = NatAlbum()
        self.run_command('ls')
        result = self.run_command('open a2')
        self.assertEqual(['unsupported'], [item.status for item in result.items])
        self.open.assert_not_called()

    def test_too_many_pages_are_refused(self):
        refs = ' '.join(f'recording:{n:08x}-5e6f-7a8b-9c0d-1e2f3a4b5c6d' for n in range(6))
        result = self.run_command(f'open {refs}')
        self.assertFalse(result.ok)
        self.assertIn('at most 5', result.error)
        self.open.assert_not_called()

    def test_five_pages_are_opened(self):
        refs = ' '.join(f'recording:{n:08x}-5e6f-7a8b-9c0d-1e2f3a4b5c6d' for n in range(5))
        result = self.run_command(f'open {refs}')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(5, self.open.call_count)

    def test_usage(self):
        self.assertFalse(self.run_command('open').ok)
        self.open.assert_not_called()
