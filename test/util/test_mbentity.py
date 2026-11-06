# Picard, the next-generation MusicBrainz tagger
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

from picard.util.mbentity import (
    MBEntityRef,
    parse_mb_entity,
)

import pytest


MBID = '0f1e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b'
CDTOC = 'Wn8eRBtfLDfM0qjYPdxrz.Zjs_U-'


@pytest.mark.parametrize(
    ('text', 'default', 'expected'),
    [
        (f'https://musicbrainz.org/release/{MBID}', None, ('release', MBID)),
        (f'https://musicbrainz.org/release/{MBID}/cover-art?x=1', None, ('release', MBID)),
        (f'https://musicbrainz.org/release-group/{MBID}', None, ('release-group', MBID)),
        (f'https://musicbrainz.org/recording/{MBID}', 'release', ('recording', MBID)),
        (f'release:{MBID}', None, ('release', MBID)),
        (f'  RELEASE:{MBID.upper()}  ', None, ('release', MBID)),
        (MBID, 'release', ('release', MBID)),
        (f'mbid://{MBID}', 'recording', ('recording', MBID)),
        (f'https://musicbrainz.org/cdtoc/{CDTOC}', None, ('cdtoc', CDTOC)),
    ],
)
def test_parse_mb_entity(text, default, expected):
    assert parse_mb_entity(text, default_entity=default) == MBEntityRef(*expected)


@pytest.mark.parametrize(
    'text',
    [
        '',
        'release',
        'not an mbid',
        # An MBID with no entity and no default says nothing about what it is.
        MBID,
        # One character short of an MBID.
        MBID[:-1],
    ],
)
def test_parse_mb_entity_nothing_found(text):
    assert parse_mb_entity(text) is None


def test_cdtoc_id_keeps_its_case():
    assert parse_mb_entity(f'cdtoc:{CDTOC}').id == CDTOC
