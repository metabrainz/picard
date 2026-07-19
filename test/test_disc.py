# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2020-2022 Philipp Wolfer
# Copyright (C) 2021-2022 Laurent Monin
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


import unittest
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

import picard.disc
from picard.util.mbserver import ServerTuple


test_toc = [1, 11, 242457, 150, 44942, 61305, 72755, 96360, 130485, 147315, 164275, 190702, 205412, 220437]


class MockDisc:
    id = 'lSOVc5h6IXSuzcamJS1Gp4_tRuA-'
    mcn = '5029343070452'
    tracks = list(range(0, 11))
    toc_string = ' '.join(str(i) for i in test_toc)


def mock_disc_submission_url():
    return picard.disc.Disc._submission_url(MockDisc.id, len(MockDisc.tracks), MockDisc.toc_string)


class DiscTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.disc')

    def test_static_submission_url_no_config(self):
        with patch.object(
            picard.util.mbserver, 'get_submission_server', return_value=ServerTuple('example.com', 443)
        ) as mocked:
            self.assertEqual(
                picard.disc.Disc._submission_url('A', 2, 'B C'),
                'https://example.com/cdtoc/attach?id=A&tracks=2&toc=B+C',
            )
            mocked.assert_called_once()

    def test_static_submission_url(self):
        self.set_config_values(
            setting={
                'server_host': 'test.musicbrainz.org',
                'server_port': 80,
                'use_server_for_submission': True,
            }
        )
        self.assertEqual(
            picard.disc.Disc._submission_url('A', 2, 'B C'),
            'http://test.musicbrainz.org/cdtoc/attach?id=A&tracks=2&toc=B+C',
        )

    @unittest.skipUnless(picard.disc.discid, "discid not available")
    def test_raise_disc_error(self):
        disc = picard.disc.Disc()
        self.assertRaises(picard.disc.discid.DiscError, disc.read, 'notadevice')

    def test_init_with_id(self):
        discid = 'theId'
        disc = picard.disc.Disc(id=discid)
        self.assertEqual(discid, disc.id)
        self.assertEqual(0, disc.tracks)
        self.assertIsNone(disc.toc_string)
        self.assertIsNone(disc.submission_url)

    @patch.object(picard.disc, 'discid')
    def test_read(self, mock_discid):
        self.set_config_values(
            setting={
                'server_host': 'musicbrainz.org',
                'server_port': 443,
                'use_server_for_submission': False,
            }
        )
        mock_discid.read = Mock(return_value=MockDisc())
        device = '/dev/cdrom1'
        disc = picard.disc.Disc()
        self.assertEqual(None, disc.id)
        self.assertEqual(None, disc.mcn)
        self.assertEqual(0, disc.tracks)
        self.assertEqual(None, disc.toc_string)
        self.assertEqual(None, disc.submission_url)
        disc.read(device)
        mock_discid.read.assert_called_with(device, features=['mcn'])
        self.assertEqual(MockDisc.id, disc.id)
        self.assertEqual(MockDisc.mcn, disc.mcn)
        self.assertEqual(len(MockDisc.tracks), disc.tracks)
        self.assertEqual(MockDisc.toc_string, disc.toc_string)
        self.assertEqual(mock_disc_submission_url(), disc.submission_url)

    @patch.object(picard.disc, 'discid')
    def test_put(self, mock_discid):
        mock_discid.put = Mock(return_value=MockDisc())
        disc = picard.disc.Disc()
        disc.put(test_toc)
        self.assertEqual(MockDisc.id, disc.id)

    @patch.object(picard.disc, 'discid')
    def test_put_invalid_toc_1(self, mock_discid):
        mock_discid.TOCError = Exception
        disc = picard.disc.Disc()
        with self.assertRaises(mock_discid.TOCError):
            disc.put([1, 11])

    @patch.object(picard.disc, 'discid')
    def test_put_invalid_toc_2(self, mock_discid):
        mock_discid.TOCError = Exception
        mock_discid.put = Mock(side_effect=mock_discid.TOCError)
        disc = picard.disc.Disc()
        with self.assertRaises(mock_discid.TOCError):
            disc.put([1, 11, 242457])

    @patch.object(picard.disc, 'discid')
    def test_submission_url(self, mock_discid):
        self.set_config_values(
            setting={
                'server_host': 'test.musicbrainz.org',
                'server_port': 80,
                'use_server_for_submission': True,
            }
        )
        mock_discid.read = Mock(return_value=MockDisc())
        disc = picard.disc.Disc()
        disc.read()
        self.assertEqual(mock_disc_submission_url(), disc.submission_url)


class MockTrack:
    def __init__(self, number, isrc=None):
        self.number = number
        self.isrc = isrc


