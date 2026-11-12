#
# Picard, the next-generation MusicBrainz tagger
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

from types import SimpleNamespace
from urllib.parse import (
    parse_qs,
    urlparse,
)

from test.picardtestcase import PicardTestCase

from picard.browser.mburls import MusicBrainzUrls
from picard.metadata import Metadata


class MusicBrainzUrlsTest(PicardTestCase):
    def test_entity_page(self):
        urls = MusicBrainzUrls('musicbrainz.org', 443)
        self.assertEqual('https://musicbrainz.org/release/123', urls.entity('release', '123'))

    def test_port_of_the_browser_integration_is_added_only_when_there_is_one(self):
        self.assertEqual(
            'https://musicbrainz.org/artist/1', MusicBrainzUrls('musicbrainz.org', 443).entity('artist', '1')
        )
        self.assertEqual(
            'https://musicbrainz.org/artist/1?tport=8000',
            MusicBrainzUrls('musicbrainz.org', 443, 8000).entity('artist', '1'),
        )

    def test_the_parameters_given_are_not_changed(self):
        params = {'a': 'b'}
        MusicBrainzUrls('musicbrainz.org', 443, 8000).build('/x', params)
        self.assertEqual({'a': 'b'}, params)

    def test_server_of_the_configuration(self):
        self.set_config_values(setting={'server_host': 'mb.example.org', 'server_port': 8000})
        self.assertEqual('http://mb.example.org:8000/work/1', MusicBrainzUrls.from_config().entity('work', '1'))

    def test_collections_of_a_user(self):
        self.assertEqual(
            'https://musicbrainz.org/user/me/collections',
            MusicBrainzUrls('musicbrainz.org', 443).collections('me'),
        )

    def test_tag_lookup_of_an_album_like_item_uses_the_album_artist_and_no_duration(self):
        metadata = Metadata(albumartist='AA', artist='A', album='LP', title='T', tracknumber='1')
        metadata.length = 1000
        urls = MusicBrainzUrls('musicbrainz.org', 443)
        query = parse_qs(urlparse(urls.tag_lookup_item(SimpleNamespace(metadata=metadata, is_album_like=True))).query)
        self.assertEqual(['AA'], query['artist'])
        self.assertEqual([''], query.get('duration', ['']))

    def test_tag_lookup_of_a_file_uses_the_artist_the_duration_and_the_name_of_the_file(self):
        metadata = Metadata(albumartist='AA', artist='A', album='LP', title='T', tracknumber='1')
        metadata.length = 1000
        item = SimpleNamespace(metadata=metadata, is_album_like=False, filename='/d/a.flac')
        urls = MusicBrainzUrls('musicbrainz.org', 443)
        query = parse_qs(urlparse(urls.tag_lookup_item(item)).query)
        self.assertEqual(['A'], query['artist'])
        self.assertEqual(['1000'], query['duration'])
        self.assertEqual(['a.flac'], query['filename'])
