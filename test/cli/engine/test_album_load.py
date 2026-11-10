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

from unittest.mock import (
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

from picard.album import Album
from picard.cli.engine.dispatch import dispatch
from picard.workspace import workspace


_MBID = '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d'


class AlbumLoadCommandTest(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self._loaded = []

        def fake_load_album(mbid, **kwargs):
            album = Album(mbid)
            self._loaded.append(mbid)
            workspace().albums[mbid] = album
            return album

        p = patch.object(workspace(), 'load_album', side_effect=fake_load_album)
        p.start()
        self.addCleanup(p.stop)

    def test_load_by_mbid_mints_album(self):
        result = dispatch(self.session, self.reg, f'album load {_MBID}')
        self.assertTrue(result.ok)
        self.assertEqual([_MBID], self._loaded)
        self.assertEqual(1, len(result.mints))
        self.assertTrue(result.mints[0].startswith('a'))
        self.assertEqual('loaded', result.items[0].status)

    def test_load_by_url(self):
        result = dispatch(self.session, self.reg, f'album load https://musicbrainz.org/release/{_MBID}')
        self.assertTrue(result.ok)
        self.assertEqual([_MBID], self._loaded)

    def test_accepted_spellings(self):
        for text in (
            _MBID,
            f'release:{_MBID}',  # the form shown by `ls` / `tree` round-trips
            f'mbid://{_MBID}',
            f'https://musicbrainz.org/release/{_MBID}',
            f'https://musicbrainz.org/release/{_MBID}/',
            f'https://musicbrainz.org/release/{_MBID}/cover-art',
        ):
            with self.subTest(text=text):
                self._loaded.clear()
                workspace().albums.clear()
                result = dispatch(self.session, self.reg, f'album load {text}')
                self.assertTrue(result.ok, result.error)
                self.assertEqual([_MBID], self._loaded)

    def test_rejected_spellings(self):
        for text in ('nope', 'release:not-an-mbid', 'https://example.com/foo'):
            with self.subTest(text=text):
                result = dispatch(self.session, self.reg, f'album load {text}')
                self.assertFalse(result.ok)
                self.assertIn('not a release MBID or URL', result.error)
        self.assertEqual([], self._loaded)

    def test_other_entities_are_not_loaded_as_releases(self):
        for entity in ('artist', 'recording', 'release-group'):
            with self.subTest(entity=entity):
                result = dispatch(self.session, self.reg, f'album load https://musicbrainz.org/{entity}/{_MBID}')
                self.assertFalse(result.ok)
                self.assertIn(f'is a {entity}, not a release', result.error)
        self.assertEqual([], self._loaded)

    def test_load_invalid_is_failure(self):
        result = dispatch(self.session, self.reg, 'album load nope')
        self.assertFalse(result.ok)
        self.assertEqual([], self._loaded)

    def test_load_missing_arg_is_failure(self):
        self.assertFalse(dispatch(self.session, self.reg, 'album load').ok)

    def test_loaded_album_is_listable(self):
        dispatch(self.session, self.reg, f'album load {_MBID}')
        listing = dispatch(self.session, self.reg, 'ls a*')
        self.assertEqual(1, len(listing.items))