class MockDiscWithIsrcs:
    id = 'lSOVc5h6IXSuzcamJS1Gp4_tRuA-'
    mcn = '5029343070452'
    tracks = [
        MockTrack(1, 'USRC17607839'),
        MockTrack(2, 'GBAYE0000351'),
        MockTrack(3, None),
        MockTrack(4, 'FRZ039100014'),
    ]
    toc_string = ' '.join(str(i) for i in test_toc)


class MockDiscWithInvalidIsrcs:
    id = 'lSOVc5h6IXSuzcamJS1Gp4_tRuA-'
    mcn = None
    tracks = [
        MockTrack(1, 'USRC17607839'),
        MockTrack(2, 'INVALID'),
        MockTrack(3, ''),
        MockTrack(4, 'GBAYE0000351'),
    ]
    toc_string = ' '.join(str(i) for i in test_toc)


class MockDiscNoIsrcAttr:
    """Simulates disc tracks without isrc attribute (feature not available)."""

    id = 'lSOVc5h6IXSuzcamJS1Gp4_tRuA-'
    mcn = None
    tracks = list(range(0, 4))
    toc_string = ' '.join(str(i) for i in test_toc)


class DiscIsrcTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.disc')

    @patch.object(picard.disc, 'discid')
    def test_read_with_isrc_feature(self, mock_discid):
        self.set_config_values(
            setting={
                'server_host': 'musicbrainz.org',
                'server_port': 443,
                'use_server_for_submission': False,
            }
        )
        mock_discid.FEATURES = ['mcn', 'isrc']
        mock_discid.read = Mock(return_value=MockDiscWithIsrcs())
        device = '/dev/cdrom1'
        disc = picard.disc.Disc()
        disc.read(device)
        mock_discid.read.assert_called_with(device, features=['mcn', 'isrc'])
        self.assertEqual({1: 'USRC17607839', 2: 'GBAYE0000351', 4: 'FRZ039100014'}, disc.isrcs)

    @patch.object(picard.disc, 'discid')
    def test_read_without_isrc_feature(self, mock_discid):
        self.set_config_values(
            setting={
                'server_host': 'musicbrainz.org',
                'server_port': 443,
                'use_server_for_submission': False,
            }
        )
        mock_discid.FEATURES = ['mcn']
        mock_discid.read = Mock(return_value=MockDiscNoIsrcAttr())
        device = '/dev/cdrom1'
        disc = picard.disc.Disc()
        disc.read(device)
        mock_discid.read.assert_called_with(device, features=['mcn'])
        self.assertEqual({}, disc.isrcs)

    @patch.object(picard.disc, 'discid')
    def test_read_with_invalid_isrcs(self, mock_discid):
        self.set_config_values(
            setting={
                'server_host': 'musicbrainz.org',
                'server_port': 443,
                'use_server_for_submission': False,
            }
        )
        mock_discid.FEATURES = ['mcn', 'isrc']
        mock_discid.read = Mock(return_value=MockDiscWithInvalidIsrcs())
        device = '/dev/cdrom1'
        disc = picard.disc.Disc()
        disc.read(device)
        # Only valid ISRCs should be stored
        self.assertEqual({1: 'USRC17607839', 4: 'GBAYE0000351'}, disc.isrcs)

    def test_extract_isrcs_with_tracks(self):
        tracks = [
            MockTrack(1, 'US-RC1-76-07839'),
            MockTrack(2, 'gbaye0000351'),
            MockTrack(3, None),
        ]
        result = picard.disc.Disc._extract_isrcs(tracks)
        self.assertEqual({1: 'USRC17607839', 2: 'GBAYE0000351'}, result)

    def test_extract_isrcs_empty(self):
        result = picard.disc.Disc._extract_isrcs([])
        self.assertEqual({}, result)

    def test_extract_isrcs_no_attr(self):
        # Tracks without isrc attribute (like plain integers from old MockDisc)
        result = picard.disc.Disc._extract_isrcs([1, 2, 3])
        self.assertEqual({}, result)

    def test_isrcs_initialized_empty(self):
        disc = picard.disc.Disc()
        self.assertEqual({}, disc.isrcs)

    def test_extract_isrcs_duplicates_skipped(self):
        # Same ISRC on multiple tracks should be skipped (drive read error)
        tracks = [
            MockTrack(1, 'USRC17607839'),
            MockTrack(2, 'USRC17607839'),
            MockTrack(3, 'GBAYE0000351'),
        ]
        result = picard.disc.Disc._extract_isrcs(tracks)
        # Duplicate ISRC removed, unique one kept
        self.assertEqual({3: 'GBAYE0000351'}, result)
