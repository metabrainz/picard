# -*- coding: utf-8 -*-
#
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.album import (
    Album,
    NatAlbum,
)
from picard.cluster import (
    Cluster,
    UnclusteredFiles,
)
from picard.file import File
from picard.track import Track

from picard.ui.infodialog import (
    AlbumInfoDialog,
    ClusterInfoDialog,
    FileInfoDialog,
    TrackInfoDialog,
)
from picard.ui.mainwindow import MainWindow


class GetInfoDialogTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    def test_album(self):
        album = MagicMock(spec=Album)
        result = MainWindow._get_info_dialog(album)
        self.assertEqual((AlbumInfoDialog, album), result)

    def test_nat_album(self):
        """NatAlbum is an Album subclass, should resolve to AlbumInfoDialog."""
        nat = MagicMock(spec=NatAlbum)
        result = MainWindow._get_info_dialog(nat)
        self.assertEqual((AlbumInfoDialog, nat), result)

    def test_cluster(self):
        cluster = MagicMock(spec=Cluster)
        result = MainWindow._get_info_dialog(cluster)
        self.assertEqual((ClusterInfoDialog, cluster), result)

    def test_unclustered_files(self):
        """UnclusteredFiles is a Cluster subclass, should resolve to ClusterInfoDialog."""
        unclustered = MagicMock(spec=UnclusteredFiles)
        result = MainWindow._get_info_dialog(unclustered)
        self.assertEqual((ClusterInfoDialog, unclustered), result)

    def test_track(self):
        track = MagicMock(spec=Track)
        result = MainWindow._get_info_dialog(track)
        self.assertEqual((TrackInfoDialog, track), result)

    def test_file(self):
        file = MagicMock(spec=File)
        with patch('picard.ui.mainwindow.iter_files_from_objects', return_value=iter([file])):
            result = MainWindow._get_info_dialog(file)
        self.assertEqual((FileInfoDialog, file), result)

    def test_file_list_with_files(self):
        """A FileList (or any non-standard object) extracts the first file."""
        file = MagicMock(spec=File)
        file_list = MagicMock()
        with patch('picard.ui.mainwindow.iter_files_from_objects', return_value=iter([file])):
            result = MainWindow._get_info_dialog(file_list)
        self.assertEqual((FileInfoDialog, file), result)

    def test_object_with_no_files(self):
        """Returns None for an object that yields no files."""
        obj = MagicMock()
        with patch('picard.ui.mainwindow.iter_files_from_objects', return_value=iter([])):
            result = MainWindow._get_info_dialog(obj)
        self.assertIsNone(result)
